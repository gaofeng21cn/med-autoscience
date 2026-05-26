# MDS Behavior Equivalence Gap Matrix

Status: `active behavior-audit reference`
Owner: `MedAutoScience Product Projection + OPL Runtime Manager integration boundary`
Date: `2026-05-09`
Purpose: `Preserve MDS parity, backend-audit, and historical fixture reference context for MAS.`
State: `support_reference`
Machine boundary: Human-readable parity reference only; current MAS and MDS-source truth remains in explicit archive imports, source provenance, contracts, tests, diagnostics, and receipts.

Related contract: `live-console-parity`

## 结论

MAS 已经做到默认 operation、默认诊断、进度可视化、artifact/quality/status/progress/cockpit/OPL handoff 不要求外部 `med-deepscientist` repo、daemon、runtime root 或 WebUI。

2026-05-26 Runtime Turn Lifecycle currentness correction 已解决旧审计中最关键的“连续跑”缺口，并把 owner 读回 OPL stage runtime / MAS domain authority split：runner completion、attempt continuation、queue、provider lifecycle 和 worker liveness 由 OPL stage runtime / `current_control_state` 承担；MAS 消费 typed closeout、owner receipt、typed blocker 或 publication authority refs，不再声明 MAS-owned generic `mas_runtime_core` turn owner。

2026-05-26 Runtime Continuity closeout currentness 补齐了 daemon 退役后另一个影响用户信任的外层行为：durable session / worker / provider attempt truth 由 OPL `current_control_state` 投影，MAS 只暴露 domain refs、owner receipts、typed blockers、progress freshness 和 handoff refs。这些能力仍是 scheduler-bound / provider-owned，不表示 MAS 变成 resident MDS daemon。

2026-05-26 Runtime Evidence currentness correction 把剩余用户感知缺口压成 MAS Progress Portal read-only projection 与 OPL runtime drilldown join 两组证据：`outer_supervision_slo` 解释 300 秒外环是否 fresh/due/stale/missing/blocked，并把运行 owner refs 指向 OPL `current_control_state` / provider attempt projection；Progress Portal 在真实 workspace 上证明 MAS per-study progress、route/decision trail、source/artifact refs 和 owner receipt / typed blocker refs 可刷新、可区分多 study、source refs 不回流旧 MDS identity。旧 `portal_console_soak`、MAS private Live Console、conversation/session read model 和 terminal attach gate 已物理退役，只保留 history/provenance。这些 surface 解决“用户怎么看 MAS 论文/domain 进度、运行 owner handoff 是否可信、真实论文自治证据是否足够”的问题，不声明 MAS 持有旧 resident daemon 低延迟交互、terminal attach 或 connector threads。

这不等于旧 MDS resident daemon 的行为被 1:1 复刻。正确完成口径是：

- `default_independence`: landed
- `full_mds_daemon_behavior_equivalence`: false
- `scheduler_contract_owner`: `opl_provider_runtime_manager`
- `current_active_scheduler_adapter`: `opl_family_runtime_provider`
- `legacy_diagnostic_scheduler_owner`: `mas_supervision_scheduler`
- `legacy_diagnostic_scheduler_adapter`: `local_launchd_retired_tombstone`
- `legacy_scheduler_cleanup_adapter`: `hermes_gateway_cron`
- `target_default_scheduler_adapter`: `opl_family_runtime_provider`
- `default_tick_shape`: OPL-owned provider SLO / scheduler replacement tick that calls MAS domain-handler or domain tick through owner receipts
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

这意味着对医生/PI 的日常影响主要集中在 3 件事：多论文 workspace 的 Portal 仍需持续验证成单篇论文工作台；runtime conversation / terminal / log / provider drilldown 需要从 OPL `current_control_state` 或 provider attempt projection 与 MAS study projection 并列展示；outer supervision 的 crash/stale recovery 仍受 OPL provider SLO / cadence 证据影响。已退役的 connector、GitOps、daemon control、workspace-local service 和 MAS private Live Console 不应作为“能力缺口”重开，除非未来有新的 OPL runtime-owner 产品需求和 audit / safety proof。

旧 MDS daemon 的关键事实是 resident `ThreadingHTTPServer` + WebSocket + session store + background connector / worker / recovery loop。MAS 当前拆成三层：domain layer 持有 study truth、owner receipt、typed blocker、publication/artifact/source authority 和 Progress Portal read-only projection；外层默认由 OPL scheduler replacement 负责 cadence、provider SLO、attempt/read-model 与 runtime manager projection；显式 legacy `local` adapter 只保留 tombstone/provenance refs，Hermes gateway cron 只读取或移除旧 scheduler 生成物。三层在“日常研究推进、owner receipt/typed blocker、恢复投影和论文/domain 进度查看”上已经解决主要运行目的问题；在 resident process、低延迟交互、WebSocket terminal attach、connector background delivery 和 in-memory session continuity 上仍不完全等价。WebSocket terminal attach / UI-issued runtime control 不是 MAS read-only progress scope；若未来补齐，必须由 OPL runtime owner surface 通过 safety / owner / audit gate 承担。

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
| supervision cadence | `purpose_equivalent_with_different_timing` | resident callbacks and worker/session loop | OPL replacement 负责 provider SLO / scheduler lifecycle；显式 legacy local adapter 不再运行 300s tick，只检查或移除旧生成物；turn-to-turn transport is owned by OPL stage runtime / current-control-state | acceptable for outer drift detection and stale recovery; normal continuation no longer waits for cron, but MAS does not claim live interactive daemon response |
| turn completion continuation | `behavior_equivalent` | runner completion normalizes state, drains queued user messages, schedules auto continuation, stops at human/terminal gates | OPL stage runtime / current-control-state performs attempt continuation and next-turn transport; MAS consumes typed closeout, owner receipt, typed blocker or publication authority refs |旧 MDS 的“一个 session 结束后怎么启动另一个 session”缺口已补齐为 OPL-owned runtime transport plus MAS domain authority refs |
| quest create/resume/pause/stop | `behavior_equivalent` | daemon API / quest service | MAS domain intent / owner receipts plus OPL stage runtime lifecycle transport | daily lifecycle controls do not require external MDS |
| live worker/session tracking | `purpose_equivalent_with_different_timing` | in-memory session store and live session API | worker lease + runner monitor + durable runtime state/read model observed by ticks | fail-closed durable liveness is stronger than stale JSON; MDS in-memory session continuity remains retired |
| crash recovery / auto-resume | `purpose_equivalent_with_different_timing` | daemon startup resume | in-process turn continuation through kernel; stale/crash recovery through next MAS scheduler tick or explicit watch/ensure runtime | normal continuation is low-latency; crash/stale recovery remains scheduler-bound but independent of MDS checkout |
| queued user messages/mailbox | `partially_equivalent` | daemon mailbox schedules turns | quest-local `user_message_queue` triggers turn scheduling; durable task intake / controller handoff handles broader work | queued messages during active worker execution are covered; chat-connector delivery is not default MAS behavior |
| progress visibility | `partially_equivalent` | Web/API status with project/quest-scoped workspace navigation | MAS Progress Portal / study-progress / cockpit, currently centered on workspace overview with study rows | fixed MAS-owned progress place exists, but multi-paper workspace UX still needs per-study/per-paper drilldown to avoid mixed interpretation |
| WebUI/WebSocket/terminal streaming | `purpose_equivalent_with_different_timing` | React WebUI, WebSocket terminal attach, bash log stream | MAS Progress Portal for paper/domain progress; OPL `current_control_state` / provider attempt projection for runtime, terminal, log and provider drilldown; MAS private Live Console and terminal attach gate are retired no-alias surfaces | users get MAS-owned progress and owner refs, while runtime observation/control is explicitly routed to OPL runtime owner surfaces |
| Portal / runtime drilldown real-workspace evidence | `purpose_equivalent_with_different_timing` | WebUI observed live status from resident daemon surfaces | MAS Progress Portal refreshes per-study progress / route / source / artifact refs; OPL `current_control_state` / provider attempt projection carries runtime drilldown refs | users get auditable read-only evidence for MAS-native progress plus explicit OPL runtime handoff; failed runtime join becomes blocker evidence rather than a hidden legacy_restore_import to MDS WebUI |
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

- `opl_current_control_state_projection`：只读投影 `study_id`、provider attempt refs、worker/run/freshness、typed blocker、owner receipt、runtime owner handoff 与 evidence refs。
- `retired_mas_recovery_projection`：MAS recovery projection 只保留 history/provenance；当前 action 列表为空，replacement surface 是 OPL `current_control_state` plus MAS typed blocker / owner receipt。
- `runtime_reconcile_trigger_projection`：读入口只展示 request / blocked reasons；它不执行 reconcile，不写 runtime truth。
- `mas_runtime_continuity_projection`：以 refs-only 方式投影到 `study-progress`、workspace cockpit、product-entry status、Progress Portal、MCP compact projection 和 OPL handoff。

这组 surface 的完成口径是“用户能看清 OPL runtime owner 是否接管、上次看到什么时候、为什么没继续、下一次由哪个 owner 恢复”。它不复刻 MDS in-memory session API，也不复刻 WebSocket terminal。质量、投稿、交付授权继续由 MAS quality/publication/artifact owner surface 持有。

## Runtime Evidence Closeout

本轮后续优化的行为口径：

- `outer_supervision_slo`: landed。它解释 outer supervision latency，默认由 OPL scheduler replacement / provider SLO projection 承担；legacy MAS local scheduler 只保留 tombstone/provenance refs 与 forbidden-caller proof。`due/stale/missing/blocked` 都会投影到用户入口，并给出 canonical one-shot reconcile dry-run 推荐。Hermes legacy diagnostic adapter 必须输出同构 SLO，而不是让 Portal / OPL 读取 Hermes-specific path。
- `portal_runtime_drilldown_join`: landed at boundary / soak pending。它证明 MAS-native Progress Portal 只写 progress/domain display evidence，runtime/terminal/log/provider drilldown 来自 OPL `current_control_state` 或 provider attempt projection；它不写 study truth、runtime truth、publication verdict 或 artifact authority。
- `paper_autonomy_stability_evidence`: evidence read model landed。它把真实 workspace 只读证据收成单一 report；如果 evidence 有 blocker，状态应保持 `evidence_landed_with_blockers`，不能宣称真实论文自治稳定性 landed。

这三项让 MAS monolith 的“可解释、可查看、可审阅证据”更接近旧 MDS daemon/WebUI 给用户的信任感，但仍遵守本矩阵的核心结论：MAS 当前不把 MDS resident daemon、旧 workspace-local service、private Live Console 或 terminal attach gate 恢复成默认依赖；Portal 的 pause/resume/stop 只展示 domain-handler / OPL owner-route handoff refs，交互式 terminal attach/input/resize/detach 若要补齐，必须走 OPL runtime owner lane，而不是重新启用旧 daemon 或 MAS private terminal owner。

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
- read model、Portal、study-progress、workspace cockpit、Product Entry 和 OPL handoff 只能解释 production impact、domain refs 和 OPL runtime handoff refs；不得写 paper/package、runtime SQLite、publication eval、controller decisions 或 quality/publication/submission ready。
- 真实 workspace blocker 必须如实记录为 blocker 和 next owner；不能因为 repo capability landed 而声明真实 `paper_autonomy_stability=landed`。

## Runtime Drilldown Authority Boundary

Progress Portal / runtime drilldown parity 只能生成 read-only progress/domain projection 和 OPL runtime handoff refs，禁止写入：

- `paper/current_package`
- `manuscript/current_package`
- `paper/submission_minimal`
- `manuscript/submission_minimal`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- `study_truth`
- `runtime_lifecycle.sqlite`
- terminal command files
- provider attempt state

## Current Version Assessment

按旧调研的差异项重评，当前版本解决了三类核心问题：

- `continuous turn loop`: 已解决。旧 MDS 的 runner-return 后状态归一化和下一 turn 调度，已由 OPL stage runtime / current-control-state transport 持有；MAS 消费 typed closeout、owner receipt、typed blocker 或 publication authority refs，cron/Hermes 不再承担主循环 owner。
- `live/stale liveness truth`: 已大幅解决。MAS 现在消费 OPL `current_control_state` / provider attempt refs，把 stale JSON live 误判压成 fail-closed handoff/read model。
- `default independence`: 已解决。默认运行、诊断、进度、artifact/quality/status/progress/cockpit/OPL handoff 不要求外部 MDS repo、daemon、runtime root 或 WebUI。

仍保留差异的地方也更清楚：

- `outer supervision latency`: 当前默认由 OPL scheduler replacement / provider SLO projection 解释；legacy local adapter 不再运行 300 秒 scheduler one-shot，也不再提供 status/remove cleanup path，Hermes gateway cron 只作 legacy diagnostic cleanup。它只影响旧证据读取/清理，不再影响正常 turn-to-turn continuation。
- `progress visibility UX`: Progress Portal 已替代默认进度查看入口，并已有 per-study Portal page、Route/Decision Trail read-only helper 与 OPL runtime handoff refs。它仍保持 `partially_equivalent`，因为真实多论文 workspace 的长期用户体验、route input 完整性和 OPL runtime drilldown join 仍需 evidence-gated polish。
- `interactive console`: MAS 私有 Live Console、conversation/session read model 和 terminal attach owner gate 已从当前控制面物理退役，只保留 history/provenance。它不是旧 MDS resident WebSocket terminal attach 的 1:1 复刻；运行 terminal/log/provider drilldown 必须来自 OPL `current_control_state` 或 provider attempt projection，MAS 只暴露 progress/domain refs、owner receipt 或 typed blocker。
- `connector background delivery`: 旧 MDS 的 QQ/Slack/Discord/Telegram/Weixin/WhatsApp/Feishu background delivery 仍不属于 MAS 默认 monolith；当前只保留 durable handoff refs。
- `in-memory session API`: MAS 选择 durable read model 与 receipt，不恢复旧 MDS in-memory session store。

## 2026-05-09 Remaining Semantic Gaps

下表只列仍可能影响用户感知或未来能力选择的差异；已明确退役且无默认产品价值的能力不进入 active implementation backlog。

| gap | current impact | why it is acceptable now | recommended improvement |
| --- | --- | --- | --- |
| Portal per-study/per-paper IA | 多论文 workspace 里，用户已能进入 per-study Portal page；真实 workspace 还需要验证长期刷新、attention queue、deep link 和 source refs 足够清晰。 | 默认进度入口、source refs、freshness、artifact locator、OPL handoff 和 per-study repo contract 已由 MAS 持有；不会回落到 MDS WebUI。 | P0 polish：继续真实 workspace user soak，修正混读、链接、source ref 可读性和 artifact grouping。 |
| Portal route / decision trail | Repo contract 已落地，但真实论文若缺 controller/evidence/runtime lineage 输入，会 fail-closed 显示 missing，用户仍看不到完整路线演进。 | `focused_lanes.portal-route-decision-trail`、`mas_progress_portal_route_decision_trail` 与 `mas_progress_portal_route_map` 已固定 read-only contract；单篇页以 SVG 研究路线地图展示阶段、路线、决策、阻塞、产物和执行回合节点，不让 Portal 重新裁决医学质量。 | P0 soak/polish：补真实 route inputs 与可读 source refs，持续验证 route map node/edge、decision rationale、blocked reason、superseded path、active/winning path。 |
| Runtime drilldown / terminal control | MAS Portal 可看 paper/domain progress、route/source/artifact refs 和 owner handoff；Progress Portal 本地 action endpoint 已退役，pause/resume/stop 意图走 domain-handler / OPL owner-route handoff refs；MAS private Live Console 与 terminal attach gate 已物理退役。 | observation/control 的 runtime 部分由 OPL `current_control_state` / provider attempt projection 承担；MAS 不恢复旧 MDS WebSocket owner，也不维护 terminal input/resize/detach command queue。 | P1/P2：继续真实 workspace owner-route handoff soak 和 OPL runtime drilldown / terminal owner safety proof。 |
| outer supervision stale/crash latency | 正常 turn-to-turn continuation 不等 scheduler tick；worker crash、stale recovery、drift detection 和部分 read-model refresh 默认由 OPL replacement / provider SLO projection 解释，也可由 operator 触发 one-shot dry-run/reconcile；legacy local adapter 只保留 tombstone/provenance refs。 | 这比旧 resident daemon 更可审计、fail-closed，且 `outer_supervision_slo` 已把 fresh/due/stale/blocked 和推荐命令投影给用户；默认 owner 是 OPL provider/runtime manager，local 是 retired tombstone，Hermes 是显式 legacy diagnostic adapter。 | P1：对真实 workspace 继续收集 SLO evidence，必要时用安全 one-shot reconcile 或 OPL provider cadence，而不是恢复 resident MDS daemon。 |
| low-latency worker/session watchdog | MAS 现在不是常驻 MDS daemon；真实 run 由 per-run wrapper 托管 `codex exec` 子进程并刷新 `worker_lease` heartbeat / cursor / exit / monitor state。child exit 可立即归一化；wrapper lost 或 stale lease 走 recovery intent / MAS scheduler fail-safe。 | 行为价值接近旧 daemon 的 worker/session 感知，但实现更小、更可审计，不会让高频 tick 触发额外 LLM 调用。 | 已落地：继续用 real workspace evidence 观察 wrapper lost、child crash、queued message、auto-continue 和 recovery intent 的端到端耗时。 |
| LLM dispatch cost visibility | 旧 MDS daemon 常驻并不等价于每次 tick 都调用 LLM；MAS domain refs 和 OPL runtime owner refs 应区分 `observe_only`、handoff request、controller apply 和 Codex worker dispatch。 | 用户能区分“页面刷新/监管 dry-run”与“真实启动 Codex worker”，避免把 300 秒 watchdog 误解成高频 LLM 花费。 | 已落地于 boundary：重复 owner_route/action fingerprint 必须 no-op suppression；后续只在真实 cost telemetry 需要时扩展预算窗口。 |
| queued mailbox / conversation view | 运行中追加 user message 已有 queue；旧 WebUI chat pane 可看 executor conversation/timeline。 | durable task intake、owner_route 和 OPL runtime receipts 已能驱动研究；App/workbench 应从 OPL `current_control_state` / provider attempt refs 并列展示 executor conversation / typed blocker / owner handoff。 | P1：继续真实 workspace soak，增强 OPL runtime drilldown join 和 source ref 可读性。 |
| artifact interactive mutation | package locator、artifact refs、current package discovery 已由 Artifact OS 持有；旧 MDS interactive artifact API 没有默认保留。 | MAS 选择 canonical-source-first，避免 UI 或 legacy artifact API 绕过 paper/package authority。 | P2：仅在 Artifact OS authority 下增加 file browser / pickup / rebuild proof view；不恢复任意 mutation API。 |
| memory/lesson service | Stage entry consumption 与 controlled closeout writeback 已落地；MAS 有 portfolio/research memory、canonical literature、stage packet、router receipt 和 calibration evidence，但不复刻 MDS generic free-form autonomous memory service。 | 经验/记忆不能直接授权质量、投稿、claim expansion 或 route；它必须经 evidence/review/controller surface 生效。 | 继续 real workspace soak，验证 stage consumed refs、router receipt、rejected writes、route impact 和 next owner 在 Progress/Portal 可见。 |

后续完善顺序建议固定为：real-workspace Progress Portal / source-ref polish -> route input completeness -> owner-route handoff soak -> OPL runtime drilldown join / terminal owner safety proof。`portal-study-scoped-ia`、`portal-route-decision-trail`、`portal-stage-artifact-path` 和 pause/resume/stop owner-route handoff 已有 repo contract；runtime conversation、terminal/log/provider refs 和 attach/control 必须从 OPL `current_control_state` / provider attempt projection 进入 App/workbench。下一步重点是让真实多论文 workspace 的用户体验稳定，同时不让 UI、connector、旧 daemon 或 MAS private Live Console 重新成为 runtime owner。

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
- 可以说：Progress Portal 提供旧 MDS WebUI 论文/domain 观察类能力的 MAS-owned read-only purpose equivalence；runtime/terminal/log/provider drilldown 归 OPL runtime owner。
- 可以说：MAS 已以 authority-split 方式保留 DeepScientist/MDS 的 stage memory/literature 目的：stage entry 读取，stage closeout 受控回写，controller/evidence/review surface 守边界。
- 可以说：旧 MDS WebUI 的 per-project/per-quest 信息架构是后续 Portal UX parity 的 clean-room oracle，当前 Portal 仍有 per-study/per-paper drilldown 缺口。
- 不能说：MAS 与旧 MDS resident daemon 行为完全等价。
- 不能说：MAS 复刻了旧 MDS generic autonomous memory service，或 memory card 可以直接授权论文质量、claim、route、publication readiness。
- 不能说：MAS 复刻了 MDS resident WebSocket terminal attach、connector background delivery、team service 或 GitOps runtime lifecycle。
- 不能说：MDS resident WebSocket terminal attach 或 UI-issued runtime control 已经被 MAS Portal 吸收；准确口径是 Portal pause/resume/stop 只展示 domain-handler / OPL owner-route handoff refs，terminal attach/input/resize/detach 若未来补齐，必须通过 OPL runtime owner safety / audit gate。
- 不能把旧 workspace-local launchd/systemd/cron/docker service 当成当前可选运行面。
