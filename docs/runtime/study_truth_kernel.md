# Study Truth Kernel Contract

## 目标

`StudyTruthKernel` 是 MAS study 级运行真相的唯一 reducer。它把 task intake、controller decision、runtime event、publication gate、quality review、package authority、delivery sync、human gate、writer lock 等输入归并为一个 `StudyTruthSnapshot`，供 `study_runtime_status`、`study_progress`、`runtime_watch`、workspace cockpit、product frontdesk 和 MCP compact projection 消费。

该合同采用三条工程原则：

- Kubernetes controller/reconcile：controller 只围绕同一个期望状态与当前状态收敛。
- Temporal durable history/replay：workflow state 由事件历史可重建，不能依赖临时投影文字。
- CQRS/Event Sourcing：写模型持有 authority，read model 只是可重建 projection。

## 稳定表面

- append-only event log：`studies/<study_id>/artifacts/truth/events.jsonl`
- materialized snapshot：`studies/<study_id>/artifacts/truth/latest.json`
- read-model embedding：`study_runtime_status.study_truth_snapshot`
- user projection embedding：`study_progress.truth_epoch` 与 `study_progress.study_truth_snapshot`

普通 status/progress read 只生成 shadow snapshot，不写 `latest.json`。只有显式 reconcile、controller tick 或调用 `materialize_truth_snapshot(...)` 才能刷新 materialized snapshot。

## Dominance Rules

- `stop_loss` 强于 publication/package/finalize/readiness projection。
- 同一 study line 的新 `task_intake` / `reviewer_revision` 强于旧 stopped/finalize/submission-ready 投影。
- `execution_owner_guard.supervisor_only=true` 时，前台只允许监督和用户沟通类动作。
- `publication_supervisor_state.bundle_tasks_downstream_only=true` 时，bundle/build/proofing 类动作阻塞。
- 缺少 `assessment_provenance.owner=ai_reviewer` 的 publication eval 不能宣布 reviewer-ready、finalize-ready 或 submission-ready。
- live writer lock 存在时，package authority 只能是 `provisionally_current_for_epoch`；writer lock 释放后才能成为稳定 current。
- `current_package` 与 `submission_minimal` 是可重建投影，不是 study authority。

## MDS 边界

MDS 只能向 MAS 提供 runtime/native/review 事件或受控后端证据。MAS 持有 study truth reducer、publication gate 解释、package authority 解释和用户可见 next action。任何 MDS 输出如果要影响用户可见动作，必须先进入 truth event，再由 reducer 产生 snapshot。

## 事故治理

后续 truth/gate/status 事故不能只补局部判断。每次事故必须同时留下三类可验证资产：

- reducer rule：把新的 dominance/invalidations 规则写进 `StudyTruthKernel`。
- fixture test：把真实冲突脱敏成 golden fixture，证明只产出一个 `canonical_next_action`。
- runbook entry：在 runtime/status 文档里记录事故模式、权威来源和禁止旁路。
