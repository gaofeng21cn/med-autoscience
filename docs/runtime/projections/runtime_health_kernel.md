# Runtime Health Kernel Contract

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime projection and read-model semantics for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable projection support only; projection truth remains in source, tests, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

## 目标

`RuntimeHealthKernel` 是 MAS 针对 `(study_id, quest_id)` 的 domain health / blocker reducer。它消费 OPL current-control-state refs、MAS owner route refs、typed closeout refs、owner receipt、typed blocker、stale progress 与 escalation 事件，归并为一个 domain diagnostic snapshot，供 `progress_projection`、`study_progress`、`domain_health_diagnostic`、workspace cockpit、product entry status 和 MCP compact projection 消费。它不再是 worker/session/runtime lifecycle truth owner。

该合同采用四条工程原则：

- Kubernetes controller/reconcile：OPL 负责 desired runtime intent 与 observed attempt state 收敛；MAS 只解释 domain blockers 与 owner receipts。
- Temporal durable history/replay：runtime health 由 OPL attempt history 与 MAS refs 重建，不能依赖 `last_launch_report` 这类最近动作摘要。
- CQRS/Event Sourcing：append-only event log 是写模型，`latest.json` 和前台字段是可重建 read model。
- SRE 运行纪律：恢复必须有 retry budget、backoff/升级语义和可解释人工介入信号。

## 稳定表面

- append-only event log：`studies/<study_id>/artifacts/runtime/health/events.jsonl`，仅记录 MAS domain health / blocker refs
- materialized snapshot：`studies/<study_id>/artifacts/runtime/health/latest.json`，不是 OPL runtime attempt truth
- read-model embedding：`progress_projection.runtime_health_snapshot`
- user projection embedding：`study_progress.runtime_health_epoch` 与 `study_progress.runtime_health_snapshot`

普通 `progress_projection` / `study_progress` read 只生成 shadow snapshot，不写 `artifacts/runtime/health/latest.json`。只有显式 reconcile、`runtime domain-health-diagnostic --apply` 或 controller tick 可以刷新 materialized snapshot。

`runtime_session` 是 retired worker/session read model 名称；当前 live/no-live、last attempt、worker liveness、retry/dead-letter 和 provider terminal truth 来自 OPL `current_control_state`。MAS projection 只能显示 OPL refs、owner receipt、typed blocker、route-back reason 和 historical fixture / explicit archive import reference；它不判断 scientific quality，不授权 publication/submission readiness，也不替代 OPL attempt ledger。

显式 `source_signature` 是 runtime health 的幂等键。同一 `(study_id, quest_id, event_type, source_signature)` 重放只能返回 existing event，不得再次追加并消耗 retry budget。没有显式 source signature 的 recover/launch attempt 仍按真实新尝试追加，继续消耗 retry budget。

显式 reconcile 入口：

```bash
uv run python -m med_autoscience.cli runtime reconcile-health --profile <profile> --study-id <study_id>
```

该入口先读取当前 `progress_projection`，再把 status payload 归一化为 runtime health events 并刷新 `artifacts/runtime/health/latest.json`。

`owner_receipt_handoff` 是 retired controller/supervisor 恢复意图 ledger 名称；当前恢复由 OPL desired intent vs actual attempt reconciliation 管理。MAS 只能返回 route-back、owner receipt、typed blocker 或 domain_health_diagnostic blocker；`runtime_reconcile_trigger` 只能展示 OPL next action 或 MAS blocker refs，用户刷新 Portal 不会直接 relaunch worker。

## Dominance Rules

- live worker / live attempt 必须由 OPL `current_control_state` 证明；MAS `runtime_liveness_audit`、`worker_running` 或 `active_run_id` 只能作为 historical/provenance refs 显示。
- fresh supervisor tick 只证明外环监管最近刷新，不能证明 worker live。
- `last_launch_report` 只保留最近动作摘要；其 `active_run_id` 在新 liveness 观测不成立时只能降为 `last_known_run_id`。
- 新式 resume result 一旦携带 `scheduled` / `started` / `queued` 字段，`status=active` 只表示 quest 仍为 active，不能证明 worker live。恢复后置条件必须要求 `active_run_id`、`started=true`、`queued=true` 或 `running` / `retrying` 快照；`scheduled=true` 但未 started、未 queued、无 `active_run_id` 必须 fail closed 为 `no_live_run_started`。
- `quest_marked_running_but_no_live_session` 必须进入有限状态机：probe / recover / relaunch / escalated，不能无限 recovering。
- strict live worker 观测到新的 `active_run_id` 时，retry budget 必须按当前 run epoch 计算；旧 run 或无 run 归属的失败历史不能让新 live run 继承 `runtime_recovery_retry_budget_exhausted`。
- 同一 active run epoch 内的 launch / recover / relaunch attempt 仍然消耗 retry budget；当前 run 自身耗尽预算后必须升级，不能无限恢复。
- retry budget 耗尽后必须输出 `canonical_runtime_action=escalate_runtime`，并禁止继续伪装成自动恢复中。
- 已交付人审/投稿包的 study 如果没有 OPL live-attempt ref，且历史 runtime state 只残留 legacy OPL-runtime redrive marker，必须投影为 `await_explicit_resume` / parked handoff，而不是重新解释成 writer。`delivery_manifest.json`、`manuscript/current_package/` 与 `manuscript/current_package.zip` 是 human-facing handoff 证据；它们不能成为 edit authority，但足以阻止 OPL repair redrive 自动重开 writer。
- `pause-runtime` 成功后若 quest 已 paused、无 `active_run_id`、无 OPL live-attempt ref，必须把 stale OPL-runtime redrive continuation 三元组降为 retired provenance，避免下一次 status read 把人工/投稿停驻重新投影成自动恢复。
- `pause-runtime` 后的 terminal control barrier 必须覆盖三个竞态源：due delayed turn 不得 drain 成新 run；旧 active worker 的 late completion 不得把 paused 改回 active；普通 `progress_projection` 读取必须投影为 `quest_user_paused_requires_explicit_wakeup`，直到显式 resume contract 释放。transport 层的释放点固定为 `resume_quest` 发出的 `explicit_resume`，它可以把同一 quest identity 从 paused 重入 running；其他 schedule 原因仍必须被 `terminal_runtime_state` 阻断。
- 历史残留的裸 `paused` read model 也属于 terminal control barrier：当 runtime state 无 `active_run_id`、无 live worker、无 `stop_reason`、无 controller continuation owner 时，普通 status/read/reconcile 只能投影为 `await_explicit_resume`，不能依赖 `_RESUMABLE_QUEST_STATUSES` 自动发起 `resume`。
- 历史残留的 `active` read model 也可能承载同一显式恢复屏障：当 `active` quest 无 `active_run_id`、无 live worker，且 runtime health 已把 dominant observation 投影为 `await_explicit_resume / quest_user_paused_requires_explicit_wakeup` 时，显式 user wakeup 只能把 stale human-takeover/user-pause barrier 清成 OPL runtime owner-route handoff；MAS 不直接恢复 provider worker。
- runtime health 只能影响 runtime action；不得反向覆盖 `StudyTruthKernel.canonical_next_action`、publication gate、package authority 或 delivery state。

## MDS 边界

MDS 只能提供 runtime/native/review/probe 事件，包括 runtime state、daemon probe、worker heartbeat、session probe 与 runtime event observed。MAS 持有 `RuntimeHealthKernel` reducer、`canonical_runtime_action`、domain blocker interpretation 与 allowed controller actions；worker liveness / attempt truth 只能来自 OPL current-control-state refs。任何 MDS 输出如果要影响用户可见运行动作，必须先进入 runtime health event，再由 reducer 产生 domain diagnostic snapshot。

## 事故治理

后续 runtime liveness / recovery 事故不能只补 MAS 局部判断。每次事故必须同时留下三类可验证资产：

- reducer rule：把新的 dominance、retry 或 invalidation 规则写进 `RuntimeHealthKernel`。
- fixture test：把真实冲突脱敏成 golden fixture，证明只产出一个 `canonical_runtime_action`。
- runbook entry：在 runtime/status 文档里记录事故模式、权威来源和禁止旁路。
