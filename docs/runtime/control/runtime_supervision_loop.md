# Runtime Supervision Loop

Owner: `MedAutoScience`
Purpose: `domain_supervision_read_model_and_owner_receipt_contract`
State: `active_runtime_control_support`
Machine boundary: 本文解释 MAS domain supervision / read-model / owner receipt 语义。机器真相继续归 MAS contracts、schema、CLI/MCP/API payload、`progress_projection`、`domain_health_diagnostic`、`publication_eval/latest.json`、`controller_decisions/latest.json`、sidecar receipt 和真实 workspace artifact。通用 provider workflow、queue、attempt ledger、retry/dead-letter、operator projection、memory/artifact locator 与 App/workbench shell 归 OPL Framework / shared family layer。

这份文档冻结 `MedAutoScience` 的 domain supervision 合同，也就是 MAS 如何读取 study/runtime-facing truth、判断 blocker、写出 supervision projection 和 owner receipt。它不再描述 MAS 自建 generic scheduler / queue / runtime platform 的计划。

一句话结论：

- `MedAutoScience` 默认不是 resident HTTP/WebSocket daemon
- 默认 scheduler owner 是 OPL `opl_provider_runtime_manager`，默认 adapter 是 `opl_family_runtime_provider`；MAS `local` adapter / LaunchAgent 已物理退役为 tombstone/provenance refs，不再安装、刷新、状态检查、清理或触发 MAS-owned LaunchAgent / tick script
- OPL-hosted production wakeup、queue、attempt、retry/dead-letter 和 operator projection 归 OPL provider；OPL 只能消费 MAS sidecar / owner receipt，不能写 MAS study truth、publication judgement、paper/package authority 或 artifact gate
- 当前 MAS domain tick contract 依序调用 `runtime domain-health-diagnostic --apply`、`runtime owner-route-reconcile --apply-safe-actions`、`supervisor-consume`、`supervisor-execute-dispatch`；默认由 OPL provider/runtime manager 唤醒，Hermes legacy diagnostic adapter 可显式生成脚本，local tombstone/provenance path 不生成脚本
- 该 outer loop 不拥有 runner completion 后的连续科研主循环，也不维护 generic runtime kernel；内层 `turn completion -> next turn` 由 OPL provider 承载，MAS 只提供 domain owner route、authorization、receipt、typed blocker 与 artifact/publication authority refs
- 旧 workspace-local `systemd` / `cron` / `launchd` / `docker` service manager 已退役；检测到它们时只作为 cleanup evidence，不作为 active scheduler 选项
- 这个 loop 的职责是发现掉线或 stale truth、执行 MAS-authorized reconciliation、写出 durable supervision surface / owner receipt，并把结果翻译成前台可见的人话

## 1. 总目标

我们要解决的不是“把日志看起来拼热闹”，而是下面这三个正式目标：

- worker 掉线后，外层必须能在有限时间内发现
- 发现后必须按固定规则自动恢复或升级
- 前台必须能持续看到几点几分发生了什么、研究推进到哪一步、现在是否需要人工介入

这三个目标必须同时成立，才算 MAS domain runtime-facing surface 可被 direct/local diagnostics 或 OPL-hosted provider 可靠托管。

除此之外还有一条 fail-closed 边界：

- 如果 outer supervisor tick 自己已经缺失或陈旧，系统也不能继续假装“MAS 仍在稳定监管”
- 这种情况必须作为正式监管异常直接暴露到 status / progress surface

## 2. authority 边界

这里的外环应按四层分工理解：

- `OPL Framework / shared family runtime`
  - 持有 production provider、queue、attempt ledger、retry/dead-letter、operator projection、generic state-machine runner、App/workbench shell 与跨 domain projection
  - 只消费 MAS 显式导出的 sidecar task、typed blocker、owner receipt 和 artifact locator，不解释医学研究状态
- `Scheduler Contract / Adapter`
  - 默认 owner 是 OPL `opl_provider_runtime_manager`，负责 provider-backed cadence、scheduler lifecycle、provider SLO、job registry/latest-run projection 和 runtime manager 投影
  - MAS contract owner 只保留 paper-progress SLO/read-model、domain tick payload、owner receipt、typed blocker、safe action refs 和 legacy tombstone/provenance projection
  - MAS-owned `local` adapter 已物理退役；公开 CLI 不再暴露 active `local` status/remove/ensure path，旧 LaunchAgent / tick script 只保留 tombstone/provenance refs
  - 显式传入 `hermes` 只走 legacy diagnostic adapter；旧 `systemd|cron|launchd|docker` manager 已移除
- `MedAutoScience`
  - 医学研究治理、supervision judgment、projection 与 reconciliation owner
- `MAS domain owner surfaces`
  - MAS 授权 work unit、domain event refs、recovery decision refs、typed blocker、owner route、artifact/publication authority refs 与 owner receipt
- `MedDeepScientist`
  - frozen source archive、historical fixture 或显式 backend audit / explicit archive import reference

对应的监管外环是：

- `provider-or-scheduler-triggered`
- `controller-judged`
- `tick-driven`
- `fail-closed`

它不是：

- 第二个 authority daemon
- 第二份 runtime truth
- 复刻旧 MDS resident daemon / WebSocket / terminal streaming 的替代物

所以权责边界固定为：

- MAS domain owner surfaces 持有医学 execution authorization / recovery decision / event refs / owner receipt truth
- `MedAutoScience` controller 持有 supervision / projection / reconciliation truth
- `OPL Framework` 持有 generic hosted runtime primitives，不持有 MAS domain truth
- `MedDeepScientist` 不持有默认 MAS operation truth

## 3. 正式执行形态

默认 outer-loop cadence 由 OPL provider/runtime manager replacement 承载。MAS domain tick sequence 是 OPL scheduler/provider 需要调用的 domain contract；`local` 已物理退役为 tombstone/provenance refs，不生成或触发 MAS 本机脚本。Hermes adapter 只剩 legacy diagnostic / cleanup provenance；OPL-hosted production path 应通过 OPL provider 消费 MAS sidecar / owner receipt，而不是把 Hermes 或 local scheduler 写成 MAS 的 generic runtime owner。旧 Hermes adapter 脚本可能位于：

- `~/.hermes/scripts/med-autoscience/<workspace-key>/watch_runtime_tick.py`

该脚本不再由 `runtime-ensure-supervision --manager hermes` 生成或刷新；`runtime-supervision-status --manager hermes` 只读取旧 job/script/session/gateway 状态，`runtime-remove-supervision --manager hermes` 只移除旧 job/script。当前 MAS one-shot tick contract 仍由 OPL provider 调用，顺序执行四个 MAS workspace entry：

1. `medautosci runtime domain-health-diagnostic --runtime-root <runtime_root> --apply`
2. `medautosci runtime owner-route-reconcile --profile <profile> --apply-safe-actions --apply-runtime-platform-repair --developer-supervisor-mode developer_apply_safe`
3. `ops/medautoscience/bin/supervisor-consume --mode developer_apply_safe --apply`
4. `ops/medautoscience/bin/supervisor-execute-dispatch --mode developer_apply_safe --apply`

`domain-health-diagnostic` 这一步每次至少做四件事：

1. 读取 managed study 的 `progress_projection` 或 `ensure_study_runtime`
2. 扫描 live quest 的 `domain_health_diagnostic`
3. 生成 study-owned `runtime_supervision/latest.json`
4. 必要时写出或刷新 `runtime_escalation_record.json`

随后 `supervisor-scan` / `supervisor-consume` / `supervisor-execute-dispatch` 负责把 workspace-level action queue、default executor dispatch request 和可执行 dispatch receipt 收成同一轮证据。也就是说，外环的核心不是“循环本身”，而是同一轮 tick 的 MAS controller contract。

真实 workspace 可能仍保留旧 Hermes job script，只调用单步 legacy `watch-runtime` wrapper。这类状态不是新 contract；默认 operator 入口应先通过 `runtime-supervision-status --profile <profile>` 读取 OPL projection，再用显式 Hermes status 查看 legacy drift，必要时用 `runtime-remove-supervision --manager hermes` 清理旧 job/script。`runtime-supervision-status` 的职责是暴露 job、script、latest session 与 drift，而不是把旧 script 解释成新的 desired behavior。

跨 study 的巡检入口是 supervisor scan：

```bash
medautosci runtime owner-route-reconcile \
  --profile <profile> \
  --studies <study_id> <study_id> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe
```

该入口写出 workspace-level `artifacts/supervision/hourly/latest.json`，只消费 MAS durable truth surfaces：`progress_projection`、`study_progress`、`domain_health_diagnostic`、`publication_eval/latest.json`、`controller_decisions/latest.json` 与 AI repair lifecycle。它的职责是形成 `action_queue`、`why_not_applied`、owner-visible request packet、typed blocker、owner receipt ref 与 `external_supervisor_required`，而不是直接修改 paper/current_package，也不是维护 generic OPL queue。

2026-05-08 Runtime Continuity closeout 又把旧 MDS daemon 退役后最关键的两类用户可见行为补齐为 MAS-owned read model / owner receipt surface：

- `runtime_session` read model：从 `progress_projection.runtime_liveness_audit`、SQLite runtime lifecycle store、owner_route/dispatch receipts 和 historical fixture / explicit archive import reference 依序投影 `active_run_id`、`last_known_run_id`、`worker_state`、`worker_running`、`last_seen_at`、event cursor、stdout ref 与 freshness。它只读，不写 runtime truth。
- `recovery_intent` ledger：supervisor scan 在每个 study projection 中写出 `runtime_recovery_intent`，记录恢复原因、next owner、retry budget、dedupe fingerprint、last attempt/result、next eligible tick 与 `current_action`。允许动作固定为 `await_next_tick`、`safe_reconcile_ready`、`recovering`、`parked`、`human_gate_required`、`escalated`。
- `runtime_reconcile_trigger` projection：`study-progress`、workspace cockpit、product-entry status 和 Progress Portal 可以显示“是否可请求一次 safe reconcile dry-run”。该投影本身不执行 reconcile、不写 runtime、不写 paper/current_package、不写 publication gate；页面刷新只会生成幂等推荐命令和 blocked reasons。

safe reconcile 的核心边界是 fail-closed：route stale、owner mismatch、manual parked、`quest_status=parked`、completed、human gate、publication gate missing、retry exhausted 都不得进入可请求状态。真正恢复仍必须走 `RuntimeHealthKernel -> owner_route -> executor -> rescan` 闭环。

2026-05-08 Runtime Evidence closeout 进一步把外层监管延迟做成可解释 SLA，而不是新增常驻进程：

- `outer_supervision_slo` read model 固定字段包括 `last_tick_at` / `latest_scheduler_run_at`、`last_reconcile_at` / `latest_supervisor_reconcile_at`、`next_due_at` 等价阈值、`tick_age_seconds` / `age_seconds`、`state=fresh|due|stale|missing|blocked`、dedupe fingerprint、authority flags 与 canonical `domain-route-reconcile --dry-run` 推荐命令。
- `fresh` 表示最新 MAS scheduler tick 或 supervisor reconcile 仍在 freshness window 内；`due` 表示应安全加速一次 one-shot reconcile；`stale` 表示外环监管已经陈旧；`missing` 表示缺监管事件或 status surface；`blocked` 表示最新 scheduler tick 失败、旧 service 冲突或 supervision contract 本身阻塞。
- 该 read model 投影到 `runtime-supervision-status`、`domain-route-reconcile` receipt、`runtime_reconcile_trigger`、`study_progress`、workspace cockpit、Product Entry 和 Progress Portal。
- 它只允许页面或 CLI 显示推荐命令，或由已有 controller/supervisor safe surface 做 dry-run/apply；读入口刷新不能直接 relaunch worker、写 runtime truth、写 paper/current_package、写 `publication_eval/latest.json` 或写 `controller_decisions/latest.json`。
- 它不改变当前 owner 分工：默认 scheduler owner 是 OPL provider/runtime manager；`local` scheduler 每 `300` 秒调用 one-shot tick 只属于显式 legacy diagnostic / cleanup adapter；Hermes gateway cron 只在显式 `--manager hermes` 时作为 legacy diagnostic adapter；旧 workspace-local `launchd/systemd/cron/docker` service 仍是 retired cleanup evidence。OPL-hosted production wakeup 由 OPL provider 持有；MAS scheduler owner / adapter / status 同构计划只覆盖 MAS direct/local diagnostic contract，以 [Domain SLO Scheduler Projection Contract](./domain_slo_scheduler_projection_contract.md) 为准。

这条外环和内层 turn lifecycle 的分界是固定的：正常 runner 返回后的 `active_run_id` / `worker_running` 清理、queued user message 优先级、`continuation_policy=auto` 的约 `0.2s` 下一 turn、human/terminal gate 停止，都由 `mas_runtime_core` 的 Runtime Turn Lifecycle Kernel 处理。MAS scheduler tick 只负责发现外层 stale/no-live、刷新 supervision/read-model、触发 safe recovery 或把异常升级；它不再是自动科研连续跑的主循环 owner。

2026-05-09 Runtime Watchdog / LLM cost closeout 把“低延迟感知”和“低成本调度”拆成两层，而不是缩短 300 秒 scheduler tick：

- 真实 runtime turn 由 MAS per-run worker wrapper 托管。wrapper 是每个 run 一个子进程，负责启动并等待 `codex exec` 子进程，刷新 `worker_lease.json` 中的 `monitor_kind=mas_per_run_worker_wrapper`、`monitor_pid`、`child_pid`、`heartbeat_at`、`last_output_at`、stdout/stderr cursor、`monitor_state` 和 `stale_reason`，并在 child exit 后立即写 `runner_exit.json`、调用 `complete_turn_and_normalize`。它不是 resident MDS daemon，也不是 workspace-local service。
- `worker_lease` / `runtime_session` / Live Console read model 现在能区分 `monitor_state=live|exited|stale|lost|unknown`，并展示 last worker heartbeat、last output、monitor owner、why waiting 与 `will_start_llm`。child exit 走低延迟归一化；wrapper lost 或 heartbeat stale 才进入 recovery intent / safe reconcile 路径，等待 MAS scheduler fail-safe tick 或显式 one-shot reconcile。
- runtime action cost contract 固定四类动作：`observe_only`、`reconcile_dry_run`、`controller_apply`、`codex_worker_dispatch`。`domain-route-reconcile --dry-run`、Portal/Console 刷新和 SLO 投影都必须是 `will_start_llm=false`；只有真正进入 MAS runtime turn / 新 owner_route action fingerprint 并启动 Codex worker 时才是 `codex_worker_dispatch`。
- supervisor reconcile、default executor dispatch 和 runtime watch report 都投影 `codex_dispatch_count`、`suppressed_dispatch_count`、`dispatch_budget_window` 与 `action_fingerprint`。重复 tick 只能刷新 read model 或写 no-op suppression；同一 study 的同一 owner_route / work-unit fingerprint 不得重复启动 Codex worker。

这个设计参考了成熟控制面经验：Kubernetes controller 用 current/desired state reconcile，不把每个 controller 都做成互相耦合的巨大循环；Temporal 用 Activity heartbeat / timeout 及时发现长任务 worker failure；systemd watchdog 用 keep-alive ping 区分服务存活；EventBridge Scheduler 用 retry / DLQ 让调度失败可追踪。MAS 对应做法是 per-run heartbeat + fail-closed reconcile + dispatch 去重，而不是高频 LLM cron。

2026-05-09 Paper Progress Degradation closeout 把“论文推进变慢”的 P0/P1 风险接进同一条外环合同：

- `paper_progress_degradation_classifier` 把旧 MDS 行为差异按是否影响自动论文产出分类；Portal/Console 诊断体验不被当作生产降级，connector/GitOps/旧 daemon lifecycle 不重新进入默认 backlog。
- controller work-unit evidence adoption 后，supervisor 必须把同一 work unit 推进到 `owner_handoff` / `publication_gate_recheck`，并带 `next_owner`、`next_work_unit`、route reason 与 idempotency key；不得继续 redrive 同一 `analysis_claim_evidence_repair` fingerprint。
- repeat suppression 的职责是阻断重复 dispatch 和无效 LLM 花费；它不得阻断 owner handoff、publication gate recheck 或 AI reviewer / writer next owner。
- `paper_progress_stall` read model 统一表达 `same_fingerprint_loop`、`read_churn_without_artifact_delta`、`stale_truth_surface`、`runtime_recovery_retry_budget_exhausted`、handoff 状态和 source refs。
- `domain-route-reconcile --dry-run` 是零 dispatch 诊断；`--apply` 只有在 fresh owner_route、未 parked、未 completed、无 human gate、无 publication gate missing、retry budget 未耗尽且 action fingerprint 新鲜时，才能通过 Codex worker dispatch。
- clean Python runner 对 `domain-route-reconcile --apply`、`domain-owner-action-dispatch --apply` 和 `sidecar dispatch` 这类 owner apply 入口启用 analysis extra，确保 analysis / harmonization owner 拿到 reproducible model rebuild 所需的统计依赖；dry-run 继续保持轻量同步，不安装 analysis extra。
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
- `owner_callable_registry` 是 callable owner 的机器锚点，当前注册 `MAS/controller`、`analysis_harmonization_owner`、`source_provenance_owner`、`provenance_limited_harmonization_owner`、`ai_reviewer`、`publication_gate`、`quality_repair_batch`、`gate_clearing_batch` 与 `delivery_sync`。`owner_callable_surface_missing` 是 controller-consumable blocker 或 repo-level callable gap；当 `requires_user_input=false` 时，不得把它投影成真实 `waiting_for_user`。当 controller decision 用 `ensure_study_runtime` 重新拉起 `unit_harmonized_validation_uncertainty_and_grouped_calibration` 这类 hard-methodology work unit 时，managed worker 必须投到 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`，不能把缺少 generic runtime action 当成用户等待或 MAS 私有 control-plane 需求。
- submission authority / delivery closure 必须在同一个 work-unit transaction 中完成 source freshness proof、delivery sync 和 gate replay。来自旧 MDS worktree 的绝对 `paper/...` 路径只可规范到当前 paper root 的同后缀 source ref，不能作为 current source blocker。
- DM002、DM003 和 Obesity 的 read-only validation 要把 `actual_write_active`、`package_delivered`、`meaningful_artifact_delta`、`next_owner`、`why_not_progressing` 同时展示；只要 publishability / AI reviewer / submission QC 未放行，就不得把 downstream package missing 写成论文进度。
- control-plane authorization 必须区分前台人工接管和 MAS managed worker：`foreground_paper_write_allowed=false` 只阻止 Codex App / manual agent 绕过 MAS 直接改论文；`managed_worker_paper_write_allowed=true` 表示当前 MAS controller work unit 可授权 worker 修改 canonical `paper/` 修订面。`publication_gate.allow_write=false` 只阻止 bundle/submission/current_package/proofing 写面，不能阻止上游 analysis-campaign/write stage 的 canonical paper 修订。
- `stale_study_delivery_mirror` 是 downstream delivery/package 信号。它可以阻止 submission bundle 交付闭环，但不得阻断仍需分析、证据、图表、指标或正文修订的 paper stage；若 delivery lane 缺 freshness proof 或 source-to-target 闭合证据，controller 应产生 terminal/actionable delivery blocker，而不是派发会把 Codex CLI 吸入 replay loop 的泛化写作任务。

2026-05-10 Paper Progress Reconciler 重构把上面的目标接入同一个 outer-loop receipt：

- `paper_progress_state` 是所有 paper-line 入口共享的 read model。它只从当前 study/runtime/progress/controller truth surfaces 推导七类公开状态：`progressing`、`awaiting_controller_redrive`、`blocked_controller_route`、`awaiting_callable_owner`、`awaiting_human`、`downstream_only`、`terminal_delivered`。
- `paper_progress_reconciler` 是 level-triggered：每次 `owner-route-reconcile` tick 都重新读取 before/after scan、consume 和 execute projection，输出 `desired_state`、`current_state`、`delta`、`decision`、`callable_contract` 与 `action_receipt`。它不信任旧 packet 的 stale conclusion，也不把 previous closeout 文案当作 current truth。
- dry-run receipt 必须保持零 dispatch；apply receipt 只有在 owner callable contract 存在、`requires_user_input=false`、`source_fingerprint` 新鲜，并且当前 execution / controller route 能解释该 action 时，才允许写 outbox receipt。
- `paper_work_unit_outbox` 是 work-unit transaction 的落账点。相同 `idempotency_key` 和相同 intent 返回 replay receipt；相同 key 不同 intent 写 `failed_closed/idempotency_key_intent_conflict`；同一 `source_fingerprint` 已启动 worker 时写 `duplicate_source_fingerprint`，不重复启动 worker。该 duplicate receipt 只阻止重复 worker start，不阻止下一 owner handoff、gate replay 或 registry repair。
- outbox 同时写 JSONL receipt 和 SQLite refs index `paper_work_unit_receipts` 索引。SQLite 只做 receipt/history/cursor projection，不成为 publication gate、controller decision、paper package、submission source 或 runtime-owned live truth。
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

这些策略同时投影到 `two_layer_ai_repair_policy`，由 `owner-route-reconcile` 和 owner-route consume 输出。这样前台看到“AI reviewer 队列积压”时，能同时看到内置 AI repair 是否已接上、是否超时，以及下一层开发者 supervisor 是否已到接手阈值。

旧 MAS watchdog 的可执行价值收敛为 MAS domain health / reconcile / owner repair kernel。`domain_health_diagnostic` 可以聚合 runtime health、safe reconcile evidence、owner route 与 AI doctor repair lifecycle；它不能作为外部 provider、OPL family task 或前台 agent 的 live runtime root 写入口。尤其在 `execution_owner_guard.supervisor_only=true` 时，apply 只允许同一 `(study_id, quest_id)` 上的 MAS controller-owned repair：action 必须是 `controller_repair`、owner 必须是 `mas_controller`、repair kind 必须在 runtime recovery allowlist 内，并且当前 `progress_projection` / runtime recovery payload 必须携带 `runtime_recovery_allowed=true`、open dispatch gate、`controller_repair_authorization(_ref).authorized=true`、`action=runtime_recovery` 与 `control_surface=domain_health_diagnostic`。外部/provider/OPL/platform repair、缺 controller repair authorization、route 不匹配或 recovery evidence 不足时必须 fail closed，写出明确 blocked reason，并保持 paper/package、publication gate、controller decision 和 live runtime-owned roots 不被前台直接改写。

2026-05-10 OPL/Hermes family runtime bridge closeout 把 read model 到执行队列的断点收口为正式 sidecar 合同：

- `medautosci sidecar export --profile <profile> --format json` 会在每个 study projection 中输出 `autonomy_continuation`，并在顶层输出 `pending_family_tasks[]`。
- 当 `slo_status.state=breach`、`runtime_supervision.runtime_decision=blocked`、`runtime_liveness_status=parked` 或 `recovery_intent.current_action=safe_reconcile_ready`，且 controller 没有 `stop_loss` / terminal stop / hard human gate 时，MAS 会生成幂等 task，默认 `task_kind=domain_route/reconcile-apply`。
- OPL/Hermes 的职责是 hydration、dedupe、queue、retry、dead-letter、approval 和 local inbox notification；它只能消费 MAS 显式导出的 `pending_family_tasks[]`，不能从只读 projection 自行推断医学动作。
- `medautosci sidecar dispatch --task <task.json> --format json` 收到 `domain_route/reconcile-apply` 后，回到 MAS owner 内调用 `domain-route-reconcile --mode developer_apply_safe --apply`，再由 MAS 自己的 `scan -> consume -> execute-dispatch -> rescan` gate 决定是否启动 Codex worker、no-op、blocked 或 human gate。
- 这个桥仍禁止写 `publication_eval/latest.json`、`controller_decisions/latest.json`、paper/current_package、submission package 或 artifact gate；它只把“发现了可自动处理的 blocker”转换成 durable executable ticket。

当 `action_queue` 包含 `publication_gate_specificity_required` 或 `return_to_ai_reviewer_workflow` 时，supervisor scan 只能物化 request packet：

- `publication_gate_specificity_required` 的 owner 是 `publication_gate`
- `return_to_ai_reviewer_workflow` 的 owner 是 `ai_reviewer`
- request packet 的 authority 是 `request_only`
- 预期输出仍回到对应 owner 的 durable surface，例如 `publication_eval/latest.json`
- supervisor 本身不得写 `publication_eval/latest.json`、不得放宽 quality/publication gate、不得改 `paper/current_package` 或 `manuscript/current_package`

Clean paper-authority cutover 的 blocked work unit 按同一条 owner chain 处理。旧 MDS / 旧 MAS 的 `publication_eval/latest.json`、prose review、controller decision、delivery manifest、current package 与 zip 只能作为 provenance；它们不能被 token normalizer、reader alias 或旧 schema 映射重新读成当前 quality / delivery truth。若新 MAS 在执行 `return_to_ai_reviewer_workflow` 或 `run_quality_repair_batch` 时发现缺 canonical paper inputs，controller action 必须 fail closed，写出 typed blocker `canonical_paper_inputs_rehydrate_required`，并把 `legacy_artifact_reader_allowed=false` 与 `mechanical_blueprint_as_canonical_allowed=false` 投影给 `write` owner。

`domain_health_diagnostic` 遇到这种 controller work unit blocked 时不得把外环崩成平台异常。它必须写 `controller_work_unit_blocked` wakeup audit / work-unit ledger event，把 blocker 留给 supervisor scan、consumer 和 dispatch executor 继续路由；该 no-op 不计为 executed dispatch，不关闭 publication gate，不写 `publication_eval/latest.json`，也不生成 `submission_minimal` 或 `manuscript/current_package`。随后 `write` owner 重新物化 canonical manuscript inputs，AI reviewer 再基于当前 request/manuscript digest 产生新的 publication eval，delivery owner 只有在 AI reviewer-backed authority current 后才能重建正式包。

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

- `controller_decisions/latest.json` 的 action 必须是 MAS domain owner-route 可解释的 continuation action；
- `controller_decisions/latest.json` 的 work-unit fingerprint 必须出现在当前 `publication_eval/latest.json`；
- next work unit 不能只是 `gate_needs_specificity` / `needs_specificity` terminal；
- 满足以上条件时，旧 action token `runtime_platform_repair` 只物化 MAS controller authorization 与 OPL runtime owner-route handoff；owner 是 MAS domain controller，generic queue / attempt / provider resume owner 是 OPL；
- handoff 前必须把当前 controller decision 与 publication eval 中同 fingerprint 的具体 `specificity_targets` / actionable target 写入 MAS authorization refs；没有可执行 target 时不能把 no-live 状态误判成可恢复 runtime；
- 只有没有当前 controller route 或当前 route 已不对齐时，retry budget exhausted 才能升级为 external supervisor handoff。

完成态与停驻态也属于 current truth。若 `progress_projection` / `study_progress` 已经给出 `quest_status=completed` 且 completion contract resolved，或 `auto_runtime_parked.parked=true` / `canonical_runtime_action=await_explicit_resume` 且没有 live worker，scan 必须清空 stale lifecycle、不给 AI reviewer 或 external supervisor 排队，并把 `owner_route.current_owner` 投为 `controller_stop` 或 completed truth。manual hold、publishability stop-loss、package-ready handoff 和 external metadata pending 都只能等待显式 resume / revision intake，不能被 no-live 噪声、旧 publication gate 或旧 AI reviewer required 重新打开 writer。

投稿包里程碑本身也是停驻边界。若最新 task intake 早于 controller-authorized delivery manifest / current_package，且 delivery manifest 签名一致、`current_package.zip` 与 audit manifest 存在、publication gate 为 clear / bundle-stage-ready，则这份交付面消费旧 task intake，系统必须投成 package-ready handoff / explicit-resume wait。旧 Codex CLI prompt、旧 `controller_work_unit_pending`、旧 reviewer-revision intake 或 active run 标签不能覆盖这个终局；只有更新的用户修改请求、stale delivery / authority blocker、AI reviewer-backed quality blocker 或显式 resume 才能重新打开 writer。

AI reviewer-backed quality blocker 是该停驻边界的正式例外，owner 仍然是 `ai_reviewer`，不是 submission metadata lane。若 `publication_eval/latest.json` 与 `controller_decisions/latest.json` 当前一致指向 `return_to_ai_reviewer_workflow`，并且 domain transition 为 `ai_reviewer_re_eval` / `domain_transition_ai_reviewer_re_eval`，paused / resumable / live runtime 必须优先保持或恢复到 AI reviewer owner route，让 AI reviewer 关闭医学论文写作质量判断。普通仅缺作者信息、伦理声明、AI declaration 或期刊 metadata 的 submission metadata parking 仍保持 explicit-resume wait 或 live pause，不能因这个例外被放宽成自动写作或自动交付。

同一轮 owner action 必须满足幂等合同。`route_epoch` 和 `source_fingerprint` 决定本轮 owner routing，具体 repo-side owner 还必须给自己的 work unit 写稳定 fingerprint：

- fingerprint 只表达语义输入，不表达普通观测时间；内容相同的 JSON/资产被同一 owner 重写后，不能因为 `mtime` 变化制造新 work unit。
- 对 package/submission authoring 类 repair，失败可在同 fingerprint 下重跑，因为缺失输出可能由同一 owner 重新生成。
- 对 non-authoring artifact input failure，例如 display input payload 缺必要字段，重复执行不会产生新信息；同 fingerprint、同 blocking artifact 的失败必须复用为稳定 blocked truth，并继续把具体 `blocking_artifact_refs` 暴露给 scan / progress / owner route。
- 因此 `scan -> consume -> execute-dispatch -> rescan` 的收敛结果应是“owner 前进或具体 blocker 稳定”，不能是同一 action 无限重放。

外层工程消费入口是：

```bash
medautosci domain-route-consume \
  --profile <profile> \
  --studies <study_id> <study_id> \
  --developer-supervisor-mode developer_apply_safe \
  --apply
```

该入口只把 scan queue 转成 owner handoff task，写入 workspace-level `artifacts/supervision/consumer/latest.json` / `history.jsonl` 以及 study-level consumer packet。它负责说明 `request_owner`、`required_output_surface`、`request_packet_ref`、forbidden surfaces 与 verification commands；它不执行 publication gate 或 AI reviewer 的专业判断，也不修改论文包。

从 2026-05-08 起，developer scheduler 的正式同 tick 行为是 `supervisor-reconcile` one-shot；该入口内部执行 `scan -> consume -> execute-dispatch -> rescan` 并写出 reconcile receipt。三段式入口保留为调试面：

```bash
medautosci runtime domain-route-reconcile \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply
```

调试时可拆成：

```bash
medautosci runtime owner-route-reconcile \
  --profile <profile> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe

medautosci domain route-consume \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply

medautosci domain route-execute-dispatch \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply
```

MAS managed Codex CLI worker 在 prompt 内执行 controller action 时会额外传入 `--managed-runtime-worker`。这不是外层开发者权限开关；它是受限的内层 worker identity。`domain route-execute-dispatch` 只有在环境和 runtime truth 同时证明当前进程属于同一 `quest_id` / `active_run_id`，并且 `.ds/runtime_state.json:last_controller_decision_authorization` 明确授权该 `controller_action` 时，才允许用当前 runtime authorization 重建本次 action 的 owner route。外层 heartbeat、人工 CLI、OPL sidecar 和普通 supervisor tick 不能使用这条通道绕过 `developer_apply_safe` gate。

如果未显式传 `--studies`，`supervisor-consume` 从最新 `hourly/latest.json` 的 `action_queue` 推导需要消费的 study 列表。consumer 会额外写出 study-level default executor dispatch request：

- `studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/<action_type>.json`

这个 dispatch request 是“把问题交给默认 Codex CLI 执行器”的机器可读派单面，包含 owner、输入 surface、必需输出 surface、forbidden surfaces 与 prompt contract。它不等同于 owner output；例如 AI reviewer 的 output 仍必须由 AI reviewer workflow 写回 owner-authorized durable surface，consumer 本身不得写 `publication_eval/latest.json`。

`domain route-execute-dispatch` 是第三步执行/落账面。它读取 `default_executor_dispatches/*`，校验 forbidden surfaces 和 prompt contract 后，只调用 owner 授权的 repo surface，或写出 `blocked_reason`。当前允许行为是：

- `publication_gate_specificity_required`：重放 `publication_gate` owner 的 gate report，并只物化 controller-owned `publication_eval/latest.json`，要求推荐动作带具体 `claim/figure/table/metric/source_path` targets。
- `runtime_platform_repair`：历史 action token；当前只调用 domain route scan 的 owner-route handoff path，产出 MAS authorization / typed blocker / owner receipt refs，OPL 负责 queue hydration、attempt 和 provider resume/relaunch。
- `return_to_ai_reviewer_workflow`：如果没有结构化 AI reviewer record，不生成评审结论，写 `blocked_reason=owner_callable_surface_missing` 与 `required_repo_surface=structured_ai_reviewer_default_executor_workflow`。

如果 `return_to_ai_reviewer_workflow` 的默认执行记录显示 `blocked_reason=ai_reviewer_workflow_failed` 且错误为 `current_package_freshness_source_eval_id_mismatch`，下一轮 supervisor scan 必须先路由到 `current_package_freshness_required` / `artifact_os`。这不是论文完整度或写作质量的脚本门禁；它只修正 owner 顺序：AI reviewer 仍持有医学质量判断，artifact owner 只负责把 human-facing current package 的 freshness proof 刷到当前 AI reviewer publication eval，之后再重试 AI reviewer / bundle-stage 路径。

执行器的默认读取权威是 workspace-level `artifacts/supervision/consumer/latest.json`。未显式传 action type 时，`domain-owner-action-dispatch` 只能从 consumer latest 当前列出的 ready dispatch 中筛选执行；study-level `default_executor_dispatches/*.json` 目录里的旧文件不能单独作为执行票据。显式传 action type 时，executor 可以读取同名 study-level persisted dispatch，但必须同时满足三项 currentness 条件：dispatch 仍是 `ready`，action/study/owner 与请求一致，并且对应 `artifacts/supervision/requests/<owner>/latest.json` 的 owner request 与 dispatch 中的 owner route 完全匹配。这个 owner-request-backed 恢复路径用于处理同一 work unit 已经被 consumer 写入 request/dispatch、随后空 scan 覆盖 `consumer/latest.json` 的情况；它不允许执行没有 owner request 的旧 dispatch，也不放宽 owner route、forbidden surfaces、prompt contract 或 repeat-suppression 校验。`domain-route-reconcile` 作为同 tick one-shot 编排时，还有一条更强的 currentness 规则：execute 必须消费本轮 `supervisor-consume` 返回的内存 payload，而不是回读上一轮落盘的 `consumer/latest.json`。这样 dry-run 不需要为了正确性写 workspace，apply 也不会被上一轮 `runtime_platform_repair` 或 `return_to_ai_reviewer_workflow` dispatch 污染。

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
- 对 `analysis_claim_evidence_repair`，adoption 可采纳同一 work-unit fingerprint 绑定的 `artifacts/reports/mas_quality_repair/latest.json`、`artifacts/reports/analysis_claim_evidence_repair/latest.json` 中带 `controller_action_invoked_first.action=run_quality_repair_batch`、完整 `targeted_publication_specificity_targets`、`canonical_artifact_delta.meaningful_artifact_delta=true` 和 gate replay cleared-blocker proof 的当前 owner receipt、`report_history/artifacts/reports/report-*.json`，或 legacy traceability reaudit report；采纳条件只证明同一 controller work unit 已写出可归属修复证据，下一步仍必须回到 publication gate recheck。
- 若受控 worker 已经完成同一 work unit，supervisor 必须进入 gate recheck、owner route 前进或下一 owner handoff；不得因为 stale queue、fresh timestamp、archived report 或 report replay 重复派发同一 work unit。
- repo-side fix landed、archive proof verified、report history 可读取，只能说明平台或证据面已有修复证据；它不等同于具体 study 已恢复、live worker 已存在、论文质量已放行或 `current_package` / `submission_minimal` 已成为当前 authority。
- `domain-transition::*` 是 MAS controller transition authority，不能被当成普通 publication eval action 处理。controller refresh materialize 后，runtime authorization 必须消费当前 `controller_decisions/latest.json` 中的 transition work unit；prompt 只读取该 authorization，不回退到旧 prompt、旧 task-intake、旧 default executor dispatch 或缺少当前 fingerprint 的 `publication_eval.recommended_actions`。允许 relay 的最低条件是：controller decision 当前、未要求 human confirmation、transition fingerprint 中的 work unit id 与 `next_work_unit.unit_id` 一致、controller action 属于该 transition 的白名单。
- live Codex CLI prompt 是 run 启动时生成的 executor snapshot。刷新 `runtime_state.last_controller_decision_authorization` 不会改写已经运行的 Codex CLI 进程；因此 controller refresh 的 postcondition 必须读取当前 `active_run_id` 的 `prompt.md`，确认它包含当前 work-unit fingerprint 或 work-unit id。若 prompt 仍指向旧 work unit，或 live worker 缺少可验证 prompt，MAS 必须用 controller-owned pause/resume 生成 fresh turn，再让新 prompt 消费当前 authorization；不得把新 work unit 仅 queue 到旧进程。
- fresh turn 生成 prompt 前还必须把当前 AI reviewer redrive 写回 runtime authorization。若 `controller_decisions/latest.json` 的 action 为 `return_to_ai_reviewer_workflow`，且 `next_work_unit` 是 `ai_reviewer_recheck` 或 `ai_reviewer_medical_prose_quality_review`，runner 必须把该 decision 绑定到当前 `active_run_id` 并写入 `.ds/runtime_state.json:current_controller_authorization`。这样 prompt、managed worker 环境和 dispatch executor 校验的是同一 run 的同一 work unit；旧 `last_controller_decision_authorization` 可以保留为历史，但不能覆盖当前 AI reviewer owner route。
- 当旧 explicit wakeup 中的 owner handoff 指向 `source_provenance_owner.recover_transport_model_provenance_or_typed_blocker`，且当前 `source_provenance_owner_result` 已是 accepted terminal typed blocker 并明确把下一步交给 `decision/methodology_reframe_route_decision` 时，fresh turn 必须把该 provenance handoff 视为 superseded。runner 应优先使用当前 controller decision / runtime authorization 生成 prompt，不得再次把 Codex worker 绑定到 `recover_transport_model_provenance`。这是 MAS owner-route 当前性规则，不是恢复 MAS 私有 scheduler、queue 或 generic runtime owner。
- 若 fresh prompt 内的 managed worker 执行 `return_to_ai_reviewer_workflow` 等 controller action 时发现 consumer dispatch 仍是旧 owner route，当前 runtime authorization 优先级高于旧 dispatch 文件。执行器应把旧 dispatch 作为输入壳，按 `current_controller_authorization` / `last_controller_decision_authorization` 重建 owner route、idempotency key 和 repeat key；只有同一 run identity、授权 action 白名单、work-unit fingerprint 和 runtime state 全部匹配时才放行。若 workspace-level consumer latest 已被后续 scan/consume 清空，但 fresh prompt 已携带 controller action 且 managed worker 显式请求同一 action，执行器可以从当前 runtime authorization 合成受限 dispatch 壳，再走同一授权校验；普通外层 supervisor 或人工 CLI 仍不能跳过 consumer latest。否则 fail closed 为 managed runtime authorization blocker，不能回落成旧 dispatch 重跑。

runtime repair 与 publication gate 的 owner routing 使用 controller terminal 证据，而不是泛化的 gate blocker：

- `gate_specificity.required=true` 本身不足以阻止 runtime relaunch；异常 stopped、paused/resume 无 live worker、active/running 但无 live worker、retry budget exhausted 仍必须进入 runtime platform repair。
- 已交付人审/投稿包的 parked handoff 是例外：当 `auto_runtime_parked` 或 delivery/current_package handoff 证据成立时，平台 repair redrive 不能自动重开 writer；若仍有 live worker，controller 应优先 pause 旧 run 并等待显式 resume / revision intake。
- 若 latest task intake 明确是 reviewer revision 或 submission refresh，用户显式唤醒可以释放 delivered-package parking；`runtime_platform_repair` source 不能借同一个 intake 自动释放该停驻。
- 只有 resume/postcondition 或 runtime status 明确给出 `gate_needs_specificity` / `needs_specificity` / `publication_gate_specificity_required`，并且来源是 controller work-unit authorization 时，supervisor 才把 no-live-worker relaunch 转交给 publication gate。
- 若 stale specificity terminal 已被带完整 targets 的 publication eval 证明满足，platform repair 可以清掉旧 terminal，并把队列推进到下一 owner；已 applied 的 runtime repair 不应继续留在当次 action queue。

前台兼容性核对必须把 project / study / runtime owner 分开：

- NF-PitNET 003 不属于 DM002/DM003 runtime 风险核对的目标，不因 DM lifecycle 或 evidence adoption 文档更新触碰其 paper、current package、submission minimal 或 runtime-owned surface。
- DM002 / DM003 是否 live、是否 no-live-worker、是否 stale、是否需要人工介入，必须 fresh 读取 `progress_projection`、`study_progress`、`runtime_supervision/latest.json`、`publication_eval/latest.json` 与 `controller_decisions/latest.json`；不能用 repo commit、lifecycle migration ledger、cold archive 或 report history 代替当前 truth。
- 如果存在 live managed runtime，或 `progress_projection.execution_owner_guard.supervisor_only=true`，前台只能进入 supervisor-only 监管态；不得直接写 runtime-owned surface，也不得修改 DM workspace 的论文正文、`current_package` 或 `submission_minimal`。
- 如果当前 truth 是 `quest_status=active` 但 `active_run_id=null` / no live session / retry budget exhausted，前台只能报告 live 兼容风险并等待 controller/runtime owner 决策；不得把 repo 修复完成表述为 study 已恢复。

第二层 Developer Supervisor Mode 是本机开发/doctor 监管模式，不是 MAS production generic scheduler。它的时间策略固定为：

- scheduler/heartbeat：每 `3600` 秒一次
- owner request `2` 小时未被 pickup，标记 `owner_pickup_overdue`
- action queue `6` 小时仍未被消费或仍无进展，标记 `developer_supervisor_attention_required`
- developer heartbeat 必须评估内置 AI monitoring/repair 是否失效，并在 `developer_apply_safe` 与本机 family user config / workspace profile authority gate 通过时消费队列、写 default executor dispatch request、执行 ready dispatch，或明确 blocked reason / next owner
- Developer Supervisor Mode 的 authority 优先来自 workspace profile 中的 `developer_supervisor_mode`、`github_username` 与 `mas_developer_github_usernames`，并可由 OPL family 用户级配置 `~/Library/Application Support/OPL/state/developer-supervisor.json`（可由 `OPL_STATE_DIR` 切换）手动关闭或覆盖；配置 `enabled=off` 时强制降级到 `external_observe`。
- `developer_apply_safe` 开启后，`github_username` 属于 `mas_developer_github_usernames` 时使用 direct commit route；其他已识别 GitHub 用户使用 pull request route；无法识别 GitHub 用户时降级到 `external_observe`。
- developer heartbeat 的作用域是 `workspace_dynamic_active_studies`：每轮从 workspace 当前 truth surface 发现 active / auto-resume / needs-repair 的 MAS study，新建 MAS 任务在下一次 heartbeat 自动纳入巡检，不要求在 Codex App prompt 里硬编码 study_id allowlist。
- 如果新任务出现 `quest_status=active` 但 `active_run_id=null`、`worker_running=false`、`runtime_liveness_status=none`、`quest_marked_running_but_no_live_session` 或 `runtime_recovery_retry_budget_exhausted`，developer heartbeat 必须判定为 active-but-not-running，并按 `scan -> consume -> execute-dispatch -> rescan` 接手平台修复。

这解释了之前的故障模式：heartbeat 只运行 `supervisor-scan` 时，系统能准确报告 `AI reviewer queue` 或 `publication_gate_specificity_required` 积压，但没有运行 `supervisor-consume`，也没有生成默认 Codex executor dispatch request，所以“AI 监测发现问题”与“AI 修复真正被派单执行”之间断开。后续如果只运行到 `supervisor-consume`，也只能得到 `dispatch_status=ready`；必须同 tick 运行 `supervisor-execute-dispatch`，才能把 ready dispatch 推进为 `executed` 或明确 blocked。

Developer Supervisor Mode 有三个正式模式：

- `internal_only`：只运行 MAS 内部 AI doctor/self-healing；不启用外层工程代理。
- `external_observe`：外层只读巡检，只投影 stale/blocked/why_not_applied，不生成可消费 safe-action request。
- `developer_apply_safe`：开发环境模式，允许 `supervisor-scan --apply-safe-actions --developer-supervisor-mode developer_apply_safe` 写 supervision/control/autonomy request、handoff packet 与 action queue。

`developer_apply_safe` 还受 workspace profile 与本机用户级配置保护：profile 是默认 authority gate，OPL family config 可以显式关闭或覆盖。这样防止普通用户或生产研究环境意外获得 direct repo write authority，同时允许已识别的非 MAS developer 通过 PR route 回灌基座修复。

`Codex App heartbeat` 不是这条 contract 的依赖。Codex App 可以作为本机开发环境的一个外部 caller 调用该入口；默认 heartbeat / scheduler cadence 由 OPL provider/runtime manager replacement 承载。MAS local scheduler contract 已退为 tombstone/provenance refs，不再定期调用 MAS tick script，也不暴露 macOS LaunchAgent active adapter。OPL-hosted production heartbeat、queue、attempt 和 operator projection 由 OPL provider 持有；Linux `systemd --user`、宿主 `cron` 和 Docker/container manager 不作为 MAS persistent local backend 落地；旧 workspace-local service manager 不再作为 active 选项。

workspace bootstrap 只渲染 MAS CLI entry，不再渲染 workspace-local host-service 模板：

- `ops/medautoscience/bin/supervisor-scan`
- `ops/medautoscience/bin/supervisor-consume`
- `ops/medautoscience/bin/supervisor-execute-dispatch`
- `ops/medautoscience/bin/supervisor-reconcile`

`supervisor-scan`、`supervisor-consume`、`supervisor-execute-dispatch` 仍保留为调试入口。MAS direct/local 只能作为 one-shot diagnostic 或 Developer Supervisor Mode heartbeat 读取并消费 MAS domain truth；不得恢复 MAS-owned scheduler adapter、tick script、LaunchAgent 或 workspace-local service。OPL-hosted 同 tick 行为应消费 MAS sidecar / owner receipt 并回到 MAS domain entry。`supervisor-reconcile` one-shot 是调试、加速和 dry-run / apply 入口。二者都不得把 scheduler 或 provider 提升为 study truth owner。

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
- `domain-route-reconcile --dry-run` 等价的 `scan -> consume -> execute-dispatch -> rescan` 只读证据；
- `workspace-monolith-migrate --dry-run` 的 migration readiness / skipped / appliable reason；
- `real_workspace_soak_monitor` 的 status/progress、active/parked/completed reason 与 legacy diagnostic evidence。

该 read model 的完成边界固定为：

- 默认 `can_claim_landed=false`，除非真实 evidence 无 blocker；
- human gate、publication gate、parked handoff、profile unreadable、runtime truth 缺失等都必须列成 blocker 和 next action；
- 只读 dry-run 可以报告 blocked、skipped 或 appliable，不做 migration apply；
- 不写 `current_package`、`submission_minimal`、`publication_eval/latest.json`、`controller_decisions/latest.json`、runtime SQLite 或 restore archive。

因此，repo capability 可以记录为 `paper_autonomy_stability_evidence=evidence_read_model_landed`；真实论文自治稳定性只能在后续 evidence 无 blocker 时单独 closeout 为 `paper_autonomy_stability=landed`。

`medautosci runtime ensure-supervision` 默认委托 OPL replacement，不注册或刷新 MAS-owned OS scheduler。`local` 现在不再是公开 CLI manager，也不返回 cleanup command；controller 层只保留 `local_launchd_retired_tombstone` projection 与 tombstone/provenance refs。显式 `--manager hermes` 只保留在 status/remove：读取旧 Hermes cron/session/gateway 证据，或清理旧 cron job/script；`ensure --manager hermes` 不是公开入口，controller direct-call 也只返回 retired tombstone。已退役的 `systemd|cron|launchd|docker` manager 不再是公开 CLI 选项，也不再有 direct-call 兼容 payload；旧 workspace-local host service 文件或 loaded 状态只作为 legacy diagnostic status 中的 `retired_cleanup_evidence` 读取和清理。清理后必须回到 OPL-hosted provider contract 或 tombstone/provenance proof，不能恢复旧 workspace-local service。

Hermes 对本地运行的必要性已经从默认路径移除；后续 MAS 仓内只能维护 legacy diagnostic cleanup 读法，不能把 Hermes manager 扩展成新的 long-run backend 覆盖面。生产级 wakeup / queue / attempt / retry-dead-letter 由 OPL provider 持有。任何保留的 direct diagnostic path 只能读取旧状态或移除旧生成物；不能复活旧 workspace-local service 模板、Hermes cron refresh 或 MAS-owned tick script 作为隐式旁路。

容器环境不是 MAS-owned generic runtime。MAS 不维护 `medautoscience:latest` 镜像，也不生成 Kubernetes CronJob manifest。容器、volume、scheduler、provider 与镜像发布由 OPL 或部署平台持有；容器内如果需要触发 MAS 监管，只能调用 MAS CLI 的 canonical tick/reconcile 入口，例如：

```bash
medautosci runtime owner-route-reconcile \
  --profile <profile> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe
```

MAS direct/local legacy diagnostic 不再定义外部 scheduler 或 MAS-owned supervision tick script。需要在开发环境做一次性处理时，应调用 `medautosci runtime domain-route-reconcile --profile <profile> --mode developer_apply_safe --apply` one-shot，或按 `owner-route-reconcile -> supervisor-consume -> supervisor-execute-dispatch` 手动执行调试链。OPL-hosted provider 应通过 MAS sidecar export/dispatch 和 owner receipt 进入同一 domain surface。直接调用 legacy `watch-runtime --max-ticks 1` 只覆盖外环检查，不覆盖同 tick 的 scan / consume / execute-dispatch 全链；上面的 scan 命令只用于调试单步扫描。

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
- 若本次 tick 允许 apply，就写 MAS domain owner-route handoff、authorization refs、typed blocker 或 owner receipt；provider resume/relaunch 交给 OPL runtime manager 消费后再 dispatch 回 MAS owner surface

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
- 前台、OPL framework handoff 和 MAS 都必须看到明确的平台级 supervisor 介入信号
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

- 对尚未 stopped 的 quest 写 OPL runtime-owner stop handoff，交由 OPL provider/queue 执行 runtime action
- 对已经 stopped 的 quest 记录 already-stopped parked lifecycle
- 写 `artifacts/autonomy/repair_lifecycle/latest.json`
- 标记 `authority = observability_only` / `controller_stop`
- 标记 `state = owner_route_required` / `parked`
- 明确 `paper_package_mutation_allowed = false`
- 明确 `manual_study_patch_allowed = false`
- 明确 `quality_gate_relaxation_allowed = false`
- 明确 `medical_claim_authoring_allowed = false`

这条规则只收口 runtime/resource 与 controller decision projection。后续如果用户、导师或审稿意见重新打开同一 paper line，仍必须走 durable revision intake 与 MAS/MDS relaunch/resume，再从 canonical paper authority 重新生成投影包。

## 6. durable surfaces

这条链路当前正式落到下面几个稳定表面：

- quest-level `domain_health_diagnostic` latest report in legacy `domain_health_diagnostic` namespace
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
- quest-level `runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- explicit archive import reference `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- study-level `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- physician-facing projection `study_progress`

其中：

- `domain_health_diagnostic` 负责 quest controller scan truth；当前文件路径仍可落在 legacy `domain_health_diagnostic` namespace
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

运行健康的用户可见动作必须来自 `RuntimeHealthKernel.canonical_runtime_action`；`last_launch_report`、`domain_health_diagnostic` legacy report 与 `runtime_supervision/latest.json` 都只能作为 input event 或 read model。

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

Canonical scheduler owner 是 OPL `opl_provider_runtime_manager`。MAS direct/local diagnostic 的 legacy owner 已退为 `local_launchd_retired_tombstone` / tombstone provenance；Hermes gateway cron 只在显式 status/remove 时作为 legacy diagnostic cleanup adapter。OPL-hosted production wakeup / queue / attempt owner 是 OPL provider。旧 Linux `systemd --user`、宿主 `cron`、macOS `launchd`、Hermes cron refresh 和 Docker/container manager service scaffold 只在历史/debug 文档或 retired diagnostic response 中出现；active scaffold 不再渲染这些旧模板。

MAS 负责“这一跳应该怎么判、怎么恢复、怎么写 durable truth”。scheduler 或 OPL provider 只负责按周期调用、承载 attempt 或投影 receipt，不持有医学研究 truth、publication judgement、paper/package authority 或 artifact gate。

这能保证未来无论宿主是 Codex、OPL framework handoff 还是 OPL App / product shell，MAS domain 合同都不漂。

## 9. 当前这条外环能恢复到哪里

当前这条外环已经能诚实做到：

- 发现 live worker 掉线、finalize parking 或恢复失败
- 通过 owner-route handoff 暴露受控恢复意图；generic resume/relaunch、attempt retry 与 provider liveness 由 OPL runtime manager 承担，MAS 只签收 domain owner receipt 或 typed blocker
- 把 `clinician_update`、`next_action_summary`、`needs_human_intervention` 写入 `runtime_supervision/latest.json`
- 在连续失败后升级为 `external_supervisor_required`，并把平台级 supervisor 介入信号写到 `runtime_escalation_record.json`、`repair_lifecycle/latest.json`、hourly supervision scan 与 `study_progress`

行为等价口径另见 [MDS Behavior Equivalence Gap Matrix](../../references/mds-parity/mds_behavior_equivalence_gap_matrix.md)。当前 outer loop 能证明的是 MAS domain supervision/read-model/receipt 与 one-shot diagnostic / Developer Supervisor Mode repair handoff；OPL-hosted production residency 仍以 OPL provider 证据为准。整体仍不声明与旧 MDS resident daemon、WebSocket terminal streaming、workspace-local scheduler 或 connector background threads 完全等价。
