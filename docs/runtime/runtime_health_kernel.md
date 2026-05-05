# Runtime Health Kernel Contract

## 目标

`RuntimeHealthKernel` 是 MAS 针对 `(study_id, quest_id)` 的唯一运行健康 reducer。它把 runtime state、daemon probe、worker heartbeat、session probe、supervisor tick、launch/recover/relaunch attempt、stale progress 与 escalation 事件归并为一个 `RuntimeHealthSnapshot`，供 `study_runtime_status`、`study_progress`、`runtime_watch`、workspace cockpit、product frontdesk 和 MCP compact projection 消费。

该合同采用四条工程原则：

- Kubernetes controller/reconcile：把 desired runtime state 与 observed runtime state 分开，controller 只做收敛动作。
- Temporal durable history/replay：runtime health 由事件历史重建，不能依赖 `last_launch_report` 这类最近动作摘要。
- CQRS/Event Sourcing：append-only event log 是写模型，`latest.json` 和前台字段是可重建 read model。
- SRE 运行纪律：恢复必须有 retry budget、backoff/升级语义和可解释人工介入信号。

## 稳定表面

- append-only event log：`studies/<study_id>/artifacts/runtime/health/events.jsonl`
- materialized snapshot：`studies/<study_id>/artifacts/runtime/health/latest.json`
- read-model embedding：`study_runtime_status.runtime_health_snapshot`
- user projection embedding：`study_progress.runtime_health_epoch` 与 `study_progress.runtime_health_snapshot`

普通 `study_runtime_status` / `study_progress` read 只生成 shadow snapshot，不写 `artifacts/runtime/health/latest.json`。只有显式 reconcile、`runtime watch --apply` 或 controller tick 可以刷新 materialized snapshot。

显式 reconcile 入口：

```bash
uv run python -m med_autoscience.cli runtime reconcile-health --profile <profile> --study-id <study_id>
```

该入口先读取当前 `study_runtime_status`，再把 status payload 归一化为 runtime health events 并刷新 `artifacts/runtime/health/latest.json`。

## Dominance Rules

- live worker 必须同时满足 `runtime_liveness_audit.status=live`、`worker_running=true`、`active_run_id!=null`。
- fresh supervisor tick 只证明外环监管最近刷新，不能证明 worker live。
- `last_launch_report` 只保留最近动作摘要；其 `active_run_id` 在新 liveness 观测不成立时只能降为 `last_known_run_id`。
- 新式 resume result 一旦携带 `scheduled` / `started` / `queued` 字段，`status=active` 只表示 quest 仍为 active，不能证明 worker live。恢复后置条件必须要求 `active_run_id`、`started=true`、`queued=true` 或 `running` / `retrying` 快照；`scheduled=true` 但未 started、未 queued、无 `active_run_id` 必须 fail closed 为 `no_live_run_started`。
- `quest_marked_running_but_no_live_session` 必须进入有限状态机：probe / recover / relaunch / escalated，不能无限 recovering。
- strict live worker 观测到新的 `active_run_id` 时，retry budget 必须按当前 run epoch 计算；旧 run 或无 run 归属的失败历史不能让新 live run 继承 `runtime_recovery_retry_budget_exhausted`。
- 同一 active run epoch 内的 launch / recover / relaunch attempt 仍然消耗 retry budget；当前 run 自身耗尽预算后必须升级，不能无限恢复。
- retry budget 耗尽后必须输出 `canonical_runtime_action=escalate_runtime`，并禁止继续伪装成自动恢复中。
- 已交付人审/投稿包的 study 如果没有 live worker，且 runtime state 只残留 `runtime_platform_repair_redrive`，必须投影为 `await_explicit_resume` / parked handoff，而不是重新解释成 writer。`delivery_manifest.json`、`manuscript/current_package/` 与 `manuscript/current_package.zip` 是 human-facing handoff 证据；它们不能成为 edit authority，但足以阻止平台 repair 自动重开 writer。
- `pause-runtime` 成功后若 quest 已 paused、无 `active_run_id`、无 worker，必须清理 stale `runtime_platform_repair_redrive` continuation 三元组，避免下一次 status read 把人工/投稿停驻重新投影成自动恢复。
- runtime health 只能影响 runtime action；不得反向覆盖 `StudyTruthKernel.canonical_next_action`、publication gate、package authority 或 delivery state。

## MDS 边界

MDS 只能提供 runtime/native/review/probe 事件，包括 runtime state、daemon probe、worker heartbeat、session probe 与 runtime event observed。MAS 持有 `RuntimeHealthKernel` reducer、`canonical_runtime_action`、worker liveness judgment 与 allowed controller actions。任何 MDS 输出如果要影响用户可见运行动作，必须先进入 runtime health event，再由 reducer 产生 snapshot。

## 事故治理

后续 runtime liveness / recovery 事故不能只补局部判断。每次事故必须同时留下三类可验证资产：

- reducer rule：把新的 dominance、retry 或 invalidation 规则写进 `RuntimeHealthKernel`。
- fixture test：把真实冲突脱敏成 golden fixture，证明只产出一个 `canonical_runtime_action`。
- runbook entry：在 runtime/status 文档里记录事故模式、权威来源和禁止旁路。
