# Study Runtime Orchestration

这份文档把 `MedAutoScience` 当前受控 study runtime orchestration 的最小稳定 contract 明确下来。

目标不是把 `study_runtime_router` 的每个内部 helper 都文档化，而是说明：

- 哪些入口是正式依赖面
- `study_runtime_status` / `ensure_study_runtime` 如何推进
- 哪些 typed surface 可以视为稳定机器接口
- 哪些内容仍属于实现细节，不应被其他模块或 Agent 当成正式 contract

在更高层定位上，这份文档描述的是 `MedAutoScience` 作为 `Research Ops` `Domain Harness OS` 时，runtime orchestration 这一层的最小稳定 contract，而不是整个 domain gateway 的全部语义。

与长期在线 supervision owner 相关的当前真相是：

- `Hermes-Agent`
  - 持有长期运行、调度与托管能力
- `MedAutoScience`
  - 持有 study/runtime supervision judgment、recovery policy 与前台 projection
- `MedDeepScientist`
  - 持有当前 concrete research execution

与 `stop / rerun / requires_human_confirmation` 相关的 outer-loop control semantics，现统一桥接到：

- [`./study_runtime_control_surface.md`](./study_runtime_control_surface.md)

与 `launch_report`、`runtime_escalation_record`、`publication_eval`、`study_decision_record` 以及 delivery/publication plane surface role 相关的 artifact 边界，现统一桥接到：

- [`./delivery_plane_contract_map.md`](./delivery_plane_contract_map.md)

## 与 study charter / startup projection 的关系

当前应按下面这条关系理解：

- `study_charter`
  - controller-owned authority artifact
- `startup_contract`
  - runtime-facing projection / transport object
- `startup_contract.study_charter_ref`
  - runtime 可稳定引用的最小 charter 投影
- `study_runtime_startup`
  - 负责从 controller truth 编译 startup projection
- `study_runtime_execution`
  - 在 create 路径 materialize durable charter，并校验 runtime-facing projection 一致性

这意味着：

- runtime orchestration 不拥有 `study_charter` authority
- runtime 也不应把 `startup_contract` 重新抬升成 study authority root
- 这层 controller 主要消费、传输、校验和回显 runtime-facing projection

## 作用域

当前实现分成八个清晰层次：

- [`src/med_autoscience/controllers/study_runtime_router.py`](../src/med_autoscience/controllers/study_runtime_router.py)
  - 作为 facade，保留正式入口 `study_runtime_status(...)` / `ensure_study_runtime(...)`
  - 负责把 read-model、execution orchestration 与少量入口 glue 收束成正式 controller 入口
- [`src/med_autoscience/controllers/study_runtime_types.py`](../src/med_autoscience/controllers/study_runtime_types.py)
  - 负责 typed surface：decision / reason / quest status enums，status object，以及 execution outcome wrappers
- [`src/med_autoscience/controllers/study_runtime_decision.py`](../src/med_autoscience/controllers/study_runtime_decision.py)
  - 负责 status read-model、decision state machine、quest runtime audit 收口
- [`src/med_autoscience/controllers/study_runtime_startup.py`](../src/med_autoscience/controllers/study_runtime_startup.py)
  - 负责 startup contract、create payload、overlay helper、startup hydration / context sync
- [`src/med_autoscience/controllers/study_runtime_completion.py`](../src/med_autoscience/controllers/study_runtime_completion.py)
  - 负责 study-level completion state 读取、completion request message 构造、completion sync
- [`src/med_autoscience/controllers/study_runtime_execution.py`](../src/med_autoscience/controllers/study_runtime_execution.py)
  - 负责 execution context、preflight、decision dispatch、create / resume / pause / completion orchestration，以及 runtime artifact persistence helper
- [`src/med_autoscience/controllers/study_runtime_resolution.py`](../src/med_autoscience/controllers/study_runtime_resolution.py)
  - 负责 study YAML 读取、study root / study id 解析，以及 execution payload 归一化
- [`src/med_autoscience/controllers/study_runtime_transport.py`](../src/med_autoscience/controllers/study_runtime_transport.py)
  - 负责 `managed_runtime_transport` 相关的 transport I/O seam，把 daemon 调用绑定收口为独立内部层
  - 薄层 consumer / test shim 至少可以通过 `managed_runtime_transport` 或 `managed_runtime_backend` 绑定默认 backend
  - `med_deepscientist_transport` 仍只作为兼容别名保留，避免旧测试和旧内部入口立即断裂
`study_runtime_router.py` 继续对外 re-export typed surface，并显式 re-export 仍被测试约束的私有 resolution / decision / startup / completion / execution / transport helper。
因此既有调用面和现有 router monkeypatch 边界，不需要因为模块化拆分而改导入或改测试策略。

当前 controller 侧对 `MedDeepScientist` 的最小稳定 transport 依赖，应收敛在显式 contract 上：

- quest create success 至少返回 `ok + snapshot.quest_id`
- quest control success 至少返回 `ok + quest_id + action + status + snapshot`
- startup-context patch success 至少返回 `ok + quest_id + snapshot`
- quest session 至少返回 `ok + quest_id + snapshot + runtime_audit`
- artifact completion success 至少返回 `ok + status + snapshot + summary_refresh`
- bash session 列表项至少包含 `bash_id + status`

对于会修改 runtime durable state 的 transport，当前主线额外固定：

- `PATCH /api/quests/{id}/startup-context` 只允许 daemon 单一路径写入
- `POST /api/quests/{id}/control` 的 `pause` / `stop` 只允许 daemon 单一路径写入
- daemon 不可达时，这些写入口直接 fail-closed
- 不再允许 controller 通过本地 quest YAML / runtime_state 文件做写旁路

对 `startup_contract` 的 authoritative ownership 也已明确：

- `MedDeepScientist` runtime-owned subset：
  - `schema_version`
  - `user_language`
  - `need_research_paper`
  - `decision_policy`
  - `launch_mode`
  - `standard_profile`
  - `custom_profile`
  - `baseline_execution_policy`
  - `review_followup_policy`
  - `manuscript_edit_mode`
- `MedAutoScience` controller-owned extensions：
  - `research_intensity`
  - `scope`
  - `baseline_mode`
  - `resource_policy`
  - `time_budget_hours`
  - `git_strategy`
  - `runtime_constraints`
  - `objectives`
  - `baseline_urls`
  - `paper_urls`
  - `entry_state_summary`
  - `review_summary`
  - `controller_first_policy_summary`
  - `automation_ready_summary`
  - `custom_brief`
  - `required_first_anchor`
  - `legacy_code_execution_allowed`
  - `startup_boundary_gate`
  - `runtime_reentry_gate`
  - `journal_shortlist`
  - `medical_analysis_contract_summary`
  - `medical_reporting_contract_summary`
  - `reporting_guideline_family`
  - `submission_targets`

这些 controller-owned extension 仍保持 flat `startup_contract` 形态；runtime 需要保证 durable persistence / stable echo / snapshot roundtrip，但不把它们升级成 runtime core authoritative schema。

对 `requested_baseline_ref` 的跨 repo 语义也应按两阶段理解：

- create-time (`POST /api/quests`)
  - 如果显式传入 `requested_baseline_ref`，成功返回表示 runtime 已经完成请求 baseline 的 materialization / confirmation，不能再把它当作“仅写 metadata”
- patch-time (`PATCH /api/quests/{id}/startup-context`)
  - 这里只允许更新 durable metadata 与 snapshot echo
  - 不能把 patch success 解释成 baseline 已 attach / confirm
- consumer 应显式检查 `snapshot.requested_baseline_ref` roundtrip，而不是假定 `baseline_gate` 已提升

对 quest completion approval，当前推荐 contract 也已升级为：

- 先通过 `artifact.interact(... reply_schema={decision_type: "quest_completion_approval"})` 创建 blocking approval request
- 再通过 `chat` 发送：
  - `reply_to_interaction_id`
  - `decision_response = {decision_type: "quest_completion_approval", approved: true}`
- runtime 现在要求 typed decision semantics；controller 不应再依赖纯文本批准词表完成 quest closure

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
- `runtime_summary_alignment`

约束：

- 核心字段缺失或改名，视为 contract break
- extras 可以按场景缺席，但已有键名不应悄悄改名
- extras 的出现条件应通过测试显式约束

summary truth 约束：

- `study_runtime_status(...)` 是 runtime 真相读取面
- `last_launch_report.json` 是 workspace summary，不是 runtime truth source
- 当直接 status 查询发现 summary 与当前 quest status 漂移时，允许 controller 用正式 persistence helper 刷新该 summary
- 这种刷新不触发 transport，也不改变 runtime 本体

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

## Future work-unit / route-unit attempt contract

本节把可复用的 runtime 编排经验医学化为 `MAS` 后续 external worker / hosted runtime 的 contract；它不改变当前 `Codex-default host-agent runtime` 的执行语义，也不要求当前 host-agent path 立即引入外部 scheduler。

### Attempt 状态机

未来每个 `work-unit / route-unit attempt` 至少要有单义状态机：

| 状态 | MAS 语义 |
| --- | --- |
| `unclaimed` | work-unit / route-unit 已由 controller 或 orchestrator 生成，但尚未分配给具体 worker；不得产生研究写入。 |
| `claimed` | 受控 worker 已领取该 unit，并记录 `claim_owner`、`workspace_root`、`root`、`cwd` 与 `attempt_count`；此时仍未进入 compute。 |
| `running` | 当前 `run_attempt_phase` 已进入 live compute / analysis / writeback / gate-repair 等具体阶段；每次进入新的 run attempt 必须递增或固定记录 `attempt_count`。 |
| `retry_queued` | MAS 对 retry queued 的等价命名；上一次 attempt 因可恢复失败、stalled detection 或外部 runtime 中断进入 bounded retry；必须记录 `failure_reason`、`backoff_until`、剩余 retry budget 与上一次 `run_attempt_phase`。 |
| `released` | 当前 owner 已释放 unit；可以是完成后的非活跃状态、terminal 状态后的审计保留，或 retry budget 用尽后的 controller 重新裁决入口。 |

`run_attempt_phase` 是 run attempt phase 的机器字段；`attempt_count` 是 attempt 计数；`failure_reason` 是 failure reason。三者都是 attempt-level machine field，不得由 dashboard、logs 或 issue tracker 反推生成。`attempt_count` 表示受控 runtime 尝试次数，不等同于 study revision 次数、paper route 次数或 publication gate 重放次数。`failure_reason` 必须保留可审计的失败类别，例如 `workspace_boundary_violation`、`runtime_stalled`、`terminal_non_active`、`transport_failure`、`controller_gate_blocked`；不得用自由文本替代结构化 reason。

### Workspace isolation

future external worker / hosted runtime 执行每个 study/work-unit 时，必须绑定受控 `workspace_root` / `root` / `cwd`，并在 attempt record 中持久化。所有可写路径必须位于该受控 root 下，任何路径越界、symlink 越界、相对路径逃逸或跨 study root 写入都必须 fail-closed，并把 `failure_reason` 写成 `workspace_boundary_violation`。

这条 workspace isolation 规则只约束未来 external worker / hosted runtime。当前 `Codex-default host-agent runtime` 仍按现有 controller + host-agent 工作方式运行，不因为本节新增 work-unit contract 而改变 CLI、MCP、product-entry 或当前 Codex path 的默认执行模型。

### Retry / backoff / reconciliation

future orchestrator 可以使用 retry/backoff/reconciliation 恢复 runtime 可用性，但不能改变 study authority。

稳定语义如下：

- `running state refresh`：active attempt 必须周期性刷新 runner 状态、last heartbeat、active process / session evidence 与当前 `run_attempt_phase`。
- `terminal/non-active handling`：一旦 worker 返回 completed、failed、cancelled、stopped 或 non-active，orchestrator 必须停止把它视为 live writer，并进入 `released`、`retry_queued` 或 controller gate，而不是继续投影为 running。
- `stalled detection`：heartbeat 过期、active_run_id 无刷新、进程证据缺失或工作区长期无可解释变更时，只能触发受控 reconciliation；不得直接写 paper truth 或 publication authority。
- `bounded retry`：每个 work-unit / route-unit 必须有显式 retry budget、backoff policy 与最后一次 `failure_reason`；超过预算后进入 controller-owned review / gate，而不是无限重启。

retry/backoff 是恢复策略，不是研究裁决策略。它只能帮助同一 controller-approved work-unit 回到可执行状态；不能创建新的 study truth、不能覆盖 `study_charter`、不能绕过 `publication_eval/latest.json` 或 `controller_decisions/latest.json`。

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
- `RELAUNCH_STOPPED`
  - quest 已处于 `stopped`，且 caller 已显式批准 stopped-quest relaunch
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

补充边界：

- `stop` **不是** `StudyRuntimeDecision` 的一部分；它属于 outer-loop controller action surface，见 `./study_runtime_control_surface.md`
- 一旦 quest 进入 `stopped`，当前 P1 contract 下：
  - `study_runtime_status(...)` 必须返回 `BLOCKED`
  - reason 固定为 `quest_stopped_requires_explicit_rerun`
  - `ensure_study_runtime(...)` 不得自动把 stopped quest 当成 resumable 状态
  - 只有显式 `allow_stopped_relaunch=true` 才允许把它改写为 `RELAUNCH_STOPPED`

## Preflight contract

`ensure_study_runtime(...)` 在真正执行 transport 前，会先跑 `_run_runtime_preflight(...)`。
这条 preflight 链当前由 `study_runtime_execution.py` 承担，router 只保留正式入口 glue。

当前最小稳定 preflight 规则：

- 对 `CREATE_AND_START` / `CREATE_ONLY` / `RESUME` / `RELAUNCH_STOPPED`
  - 必须先确认 analysis bundle ready
  - 如果 runtime reentry 要求 managed skill audit，则 profile 必须允许 medical overlay
  - 对 `RESUME` / `RELAUNCH_STOPPED`，如果启用了 medical overlay，必须先确保 overlay roots ready
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
- stopped relaunch 路径
  - controller 先把 blocked stopped 状态改写为 `RELAUNCH_STOPPED`
  - transport 仍复用 daemon `resume_quest(...)`
  - 但 runtime binding / launch report 的 `last_action` 必须写成 `relaunch_stopped`
- blocked refresh 路径
  - 只在特定 blocked 场景下刷新 startup context / hydration
  - 不触发 resume
- pause 路径
  - 只调用 `pause_quest(...)`
- completion 路径
  - `PAUSE_AND_COMPLETE` 会先 pause
  - 随后统一走 completion sync，并把 decision 最终收敛到 `COMPLETED`

这条执行链当前由 `study_runtime_execution.py` 承担；具体 daemon transport 调用已经下沉到 `study_runtime_transport.py`，router 上同名私有 helper 只是 facade re-export / monkeypatch seam，不应被误认为独立 contract 层。

## Artifact persistence contract

`ensure_study_runtime(...)` 在执行结束后，始终会通过 execution helper 调用 `persist_runtime_artifacts(...)`。

这一步属于稳定 contract，因为上层依赖这些 artifact 作为可审计真相，包括：

- runtime binding
- launch report
- startup payload path
- last action
- 序列化后的 status payload
- daemon result

也就是说，即使最终 decision 是 `BLOCKED` 或 `NOOP`，只要进入了受控 orchestration，artifact 落盘仍是正式行为的一部分。

当前实现上，这条 persistence 链仍由 `study_runtime_execution.py` 决定时机；具体 transport I/O 已经下沉到 `study_runtime_transport.py`，router 上对应的 helper 只是 facade seam，用来保持现有 monkeypatch / topology 兼容语义。

## 当前明确不属于稳定面的内容

以下内容当前仍视为实现细节，不应被其他模块直接绑定：

- `_status_state(...)`、`_run_runtime_preflight(...)`、`_execute_*` 等私有 helper 名称
- `_load_yaml_dict(...)`、`_resolve_study(...)`、`_execution_payload(...)` 等 resolution 细节
- `_build_execution_context(...)`、`_build_context_create_payload(...)`、`_persist_runtime_artifacts(...)` 等 execution/orchestration 细节
- `_create_quest(...)`、`_resume_quest(...)`、`_pause_quest(...)`、`_inspect_quest_live_execution(...)` 等 transport seam 细节
- `study_runtime_resolution.py` / `study_runtime_decision.py` / `study_runtime_startup.py` / `study_runtime_completion.py` / `study_runtime_execution.py` / `study_runtime_transport.py` 内部尚未升级成 spec 的组装细节
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
- router topology tests 约束 router facade 继续 re-export 已拆分的 resolution / decision / startup / completion / execution / transport helper（包括 persistence seam），并守住 patch-through 兼容语义
- runtime protocol topology tests 约束 runtime layout / path contract
- workspace contract tests 约束 orchestration 依赖的 workspace readiness 前提

后续如果新增 decision、extra key、typed symbol 或 execution phase，应先更新这份文档，再补对应测试。
