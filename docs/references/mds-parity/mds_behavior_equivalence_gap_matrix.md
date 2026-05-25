# MDS Behavior Equivalence Gap Matrix

Status: `active behavior-audit reference`
Owner: `MedAutoScience Runtime OS`
Date: `2026-05-09`
Purpose: `Preserve MDS parity, backend-audit, and historical fixture reference context for MAS.`
State: `support_reference`
Machine boundary: Human-readable parity reference only; current MAS and MDS-source truth remains in explicit archive imports, source provenance, contracts, tests, diagnostics, and receipts.

Related contract: `live-console-parity`

## 结论

MAS 已经做到默认 operation、默认诊断、进度可视化、artifact/quality/status/progress/cockpit/OPL handoff 不要求外部 `med-deepscientist` repo、daemon、runtime root 或 WebUI。

2026-05-08 Runtime Turn Lifecycle correction 已解决旧审计中最关键的“连续跑”缺口：runner completion 不再等外部 cron 触发下一轮，而是在 MAS-owned `mas_runtime_core` 内通过 `complete_turn_and_normalize` 清理 `active_run_id` / `worker_running`，按 queued user messages、human gate、terminal status 与 `continuation_policy` 决定下一 turn；`auto_continue` 仍保持约 `0.2s` 的低延迟 kernel timer。

2026-05-08 Runtime Continuity closeout 补齐了 daemon 退役后另一个影响用户信任的外层行为：durable session/worker tracking 和 crash-recovery intent。MAS 现在用 `runtime_session` read model 投影 worker/last seen/run/freshness，用 `recovery_intent` ledger 记录恢复原因、next owner、retry budget 与 current action，用 `runtime_reconcile_trigger` 给读入口展示一次 safe reconcile 的幂等推荐。这些能力仍是 scheduler-bound / controller-owned，不表示 MAS 变成 resident MDS daemon。

2026-05-08 Runtime Evidence closeout 又把剩余用户感知缺口压成三组可审阅 evidence：`outer_supervision_slo` 解释 300 秒外环是否 fresh/due/stale/missing/blocked，并给出 safe one-shot reconcile dry-run；`portal_console_soak` 在真实 workspace 上证明 MAS Progress Portal / Live Console 可刷新、可区分多 study/run、source refs 不回流旧 MDS identity；`paper_autonomy_stability_evidence` 把真实 profile inventory、supervisor reconcile dry-run、workspace migration dry-run 和 real workspace soak monitor 合成单一 read model。这些 surface 解决“用户怎么看监管是否还在、页面是否可信、真实论文自治证据是否足够”的问题，不声明旧 resident daemon 低延迟交互或 connector threads 1:1 等价。

这不等于旧 MDS resident daemon 的行为被 1:1 复刻。正确完成口径是：

- `default_independence`: landed
- `full_mds_daemon_behavior_equivalence`: false
- `scheduler_contract_owner`: `opl_provider_runtime_manager`
- `current_active_scheduler_adapter`: `opl_family_runtime_provider`
- `legacy_diagnostic_scheduler_owner`: `mas_supervision_scheduler`
- `legacy_diagnostic_scheduler_adapter`: `local_launchd_retired_tombstone`
- `legacy_scheduler_cleanup_adapter`: `hermes_gateway_cron`
- `target_default_scheduler_adapter`: `opl_family_runtime_provider`
- `default_tick_shape`: OPL-owned provider SLO / scheduler replacement tick that calls MAS sidecar or domain tick through owner receipts
- `legacy_local_tick_interval_seconds`: `retired`
- `legacy_local_tick_sequence`: `retired_tombstone_only`

2026-05-10 Stage-Led Autonomy update：`memory / lesson store` 已从 generic autonomous memory service 缺口收敛为 `purpose_equivalent_with_authority_split`。MAS 通过 `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt` 和 `stage_recall_index` 保留 DeepScientist/MDS 的 stage memory/literature 目的，但 authority 分在 workspace、study、quest、evidence/review ledger、controller decision 和 human gate。真实 paper line 仍需继续 soak，证明 consumed refs、accepted/rejected writes、route impact 和 next owner 可见。

2026-05-09 fresh assessment，经 2026-05-10 stage knowledge update 修订：当前差异不再是“MAS 还依赖 MDS 才能跑”，而是“MAS 选择了 durable / scheduler-bound / read-only-first / authority-split 的 monolith 实现，和旧 MDS resident daemon + WebUI 的交互体验并不完全相同”。按机器矩阵复核，17 个行为面中：

- `2` 个已达到 `behavior_equivalent`：turn completion continuation、quest create/resume/pause/stop。
- `6` 个是 `purpose_equivalent_with_different_timing`：daemon residency、supervision cadence、live worker/session tracking、crash recovery、WebUI/terminal observation、MCP surface。
- `1` 个是 `purpose_equivalent_with_authority_split`：memory/lesson store。
- `3` 个是 `partially_equivalent`：queued user messages/mailbox、progress visibility、artifact interaction handoff。
- `4` 个是 `not_equivalent_retired`：connector/channel background delivery、GitOps state management、MDS daemon lifecycle controls、workspace-local host service。
- `1` 个是 `historical_fixture_only`：team/multi-agent coordination。

这意味着对医生/PI 的日常影响主要集中在 3 件事：多论文 workspace 的 Portal 还不够像单篇论文工作台；Live Console 仍是只读观察，不是交互式 terminal/control；outer supervision 的 crash/stale recovery 仍受 OPL provider SLO / cadence 证据影响。已退役的 connector、GitOps、daemon control、workspace-local service 不应作为“能力缺口”重开，除非未来有新的产品需求和 MAS owner / audit / safety proof。

旧 MDS daemon 的关键事实是 resident `ThreadingHTTPServer` + WebSocket + session store + background connector / worker / recovery loop。MAS 当前拆成三层：内层 Runtime Core / turn lifecycle kernel 已承担 runner 返回后的连续科研主循环；外层默认由 OPL scheduler replacement 负责 cadence、provider SLO 与 runtime manager projection，MAS supervision contract 保留 drift detection、stale recovery、read-model refresh、domain tick payload、owner receipt 和 legacy diagnostic projection；显式 legacy `local` adapter 只保留 tombstone/provenance refs，Hermes gateway cron 只读取或移除旧 scheduler 生成物；Product Projection 负责 Portal / Live Console / progress 只读展示。三层在“日常研究推进、turn-to-turn continuation、恢复投影和进度查看”上已经解决主要运行目的问题；在 resident process、低延迟交互、WebSocket terminal attach、connector background delivery 和 in-memory session continuity 上仍不完全等价。WebSocket terminal attach / UI-issued runtime control 不是当前 read-only closeout 的 landed scope，也不应写成 abandoned；它们属于后续 interactive parity candidate，需要单独 safety / owner / audit gate。

2026-05-09 paper progress degradation closeout：自动论文产出能力的降级判断现在由同一矩阵内的 `paper_progress_degradation_classifier` 持有。允许分类固定为 `production_degrading`、`production_risk`、`diagnostic_degrading`、`acceptable_design_difference`、`retired_non_goal`。其中 P0 `production_degrading` 不是来自旧 MDS daemon 本身，而是来自 MAS-native 自动推进闭环的三类 overlay：`owner_handoff_dispatch`、`repeat_suppression`、`work_unit_redrive`。对应 closeout 已 landed：controller work-unit evidence adoption 必须 handoff 到 publication gate / AI reviewer / writer / next owner；repeat suppression 只能压住重复 dispatch，不能压住 handoff；same-fingerprint loop、read churn、stale truth surface 与 retry budget exhausted 必须进入 `paper_progress_stall` / safe reconcile guard。这个分类层用来判断“是否影响自动论文产出”，不把 Portal/Live Console 诊断体验问题夸大成生产降级，也不把 connector/GitOps/旧 daemon lifecycle 这类 retired surface 放回默认 backlog。

## 行为分类

机器可读矩阵在 `med_autoscience.controllers.mds_capability_parity.build_mds_behavior_equivalence_matrix()`。

允许分类只有：

- `behavior_equivalent`: 行为目标和默认用户影响等价。
- `purpose_equivalent_with_different_timing`: 目标等价，但节奏、延迟或实现方式有显著差异。
- `purpose_equivalent_with_authority_split`: 目标等价，但 MAS 将旧 MDS 的通用服务拆成 workspace / study / quest / evidence / review / controller owner surface；该分类不能授权质量、claim 或 publication readiness。
- `partially_equivalent`: MAS 覆盖研究主流程，但旧 MDS 的部分 UX、交互或附属能力尚未完整落地为 MAS 默认体验。
- `not_equivalent_retired`: 旧能力不再作为 MAS 默认能力保留。
- `historical_fixture_only`: 只作为历史行为对照或回归 fixture。

当前汇总：

| class | count |
| --- | ---: |
| `behavior_equivalent` | 2 |
| `purpose_equivalent_with_different_timing` | 6 |
| `purpose_equivalent_with_authority_split` | 1 |
| `partially_equivalent` | 3 |
| `not_equivalent_retired` | 4 |
| `historical_fixture_only` | 1 |

## 关键行为差异

| behavior surface | classification | MDS behavior | MAS behavior | user impact |
| --- | --- | --- | --- | --- |
| daemon residency | `purpose_equivalent_with_different_timing` | resident HTTP/WebSocket daemon | 默认外层 cadence 由 OPL `opl_provider_runtime_manager` / `opl_family_runtime_provider` 持有；MAS local adapter 已物理退役为 tombstone/provenance refs；Hermes 是 legacy diagnostic cleanup adapter | drift detection and recovery can be scheduler-bound; no MAS resident daemon is claimed |
| supervision cadence | `purpose_equivalent_with_different_timing` | resident callbacks and worker/session loop | OPL replacement 负责 provider SLO / scheduler lifecycle；显式 legacy local adapter 不再运行 300s tick，只检查或移除旧生成物; turn-to-turn continuation is owned by the MAS kernel | acceptable for outer drift detection and stale recovery; normal continuation no longer waits for cron, but live interactive daemon response is still not claimed |
| turn completion continuation | `behavior_equivalent` | runner completion normalizes state, drains queued user messages, schedules auto continuation, stops at human/terminal gates | MAS Runtime Turn Lifecycle Kernel performs the same normalization and next-turn decision with runner monitor, delayed timer, worker lease, user queue and receipt |旧 MDS 的“一个 session 结束后怎么启动另一个 session”缺口已补齐为 MAS-owned runtime behavior |
| quest create/resume/pause/stop | `behavior_equivalent` | daemon API / quest service | MAS Runtime OS / study runtime router | daily lifecycle controls do not require external MDS |
| live worker/session tracking | `purpose_equivalent_with_different_timing` | in-memory session store and live session API | worker lease + runner monitor + durable runtime state/read model observed by ticks | fail-closed durable liveness is stronger than stale JSON; MDS in-memory session continuity remains retired |
| crash recovery / auto-resume | `purpose_equivalent_with_different_timing` | daemon startup resume | in-process turn continuation through kernel; stale/crash recovery through next MAS scheduler tick or explicit watch/ensure runtime | normal continuation is low-latency; crash/stale recovery remains scheduler-bound but independent of MDS checkout |
| queued user messages/mailbox | `partially_equivalent` | daemon mailbox schedules turns | quest-local `user_message_queue` triggers turn scheduling; durable task intake / controller handoff handles broader work | queued messages during active worker execution are covered; chat-connector delivery is not default MAS behavior |
| progress visibility | `partially_equivalent` | Web/API status with project/quest-scoped workspace navigation | MAS Progress Portal / study-progress / cockpit, currently centered on workspace overview with study rows | fixed MAS-owned progress place exists, but multi-paper workspace UX still needs per-study/per-paper drilldown to avoid mixed interpretation |
| WebUI/WebSocket/terminal streaming | `purpose_equivalent_with_different_timing` | React WebUI, WebSocket terminal attach, bash log stream | Progress Portal for progress plus MAS-authored Live Console session read model, static shell, snapshot/loopback SSE stream, gated Portal pause/resume/stop runtime owner apply, and MAS terminal attach owner gate | users get MAS-owned progress, runtime observation, local-loopback authorized runtime control for pause/resume/stop, and attach/input/resize/detach UI/API when a MAS owner is available; without owner it fails closed |
| Portal / Live Console real-workspace evidence | `purpose_equivalent_with_different_timing` | WebUI observed live status from resident daemon surfaces | MAS `portal_console_soak` refreshes Portal and Live Console read models, checks multi-study/run disambiguation, terminal/log refs, source-ref cleanliness and MAS identity | users get auditable read-only evidence for the MAS-native visual surfaces; failed soak becomes blocker evidence rather than a hidden legacy_restore_import to MDS WebUI |
| connector/channel background delivery | `not_equivalent_retired` | QQ/Slack/Discord/Telegram/Weixin/WhatsApp/Feishu background threads | durable handoff refs for external consumers | chat connector delivery is outside default MAS monolith operation |
| MCP surface | `purpose_equivalent_with_different_timing` | daemon-backed MCP | MAS MCP calls owner surfaces directly | MAS truth/status/progress surfaces covered without MDS daemon |
| GitOps state management | `not_equivalent_retired` | root Git / quest Git / diff reader | SQLite lifecycle + restore proof + plain quest dirs | intentional behavior change; Git no longer owns runtime lifecycle |
| memory / lesson store | `purpose_equivalent_with_authority_split` | memory service / lesson store | portfolio research memory、canonical literature、`stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt`、`stage_recall_index` | stage 能在 entry 消费 memory/literature，在 closeout 提交受控写回；memory 仍不能授权质量、claim、route 或 publication readiness |
| team / multi-agent coordination | `historical_fixture_only` | MDS team service | MAS owner_route/controller coordination | team behavior is reference fixture only |
| artifact interaction handoff | `partially_equivalent` | daemon artifact interactions | Artifact OS locator / package handoff / controller refs | package discovery covered; interactive artifact mutation retired |
| daemon lifecycle controls | `not_equivalent_retired` | start/stop/restart MDS daemon | default OPL scheduler replacement projection; legacy local tombstone refs; Hermes cron as explicit legacy diagnostic cleanup adapter | no MAS-native MDS daemon control path is needed |
| workspace-local host service | `not_equivalent_retired` | historical MAS launchd/systemd/cron bridge | retired tombstone/provenance evidence; canonical default owner is OPL scheduler replacement; MAS local adapter is not an active cleanup option | old host services should be removed, not kept as active option |
| paper autonomy stability evidence | `purpose_equivalent_with_different_timing` | daemon plus WebUI often implied progress was still autonomously managed | MAS read-only evidence combines profile inventory, status/progress readability, supervisor reconcile dry-run, workspace migration dry-run and soak monitor blockers | users can see concrete blockers and next actions; landed paper autonomy remains evidence-gated and cannot be inferred from functional monolith alone |

## Runtime Continuity Completion

本轮 landed surface 固定为：

- `runtime_session_read_model`：只读投影 `study_id`、`quest_id`、`active_run_id`、`last_known_run_id`、`worker_state`、`worker_running`、`runtime_liveness_status`、`started_at`、`last_seen_at`、`last_event_cursor`、`last_stdout_ref`、freshness 与 evidence refs。
- `runtime_recovery_intent`：supervisor-owned ledger，记录恢复原因、next owner、retry budget、dedupe fingerprint、last attempt/result、next eligible tick 与 `current_action`。
- `runtime_reconcile_trigger_projection`：读入口只展示 safe reconcile 推荐与 blocked reasons；它不执行 reconcile，不写 runtime truth。
- `mas_runtime_continuity_projection`：投影到 `study-progress`、workspace cockpit、product-entry status、Progress Portal、MCP compact projection 和 OPL handoff。

这组 surface 的完成口径是“用户能看清有没有 worker、上次看到什么时候、为什么没继续、下一次怎么恢复”。它不复刻 MDS in-memory session API，也不复刻 WebSocket terminal。质量、投稿、交付授权继续由 MAS quality/publication/artifact owner surface 持有。

## Runtime Evidence Closeout

本轮后续优化的行为口径：

- `outer_supervision_slo`: landed。它解释 outer supervision latency，默认由 OPL scheduler replacement / provider SLO projection 承担；legacy MAS local scheduler 只保留 tombstone/provenance refs 与 forbidden-caller proof。`due/stale/missing/blocked` 都会投影到用户入口，并给出 canonical one-shot reconcile dry-run 推荐。Hermes legacy diagnostic adapter 必须输出同构 SLO，而不是让 Portal / OPL 读取 Hermes-specific path。
- `portal_console_soak`: landed。它证明 MAS-native Portal / Live Console 的 read-only display surface 可在真实 workspace 上审阅；它只写 display evidence，不写 truth。
- `paper_autonomy_stability_evidence`: evidence read model landed。它把真实 workspace 只读证据收成单一 report；如果 evidence 有 blocker，状态应保持 `evidence_landed_with_blockers`，不能宣称真实论文自治稳定性 landed。

这三项让 MAS monolith 的“可解释、可查看、可审阅证据”更接近旧 MDS daemon/WebUI 给用户的信任感，但仍遵守本矩阵的核心结论：MAS 当前不把 MDS resident daemon 或旧 workspace-local service 恢复成默认依赖；Portal 的 pause/resume/stop 已通过 MAS runtime owner apply 落地，交互式 terminal attach/input/resize/detach 若要补齐，必须走 MAS-native interactive parity lane，而不是重新启用旧 daemon 作为 owner。

## Paper Progress Degradation Closeout

当前用于判断“是否降低旧 MAS+MDS 自动论文推进能力”的 surface 已固定为：

- `mds_paper_progress_degradation_classifier`：把 17 个 MDS behavior surface 映射到生产影响类别，并要求每项带 `production_path`、`rationale` 和 `required_guard_surface`。
- `owner_handoff_dispatch` overlay：如果 evidence adoption 后无法把 work unit 交给下一 owner，属于 P0 真降级。
- `repeat_suppression` overlay：如果 suppression 让同一 fingerprint 无限 no-op 或压掉 handoff，属于 P0 真降级。
- `work_unit_redrive` overlay：如果 stale/failed work unit 不能在 MAS owner guard 下 redrive，属于 P0 真降级。
- `paper_progress_stall`：统一投影 `same_fingerprint_loop`、`read_churn_without_artifact_delta`、`stale_truth_surface`、`runtime_recovery_retry_budget_exhausted` 和 handoff 状态。
- `mas_production_blocker_impact_projection`：向用户面解释 `affects_output`、`next_owner`、`why_not_running`、`same_fingerprint_or_handoff`、`will_start_llm`、safe reconcile command、route 和 source refs。
- `paper_progress_degradation_evidence`：在真实 profile 上记录 status/progress 可读性、owner_route 前进、publication gate / AI reviewer / writer handoff、Portal/Console refs 和 safe reconcile dry-run 的 blocker / next action。

Guard 口径：

- `runtime-supervisor-reconcile --dry-run` 必须保持零 Codex dispatch。
- `--apply` 只能在 fresh owner_route、未 parked、未 completed、无 human gate、无 publication gate missing、retry budget 未耗尽且 action fingerprint 新鲜时启动 Codex worker。
- read model、Portal、Live Console、study-progress、workspace cockpit、Product Entry 和 OPL handoff 只能解释 production impact 和深链 source refs；不得写 paper/package、runtime SQLite、publication eval、controller decisions 或 quality/publication/submission ready。
- 真实 workspace blocker 必须如实记录为 blocker 和 next owner；不能因为 repo capability landed 而声明真实 `paper_autonomy_stability=landed`。

## Live Console Parity Authority Boundary

`live-console-parity` 只能生成 read-only observation surface，禁止写入：

- `paper/current_package`
- `manuscript/current_package`
- `paper/submission_minimal`
- `manuscript/submission_minimal`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- `study_truth`
- `runtime_lifecycle.sqlite`

## Current Version Assessment

按旧调研的差异项重评，当前版本解决了三类核心问题：

- `continuous turn loop`: 已解决。旧 MDS 的 runner-return 后状态归一化和下一 turn 调度，已由 MAS Runtime Turn Lifecycle Kernel 持有；cron/Hermes 不再承担主循环 owner。
- `live/stale liveness truth`: 已大幅解决。MAS 现在用 worker lease、runner monitor、turn receipt、runtime_session read model 和 recovery_intent 把 stale JSON live 误判压成 fail-closed read model。
- `default independence`: 已解决。默认运行、诊断、进度、artifact/quality/status/progress/cockpit/OPL handoff 不要求外部 MDS repo、daemon、runtime root 或 WebUI。

仍保留差异的地方也更清楚：

- `outer supervision latency`: 当前默认由 OPL scheduler replacement / provider SLO projection 解释；legacy local adapter 不再运行 300 秒 scheduler one-shot，也不再提供 status/remove cleanup path，Hermes gateway cron 只作 legacy diagnostic cleanup。它只影响旧证据读取/清理，不再影响正常 turn-to-turn continuation。
- `progress visibility UX`: Progress Portal 已替代默认进度查看入口，并已有 per-study Portal page、Route/Decision Trail read-only helper、conversation read model 与 soak evidence keys。它仍保持 `partially_equivalent`，因为真实多论文 workspace 的长期用户体验、route input 完整性和交互深度仍需 evidence-gated polish。
- `interactive console`: MAS 私有 Live Console、conversation/session read model 和 terminal attach owner gate 已从当前控制面物理退役，只保留 history/provenance。它不是旧 MDS resident WebSocket terminal attach 的 1:1 复刻；运行 terminal/log/provider drilldown 必须来自 OPL `current_control_state` 或 provider attempt projection，MAS 只暴露 progress/domain refs、owner receipt 或 typed blocker。
- `connector background delivery`: 旧 MDS 的 QQ/Slack/Discord/Telegram/Weixin/WhatsApp/Feishu background delivery 仍不属于 MAS 默认 monolith；当前只保留 durable handoff refs。
- `in-memory session API`: MAS 选择 durable read model 与 receipt，不恢复旧 MDS in-memory session store。

## 2026-05-09 Remaining Semantic Gaps

下表只列仍可能影响用户感知或未来能力选择的差异；已明确退役且无默认产品价值的能力不进入 active implementation backlog。

| gap | current impact | why it is acceptable now | recommended improvement |
| --- | --- | --- | --- |
| Portal per-study/per-paper IA | 多论文 workspace 里，用户已能进入 per-study Portal page；真实 workspace 还需要验证长期刷新、attention queue、deep link 和 source refs 足够清晰。 | 默认进度入口、source refs、freshness、artifact locator、OPL handoff 和 per-study repo contract 已由 MAS 持有；不会回落到 MDS WebUI。 | P0 polish：继续真实 workspace user soak，修正混读、链接、source ref 可读性和 artifact grouping。 |
| Portal route / decision trail | Repo contract 已落地，但真实论文若缺 controller/evidence/runtime lineage 输入，会 fail-closed 显示 missing，用户仍看不到完整路线演进。 | `focused_lanes.portal-route-decision-trail`、`mas_progress_portal_route_decision_trail` 与 `mas_progress_portal_route_map` 已固定 read-only contract；单篇页以 SVG 研究路线地图展示阶段、路线、决策、阻塞、产物和执行回合节点，不让 Portal 重新裁决医学质量。 | P0 soak/polish：补真实 route inputs 与可读 source refs，持续验证 route map node/edge、decision rationale、blocked reason、superseded path、active/winning path。 |
| Live Console interactive terminal/control | 当前能看 session/run、terminal/log tail、SSE/snapshot 和 action intent；Progress Portal 在显式 `--serve --enable-actions` 下可执行 pause/resume/stop；Live Console 在 `--serve --enable-terminal-attach` 下提供本机 loopback attach/input/resize/detach API，输入经 MAS token/lease/idempotency/audit 后进入 per-run PTY command queue；无 attach-capable live run 时 fail closed。 | observation 已覆盖旧 WebUI 的“看状态/日志/终端尾部”目的；pause/resume/stop 已走 runtime owner apply；terminal input 继续由 terminal owner、authorization、idempotency 和审计合同约束，且不恢复旧 MDS WebSocket owner。 | P1/P2：继续真实 workspace action receipt soak 和 terminal attach owner soak。 |
| outer supervision stale/crash latency | 正常 turn-to-turn continuation 不等 scheduler tick；worker crash、stale recovery、drift detection 和部分 read-model refresh 默认由 OPL replacement / provider SLO projection 解释，也可由 operator 触发 one-shot dry-run/reconcile；legacy local adapter 只保留 tombstone/provenance refs。 | 这比旧 resident daemon 更可审计、fail-closed，且 `outer_supervision_slo` 已把 fresh/due/stale/blocked 和推荐命令投影给用户；默认 owner 是 OPL provider/runtime manager，local 是 retired tombstone，Hermes 是显式 legacy diagnostic adapter。 | P1：对真实 workspace 继续收集 SLO evidence，必要时用安全 one-shot reconcile 或 OPL provider cadence，而不是恢复 resident MDS daemon。 |
| low-latency worker/session watchdog | MAS 现在不是常驻 MDS daemon；真实 run 由 per-run wrapper 托管 `codex exec` 子进程并刷新 `worker_lease` heartbeat / cursor / exit / monitor state。child exit 可立即归一化；wrapper lost 或 stale lease 走 recovery intent / MAS scheduler fail-safe。 | 行为价值接近旧 daemon 的 worker/session 感知，但实现更小、更可审计，不会让高频 tick 触发额外 LLM 调用。 | 已落地：继续用 real workspace evidence 观察 wrapper lost、child crash、queued message、auto-continue 和 recovery intent 的端到端耗时。 |
| LLM dispatch cost visibility | 旧 MDS daemon 常驻并不等价于每次 tick 都调用 LLM；MAS 现在把动作显式分成 `observe_only`、`reconcile_dry_run`、`controller_apply`、`codex_worker_dispatch`。Portal/Console/supervisor/domain_health_diagnostic 均可显示 `will_start_llm` 和 dispatch counters。 | 用户能区分“页面刷新/监管 dry-run”与“真实启动 Codex worker”，避免把 300 秒 watchdog 误解成高频 LLM 花费。 | 已落地：重复 owner_route/action fingerprint 必须 no-op suppression；后续只在真实 cost telemetry 需要时扩展预算窗口。 |
| queued mailbox / conversation view | 运行中追加 user message 已有 queue；旧 WebUI chat pane 可看 executor conversation/timeline。 | durable task intake、owner_route 和 runtime receipts 已能驱动研究；per-study Portal 已显示 Conversation panel，消费 user queue、turn receipts、runtime control/blocker 和 tool/action refs。 | P1：继续真实 workspace soak，增强 streaming transcript/source ref 可读性。 |
| artifact interactive mutation | package locator、artifact refs、current package discovery 已由 Artifact OS 持有；旧 MDS interactive artifact API 没有默认保留。 | MAS 选择 canonical-source-first，避免 UI 或 legacy artifact API 绕过 paper/package authority。 | P2：仅在 Artifact OS authority 下增加 file browser / pickup / rebuild proof view；不恢复任意 mutation API。 |
| memory/lesson service | Stage entry consumption 与 controlled closeout writeback 已落地；MAS 有 portfolio/research memory、canonical literature、stage packet、router receipt 和 calibration evidence，但不复刻 MDS generic free-form autonomous memory service。 | 经验/记忆不能直接授权质量、投稿、claim expansion 或 route；它必须经 evidence/review/controller surface 生效。 | 继续 real workspace soak，验证 stage consumed refs、router receipt、rejected writes、route impact 和 next owner 在 Progress/Portal 可见。 |

后续完善顺序建议固定为：real-workspace `portal_console_soak` / source-ref polish -> route input completeness -> action receipt soak -> terminal attach owner soak。`portal-study-scoped-ia`、`portal-route-decision-trail`、`portal-stage-artifact-path`、visible `runtime-conversation-read-model` timeline、study-scoped Live Console、pause/resume/stop authorized apply 和 terminal attach owner gate 已有 repo contract；下一步重点是让真实多论文 workspace 的用户体验稳定，同时不让 UI、connector 或旧 daemon 重新成为 runtime owner。

## 旧 Workspace-Local Service Policy

旧 workspace-local `systemd` / `cron` / `launchd` / `docker` service manager 不再是 active MAS runtime option。

当前规则：

- 新 workspace 不渲染 `watch-runtime-service-runner`。
- 新 workspace 不渲染 `ops/medautoscience/supervisor/systemd/*`。
- 新 workspace 不渲染 `ops/medautoscience/supervisor/cron/*`。
- 新 workspace 不渲染 `ops/medautoscience/supervisor/launchd/README.md`。
- `runtime-ensure-supervision --manager systemd|cron|launchd|docker` 已不再是可调用入口；CLI parser 和 controller façade 均拒绝这些 manager。
- 检测到旧 service file 或 loaded state 时，只作为 legacy diagnostic adapter status 中的 `retired_cleanup_evidence`；清理后回到 OPL scheduler replacement 默认 owner，MAS local adapter 只保留 tombstone/provenance refs。

历史上这些 service 曾作为迁移桥和真实 workspace 排障证据存在。当前 active docs/code/scaffold 不应把它们写成可选 scheduler；历史记录只服务 debug。

## 使用规则

后续 Agent 回答 “MAS 是否完全吸收 MDS” 时，应使用下面口径：

- 可以说：MAS 默认 operation / diagnostic / progress / artifact / quality surfaces 不再要求外部 MDS repo、daemon、runtime root 或 WebUI。
- 可以说：MAS 以 capability supersede / rewrite / retire 方式完成 functional monolith closeout。
- 可以说：Live Console 提供旧 MDS WebUI 观察类能力的 MAS-owned read-only purpose equivalence。
- 可以说：MAS 已以 authority-split 方式保留 DeepScientist/MDS 的 stage memory/literature 目的：stage entry 读取，stage closeout 受控回写，controller/evidence/review surface 守边界。
- 可以说：旧 MDS WebUI 的 per-project/per-quest 信息架构是后续 Portal UX parity 的 clean-room oracle，当前 Portal 仍有 per-study/per-paper drilldown 缺口。
- 不能说：MAS 与旧 MDS resident daemon 行为完全等价。
- 不能说：MAS 复刻了旧 MDS generic autonomous memory service，或 memory card 可以直接授权论文质量、claim、route、publication readiness。
- 不能说：MAS 复刻了 MDS resident WebSocket terminal attach、connector background delivery、team service 或 GitOps runtime lifecycle。
- 不能说：MDS resident WebSocket terminal attach 或 UI-issued runtime control 已经被放弃；准确口径是 Portal pause/resume/stop 已通过 MAS-native runtime owner apply 落地，terminal attach/input/resize/detach 通过 MAS-native safety / owner / audit gate，默认无 owner fail closed。
- 不能把旧 workspace-local launchd/systemd/cron/docker service 当成当前可选运行面。
