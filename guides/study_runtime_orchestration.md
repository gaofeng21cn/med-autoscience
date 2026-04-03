# Study Runtime Orchestration

这份文档把 `MedAutoScience` 当前受控 study runtime orchestration 的最小稳定 contract 明确下来。

目标不是把 `study_runtime_router` 的每个内部 helper 都文档化，而是说明：

- 哪些入口是正式依赖面
- `study_runtime_status` / `ensure_study_runtime` 如何推进
- 哪些 typed surface 可以视为稳定机器接口
- 哪些内容仍属于实现细节，不应被其他模块或 Agent 当成正式 contract

## 作用域

当前实现分成四个清晰层次：

- [`src/med_autoscience/controllers/study_runtime_router.py`](../src/med_autoscience/controllers/study_runtime_router.py)
  - 作为 facade，保留正式入口 `study_runtime_status(...)` / `ensure_study_runtime(...)`
  - 持有决策推进、preflight、transport orchestration 与 runtime artifact 落盘主干
- [`src/med_autoscience/controllers/study_runtime_types.py`](../src/med_autoscience/controllers/study_runtime_types.py)
  - 负责 typed surface：decision / reason / quest status enums，status object，以及 execution outcome wrappers
- [`src/med_autoscience/controllers/study_runtime_startup.py`](../src/med_autoscience/controllers/study_runtime_startup.py)
  - 负责 startup contract、create payload、overlay helper、startup hydration / context sync
- [`src/med_autoscience/controllers/study_runtime_completion.py`](../src/med_autoscience/controllers/study_runtime_completion.py)
  - 负责 study-level completion state 读取、completion request message 构造、completion sync
`study_runtime_router.py` 继续对外 re-export typed surface，并显式 re-export 仍被测试约束的私有 startup / completion helper。
因此既有调用面和现有 router monkeypatch 边界，不需要因为模块化拆分而改导入或改测试策略。

## 正式入口

当前正式入口只有两个：

- `study_runtime_status(...)`
  - 只读，返回序列化后的 `StudyRuntimeStatus`
- `ensure_study_runtime(...)`
  - 读状态、跑 preflight、按决策执行 transport，并最终返回序列化后的 `StudyRuntimeStatus`

两者都接受：

- `profile: WorkspaceProfile`
- `study_id` 或 `study_root` 之一
- 可选 `entry_mode`

`ensure_study_runtime(...)` 额外接受：

- `force`
- `source`

正式调用方应把这两个入口视为 controller contract，而不是直接拼 transport payload 或直接调用 `MedDeepScientist` runtime。

## 稳定 typed surface

以下 typed symbols 现在属于稳定机器接口的一部分：

- `StudyRuntimeDecision`
- `StudyRuntimeReason`
- `StudyRuntimeQuestStatus`
- `StudyRuntimeBindingAction`
- `StudyRuntimeDaemonStep`
- `StudyRuntimeAuditStatus`
- `StudyRuntimeAuditRecord`
- `StudyRuntimeAnalysisBundleResult`
- `StudyRuntimeOverlayAudit`
- `StudyRuntimeOverlayResult`
- `StudyRuntimeStartupContextSyncResult`
- `StudyRuntimePartialQuestRecoveryResult`
- `StudyRuntimeWorkspaceContractsSummary`
- `StudyRuntimeStartupDataReadinessReport`
- `StudyRuntimeStartupBoundaryGate`
- `StudyRuntimeReentryGate`
- `StudyCompletionSyncResult`
- `StudyRuntimeStatus`
- `StudyRuntimeExecutionContext`
- `StudyRuntimeExecutionOutcome`

这些类型现在定义在 `study_runtime_types.py`，并由 `study_runtime_router.py` 原样 re-export。

约束如下：

- 新增字段或 enum 值时，必须同步补测试
- 如果要移动定义位置，必须继续保持 router re-export 不变
- 不能让外部调用方只能靠未文档化的 dict 细节才能驱动 controller

## 返回 payload 的最小稳定面

两个正式入口都返回 `StudyRuntimeStatus.to_dict()` 的结果。

核心字段包括：

- `schema_version`
- `study_id`
- `study_root`
- `entry_mode`
- `execution`
- `quest_id`
- `quest_root`
- `quest_exists`
- `quest_status`
- `runtime_binding_path`
- `runtime_binding_exists`
- `workspace_contracts`
- `startup_data_readiness`
- `startup_boundary_gate`
- `runtime_reentry_gate`
- `study_completion_contract`
- `controller_first_policy_summary`
- `automation_ready_summary`
- `decision`
- `reason`

附加字段按场景出现，当前允许的 orchestration extras 包括：

- `startup_contract_validation`
- `analysis_bundle`
- `runtime_overlay`
- `startup_context_sync`
- `partial_quest_recovery`
- `startup_hydration`
- `startup_hydration_validation`
- `completion_sync`
- `bash_session_audit`
- `runtime_liveness_audit`
- `launch_report_path`
- `startup_payload_path`

约束：

- 核心字段缺失或改名，视为 contract break
- extras 可以按场景缺席，但已有键名不应悄悄改名
- extras 的出现条件应通过测试显式约束

## 状态推进顺序

`study_runtime_status(...)` 的决策顺序当前固定为：

1. 解析 `study.yaml` 与 execution payload
2. 解析现有 quest runtime 状态
3. 汇总 workspace contracts、startup data readiness、startup boundary、runtime reentry、study completion state
4. 判断是否属于 lightweight 路径
5. 判断 study completion 是否已经 ready
6. 判断 workspace / data readiness / startup contract resolution 是否允许推进
7. 结合 quest 是否存在、是否 live、是否 resumable，给出最终 decision / reason

也就是说，`study_runtime_status(...)` 不是“把若干 dict 拼起来”，而是一个确定性的状态机读面。

## 决策分层

当前 decision 分三类：

- 只读或轻量类
  - `LIGHTWEIGHT`
  - `NOOP`
  - `COMPLETED`
- 阻塞类
  - `BLOCKED`
  - `CREATE_ONLY`
- 需要 runtime mutation 的执行类
  - `CREATE_AND_START`
  - `RESUME`
  - `PAUSE`
  - `SYNC_COMPLETION`
  - `PAUSE_AND_COMPLETE`

稳定语义如下：

- `LIGHTWEIGHT`
  - 当前 study 不属于 managed runtime 路径，不应触发 transport 调用
- `BLOCKED`
  - 当前 study 属于 managed 路径，但存在明确 gate 阻塞
- `CREATE_ONLY`
  - 允许创建 quest，但暂不允许进入 compute stage
- `CREATE_AND_START`
  - 允许创建 quest 并立刻恢复为 running
- `RESUME`
  - quest 已存在且满足恢复条件
- `PAUSE`
  - 现有 live runtime 不再满足运行条件，必须收回到 paused
- `SYNC_COMPLETION`
  - completion contract 已 ready，且无需先 pause
- `PAUSE_AND_COMPLETE`
  - completion contract 已 ready，但 live runtime 需要先 pause 再 completion sync
- `NOOP`
  - quest 已 live 且所有 gate 允许继续运行
- `COMPLETED`
  - 当前 study 已视为完成，不再需要新的 runtime 动作

## Preflight contract

`ensure_study_runtime(...)` 在真正执行 transport 前，会先跑 `_run_runtime_preflight(...)`。

当前最小稳定 preflight 规则：

- 对 `CREATE_AND_START` / `CREATE_ONLY` / `RESUME`
  - 必须先确认 analysis bundle ready
  - 如果 runtime reentry 要求 managed skill audit，则 profile 必须允许 medical overlay
  - 对 `RESUME`，如果启用了 medical overlay，必须先确保 overlay roots ready
- 对已有 quest 的非创建路径
  - 如果启用了 medical overlay，会做 overlay audit
  - 对 live quest，如果 overlay audit 失败，会把 decision 改写为 `PAUSE`

这意味着 `study_runtime_status(...)` 给出的 decision 还不是最终执行动作；
`ensure_study_runtime(...)` 可以在 preflight 后把 decision 收窄成更保守但更正确的动作。

## 执行 contract

当前执行阶段固定遵守这些规则：

- create 路径
  - 始终先 `create_quest(auto_start=False)`
  - 若目标是 `CREATE_AND_START`，再显式调用一次 `resume_quest(...)`
- resume 路径
  - 先同步 startup context
  - 再执行 startup hydration 与 validation
  - hydration clear 后才允许 `resume_quest(...)`
- blocked refresh 路径
  - 只在特定 blocked 场景下刷新 startup context / hydration
  - 不触发 resume
- pause 路径
  - 只调用 `pause_quest(...)`
- completion 路径
  - `PAUSE_AND_COMPLETE` 会先 pause
  - 随后统一走 completion sync，并把 decision 最终收敛到 `COMPLETED`

## Artifact persistence contract

`ensure_study_runtime(...)` 在执行结束后，始终会调用 `persist_runtime_artifacts(...)`。

这一步属于稳定 contract，因为上层依赖这些 artifact 作为可审计真相，包括：

- runtime binding
- launch report
- startup payload path
- last action
- 序列化后的 status payload
- daemon result

也就是说，即使最终 decision 是 `BLOCKED` 或 `NOOP`，只要进入了受控 orchestration，artifact 落盘仍是正式行为的一部分。

## 当前明确不属于稳定面的内容

以下内容当前仍视为实现细节，不应被其他模块直接绑定：

- `_status_state(...)`、`_run_runtime_preflight(...)`、`_execute_*` 等私有 helper 名称
- `study_runtime_startup.py` / `study_runtime_completion.py` 内部尚未升级成 spec 的组装细节
- overlay materialization payload 的完整内部结构
- analysis bundle payload 的完整内部结构
- runtime audit payload 中未被 typed wrapper 明确收口的自由字段
- 各类 report JSON 的全文 schema

如果未来这些内容也要被跨模块依赖，应先升级成显式 spec，再允许成为正式 contract。

## 回归测试锚点

当前这份 spec 主要由以下测试约束：

- [`tests/test_study_runtime_router.py`](../tests/test_study_runtime_router.py)
- [`tests/test_study_runtime_router_topology.py`](../tests/test_study_runtime_router_topology.py)
- [`tests/test_runtime_protocol_topology.py`](../tests/test_runtime_protocol_topology.py)
- [`tests/test_workspace_contracts.py`](../tests/test_workspace_contracts.py)

其中：

- router tests 约束 decision、typed surface、preflight 和 execution behavior
- router topology tests 约束 router facade 继续 re-export 已拆分的 startup / completion helper
- runtime protocol topology tests 约束 runtime layout / path contract
- workspace contract tests 约束 orchestration 依赖的 workspace readiness 前提

后续如果新增 decision、extra key、typed symbol 或 execution phase，应先更新这份文档，再补对应测试。
