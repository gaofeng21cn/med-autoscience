# Runtime Supervision Loop

这份文档冻结 `MedAutoScience` 的外环监管合同，也就是当前的 outer `supervisor loop` contract。

一句话结论：

- `MedAutoScience` 默认不是 resident HTTP/WebSocket daemon
- 默认 scheduler adapter 是 `local`，每 `300` 秒调用一次 MAS-owned supervision tick script；macOS backend 已落到 MAS-owned LaunchAgent；contract owner 是 `MAS supervision scheduler contract`
- 当前 desired tick script 依序调用 `watch-runtime --max-ticks 1`、`supervisor-scan`、`supervisor-consume`、`supervisor-execute-dispatch`
- 该 outer loop 不拥有 runner completion 后的连续科研主循环；内层 `turn completion -> next turn` 由 MAS Runtime Turn Lifecycle Kernel 低延迟处理
- 旧 workspace-local `systemd` / `cron` / `launchd` / `docker` service manager 已退役；检测到它们时只作为 cleanup evidence，不作为 active scheduler 选项
- 这个 loop 的职责是发现掉线、执行 reconciliation、写出 durable supervision surface，并把结果翻译成前台可见的人话

## 1. 总目标

我们要解决的不是“把日志看起来拼热闹”，而是下面这三个正式目标：

- worker 掉线后，外层必须能在有限时间内发现
- 发现后必须按固定规则自动恢复或升级
- 前台必须能持续看到几点几分发生了什么、研究推进到哪一步、现在是否需要人工介入

这三个目标必须同时成立，才算 managed runtime 真正可托管。

除此之外还有一条 fail-closed 边界：

- 如果 outer supervisor tick 自己已经缺失或陈旧，系统也不能继续假装“MAS 仍在稳定监管”
- 这种情况必须作为正式监管异常直接暴露到 status / progress surface

## 2. authority 边界

这里的外环应按三层分工理解：

- `Scheduler Contract / Adapter`
  - contract owner 是 `MAS supervision scheduler contract`
  - 负责按约定 cadence 调用 MAS supervision tick script
  - 当前默认 adapter 是 MAS-owned `local` scheduler；macOS backend 已落地为 LaunchAgent
  - 显式传入 `systemd|cron|launchd|docker` 当前必须 fail-closed；显式 `hermes` 只走 optional adapter
- `MedAutoScience`
  - 医学研究治理、supervision judgment、projection 与 reconciliation owner
- `MAS Runtime OS`
  - 默认 runtime/backend state、event、recovery 与 quest lifecycle owner
- `MedDeepScientist`
  - frozen source archive、historical fixture 或显式 backend audit / explicit archive import reference

对应的监管外环是：

- `scheduler-adapter-hosted`
- `controller-judged`
- `tick-driven`
- `fail-closed`

它不是：

- 第二个 authority daemon
- 第二份 runtime truth
- 复刻旧 MDS resident daemon / WebSocket / terminal streaming 的替代物

所以权责边界固定为：

- `MAS Runtime OS` 持有默认 runtime execution / recovery / event truth
- `MedAutoScience` controller 持有 supervision / projection / reconciliation truth
- `MedDeepScientist` 不持有默认 MAS operation truth

## 3. 正式执行形态

当前正式 outer-loop tick 由 scheduler adapter 调用 MAS 生成的 script。Hermes adapter 下的脚本位于：

- `~/.hermes/scripts/med-autoscience/<workspace-key>/watch_runtime_tick.py`

该脚本由 `runtime-ensure-supervision --manager hermes` 生成，并注册进 `~/.hermes/cron/jobs.json`。当前 desired script 顺序执行四个 MAS workspace entry：

1. `ops/medautoscience/bin/watch-runtime --interval-seconds 300 --max-ticks 1`
2. `ops/medautoscience/bin/supervisor-scan --apply-safe-actions --apply-runtime-platform-repair --developer-supervisor-mode developer_apply_safe`
3. `ops/medautoscience/bin/supervisor-consume --mode developer_apply_safe --apply`
4. `ops/medautoscience/bin/supervisor-execute-dispatch --mode developer_apply_safe --apply`

`watch-runtime` 这一步每次至少做四件事：

1. 读取 managed study 的 `study_runtime_status` 或 `ensure_study_runtime`
2. 扫描 live quest 的 `runtime_watch`
3. 生成 study-owned `runtime_supervision/latest.json`
4. 必要时写出或刷新 `runtime_escalation_record.json`

随后 `supervisor-scan` / `supervisor-consume` / `supervisor-execute-dispatch` 负责把 workspace-level action queue、default executor dispatch request 和可执行 dispatch receipt 收成同一轮证据。也就是说，外环的核心不是“循环本身”，而是同一轮 tick 的 MAS controller contract。

真实 workspace 可能仍保留旧 Hermes job script，只调用单步 `watch-runtime`。这类状态不是新 contract；应通过 `runtime-ensure-supervision --profile <profile>` 刷新。`runtime-supervision-status` 的职责是暴露 job、script、latest session 与 drift，而不是把旧 script 解释成新的 desired behavior。

跨 study 的巡检入口是 supervisor scan：

```bash
medautosci runtime supervisor-scan \
  --profile <profile> \
  --studies <study_id> <study_id> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe
```

该入口写出 workspace-level `artifacts/supervision/hourly/latest.json`，只消费 MAS durable truth surfaces：`study_runtime_status`、`study_progress`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json` 与 AI repair lifecycle。它的职责是形成 `action_queue`、`why_not_applied`、owner-visible request packet 与 `external_supervisor_required`，而不是直接修改 paper/current_package。

2026-05-08 Runtime Continuity closeout 又把旧 MDS daemon 退役后最关键的两类用户可见行为补齐为 MAS-owned surface：

- `runtime_session` read model：从 `study_runtime_status/runtime_liveness_audit`、SQLite runtime lifecycle store、owner_route/dispatch receipts 和historical fixture / explicit archive import reference 依序投影 `active_run_id`、`last_known_run_id`、`worker_state`、`worker_running`、`last_seen_at`、event cursor、stdout ref 与 freshness。它只读，不写 runtime truth。
- `recovery_intent` ledger：supervisor scan 在每个 study projection 中写出 `runtime_recovery_intent`，记录恢复原因、next owner、retry budget、dedupe fingerprint、last attempt/result、next eligible tick 与 `current_action`。允许动作固定为 `await_next_tick`、`safe_reconcile_ready`、`recovering`、`parked`、`human_gate_required`、`escalated`。
- `runtime_reconcile_trigger` projection：`study-progress`、workspace cockpit、product-entry status 和 Progress Portal 可以显示“是否可请求一次 safe reconcile dry-run”。该投影本身不执行 reconcile、不写 runtime、不写 paper/current_package、不写 publication gate；页面刷新只会生成幂等推荐命令和 blocked reasons。

safe reconcile 的核心边界是 fail-closed：route stale、owner mismatch、manual parked、`quest_status=parked`、completed、human gate、publication gate missing、retry exhausted 都不得进入可请求状态。真正恢复仍必须走 `RuntimeHealthKernel -> owner_route -> executor -> rescan` 闭环。

2026-05-08 Runtime Evidence closeout 进一步把外层监管延迟做成可解释 SLA，而不是新增常驻进程：

- `outer_supervision_slo` read model 固定字段包括 `last_tick_at` / `latest_scheduler_run_at`、`last_reconcile_at` / `latest_supervisor_reconcile_at`、`next_due_at` 等价阈值、`tick_age_seconds` / `age_seconds`、`state=fresh|due|stale|missing|blocked`、dedupe fingerprint、authority flags 与 canonical `runtime-supervisor-reconcile --dry-run` 推荐命令。
- `fresh` 表示最新 MAS scheduler tick 或 supervisor reconcile 仍在 freshness window 内；`due` 表示应安全加速一次 one-shot reconcile；`stale` 表示外环监管已经陈旧；`missing` 表示缺监管事件或 status surface；`blocked` 表示最新 scheduler tick 失败、旧 service 冲突或 supervision contract 本身阻塞。
- 该 read model 投影到 `runtime-supervision-status`、`runtime-supervisor-reconcile` receipt、`runtime_reconcile_trigger`、`study_progress`、workspace cockpit、Product Entry 和 Progress Portal。
- 它只允许页面或 CLI 显示推荐命令，或由已有 controller/supervisor safe surface 做 dry-run/apply；读入口刷新不能直接 relaunch worker、写 runtime truth、写 paper/current_package、写 `publication_eval/latest.json` 或写 `controller_decisions/latest.json`。
- 它不改变当前 adapter 事实：默认 `local` scheduler 每 `300` 秒调用 one-shot tick；Hermes gateway cron 只在显式 `--manager hermes` 时作为 optional adapter；旧 workspace-local `launchd/systemd/cron/docker` service 仍是 retired cleanup evidence。scheduler owner / adapter / status 同构计划以 [Supervision Scheduler Contract](./supervision_scheduler_contract.md) 为准。

这条外环和内层 turn lifecycle 的分界是固定的：正常 runner 返回后的 `active_run_id` / `worker_running` 清理、queued user message 优先级、`continuation_policy=auto` 的约 `0.2s` 下一 turn、human/terminal gate 停止，都由 `mas_runtime_core` 的 Runtime Turn Lifecycle Kernel 处理。MAS scheduler tick 只负责发现外层 stale/no-live、刷新 supervision/read-model、触发 safe recovery 或把异常升级；它不再是自动科研连续跑的主循环 owner。

2026-05-09 Runtime Watchdog / LLM cost closeout 把“低延迟感知”和“低成本调度”拆成两层，而不是缩短 300 秒 scheduler tick：

- 真实 runtime turn 由 MAS per-run worker wrapper 托管。wrapper 是每个 run 一个子进程，负责启动并等待 `codex exec` 子进程，刷新 `worker_lease.json` 中的 `monitor_kind=mas_per_run_worker_wrapper`、`monitor_pid`、`child_pid`、`heartbeat_at`、`last_output_at`、stdout/stderr cursor、`monitor_state` 和 `stale_reason`，并在 child exit 后立即写 `runner_exit.json`、调用 `complete_turn_and_normalize`。它不是 resident MDS daemon，也不是 workspace-local service。
- `worker_lease` / `runtime_session` / Live Console read model 现在能区分 `monitor_state=live|exited|stale|lost|unknown`，并展示 last worker heartbeat、last output、monitor owner、why waiting 与 `will_start_llm`。child exit 走低延迟归一化；wrapper lost 或 heartbeat stale 才进入 recovery intent / safe reconcile 路径，等待 MAS scheduler fail-safe tick 或显式 one-shot reconcile。
- runtime action cost contract 固定四类动作：`observe_only`、`reconcile_dry_run`、`controller_apply`、`codex_worker_dispatch`。`runtime-supervisor-reconcile --dry-run`、Portal/Console 刷新和 SLO 投影都必须是 `will_start_llm=false`；只有真正进入 MAS runtime turn / 新 owner_route action fingerprint 并启动 Codex worker 时才是 `codex_worker_dispatch`。
- supervisor reconcile、default executor dispatch 和 runtime watch report 都投影 `codex_dispatch_count`、`suppressed_dispatch_count`、`dispatch_budget_window` 与 `action_fingerprint`。重复 tick 只能刷新 read model 或写 no-op suppression；同一 study 的同一 owner_route / work-unit fingerprint 不得重复启动 Codex worker。

这个设计参考了成熟控制面经验：Kubernetes controller 用 current/desired state reconcile，不把每个 controller 都做成互相耦合的巨大循环；Temporal 用 Activity heartbeat / timeout 及时发现长任务 worker failure；systemd watchdog 用 keep-alive ping 区分服务存活；EventBridge Scheduler 用 retry / DLQ 让调度失败可追踪。MAS 对应做法是 per-run heartbeat + fail-closed reconcile + dispatch 去重，而不是高频 LLM cron。

2026-05-09 Paper Progress Degradation closeout 把“论文推进变慢”的 P0/P1 风险接进同一条外环合同：

- `paper_progress_degradation_classifier` 把旧 MDS 行为差异按是否影响自动论文产出分类；Portal/Console 诊断体验不被当作生产降级，connector/GitOps/旧 daemon lifecycle 不重新进入默认 backlog。
- controller work-unit evidence adoption 后，supervisor 必须把同一 work unit 推进到 `owner_handoff` / `publication_gate_recheck`，并带 `next_owner`、`next_work_unit`、route reason 与 idempotency key；不得继续 redrive 同一 `analysis_claim_evidence_repair` fingerprint。
- repeat suppression 的职责是阻断重复 dispatch 和无效 LLM 花费；它不得阻断 owner handoff、publication gate recheck 或 AI reviewer / writer next owner。
- `paper_progress_stall` read model 统一表达 `same_fingerprint_loop`、`read_churn_without_artifact_delta`、`stale_truth_surface`、`runtime_recovery_retry_budget_exhausted`、handoff 状态和 source refs。
- `runtime-supervisor-reconcile --dry-run` 是零 dispatch 诊断；`--apply` 只有在 fresh owner_route、未 parked、未 completed、无 human gate、无 publication gate missing、retry budget 未耗尽且 action fingerprint 新鲜时，才能通过 Codex worker dispatch。
- study-progress、Portal、Live Console、workspace cockpit、Product Entry 和 OPL handoff 只能投影 `affects_output`、`next_owner`、`why_not_running`、`same_fingerprint_or_handoff`、`will_start_llm`、safe reconcile command 和 source refs；它们不得写 paper/package、publication gate、controller decision、runtime SQLite 或 quality/publication/submission ready。

2026-05-10 durable autonomy closeout 又把 `autonomy_progress_slo_status` 的 breach 解释收成正式 read model：

- `state=breach` 必须带 `breach_reason` 与 `breach_explanation`，不能只暴露低信息 `breach_types`。
- `breach_explanation.category` 必须落在 `owner_route`、`human_gate`、`bundle_blocker`、`quality_repair`、`worker_recovery`、`safe_reconcile_dry_run` 之一。
- 同一投影需要把 MAS-owned runtime continuity 线索串起来：`owner_route`、`worker_lease` / `runtime_session`、checkpoint lineage / resume contract、`runtime_health_snapshot.retry_budget_remaining`、recovery intent dedupe fingerprint、idempotent dispatch receipt、controller apply receipt 与 safe reconcile dry-run command。
- 这是只读解释层；它不执行 reconcile、不启动 Codex worker、不写 paper/package、不写 `publication_eval/latest.json`、不写 `controller_decisions/latest.json`，也不恢复 MDS resident daemon。

2026-05-10 Paper Progress SLO closeout 把外环监管的最高目标收口为“论文是否前进”：

- `worker_running=true`、`active_run_id` 存在、controller 写出 repair packet、gate audit 刷新，都只是中间信号；用户可见 progress 只有在 canonical manuscript/table/figure/result 变化、submission source/current package freshness proof、AI reviewer judgement 更新，或 publication gate replay 后 owner 前进时，才显示 `meaningful_artifact_delta=true`。
- live worker 超过 grace window 仍无论文产物级增量时，投影为 `live_no_paper_delta` / `paper_progress_stall`，并进入 controller-owned redrive 或 owner handoff；repeat suppression 只能压住重复 dispatch，不得压住 handoff、gate replay 或 next owner。
- 每个 paper work unit 必须能解释 `owner`、`callable_surface`、`required_inputs`、`required_outputs`、`artifact_delta_predicate`、`gate_replay_target`、`idempotency_key` 与 `source_fingerprint`。terminal success 需要 owner receipt、required output、artifact delta 或 gate replay result 同时成立。
- `owner_callable_registry` 是 callable owner 的机器锚点，当前注册 `MAS/controller`、`ai_reviewer`、`publication_gate`、`quality_repair_batch`、`gate_clearing_batch` 与 `delivery_sync`。`owner_callable_surface_missing` 是 controller-consumable blocker 或 repo-level callable gap；当 `requires_user_input=false` 时，不得把它投影成真实 `waiting_for_user`。
- submission authority / delivery closure 必须在同一个 work-unit transaction 中完成 source freshness proof、delivery sync 和 gate replay。来自旧 MDS worktree 的绝对 `paper/...` 路径只可规范到当前 paper root 的同后缀 source ref，不能作为 current source blocker。
- DM002、DM003 和 Obesity 的 read-only validation 要把 `actual_write_active`、`package_delivered`、`meaningful_artifact_delta`、`next_owner`、`why_not_progressing` 同时展示；只要 publishability / AI reviewer / submission QC 未放行，就不得把 downstream package missing 写成论文进度。

2026-05-10 Paper Progress Reconciler 重构把上面的目标接入同一个 outer-loop receipt：

- `paper_progress_state` 是所有 paper-line 入口共享的 read model。它只从当前 study/runtime/progress/controller truth surfaces 推导七类公开状态：`progressing`、`awaiting_controller_redrive`、`blocked_controller_route`、`awaiting_callable_owner`、`awaiting_human`、`downstream_only`、`terminal_delivered`。
- `paper_progress_reconciler` 是 level-triggered：每次 `runtime supervisor-reconcile` tick 都重新读取 before/after scan、consume 和 execute projection，输出 `desired_state`、`current_state`、`delta`、`decision`、`callable_contract` 与 `action_receipt`。它不信任旧 packet 的 stale conclusion，也不把 previous closeout 文案当作 current truth。
- dry-run receipt 必须保持零 dispatch；apply receipt 只有在 owner callable contract 存在、`requires_user_input=false`、`source_fingerprint` 新鲜，并且当前 execution / controller route 能解释该 action 时，才允许写 outbox receipt。
- `paper_work_unit_outbox` 是 work-unit transaction 的落账点。相同 `idempotency_key` 和相同 intent 返回 replay receipt；相同 key 不同 intent 写 `failed_closed/idempotency_key_intent_conflict`；同一 `source_fingerprint` 已启动 worker 时写 `duplicate_source_fingerprint`，不重复启动 worker。该 duplicate receipt 只阻止重复 worker start，不阻止下一 owner handoff、gate replay 或 registry repair。
- outbox 同时写 JSONL receipt 和 SQLite sidecar `paper_work_unit_receipts` 索引。SQLite 只做 receipt/history/cursor projection，不成为 publication gate、controller decision、paper package、submission source 或 runtime-owned live truth。
- retry-budget 语义现在按 paper progress contract 重判：`runtime_recovery_retry_budget_exhausted` 在 route、owner、fingerprint 和 gate 可解释时变成 `awaiting_controller_redrive` / `controller_redrive`；route 或 callable 缺失时变成 `blocked_controller_route` 或 `awaiting_callable_owner`，并暴露唯一 repo-level gap。
- Obesity 这类 `execution_owner_guard.supervisor_only=true` 且 live worker 已有 artifact delta 的状态，用户面 next owner 显示 `supervisor_only/live_quality_repair`；delivery missing 保持 downstream-only，不抢跑 delivery package，也不伪造 `package_delivered=true`。
- Progress Portal workspace dashboard 消费这些投影，显示 workspace attention、live paper-line count、freshness、每篇论文的阶段/运行健康/监管心跳/下一步和 source provenance；它只读展示，不执行 reconcile，不写 live paper artifact。

该设计借鉴的外部工程模式是：Kubernetes controller 的 desired/current reconcile loop、AWS caller-provided idempotency token 与 retry/backoff/jitter、Temporal Activity timeout/heartbeat/retry contract，以及 SRE 将 SLO 贴近用户旅程的实践。MAS 不引入这些外部系统作为 runtime dependency；只吸收模式，把论文资产增量作为自己的用户旅程 SLO。

MAS 的内置 AI repair 是第一层修复机制。它使用默认执行器 policy：

- `executor_kind = codex_cli_default`
- `executor_name = Codex CLI`
- model、reasoning effort 与本机 Codex 配置保持继承
- chat-completion-only executor 禁止作为 repair executor

第一层的时间策略固定为：

- 内置 MAS AI 监测 tick：每 `300` 秒一次
- 无 meaningful artifact/progress 后 `1800` 秒进入 AI repair 判断
- AI doctor request 写出后 `900` 秒仍未被处理，升级为 timeout/platform repair
- 触发信号包括 `no_meaningful_progress`、`same_fingerprint_loop`、`read_churn_without_artifact_delta`、`stale_truth_surface` 与 `runtime_recovery_retry_budget_exhausted`

这些策略同时投影到 `two_layer_ai_repair_policy`，由 `runtime supervisor-scan` 和 `runtime supervisor-consume` 输出。这样前台看到“AI reviewer 队列积压”时，能同时看到内置 AI repair 是否已接上、是否超时，以及下一层开发者 supervisor 是否已到接手阈值。

2026-05-10 OPL/Hermes family runtime bridge closeout 把 read model 到执行队列的断点收口为正式 sidecar 合同：

- `medautosci sidecar export --profile <profile> --format json` 会在每个 study projection 中输出 `autonomy_continuation`，并在顶层输出 `pending_family_tasks[]`。
- 当 `slo_status.state=breach`、`runtime_supervision.runtime_decision=blocked`、`runtime_liveness_status=parked` 或 `recovery_intent.current_action=safe_reconcile_ready`，且 controller 没有 `stop_loss` / terminal stop / hard human gate 时，MAS 会生成幂等 task，默认 `task_kind=runtime_supervisor/reconcile-apply`。
- OPL/Hermes 的职责是 hydration、dedupe、queue、retry、dead-letter、approval 和 local inbox notification；它只能消费 MAS 显式导出的 `pending_family_tasks[]`，不能从只读 projection 自行推断医学动作。
- `medautosci sidecar dispatch --task <task.json> --format json` 收到 `runtime_supervisor/reconcile-apply` 后，回到 MAS owner 内调用 `runtime-supervisor-reconcile --mode developer_apply_safe --apply`，再由 MAS 自己的 `scan -> consume -> execute-dispatch -> rescan` gate 决定是否启动 Codex worker、no-op、blocked 或 human gate。
- 这个桥仍禁止写 `publication_eval/latest.json`、`controller_decisions/latest.json`、paper/current_package、submission package 或 artifact gate；它只把“发现了可自动处理的 blocker”转换成 durable executable ticket。

当 `action_queue` 包含 `publication_gate_specificity_required` 或 `return_to_ai_reviewer_workflow` 时，supervisor scan 只能物化 request packet：

- `publication_gate_specificity_required` 的 owner 是 `publication_gate`
- `return_to_ai_reviewer_workflow` 的 owner 是 `ai_reviewer`
- request packet 的 authority 是 `request_only`
- 预期输出仍回到对应 owner 的 durable surface，例如 `publication_eval/latest.json`
- supervisor 本身不得写 `publication_eval/latest.json`、不得放宽 quality/publication gate、不得改 `paper/current_package` 或 `manuscript/current_package`

每个 study scan 还必须生成同一个 `owner_route`，并把它复制进 action、handoff packet、consumer dispatch 与 executor prompt contract。`owner_route` 是 `scan -> consume -> execute-dispatch -> rescan` 的路由票据，字段至少包括：

- `route_epoch`：来自 `StudyTruthKernel` 的 truth/authority epoch；缺失时用当前 status source 派生。
- `source_fingerprint`：当前 truth/status/progress/action 的稳定指纹。
- `current_owner` 与 `next_owner`：当前写入 owner 与下一可执行 owner。
- `owner_reason`：本轮路由原因，例如 `ai_reviewer_assessment_required`、`publication_gate_specificity_required` 或 runtime repair reason。
- `allowed_actions` / `blocked_actions`：本轮允许执行和明确禁止执行的 supervisor action。
- `idempotency_key`：由 study、epoch、fingerprint、owner、reason 和 action 集合派生；用于拒绝旧 dispatch。

consumer 只能传播该 route，不能重新解释 owner。request handoff 和 default executor dispatch 都必须通过同一 `owner_route.allowed_actions` gate；route 缺失、next owner 不匹配或 action 不在 allowed set 内时，只能写 blocked task，不能写 owner request packet。executor 执行前必须把 dispatch 中的 route 与最新 `hourly/latest.json` 的 route 对齐；如果 epoch、fingerprint、owner 或 reason 已变化，执行器必须写 `blocked_reason=owner_route_stale`，等待下一轮 consume 生成新 dispatch。

`allowed_actions` 只表达当前 `next_owner` 可以执行的动作，不是 action queue 的全集。scan 可以同时暴露后续 owner 的观测动作，例如 AI reviewer request；但本轮 dispatch executor 只能执行 owner_route 允许的动作。这样 runtime liveness 的 retry/exhausted 噪声、publication gate 的 blocker、AI reviewer 的质量判断和 artifact freshness 的修复任务不会在同一个 tick 互相抢 owner。

当 no-live / retry-exhausted 与当前 controller decision 同时存在时，scan 必须先做 current truth 对齐：

- `controller_decisions/latest.json` 的 action 必须是 runtime redrive 类 action；
- `controller_decisions/latest.json` 的 work-unit fingerprint 必须出现在当前 `publication_eval/latest.json`；
- next work unit 不能只是 `gate_needs_specificity` / `needs_specificity` terminal；
- 满足以上条件时，`runtime_platform_repair` 的 owner 是 `mas_controller`，authority 是 `observability_only`，reason 是 `runtime_controller_redrive_required`；
- relaunch 前必须把当前 controller decision 与 publication eval 中同 fingerprint 的具体 `specificity_targets` / actionable target 写入 runtime state 的 controller authorization；没有可执行 target 时不能把 no-live 状态误判成可恢复 runtime；
- 只有没有当前 controller route 或当前 route 已不对齐时，retry budget exhausted 才能升级为 external supervisor handoff。

完成态与停驻态也属于 current truth。若 `study_runtime_status` / `study_progress` 已经给出 `quest_status=completed` 且 completion contract resolved，或 `auto_runtime_parked.parked=true` / `canonical_runtime_action=await_explicit_resume` 且没有 live worker，scan 必须清空 stale lifecycle、不给 AI reviewer 或 external supervisor 排队，并把 `owner_route.current_owner` 投为 `controller_stop` 或 completed truth。manual hold、publishability stop-loss、package-ready handoff 和 external metadata pending 都只能等待显式 resume / revision intake，不能被 no-live 噪声、旧 publication gate 或旧 AI reviewer required 重新打开 writer。

同一轮 owner action 必须满足幂等合同。`route_epoch` 和 `source_fingerprint` 决定本轮 owner routing，具体 repo-side owner 还必须给自己的 work unit 写稳定 fingerprint：

- fingerprint 只表达语义输入，不表达普通观测时间；内容相同的 JSON/资产被同一 owner 重写后，不能因为 `mtime` 变化制造新 work unit。
- 对 package/submission authoring 类 repair，失败可在同 fingerprint 下重跑，因为缺失输出可能由同一 owner 重新生成。
- 对 non-authoring artifact input failure，例如 display input payload 缺必要字段，重复执行不会产生新信息；同 fingerprint、同 blocking artifact 的失败必须复用为稳定 blocked truth，并继续把具体 `blocking_artifact_refs` 暴露给 scan / progress / owner route。
- 因此 `scan -> consume -> execute-dispatch -> rescan` 的收敛结果应是“owner 前进或具体 blocker 稳定”，不能是同一 action 无限重放。

外层工程消费入口是：

```bash
medautosci runtime-supervisor-consume \
  --profile <profile> \
  --studies <study_id> <study_id> \
  --developer-supervisor-mode developer_apply_safe \
  --apply
```

该入口只把 scan queue 转成 owner handoff task，写入 workspace-level `artifacts/supervision/consumer/latest.json` / `history.jsonl` 以及 study-level consumer packet。它负责说明 `request_owner`、`required_output_surface`、`request_packet_ref`、forbidden surfaces 与 verification commands；它不执行 publication gate 或 AI reviewer 的专业判断，也不修改论文包。

从 2026-05-08 起，developer scheduler 的正式同 tick 行为是 `supervisor-reconcile` one-shot；该入口内部执行 `scan -> consume -> execute-dispatch -> rescan` 并写出 reconcile receipt。三段式入口保留为调试面：

```bash
medautosci runtime supervisor-reconcile \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply
```

调试时可拆成：

```bash
medautosci runtime supervisor-scan \
  --profile <profile> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe

medautosci runtime supervisor-consume \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply

medautosci runtime supervisor-execute-dispatch \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply
```

如果未显式传 `--studies`，`supervisor-consume` 从最新 `hourly/latest.json` 的 `action_queue` 推导需要消费的 study 列表。consumer 会额外写出 study-level default executor dispatch request：

- `studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/<action_type>.json`

这个 dispatch request 是“把问题交给默认 Codex CLI 执行器”的机器可读派单面，包含 owner、输入 surface、必需输出 surface、forbidden surfaces 与 prompt contract。它不等同于 owner output；例如 AI reviewer 的 output 仍必须由 AI reviewer workflow 写回 owner-authorized durable surface，consumer 本身不得写 `publication_eval/latest.json`。

`runtime supervisor-execute-dispatch` 是第三步执行/落账面。它读取 `default_executor_dispatches/*`，校验 forbidden surfaces 和 prompt contract 后，只调用 owner 授权的 repo surface，或写出 `blocked_reason`。当前允许行为是：

- `publication_gate_specificity_required`：重放 `publication_gate` owner 的 gate report，并只物化 controller-owned `publication_eval/latest.json`，要求推荐动作带具体 `claim/figure/table/metric/source_path` targets。
- `runtime_platform_repair`：调用已有 runtime supervisor scan 的 safe platform repair path。
- `return_to_ai_reviewer_workflow`：如果没有结构化 AI reviewer record，不生成评审结论，写 `blocked_reason=owner_callable_surface_missing` 与 `required_repo_surface=structured_ai_reviewer_default_executor_workflow`。

执行器的默认读取权威是 workspace-level `artifacts/supervision/consumer/latest.json`。无论调用方是否显式传 action type，`runtime supervisor-execute-dispatch` 都只能从 consumer latest 当前列出的 ready dispatch 中筛选执行；study-level `default_executor_dispatches/*.json` 目录里的旧文件不能单独作为执行票据。这样可以避免旧 `runtime_platform_repair` 或旧 `return_to_ai_reviewer_workflow` dispatch 在下一轮 scan/consume 已经改判 owner 后继续执行。

publication gate 与 AI reviewer 的 currentness 使用 work-unit fingerprint，而不是最近生成时间：

- gate report 每次重放都可能生成新的 `generated_at`，这个时间戳不能单独使 AI reviewer-backed `publication_eval/latest.json` 过期。
- AI reviewer-backed eval 只有在 `study_id`、`quest_id`、`paper_root` 匹配，并且推荐动作携带同一个 publication work-unit fingerprint 时，才能覆盖同语义 gate 重放。
- 对 `bundle_stage_blocked` 的 specificity gate，AI reviewer eval 还必须携带完整 `claim/figure/table/metric/source_path` specificity targets；否则 publication gate 必须刷新 mechanical projection，补齐当前阻断目标，并重新要求 AI reviewer workflow。
- mechanical projection 只能具体化 blocker 和 owner handoff，不能关闭 AI reviewer 质量判断；AI reviewer output 也不能用缺 target 的旧记录阻止 publication gate 更新当前 blocker targets。

controller work-unit evidence adoption 采用同一条 AI-first 边界：

- adoption 只识别客观、受控、可归属的 evidence，例如 owner-authorized output、controller work-unit fingerprint、artifact checksum、restore proof、runtime event、runtime supervision tick、worker liveness 和 freshness/currentness proof。
- adoption 不判断医学叙事质量、科学结论质量、publishability 或 submission readiness；这些判断仍由 AI reviewer workflow、publication gate 与 MAS study truth surface 持有。
- `cold_archive`、`report_history`、runtime report store 和 lifecycle restore proof 只能作为 restore/report evidence source；它们可以证明历史报告、运行事件或 artifact 可恢复，但不能替代 `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_charter`、`evidence_ledger`、`review_ledger` 或当前 paper/package authority。
- 当当前 controller work unit 的受控证据被采纳后，runtime status 使用 `controller_work_unit_evidence_adopted` 表示本轮不再 relaunch 同一个 work unit；下一 owner 是 publication gate / controller recheck，且不得把该状态解释为 write、finalize、submission package 或 publishability 放行。
- 对 `analysis_claim_evidence_repair`，adoption 可采纳同一 work-unit fingerprint 绑定的 `artifacts/reports/mas_quality_repair/latest.json`、`report_history/artifacts/reports/report-*.json` 或 legacy traceability reaudit report；采纳条件只证明同一 controller work unit 已写出可归属修复证据，下一步仍必须回到 publication gate recheck。
- 若受控 worker 已经完成同一 work unit，supervisor 必须进入 gate recheck、owner route 前进或下一 owner handoff；不得因为 stale queue、fresh timestamp、archived report 或 report replay 重复派发同一 work unit。
- repo-side fix landed、archive proof verified、report history 可读取，只能说明平台或证据面已有修复证据；它不等同于具体 study 已恢复、live worker 已存在、论文质量已放行或 `current_package` / `submission_minimal` 已成为当前 authority。

runtime repair 与 publication gate 的 owner routing 使用 controller terminal 证据，而不是泛化的 gate blocker：

- `gate_specificity.required=true` 本身不足以阻止 runtime relaunch；异常 stopped、paused/resume 无 live worker、active/running 但无 live worker、retry budget exhausted 仍必须进入 runtime platform repair。
- 已交付人审/投稿包且无 live worker 的 parked handoff 是例外：当 `auto_runtime_parked` 或 delivery/current_package handoff 证据成立时，平台 repair redrive 不能自动重开 writer，只能等待显式 resume / revision intake。
- 若 latest task intake 明确是 reviewer revision 或 submission refresh，用户显式唤醒可以释放 delivered-package parking；`runtime_platform_repair` source 不能借同一个 intake 自动释放该停驻。
- 只有 resume/postcondition 或 runtime status 明确给出 `gate_needs_specificity` / `needs_specificity` / `publication_gate_specificity_required`，并且来源是 controller work-unit authorization 时，supervisor 才把 no-live-worker relaunch 转交给 publication gate。
- 若 stale specificity terminal 已被带完整 targets 的 publication eval 证明满足，platform repair 可以清掉旧 terminal，并把队列推进到下一 owner；已 applied 的 runtime repair 不应继续留在当次 action queue。

前台兼容性核对必须把 project / study / runtime owner 分开：

- NF-PitNET 003 不属于 DM002/DM003 runtime 风险核对的目标，不因 DM lifecycle 或 evidence adoption 文档更新触碰其 paper、current package、submission minimal 或 runtime-owned surface。
- DM002 / DM003 是否 live、是否 no-live-worker、是否 stale、是否需要人工介入，必须 fresh 读取 `study_runtime_status`、`study_progress`、`runtime_supervision/latest.json`、`publication_eval/latest.json` 与 `controller_decisions/latest.json`；不能用 repo commit、lifecycle migration ledger、cold archive 或 report history 代替当前 truth。
- 如果存在 live managed runtime，或 `study_runtime_status.execution_owner_guard.supervisor_only=true`，前台只能进入 supervisor-only 监管态；不得直接写 runtime-owned surface，也不得修改 DM workspace 的论文正文、`current_package` 或 `submission_minimal`。
- 如果当前 truth 是 `quest_status=active` 但 `active_run_id=null` / no live session / retry budget exhausted，前台只能报告 live 兼容风险并等待 controller/runtime owner 决策；不得把 repo 修复完成表述为 study 已恢复。

第二层 Developer Supervisor Mode 的时间策略固定为：

- scheduler/heartbeat：每 `3600` 秒一次
- owner request `2` 小时未被 pickup，标记 `owner_pickup_overdue`
- action queue `6` 小时仍未被消费或仍无进展，标记 `developer_supervisor_attention_required`
- developer heartbeat 必须评估内置 AI monitoring/repair 是否失效，并在 `developer_apply_safe` 与本机 family user config / auto-default authority gate 通过时消费队列、写 default executor dispatch request、执行 ready dispatch，或明确 blocked reason / next owner
- Developer Supervisor Mode 的 authority 优先来自 OPL family 用户级配置 `~/Library/Application Support/OPL/state/developer-supervisor.json`（可由 `OPL_STATE_DIR` 切换）；配置 `enabled=on` 时可显式开启，`enabled=off` 时强制降级到 `external_observe`，`enabled=auto` 时才使用 GitHub 登录作为安装期默认探测信号。
- 对 GitHub 用户 `gaofeng21cn` 的本机环境，`enabled=auto` 默认允许 `developer_apply_safe`；其他用户或生产环境默认降级到 `external_observe`，但可以通过受控用户级配置或 profile / command 显式开启。
- developer heartbeat 的作用域是 `workspace_dynamic_active_studies`：每轮从 workspace 当前 truth surface 发现 active / auto-resume / needs-repair 的 MAS study，新建 MAS 任务在下一次 heartbeat 自动纳入巡检，不要求在 Codex App prompt 里硬编码 study_id allowlist。
- 如果新任务出现 `quest_status=active` 但 `active_run_id=null`、`worker_running=false`、`runtime_liveness_status=none`、`quest_marked_running_but_no_live_session` 或 `runtime_recovery_retry_budget_exhausted`，developer heartbeat 必须判定为 active-but-not-running，并按 `scan -> consume -> execute-dispatch -> rescan` 接手平台修复。

这解释了之前的故障模式：heartbeat 只运行 `supervisor-scan` 时，系统能准确报告 `AI reviewer queue` 或 `publication_gate_specificity_required` 积压，但没有运行 `supervisor-consume`，也没有生成默认 Codex executor dispatch request，所以“AI 监测发现问题”与“AI 修复真正被派单执行”之间断开。后续如果只运行到 `supervisor-consume`，也只能得到 `dispatch_status=ready`；必须同 tick 运行 `supervisor-execute-dispatch`，才能把 ready dispatch 推进为 `executed` 或明确 blocked。

Developer Supervisor Mode 有三个正式模式：

- `internal_only`：只运行 MAS 内部 AI doctor/self-healing；不启用外层工程代理。
- `external_observe`：外层只读巡检，只投影 stale/blocked/why_not_applied，不生成可消费 safe-action request。
- `developer_apply_safe`：开发环境模式，允许 `supervisor-scan --apply-safe-actions --developer-supervisor-mode developer_apply_safe` 写 supervision/control/autonomy request、handoff packet 与 action queue。

`developer_apply_safe` 还受本机用户级配置保护：OPL family config 是 authority gate；GitHub 登录只在 `enabled=auto` 时作为默认探测信号。这样防止普通用户或生产研究环境意外获得 repo-level developer supervisor authority，同时允许受控机器随时手动开启或关闭。

`Codex App heartbeat` 不是这条 contract 的依赖。Codex App 可以作为本机开发环境的一个外部 caller 调用该入口；MAS canonical scheduler contract 仍是 scheduler adapter 定期调用同一个 MAS tick script。默认 adapter 是 `local`，macOS backend 使用 LaunchAgent。Linux `systemd --user`、宿主 `cron` 和 Docker/container manager 尚未作为 persistent local backend 落地；旧 workspace-local service manager 不再作为 active 选项。

workspace bootstrap 只渲染 MAS CLI entry，不再渲染 workspace-local host-service 模板：

- `ops/medautoscience/bin/supervisor-scan`
- `ops/medautoscience/bin/supervisor-consume`
- `ops/medautoscience/bin/supervisor-execute-dispatch`
- `ops/medautoscience/bin/supervisor-reconcile`

`supervisor-scan`、`supervisor-consume`、`supervisor-execute-dispatch` 仍保留为调试入口。正式同 tick 行为由 scheduler adapter 调用 MAS-owned tick script 承接；`supervisor-reconcile` one-shot 是调试、加速和 dry-run / apply 入口。二者都不得把 scheduler 提升为 study truth owner。

## Real-Paper Autonomy Soak Inventory

paper autonomy stability 的证据层独立于 functional monolith closeout。functional monolith 说明默认 runtime / status / progress / portal / diagnostic 能力已经 MAS-owned；真实论文自治稳定性还必须证明现有论文 workspace 在只读 inventory、supervisor reconcile、migration dry-run 和 soak 观察下可解释。

Lane 5/6 的 dry-run harness 是：

```bash
uv run python scripts/real-paper-autonomy-soak-inventory.py \
  --yang-root /Users/gaofeng/workspace/Yang
```

该 harness 枚举 `/Users/gaofeng/workspace/Yang/*/ops/medautoscience/profiles/*.toml`，只读输出：

- profile / workspace / runtime root 可读性；
- study status/progress surface 可读性；
- active、parked、completed 或 unreadable 的 reason；
- legacy MDS launcher/default runner evidence；
- profile/study migration readiness 的 dry-run 分类。

边界固定如下：

- 不写真实 workspace；
- 不执行 reconcile apply；
- 不做 migration apply；
- 不 relaunch runtime；
- 不写 `current_package`、`submission_minimal`、`publication_eval/latest.json` 或 publication gate；
- 不替代后续 Lane 1 blocker fix、Lane 2 reconcile CLI、Lane 3 owner_route schema、Lane 4 migration apply。

这份 inventory 是 `control-plane-autonomy` 与 `workspace-monolith-migration` focused lane 的输入证据；它只能证明“状态可枚举、可读、可解释”，不能证明论文质量、投稿 readiness 或 autonomous runtime 已完成迁移。

## Paper Autonomy Stability Evidence

`paper_autonomy_stability_evidence` 是真实论文自治稳定性的单一 read model closeout 面。它组合四类输入：

- `real_paper_autonomy_soak_inventory` 的真实 profile inventory；
- `runtime-supervisor-reconcile --dry-run` 等价的 `scan -> consume -> execute-dispatch -> rescan` 只读证据；
- `workspace-monolith-migrate --dry-run` 的 migration readiness / skipped / appliable reason；
- `real_workspace_soak_monitor` 的 status/progress、active/parked/completed reason 与 legacy diagnostic evidence。

该 read model 的完成边界固定为：

- 默认 `can_claim_landed=false`，除非真实 evidence 无 blocker；
- human gate、publication gate、parked handoff、profile unreadable、runtime truth 缺失等都必须列成 blocker 和 next action；
- 只读 dry-run 可以报告 blocked、skipped 或 appliable，不做 migration apply；
- 不写 `current_package`、`submission_minimal`、`publication_eval/latest.json`、`controller_decisions/latest.json`、runtime SQLite 或 restore archive。

因此，repo capability 可以记录为 `paper_autonomy_stability_evidence=evidence_read_model_landed`；真实论文自治稳定性只能在后续 evidence 无 blocker 时单独 closeout 为 `paper_autonomy_stability=landed`。

`medautosci runtime ensure-supervision` 默认注册或刷新 MAS-owned `local` adapter；macOS 会写入 LaunchAgent、tick script、install proof 和 scheduler receipt。显式 `--manager hermes` 会走 optional Hermes gateway cron adapter。如果显式传入 `--manager systemd|cron|launchd|docker`，命令必须 fail-closed 返回 `retired_workspace_local_service_manager`，不渲染模板、不给安装命令、不写旧 install proof。检测到旧 workspace-local host service 文件或 loaded 状态时，只能把它作为 `retired_cleanup_evidence` 清理，然后回到 MAS scheduler contract。

Hermes 对本地运行的必要性已经从默认路径移除；后续只能扩展正式 local scheduler adapter 的 backend 覆盖面。新增 backend 必须调用同一个 MAS tick script、写出同构 status / latest-run / SLO projection，并满足与 Hermes adapter 相同的幂等、去重、失败可见性和 retired-service cleanup 规则；不能复活旧 workspace-local service 模板作为隐式旁路。

容器环境不是 MAS-owned runtime。MAS 不维护 `medautoscience:latest` 镜像，也不生成 Kubernetes CronJob manifest。容器、volume、gateway、scheduler 与镜像发布由 OPL、Hermes 或部署平台持有；容器内如果需要触发 MAS 监管，只能调用 MAS CLI 的 canonical tick/reconcile 入口，例如：

```bash
medautosci runtime supervisor-scan \
  --profile <profile> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe
```

默认外部 scheduler 应调用 MAS-owned supervision tick script；如果只能调用单条命令，应调用同等 `medautosci runtime supervisor-reconcile --profile <profile> --mode developer_apply_safe --apply` one-shot。直接调用 `watch-runtime --max-ticks 1` 只覆盖外环检查，不覆盖同 tick 的 scan / consume / execute-dispatch 全链；上面的 scan 命令只用于调试单步扫描。

同时，外环还必须对“最近一次 supervisor tick 是否仍然新鲜”给出正式判断：

- `fresh`
- `missing`
- `stale`
- `invalid`

只要不是 `fresh`，前台就必须明确表述为“监管心跳异常”，不能继续把研究描述成被持续托管监管。

## 4. fail-closed live 语义

外层只有在下面条件同时满足时，才允许把运行面声明为 live managed runtime：

- `runtime_liveness_audit.status == live`
- `runtime_audit.worker_running == true`
- `active_run_id != null`

只要缺任一项，就不能再宣称“这是一个正常 live 的 managed runtime”。

这时必须明确落在以下之一：

- `recovering`
- `degraded`
- `external_supervisor_required`

这就是 fail-closed 语义。

## 5. reconciliation 规则

外环针对“表面 active/running、实际没有 live worker”的正式处理规则固定为：

### 5.1 首次发现掉线

- 写 `runtime_supervision/latest.json`
- `health_status = recovering` 或 `degraded`
- 若本次 tick 允许 apply，就调用 `ensure_study_runtime`

### 5.2 恢复成功

- 下一次 tick 确认：
  - `runtime_liveness_audit.status == live`
  - `worker_running == true`
  - `active_run_id != null`
- `runtime_supervision/latest.json` 回到 `live`
- `last_transition = recovered`

### 5.3 恢复连续失败

- `consecutive_failure_count` 增长
- 达到阈值后升级为 `external_supervisor_required`
- 写 `runtime_escalation_record.json`
- 前台和 Gateway/MAS 都必须看到明确的平台级 supervisor 介入信号
- control plane 不得继续把该状态伪装成 recovering dispatch

### 5.4 controller-owned finalize parking

如果 quest 进入下面这类停车态：

- `status = active` 或 `running`
- `active_run_id = null`
- `continuation_policy = wait_for_user_or_resume`
- `continuation_reason = unchanged_finalize_state`

那么 MAS 必须把它视为 `controller-owned parking`，而不是默认等用户。

也就是说：

- `finalize_ready` 只代表 paper-line-local recommendation
- 是否真的进入 `finalize`，仍由 MAS 外环根据 `publication_supervisor_state`、`controller_decisions/latest.json`、`pending_user_interaction`、`interaction_arbitration` 统一仲裁
- 只有当显式 contract 表明确实需要 external secret / credential 或 controller 要求人工确认时，才允许保持 user-blocking
- 否则这类 parking 必须被 MAS 自动吸收并恢复，不得把程序内 routing 判断抛给用户

### 5.5 stopped submission milestone parking

如果 quest 已经进入 `stopped`，但 MAS 的当前 controller truth 表明它只是 submission/finalize 里程碑停车，外环必须刷新 controller-owned parked decision，并把该状态写成正式停车，而不是把旧 stopped state 解释成可人工 patch 的许可。

在 `developer_apply_safe` 且本机用户级 authority gate 允许的前提下，supervisor scan 可以执行的动作只有：

- 通过 runtime backend `stop_quest` 或 already-stopped 结果确认 runtime 资源已释放
- 写 `artifacts/autonomy/repair_lifecycle/latest.json`
- 标记 `authority = controller_stop`
- 标记 `state = parked`
- 明确 `paper_package_mutation_allowed = false`
- 明确 `manual_study_patch_allowed = false`
- 明确 `quality_gate_relaxation_allowed = false`
- 明确 `medical_claim_authoring_allowed = false`

这条规则只收口 runtime/resource 与 controller decision projection。后续如果用户、导师或审稿意见重新打开同一 paper line，仍必须走 durable revision intake 与 MAS/MDS relaunch/resume，再从 canonical paper authority 重新生成投影包。

## 6. durable surfaces

这条链路当前正式落到下面几个稳定表面：

- quest-level `runtime_watch/latest.json`
- study-level `studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json`
- study-level `studies/<study_id>/artifacts/autonomy/repair_lifecycle/latest.json`
- workspace-level `artifacts/supervision/hourly/latest.json`
- workspace-level `artifacts/supervision/consumer/latest.json`
- workspace-level `artifacts/supervision/consumer/history.jsonl`
- study-level `studies/<study_id>/artifacts/supervision/consumer/<action_type>.json`
- study-level `studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/<action_type>.json`
- study-level `studies/<study_id>/artifacts/supervision/consumer/default_executor_execution/latest.json`
- study-level `studies/<study_id>/artifacts/supervision/requests/publication_gate_specificity/latest.json`
- study-level `studies/<study_id>/artifacts/supervision/requests/ai_reviewer/latest.json`
- quest-level `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- study-level `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- physician-facing projection `study_progress`

其中：

- `runtime_watch/latest.json` 负责 quest controller scan truth
- `artifacts/runtime/health/latest.json` 负责 reducer-owned runtime health truth
- `runtime_supervision/latest.json` 负责 outer-loop supervision read model，并携带 `runtime_health_epoch`
- `repair_lifecycle/latest.json` 负责投影 AI doctor repair 从 request、diagnosis、repair action 到 apply attempt 的生命周期
- `artifacts/supervision/hourly/latest.json` 负责跨 study 巡检 action queue 与 why-not-applied 投影
- `artifacts/supervision/consumer/latest.json` 与 study-level consumer packets 负责把外层 queue 消费成 request-owner handoff task
- `default_executor_dispatches/*` 负责把未被 owner 接手的 queue 转成默认 Codex CLI 执行器派单，不承担 publication/AI reviewer output authority
- `default_executor_execution/latest.json` 负责记录 ready dispatch 的执行尝试、owner callable surface、blocked reason 与 written execution ledger
- `artifacts/supervision/requests/*/latest.json` 负责保存 owner-visible request packet；它们是 request surface，不是 owner output surface
- `study_progress` 负责把这些 truth 翻译成医生/PI 能看懂的前台进度

不要把 runtime health truth 硬塞进：

- `publication_eval/latest.json`
- `controller_decisions/latest.json`

这两个表面仍然各自承担发表判断与 controller 决策的真相职责。

运行健康的用户可见动作必须来自 `RuntimeHealthKernel.canonical_runtime_action`；`last_launch_report`、`runtime_watch/latest.json` 与 `runtime_supervision/latest.json` 都只能作为 input event 或 read model。

## 7. 前台可见语义

只要 `runtime_supervision/latest.json` 处于：

- `recovering`
- `degraded`
- `external_supervisor_required`

前台就必须优先展示 runtime health，而不是被论文阶段覆盖。

也就是说，即使 paper line 正在 `finalize`，只要 worker 掉线，前台也要先明确告诉医生：

- 什么时候发现掉线
- 是否已经尝试恢复
- 当前是恢复中、恢复失败，还是已升级
- 下一步系统准备做什么
- 是否已经需要人工介入

只要 AI repair 处于 `ready_for_repair` 但未 apply，前台必须展示：

- `blocked_reason`
- `next_owner`
- `external_supervisor_required`
- 最近一次 `last_apply_attempt_at`

禁止只显示 `awaiting_ai_doctor` 或 `ready_for_repair` 而不解释为什么没有执行。

## 8. 与常驻 daemon 的关系

从 contract 角度说，`MedAutoScience` 没有必要因为这个问题变成第二个 authority daemon。

更合理的形态是：

- 先把单次 `supervisor tick` 做严谨
- 再由外部 scheduler 周期调用它

当前唯一 canonical scheduler owner 是 `MAS supervision scheduler contract`。默认 adapter 是 MAS-owned `local` scheduler；macOS backend 已落地为 LaunchAgent；Hermes gateway cron 只在显式 `--manager hermes` 时作为 optional adapter。旧 Linux `systemd --user`、宿主 `cron`、macOS `launchd` 和 Docker/container manager service scaffold 只在历史/debug 文档或 retired diagnostic response 中出现；active scaffold 不再渲染这些旧模板。

MAS 负责“这一跳应该怎么判、怎么恢复、怎么写 durable truth”。scheduler 只负责按周期调用，不持有医学或 runtime authority。

这能保证未来无论宿主变成 Codex、Gateway 还是 managed web runtime，合同都不漂。

## 9. 当前这条外环能恢复到哪里

当前这条外环已经能诚实做到：

- 发现 live worker 掉线、finalize parking 或恢复失败
- 通过 backend contract 请求 `ensure_study_runtime`、resume、relaunch 这类受控恢复
- 把 `clinician_update`、`next_action_summary`、`needs_human_intervention` 写入 `runtime_supervision/latest.json`
- 在连续失败后升级为 `external_supervisor_required`，并把平台级 supervisor 介入信号写到 `runtime_escalation_record.json`、`repair_lifecycle/latest.json`、hourly supervision scan 与 `study_progress`

行为等价口径另见 [MDS Behavior Equivalence Gap Matrix](../../references/mds-parity/mds_behavior_equivalence_gap_matrix.md)。当前 outer loop 能证明的是默认 MAS 独立监管和 scheduler-bound stale recovery；内层 turn completion continuation 已由 MAS kernel 达到行为等价。整体仍不声明与旧 MDS resident daemon、WebSocket terminal streaming 或 connector background threads 完全等价。
