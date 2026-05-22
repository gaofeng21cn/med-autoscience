# Durable Workflow Contract

Runtime OS 的目标是让长时研究任务可暂停、可恢复、可重放、可审计。它只持有运行健康与恢复动作，不持有医学论文质量判断。

## State Model

稳定状态为 `queued`、`running`、`awaiting_artifact_delta`、`route_back`、`awaiting_human_gate`、`recovering`、`completed`、`escalated`。每个状态必须有 `resume_action`，且 `resume_action` 必须回到 controller-owned durable surface。

## Durability Guarantees

- pause / resume from restore point
- event-sourced replay
- idempotent controller tick
- human gate as durable decision
- retry budget before escalation

## Event Replay

Runtime OS 必须用 durable event log 恢复状态。replay 从 `restore_point_id` 开始，按 `recorded_at` 排序，用 `event_id` 去重；重放结果必须能重建 `active_state`、`active_run_id`、`work_unit_id`、`retry_budget_remaining` 与 `pending_human_gate_decision_id`。允许的 event classes 包括 runtime observation、worker heartbeat、artifact delta、route-back decision、human gate decision、recovery attempt 与 retry budget decrement。

## Idempotent Tick

controller tick 的幂等键由 `program_id`、`study_id`、`quest_id`、`active_run_id`、`work_unit_id`、`restore_point_id` 与 `tick_sequence` 组成。重复 tick 只能返回已有 decision ref；它可以写 `progress_projection`、`domain_health_diagnostic`、`runtime_escalation_record.json` 与 `artifacts/controller_decisions/latest.json`，但不能创建或覆盖 study truth、不能覆盖 quality truth、不能声明 publication ready。

## Human Gate

human gate 是 durable decision，不是 chat 里的临时许可。`awaiting_human_gate` 恢复时必须引用 `decision_id`，并从 `artifacts/controller_decisions/latest.json` 读取 `decided_by`、`decided_at`、`decision`、`scope`、`evidence_refs` 与 `resume_action`。没有 durable decision 的 human gate 不能恢复执行。

## Retry Budget

retry budget 绑定 controller route work unit，通过 `attempt_count` 与 `retry_budget_remaining` 表达。每次消耗 budget 必须产生 `retry_budget_decremented` event；budget 用尽后进入 `escalated`，并先写 `runtime_escalation_record.json`，再进入 platform repair、human gate decision 或 route redesign。

## Boundary

`artifacts/runtime/health/latest.json` 是 runtime health truth；`artifacts/publication_eval/latest.json` 仍由 Quality OS 持有；`StudyTruthKernel` 继续持有 canonical study truth。runtime health 只能用于 observability 与 recovery，不能把论文质量改成 ready，不能覆盖 `publication_eval/latest.json`，也不能覆盖 StudyTruthKernel 的 canonical next action。read model 只能投影已有 truth，不能回写成新的 study truth 或 quality truth。
