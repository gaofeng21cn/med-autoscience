# Study Runtime Orchestration

Owner: `MedAutoScience domain runtime control`
Purpose: `study_runtime_orchestration_contract`
State: `active_runtime_control_support`
Machine boundary: 本文是人读 runtime control contract。MAS 机器真相归 controller/domain-authority refs surfaces、CLI/MCP/API payload、owner receipt、controller durable domain artifacts、contracts 和真实 workspace evidence；provider、queue、attempt、runner 与 current-control-state 真相归 OPL Framework。

这份文档把 `MedAutoScience` 当前 domain runtime-facing refs 与 OPL runtime-control handoff 的最小稳定 contract 明确下来。

目标不是把 `study_runtime_router` 的每个内部 helper 都文档化，而是说明：

- 哪些入口是正式依赖面
- `progress_projection` / `request_opl_stage_attempt` 如何读取 MAS domain refs 并交给 OPL runtime-control owner
- 哪些 typed surface 可以视为稳定机器接口
- 哪些内容仍属于实现细节，不应被其他模块或 Agent 当成正式 contract

在更高层定位上，这份文档描述的是 `MedAutoScience` 作为独立 medical research domain agent 的 runtime orchestration 最小稳定 contract，而不是整个 domain agent 的全部语义。

与长期在线 supervision owner 相关的当前真相是：

- `OPL framework provider`
  - 持有 Full online path 的长期运行、调度与托管能力；Temporal-backed provider 是生产路径，`hermes_agent` 只作为显式非默认 executor/proof lane 出现
- `MedAutoScience`
  - 持有 study/runtime domain supervision judgment、recovery policy、owner receipt、typed blocker 与前台 domain refs projection；不持有 provider、queue、attempt、runner 或 current-control-state 控制面
- `Codex CLI`
  - 是 MAS stage 内默认 concrete executor 和最小执行单元

与 `stop / rerun / requires_human_confirmation` 相关的 outer-loop control semantics，现统一桥接到：

- [`./study_runtime_control_surface.md`](./study_runtime_control_surface.md)

与 `publication_supervisor_state`、publication gate、task intake、controller authorization 和 runtime liveness 如何转换成 `route_target` / `next_work_unit` / `controller_action` 相关的正式语义，必须按 MAS-owned domain transition table 理解。当前代码仍有多个实现入口，但 contract 目标是集中、可测试、可由 transition matrix 验证的 domain table。OPL 可以承载通用 state-machine runner、attempt/retry/human-gate/dispatch receipt 等框架能力；MAS 仍持有医学 domain transition table，不能把 publication gate、AI reviewer judgement、submission authority 或 claim/evidence/display blocker 的解释交给 OPL。

与 `launch_report`、`runtime_escalation_record`、`publication_eval`、`study_decision_record` 以及 delivery/publication plane surface role 相关的 artifact 边界，现统一桥接到：

- [`../contracts/delivery_plane_contract_map.md`](../contracts/delivery_plane_contract_map.md)

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

当前历史实现曾分成八个层次；本 physical-retirement lane 只把它们作为 provenance、diagnostic reader 或 domain-authority refs 来源读取：

- [`src/med_autoscience/controllers/study_runtime_router.py`](../../../src/med_autoscience/controllers/study_runtime_router.py)
  - 作为 historical diagnostic reader，保留 `progress_projection(...)` / `request_opl_stage_attempt(...)` 的读取和 owner-route refs 投影语义
  - 不再是 MAS 私有 provider、queue、attempt、resume/relaunch 或 lifecycle 控制面
- [`src/med_autoscience/controllers/study_runtime_types.py`](../../../src/med_autoscience/controllers/study_runtime_types.py)
  - 负责 typed surface：decision / reason / quest status enums，status object，以及 execution outcome wrappers
- [`src/med_autoscience/controllers/study_runtime_decision.py`](../../../src/med_autoscience/controllers/study_runtime_decision.py)
  - 负责 status read-model、decision state machine、quest runtime audit 收口
- [`src/med_autoscience/controllers/study_runtime_startup.py`](../../../src/med_autoscience/controllers/study_runtime_startup.py)
  - 负责 startup contract、create payload、overlay helper、startup hydration / context sync
- [`src/med_autoscience/controllers/study_runtime_completion.py`](../../../src/med_autoscience/controllers/study_runtime_completion.py)
  - 负责 study-level completion state 读取、completion request message 构造、completion sync
- [`src/med_autoscience/controllers/study_runtime_execution.py`](../../../src/med_autoscience/controllers/study_runtime_execution.py)
  - 仅作为历史 execution contract 与迁移输入读取；当前可持续 runtime mutation、attempt、resume/relaunch、pause/stop 和 current-control-state 归 OPL runtime owner
- [`src/med_autoscience/controllers/study_runtime_resolution.py`](../../../src/med_autoscience/controllers/study_runtime_resolution.py)
  - 负责 study YAML 读取、study root / study id 解析，以及 execution payload 归一化
- historical managed-runtime transport consumer refs
  - 只作为 retired provenance 与 domain authority handoff refs 语境读取；通用 runtime transport 已归 OPL provider-backed stage runtime
  - 薄层 consumer / test-only patch target 只能绑定 MAS DomainIntent、owner receipt、typed blocker、domain authority refs 或 OPL provider backend contract；不能把任何 MAS-local transport/backend 名称写成 generic default backend owner
  - 旧 MDS transport alias 与 MAS-local transport alias 均已退役；controller / router / test patch target 必须绑定 OPL provider backend、DomainIntent refs 或 owner receipt/typed blocker，不再使用 MAS 私有 transport alias
`study_runtime_router.py` 继续对外 re-export typed surface，并显式 re-export 仍被测试约束的私有 resolution / decision / startup / completion / execution / transport helper。
因此既有调用面和现有 router monkeypatch 边界，不需要因为模块化拆分而改导入或改测试策略。

历史 controller 侧对 managed runtime backend 的 transport 依赖只作为 retired provenance / OPL handoff 输入保留；当前不能把这些返回形态重新声明为 MAS-owned backend contract：

- quest create success 至少返回 `ok + snapshot.quest_id`
- quest control success 至少返回 `ok + quest_id + action + status + snapshot`
- startup-context patch success 至少返回 `ok + quest_id + snapshot`
- quest session 至少返回 `ok + quest_id + snapshot + runtime_audit`
- artifact completion success 至少返回 `ok + status + snapshot + summary_refresh`
- bash session 列表项至少包含 `bash_id + status`

对于会修改 runtime durable state 的 transport，当前主线额外固定：

- `PATCH /api/quests/{id}/startup-context` 只允许 OPL runtime owner route 写入；MAS 只提供 controller authorization、DomainIntent 和 domain refs
- `POST /api/quests/{id}/control` 的 `pause` / `stop` 只允许 OPL runtime owner route 写入；MAS 只签 domain receipt 或 typed blocker
- OPL provider/current-control-state 不可达时，这些写入口直接 fail-closed
- 不再允许 controller 通过本地 quest YAML / runtime_state 文件做写旁路

对 `startup_contract` 的 authoritative ownership 也已明确：

- MAS domain authority-owned subset：
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

这些 controller-owned extension 仍保持 flat `startup_contract` 形态；runtime 需要保证 durable persistence / stable echo / snapshot roundtrip，但不把它们升级成 runtime core authoritative schema。旧 MDS/DeepScientist 对这些字段的命名与回显行为只作为 provenance、parity oracle 或 explicit archive import reference 保留。

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

## Domain Refs 入口

当前 MAS-facing 入口只有两个 domain refs / diagnostic reader：

- `progress_projection(...)`
  - 只读，返回序列化后的 `ProgressProjectionStatus`，不得写 OPL runtime truth
- `request_opl_stage_attempt(...)`
  - 读状态、跑 MAS domain preflight，输出 controller authorization、owner-route handoff、owner receipt 或 typed blocker；不得直接执行 provider resume/relaunch、queue hydration、attempt retry 或 MAS 私有 lifecycle mutation

两者都接受：

- `profile: WorkspaceProfile`
- `study_id` 或 `study_root` 之一
- 可选 `entry_mode`

`request_opl_stage_attempt(...)` 额外接受：

- `force`
- `source`

正式调用方应把这两个入口视为 MAS domain refs contract，而不是直接拼 transport payload、直接调用 managed runtime backend，或把历史 transport helper 当当前控制面。旧 `MedDeepScientist` runtime 只作为 frozen source archive、historical fixture、explicit archive import、backend audit 或 parity oracle reference 出现。

2026-05-21 owner-route 边界补充：`request_opl_stage_attempt(...)` 仍是 MAS direct diagnostic / controller contract，但不能被新的 domain-route repair 当成 MAS 私有 provider resume、queue hydration、attempt retry 或 relaunch owner。stopped / failed / no-live / waiting-owner 这类通用运行恢复，现在由 MAS 写出 controller authorization、owner-route handoff、owner receipt 或 typed blocker，再交给 OPL runtime manager 承担 generic liveness、queue、attempt、retry/dead-letter 和 provider resume/relaunch；OPL dispatch 回 MAS 后，MAS 再执行 domain owner callable 或签收 blocker。

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
- `ProgressProjectionStatus`
- `StudyRuntimeExecutionContext`
- `StudyRuntimeExecutionOutcome`

这些类型现在定义在 `study_runtime_types.py`，并由 `study_runtime_router.py` 原样 re-export。

约束如下：

- 新增字段或 enum 值时，必须同步补测试
- 如果要移动定义位置，必须继续保持 router re-export 不变
- 不能让外部调用方只能靠未文档化的 dict 细节才能驱动 controller

## 返回 payload 的最小稳定面

两个正式入口都返回 `ProgressProjectionStatus.to_dict()` 的结果。

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
- `runtime_health_snapshot`
- `runtime_health_epoch`
- `launch_report_path`
- `startup_payload_path`
- `runtime_summary_alignment`

约束：

- 核心字段缺失或改名，视为 contract break
- extras 可以按场景缺席，但已有键名不应悄悄改名
- extras 的出现条件应通过测试显式约束

summary truth 约束：

- `progress_projection(...)` 是 runtime 真相读取面
- `last_launch_report.json` 是 workspace summary，不是 runtime truth source
- `artifacts/runtime/health/latest.json` 是 reducer-owned runtime health read model；普通 `progress_projection` 只内嵌 shadow snapshot，不刷新该文件
- 当直接 status 查询发现 summary 与当前 quest status 漂移时，允许 controller 用正式 persistence helper 刷新该 summary
- 这种刷新不触发 transport，也不改变 runtime 本体

## 状态推进顺序

`progress_projection(...)` 的决策顺序当前固定为：

1. 解析 `study.yaml` 与 execution payload
2. 解析现有 quest runtime 状态
3. 汇总 workspace contracts、startup data readiness、startup boundary、runtime reentry、study completion state
4. 判断是否属于 lightweight 路径
5. 判断 study completion 是否已经 ready
6. 判断 workspace / data readiness / startup contract resolution 是否允许推进
7. 结合 quest 是否存在、是否 live、是否 resumable，给出最终 decision / reason

也就是说，`progress_projection(...)` 不是“把若干 dict 拼起来”，而是一个确定性的状态机读面。

## Transition Table 与 OPL Framework 边界

当前 runtime orchestration 有两层状态机，不能混成一个 owner：

- OPL/framework generic state machine：stage attempt、provider abstraction、queue/wakeup、retry/dead-letter、human gate signal/query、attempt receipt、dispatch receipt、transition matrix runner、shared lifecycle/index/restore primitives。
- MAS domain transition table：study truth、publication gate、AI reviewer、paper quality、submission authority、artifact/package authority、domain owner route、`decision_type`、`route_target`、`next_work_unit` 和 `controller_action`。

因此，集中表是目标，但集中表的 owner 是 MAS domain table。OPL 后续可以提供统一 runner 和 schema，让 MAS/MAG/RCA 以 domain spec 的方式接入；OPL 不持有 MAS 的医学状态含义，也不能根据 OPL 自己的状态字段直接决定某篇论文是否 publishable、是否进入 finalize、是否刷新 package 或是否关闭 AI reviewer gate。

任何新增 MAS transition 都应同时落三件事：

1. domain transition table/spec 中的输入、guard、输出和 fail-closed reason。
2. table-driven matrix test，覆盖正向转换和至少一个相邻误转场景。
3. controller decision / runtime authorization 的 receipt 字段，保证 executor 看到的是同一个 `route_target`、`next_work_unit` 和 fingerprint。

## OPL work-unit / route-unit attempt refs contract

本节把可复用的 runtime 编排经验收口为 OPL provider attempt refs contract。MAS 只声明 work-unit / route-unit 的 domain refs、owner receipt、typed blocker、artifact/source/quality refs 和 no-forbidden-write 约束；OPL 承载 external worker、hosted runtime、scheduler、attempt registry、retry/backoff 和 operator projection。它不改变当前 `Codex-default host-agent runtime` 的执行语义，也不要求当前 host-agent path 立即引入外部 scheduler。

### Attempt 状态机

未来每个 `work-unit / route-unit attempt` 至少要有单义状态机：

| 状态 | OPL runtime/control 语义 |
| --- | --- |
| `unclaimed` | work-unit / route-unit 已由 controller 或 orchestrator 生成，但尚未分配给具体 worker；不得产生研究写入。 |
| `claimed` | 受控 worker 已领取该 unit，并记录 `claim_owner`、`workspace_root`、`root`、`cwd` 与 `attempt_count`；此时仍未进入 compute。 |
| `running` | 当前 `run_attempt_phase` 已进入 live compute / analysis / writeback / gate-repair 等具体阶段；每次进入新的 run attempt 必须递增或固定记录 `attempt_count`。 |
| `retry_queued` | OPL retry queued 状态；上一次 attempt 因可恢复失败、stalled detection 或外部 runtime 中断进入 bounded retry；必须记录 `failure_reason`、`backoff_until`、剩余 retry budget 与上一次 `run_attempt_phase`。MAS 只消费 failure refs 并返回 domain receipt 或 typed blocker。 |
| `released` | 当前 owner 已释放 unit；可以是完成后的非活跃状态、terminal 状态后的审计保留，或 retry budget 用尽后的 controller 重新裁决入口。 |

`run_attempt_phase` 是 run attempt phase 的机器字段；`attempt_count` 是 attempt 计数；`failure_reason` 是 failure reason。三者都是 attempt-level machine field，不得由 dashboard、logs 或 issue tracker 反推生成。`attempt_count` 表示受控 runtime 尝试次数，不等同于 study revision 次数、paper route 次数或 publication gate 重放次数。`failure_reason` 必须保留可审计的失败类别，例如 `workspace_boundary_violation`、`runtime_stalled`、`terminal_non_active`、`transport_failure`、`controller_gate_blocked`；不得用自由文本替代结构化 reason。

当前 repo-side 机器合同由 `work_unit_runtime_attempt_record` 表达为 OPL-owned runtime registry / observability ref。该 record 至少固定 `program_id`、`study_id`、`quest_id`、`active_run_id`、`work_unit_id`、`route_id`、`attempt_state`、`attempt_count`、`run_attempt_phase`、`failure_reason`、`workspace_root`、`cwd`、`backoff_until` 与 `retry_budget_remaining`。它只能作为 runtime registry / observability record；`can_create_study_truth=false`，`can_override_publication_eval=false`，不能替代 `controller_decisions/latest.json`。

### Workspace isolation

OPL external worker / hosted runtime 执行每个 study/work-unit 时，必须绑定受控 `workspace_root` / `root` / `cwd`，并在 attempt record 中持久化。所有可写路径必须位于该受控 root 下，任何路径越界、symlink 越界、相对路径逃逸或跨 study root 写入都必须 fail-closed，并把 `failure_reason` 写成 `workspace_boundary_violation`。

这条 workspace isolation 规则只约束 OPL external worker / hosted runtime。当前 `Codex-default host-agent runtime` 仍按现有 controller + host-agent 工作方式运行，不因为本节新增 work-unit contract 而改变 CLI、MCP、product-entry 或当前 Codex path 的默认执行模型。

### Retry / backoff / reconciliation

future orchestrator 可以使用 retry/backoff/reconciliation 恢复 runtime 可用性，但不能改变 study authority。

稳定语义如下：

- `running state refresh`：active attempt 必须周期性刷新 runner 状态、last heartbeat、active process / session evidence 与当前 `run_attempt_phase`。
- `terminal/non-active handling`：一旦 worker 返回 completed、failed、cancelled、stopped 或 non-active，orchestrator 必须停止把它视为 live writer，并进入 `released`、`retry_queued` 或 controller gate，而不是继续投影为 running。
- `stalled detection`：heartbeat 过期、active_run_id 无刷新、进程证据缺失或工作区长期无可解释变更时，只能触发受控 reconciliation；不得直接写 paper truth 或 publication authority。
- `bounded retry`：每个 work-unit / route-unit 必须有显式 retry budget、backoff policy 与最后一次 `failure_reason`；超过预算后进入 controller-owned review / gate，而不是无限重启。

retry/backoff 是恢复策略，不是研究裁决策略。它只能帮助同一 controller-approved work-unit 回到可执行状态；不能创建新的 study truth、不能覆盖 `study_charter`、不能绕过 `publication_eval/latest.json` 或 `controller_decisions/latest.json`。

### Runtime telemetry and accounting

OPL external worker / hosted runtime 的 telemetry 必须服务恢复、审计和 operator projection，不承担医学质量裁决。

每条 runtime lifecycle event 至少应保留稳定键：

- `program_id`
- `study_id`
- `quest_id`
- `active_run_id`
- `work_unit_id`
- `route_id`
- `attempt_count`
- `run_attempt_phase`
- `session_id`
- `event_type`
- `outcome`
- `failure_reason`
- `worker_host`
- `workspace_root`
- `cwd`
- `timestamp`

稳定日志优先使用确定性 `event_type` 和短 `failure_reason`，例如 `attempt_claimed`、`attempt_started`、`agent_message`、`token_usage_updated`、`rate_limit_updated`、`attempt_completed`、`retry_queued`、`terminal_non_active`、`workspace_cleanup_started`、`workspace_cleanup_completed`。日志不得把大 payload、整稿、raw data、完整 ledger 或投稿包内容直接塞进 event；需要定位时只写 artifact/ref/path/fingerprint。

token/runtime accounting 采用绝对值优先：

- `thread/tokenUsage/updated.tokenUsage.total` 或同等 thread-scoped cumulative total 是 live total 的首选来源。
- `total_token_usage` / `tokenUsage.total` 表示累计快照；`last_token_usage` / `tokenUsage.last` 表示最新增量。
- dashboard、API、status 或 `runtime_efficiency` 不得把 delta 再累加到已经接受的 absolute total 上。
- `turn/completed.usage` 和泛名 `usage` 必须按 event type / payload path 解释，不能仅凭字段名当成 cumulative total。
- `model_context_window` / context-window normalization 必须和 token spend 分开显示；它不是消费，也不能被解释为医学产出强度。
- rate-limit snapshot 可以投影 `provider`、`primary_remaining`、`secondary_remaining`、`reset_after_seconds`、`retry_after_seconds`，但只能作为 runtime throttling / backoff 依据，不能推动 paper route 或 publication readiness。

### Snapshot observability evidence

operator-facing snapshot 应固定为 read-only projection，并至少能回答：

- 当前 `running` / `retrying` / `released` unit 数量。
- 每个 running unit 的 `study_id`、`quest_id`、`active_run_id`、`session_id`、`worker_host`、`workspace_root`、`run_attempt_phase`、`attempt_count`、runtime age、last event 和 last heartbeat。
- 每个 retry queued unit 的 `attempt_count`、`failure_reason`、`backoff_until`、remaining retry budget、worker/workspace ref。
- 全局 runtime totals：runtime seconds、accepted absolute token totals、latest rate-limit snapshot、snapshot `generated_at`。
- snapshot read timeout 或 source unavailable 时，返回 `snapshot_timeout` / `snapshot_unavailable`，不得把缺失 snapshot 写回成 study truth。

snapshot fixtures / regression evidence 应覆盖至少三类状态：idle、running with session/token usage、retry/backoff queue。它们是 operator projection regression oracle，不是 `study_charter`、`evidence_ledger`、`review_ledger`、`publication_eval/latest.json` 或 `controller_decisions/latest.json` 的替代来源。

### Hosted worker trust boundary and secret handling

OPL external worker / hosted runtime 在获得任何 study write 权限前，必须先留下 hosted worker safety preflight。该 preflight 至少回答：

- 当前 worker 是 trusted-environment、restricted-environment，还是混合 posture。
- 它依赖哪些 approval / sandbox / network / filesystem controls；workspace isolation 只是 baseline control，不能单独视为足够安全。
- worker identity、claim owner、delegation or authorization ref、allowed action scope、credential scope 与 expiry；identity 无法验证、authorization ref 缺失、scope escalation、credential expired 或 trust evidence 缺失时，一律 fail-closed。
- secret handling 规则：workflow/config 可以引用 `$VAR` 或等价 secret indirection，但 logs、event payload、snapshot、dashboard、handoff、evidence record 都不得输出 raw API token、secret env value、key material 或 provider credential。
- external tracker/tool access 必须最小化并绑定 study/work-unit scope；不得把通用 Linear/GitHub/API/token access 交给 worker 当成默认能力。
- hook safety 规则：workspace hooks 是 fully trusted configuration，必须有 timeout、bounded output、cwd/root boundary check 和 failure classification；hook failure 不得写 paper truth 或 publication authority。
- evidence write rule：任何 consequential external worker action 都应先有 intent、authorization ref 和 expected output refs；如果 authorization evidence 或 runtime event evidence 无法写入，写操作不得继续。

本节只固定 MAS 的 fail-closed 安全前置合同。它不引入 cryptographic identity layer、trust score service、cross-framework credential bridge 或 tamper-evident audit bundle；这些仍是 `watch_only` 的 future hosted-runtime 授权议题。当前 MAS 继续使用 controller authorization、durable records、workspace boundary、runtime events 和 publication/evidence surfaces 作为可执行 owner。

### Workspace lifecycle and teardown hygiene

OPL external worker / hosted runtime 可以有 `after_create`、`before_run`、`after_run`、`before_remove` 等 workspace lifecycle hook，但 hook 只用于准备、校验、打包或清理 runtime workspace，不得直接改变 paper truth 或 publication authority。

workspace teardown 必须满足：

- cleanup 前先持久化 cleanup evidence，包括 `study_id`、`quest_id`、`active_run_id`、`work_unit_id`、`workspace_root`、`cleanup_reason`、preserved artifact refs、started/completed timestamps。
- cleanup 只允许删除受控 workspace 内的 runtime scratch；不得删除 study charter、evidence/review ledger、publication eval、controller decisions、manuscript/package refs 或 runtime escalation records。
- terminal/released cleanup 与 non-active stop 语义分开：terminal cleanup 可以在 controller 确认后释放 runtime workspace；non-active stop 只能停止 writer 并保留恢复/审计所需材料。
- path canonicalization 必须解析 symlink，任何 root escape、relative path escape、跨 study root 写入或 cleanup target 越界都必须 fail-closed，`failure_reason=workspace_boundary_violation`。
- external issue tracker 或 PR cleanup 不属于 MAS 默认 teardown。若未来需要关闭外部 PR、issue 或 hosted runtime ticket，必须另有 repo-tracked integration contract；不得把 Linear/GitHub/Symphony teardown hook 写成 MAS 必需流程。

## Retired Decision Projection 分层

历史 decision enum 只作为 MAS domain refs / diagnostic projection 读取，不能重新提升成 domain-owned runtime mutation plan。分三类理解：

- 只读或轻量类
  - `LIGHTWEIGHT`
  - `NOOP`
  - `COMPLETED`
- 阻塞类
  - `BLOCKED`
  - `CREATE_ONLY`
- 需要交给 OPL runtime owner 的历史执行类
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
  - 只能生成 OPL provider attempt request / owner-route refs，不由 MAS 直接创建并恢复 provider attempt
- `RESUME`
  - quest 已存在且满足恢复条件时，MAS 只能输出 resume intent / owner receipt / typed blocker，provider resume 归 OPL
- `RELAUNCH_STOPPED`
  - quest 已处于 `stopped`，且 caller 已显式批准 stopped-quest relaunch
  - caller 显式批准可以来自 CLI 的 `allow_stopped_relaunch=true`，也可以来自 controller-owned current work unit / domain transition redrive；两者都必须保留 MAS owner authorization 证据
  - 若 quest 已处于 `failed` 终态，而最新同线修订 / invalid-blocking 状态已由 controller 判为可恢复，`allow_stopped_relaunch=true` 同样必须走 `RELAUNCH_STOPPED`，不能退回普通 `RESUME`
- `PAUSE`
  - 现有 live runtime 不再满足运行条件时，MAS 输出 pause intent / typed blocker；实际 pause 写入口归 OPL current-control-state owner
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
  - `failed` 终态按同一 terminal relaunch 边界处理
  - `progress_projection(...)` 必须返回 `BLOCKED`
  - reason 固定为 `quest_stopped_requires_explicit_rerun`
  - `request_opl_stage_attempt(...)` 不得自动把 stopped quest 当成 resumable 状态
  - 只有显式 `allow_stopped_relaunch=true` 才允许把它改写为 `RELAUNCH_STOPPED`

## Preflight / Handoff Contract

`request_opl_stage_attempt(...)` 在输出 owner-route handoff、owner receipt 或 typed blocker 前，会先跑 MAS domain preflight。
这条 preflight 链当前只证明 MAS domain refs 是否足够；它不授权 MAS 私有 transport mutation。

当前最小稳定 preflight 规则：

- 对 `CREATE_AND_START` / `CREATE_ONLY` / `RESUME` / `RELAUNCH_STOPPED`
  - 必须先确认 analysis bundle ready；该检查和修复绑定当前 study workspace 的运行 Python（`<workspace>/.venv/bin/python3`）或 repo clean runner 的外置 venv，不绑定 MAS checkout 内的 `.venv`
  - 如果 runtime reentry 要求 managed skill audit，则 profile 必须允许 medical overlay
  - 对 `RESUME` / `RELAUNCH_STOPPED`，如果启用了 medical overlay，必须先确保 overlay roots ready
- 对已有 quest 的非创建路径
  - 如果启用了 medical overlay，会做 overlay audit
  - 对 live quest，如果 overlay audit 失败，会把 decision 改写为 `PAUSE`

这意味着 `progress_projection(...)` 给出的 decision 只是 domain refs projection；
`request_opl_stage_attempt(...)` 可以在 preflight 后把 decision 收窄成更保守的 owner-route handoff 或 typed blocker。

## Retired Execution Provenance

以下规则只保留为 retired execution provenance / OPL handoff mapping；不得作为 MAS-owned transport、scheduler、queue 或 lifecycle 控制面复活：

- create 路径
  - 历史行为是先 `create_quest(auto_start=False)` 再 resume；当前只能映射成 OPL provider attempt request / owner-route refs
- resume 路径
  - 先同步 startup context
  - 再执行 startup hydration 与 validation
  - hydration clear 后只能允许 OPL resume/hydrate provider attempt；MAS 不直接 `resume_quest(...)`
- stopped relaunch 路径
  - 仅限 direct diagnostic / explicit controller relaunch 场景；domain-route repair 不再把 stopped controller work unit 改写成 MAS 私有 relaunch
  - controller 先把 blocked stopped 或 controller-authorized stopped relaunch 状态改写为 `RELAUNCH_STOPPED`
  - 当前 MAS 只能输出 `RELAUNCH_STOPPED` 意图、owner authorization、typed blocker 或 owner-route handoff refs；provider terminal-state release、attempt hydration、queue/retry/dead-letter 与 relaunch ownership 属于 OPL current-control-state / runtime manager
  - historical `relaunch_stopped_quest(...)` 与 `resume_quest(...)` 只能作为 retired transport provenance / diagnostic mapping 读取；普通 resume 语义不得被 stopped / failed relaunch 需求放宽
  - OPL runtime owner 接受 relaunch 后，controller-facing runtime binding / launch report 的 `last_action` 必须写成 `relaunch_stopped`
- blocked refresh 路径
  - 只在特定 blocked 场景下刷新 startup context / hydration
  - 不触发 resume
- pause 路径
  - 只输出 pause intent / owner receipt / typed blocker / owner-route handoff refs；实际 pause 写入口归 OPL current-control-state / runtime manager
- completion 路径
  - `PAUSE_AND_COMPLETE` 会先输出 pause intent / owner-route handoff refs，由 OPL 完成实际 pause 后再进入 completion sync
  - 随后统一走 completion sync，并把 decision 最终收敛到 `COMPLETED`

这条历史执行链已退役为 provenance。任何仍出现的 `study_runtime_execution.py`、`study_runtime_transport.py` 或 router transport helper refs，只能作为 migration input、diagnostic explanation 或 tombstone 读取。

## Artifact / Receipt Persistence Contract

`request_opl_stage_attempt(...)` 在 domain preflight / handoff 结束后，只能写 MAS owner receipt、typed blocker、domain refs 或 diagnostic artifact；OPL runtime truth artifact 归 OPL current-control-state。

这一步属于稳定 contract，因为上层依赖这些 artifact 作为可审计真相，包括：

- runtime binding / launch report 的 MAS-facing projection 字段
- startup payload path
- last action
- 序列化后的 status payload
- owner-route handoff / owner receipt / typed blocker refs

也就是说，即使最终 decision 是 `BLOCKED` 或 `NOOP`，只要进入了受控 orchestration，MAS-facing diagnostic / domain refs artifact 落盘仍是正式行为的一部分；OPL runtime truth artifact 不在 MAS 持久化链内。

当前实现上，这条 persistence 链仍由 `study_runtime_execution.py` 作为历史迁移输入暴露时机；具体 transport I/O 的历史代码只作为 retired provenance 读取。router 上对应 helper 只允许作为 test-only patch target 和 diagnostic ref，不构成兼容入口或 MAS 私有 runtime 控制面。

## 当前明确不属于稳定面的内容

以下内容当前仍视为实现细节，不应被其他模块直接绑定：

- `_status_state(...)`、`_run_runtime_preflight(...)`、`_execute_*` 等私有 helper 名称
- `_load_yaml_dict(...)`、`_resolve_study(...)`、`_execution_payload(...)` 等 resolution 细节
- `_build_execution_context(...)`、`_build_context_create_payload(...)`、`_persist_runtime_artifacts(...)` 等 execution/orchestration 细节
- `_create_quest(...)`、`_resume_quest(...)`、`_relaunch_stopped_quest(...)`、`_pause_quest(...)`、`_inspect_quest_live_execution(...)` 等 transport seam 细节
- `study_runtime_resolution.py` / `study_runtime_decision.py` / `study_runtime_startup.py` / `study_runtime_completion.py` / `study_runtime_execution.py` / `study_runtime_transport.py` 内部尚未升级成 spec 的组装细节
- overlay materialization payload 的完整内部结构
- analysis bundle payload 的完整内部结构
- runtime audit payload 中未被 typed wrapper 明确收口的自由字段
- 各类 report JSON 的全文 schema

如果未来这些内容也要被跨模块依赖，应先升级成显式 spec，再允许成为正式 contract。

## 回归测试锚点

当前这份 spec 主要由以下测试约束：

- [`tests/test_study_runtime_router.py`](../../../tests/test_study_runtime_router.py)
- [`tests/test_study_runtime_router_topology.py`](../../../tests/test_study_runtime_router_topology.py)
- [`tests/test_runtime_protocol_topology.py`](../../../tests/test_runtime_protocol_topology.py)
- [`tests/test_workspace_contracts.py`](../../../tests/test_workspace_contracts.py)

其中：

- router tests 约束 decision、typed surface、preflight 和 execution behavior
- router topology tests 约束历史 router patch target 只能作为 diagnostic / provenance ref 暴露，不能重新生成兼容入口或 MAS 私有 runtime 控制面
- runtime protocol topology tests 约束 runtime layout / path contract
- workspace contract tests 约束 orchestration 依赖的 workspace readiness 前提

后续如果新增 decision、extra key、typed symbol 或 execution phase，应先更新这份文档，再补对应测试。
