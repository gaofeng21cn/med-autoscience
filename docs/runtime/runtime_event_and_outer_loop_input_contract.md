# Runtime Event And Outer-Loop Input Contract

## 1. 目标

本文件冻结当前已经落地的正式 contract：

- `MedDeepScientist` 负责 quest-owned native runtime truth
- `MedAutoScience` 负责 study-owned supervision / escalation / decision truth
- managed runtime 的 outer loop 必须同时消费这两层正式输入，不能再靠本仓 controller 重写 quest-owned `runtime_events/*`

这份 contract 解决的是“runtime 已经降级、暂停、停车或等待输入，但 MAS 看不见”的结构性问题。当前系统里，quest-owned truth 与 study-owned truth 已经拆开，不能再混写。

## 2. Truth Owner 与 Surface

### 2.1 Quest-owned native runtime truth

权威 owner：`MedDeepScientist runtime core`

稳定表面：

- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_events/<timestamp>_<event_kind>.json`
- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/runtime_events/latest.json`

这是 quest-owned truth，不是 launch report、runtime watch，也不是 study-owned controller summary。

### 2.2 Study-owned outer-loop truth

权威 owner：`MedAutoScience`

稳定表面：

- `study_runtime_status`
- `runtime_supervision/latest.json`
- `runtime_escalation_record.json`
- `controller_decisions/latest.json`
- `publication_eval/latest.json`

这些表面负责 study-owned judgment，不负责伪装成 quest-owned runtime truth。

### 2.3 Workspace knowledge / literature truth

权威 owner：workspace-level contract

稳定表面：

- `portfolio/research_memory/*`
- `portfolio/research_memory/literature/registry.jsonl`
- `portfolio/research_memory/literature/references.bib`
- `portfolio/research_memory/literature/coverage/latest.json`
- `studies/<study_id>/artifacts/reference_context/latest.json`

这层已经是 `P1` 完成态，不再由 quest-local literature cache 充当 authority root。

## 3. Session / Transport Contract

`GET /api/quests/{quest_id}/session` 的 stable transport contract 至少包含：

- `quest_id`
- `snapshot`
- `runtime_audit`

native runtime truth 扩展字段：

- `runtime_event_ref`
- `runtime_event`

规则：

- `runtime_event_ref` 若存在，必须是合法 durable ref
- `runtime_event` 若存在，必须是合法 native runtime event payload
- 若二者同时存在，必须指向同一个 durable artifact
- `runtime_event.quest_id` 必须与 session `quest_id` 一致
- MAS transport 必须原样透传这对字段，不得静默丢弃，不得在 transport 层重新生成 quest-owned event

## 4. Managed Study Status Contract

对 managed runtime 且 quest 已存在的 study，`study_runtime_status` 必须满足：

- `runtime_event_ref` 直接来自 session-native `runtime_event_ref`
- `runtime_event` 可内联暴露最新 native event payload
- `decision` / `reason` 仍是 study-owned controller judgment
- `supervisor_tick_audit.status` 仍是 study-owned freshness truth
- `runtime_escalation_ref` 仍是 study-owned escalation truth

禁止事项：

- 不得再由 `study_runtime_status` 把本地观测重新写成 quest-owned `status_observed` event
- 不得再由 `study_runtime_execution` 把 create / resume / pause / completion 动作写成 quest-owned `transition_applied` event
- `runtime_supervision` 可以在 study-level supervision report 中回显 `runtime_event_ref`，但不得覆盖 quest-owned `runtime_events/latest.json`

## 5. Formal Outer-Loop Input

对 managed runtime，outer loop 的正式输入固定为：

- quest-owned `runtime_event_ref`
- optional `runtime_event`
- study-owned `decision`
- study-owned `reason`
- study-owned `supervisor_tick_audit.status`
- study-owned `runtime_escalation_ref`
- `publication_eval/latest.json`

语义分工：

- native runtime event 提供 quest runtime truth：
  - `quest_status`
  - `display_status`
  - `active_run_id`
  - `runtime_liveness_status`
  - `worker_running`
  - `stop_reason`
  - `continuation_policy`
  - `continuation_reason`
  - `interaction_action`
  - `interaction_requires_user_input`
  - `active_interaction_id`
- study-owned surfaces 提供 outer-loop judgment truth：
  - `decision`
  - `reason`
  - `supervisor_tick_status`
  - `runtime_escalation_ref`

换句话说，outer loop 现在消费的是：

- runtime 自报的 quest truth
- MAS 自己的 study-owned control truth

而不是 MAS 自己代 runtime 再写一份 quest truth。

## 6. Fail-Closed 规则

对 managed runtime，outer loop 必须继续 fail-closed：

- 缺 `runtime_event_ref` 时，不得把 managed runtime 说成输入完整
- `runtime_event_ref` 指向的 artifact 不存在、schema 非法、`quest_id` 不匹配时，必须报错
- `supervisor_tick_audit.status != fresh` 时，不得把当前 runtime 输入表述成稳定托管中
- `runtime_escalation_ref` 缺失或非法时，不得把需要 escalation 的场景描述成正常可继续
- 不允许再用 controller-side synthetic event 覆盖 native runtime truth
- 不允许把 `runtime_watch`、`launch_report` 或 `study_progress` 升格成 quest runtime truth

## 7. 当前完成状态

当前正式状态如下：

- `P0 runtime native truth`：已完成，上游完成点为 `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a`
- `MedAutoScience` consumer-side cutover：已完成，managed runtime 不再覆盖 quest-owned `runtime_events/*`
- `P1 workspace canonical literature / knowledge truth`：已完成
- 当前剩余 active tranche：`P2 controlled cutover -> physical monorepo migration`

因此，这份文件不再把 `runtime event contract` 写成“MAS 物化的一份 projection contract”，而是把它写成：

- runtime-native quest truth
- study-owned outer-loop truth
- 二者之间的正式拼接规则
