# MDS Behavior Equivalence Gap Matrix

Status: `active behavior-audit reference`
Owner: `MedAutoScience Runtime OS`
Date: `2026-05-09`
Related contract: `live-console-parity`

## 结论

MAS 已经做到默认 operation、默认诊断、进度可视化、artifact/quality/status/progress/cockpit/OPL handoff 不要求外部 `med-deepscientist` repo、daemon、runtime root 或 WebUI。

2026-05-08 Runtime Turn Lifecycle correction 已解决旧审计中最关键的“连续跑”缺口：runner completion 不再等外部 cron 触发下一轮，而是在 MAS-owned `mas_runtime_core` 内通过 `complete_turn_and_normalize` 清理 `active_run_id` / `worker_running`，按 queued user messages、human gate、terminal status 与 `continuation_policy` 决定下一 turn；`auto_continue` 仍保持约 `0.2s` 的低延迟 kernel timer。

2026-05-08 Runtime Continuity closeout 补齐了 daemon 退役后另一个影响用户信任的外层行为：durable session/worker tracking 和 crash-recovery intent。MAS 现在用 `runtime_session` read model 投影 worker/last seen/run/freshness，用 `recovery_intent` ledger 记录恢复原因、next owner、retry budget 与 current action，用 `runtime_reconcile_trigger` 给读入口展示一次 safe reconcile 的幂等推荐。这些能力仍是 scheduler-bound / controller-owned，不表示 MAS 变成 resident MDS daemon。

2026-05-08 Runtime Evidence closeout 又把剩余用户感知缺口压成三组可审阅 evidence：`outer_supervision_slo` 解释 300 秒外环是否 fresh/due/stale/missing/blocked，并给出 safe one-shot reconcile dry-run；`portal_console_soak` 在真实 workspace 上证明 MAS Progress Portal / Live Console 可刷新、可区分多 study/run、source refs 不回流旧 MDS identity；`paper_autonomy_stability_evidence` 把真实 profile inventory、supervisor reconcile dry-run、workspace migration dry-run 和 real workspace soak monitor 合成单一 read model。这些 surface 解决“用户怎么看监管是否还在、页面是否可信、真实论文自治证据是否足够”的问题，不声明旧 resident daemon 低延迟交互或 connector threads 1:1 等价。

这不等于旧 MDS resident daemon 的行为被 1:1 复刻。正确完成口径是：

- `default_independence`: landed
- `full_mds_daemon_behavior_equivalence`: false
- `default_scheduler_adapter`: `hermes_gateway_cron`
- `default_tick_interval_seconds`: `300`
- `default_tick_shape`: MAS-owned supervision tick script
- `default_tick_sequence`: `watch-runtime --max-ticks 1` -> `supervisor-scan` -> `supervisor-consume` -> `supervisor-execute-dispatch`

2026-05-09 fresh assessment：当前差异不再是“MAS 还依赖 MDS 才能跑”，而是“MAS 选择了 durable / scheduler-bound / read-only-first 的 monolith 实现，和旧 MDS resident daemon + WebUI 的交互体验并不完全相同”。按机器矩阵复核，17 个行为面中：

- `2` 个已达到 `behavior_equivalent`：turn completion continuation、quest create/resume/pause/stop。
- `6` 个是 `purpose_equivalent_with_different_timing`：daemon residency、supervision cadence、live worker/session tracking、crash recovery、WebUI/terminal observation、MCP surface。
- `4` 个是 `partially_equivalent`：queued user messages/mailbox、progress visibility、memory/lesson store、artifact interaction handoff。
- `4` 个是 `not_equivalent_retired`：connector/channel background delivery、GitOps state management、MDS daemon lifecycle controls、workspace-local host service。
- `1` 个是 `historical_fixture_only`：team/multi-agent coordination。

这意味着对医生/PI 的日常影响主要集中在 3 件事：多论文 workspace 的 Portal 还不够像单篇论文工作台；Live Console 仍是只读观察，不是交互式 terminal/control；outer supervision 的 crash/stale recovery 仍受 300 秒外环 tick 影响。已退役的 connector、GitOps、daemon control、workspace-local service 不应作为“能力缺口”重开，除非未来有新的产品需求和 MAS owner / audit / safety proof。

旧 MDS daemon 的关键事实是 resident `ThreadingHTTPServer` + WebSocket + session store + background connector / worker / recovery loop。MAS 当前拆成两层：内层 turn lifecycle kernel 已承担 runner 返回后的连续科研主循环；外层 Hermes gateway cron 仍承担 drift detection、stale recovery、read-model refresh 与 supervision tick。二者在“日常研究推进、turn-to-turn continuation、恢复投影和进度查看”上已经解决主要运行目的问题；在 resident process、低延迟交互、WebSocket terminal attach、connector background delivery 和 in-memory session continuity 上仍不完全等价。WebSocket terminal attach / UI-issued runtime control 不是当前 read-only closeout 的 landed scope，也不应写成 abandoned；它们属于后续 interactive parity candidate，需要单独 safety / owner / audit gate。

## 行为分类

机器可读矩阵在 `med_autoscience.controllers.mds_capability_parity.build_mds_behavior_equivalence_matrix()`。

允许分类只有：

- `behavior_equivalent`: 行为目标和默认用户影响等价。
- `purpose_equivalent_with_different_timing`: 目标等价，但节奏、延迟或实现方式有显著差异。
- `partially_equivalent`: MAS 覆盖研究主流程，但旧 MDS 的部分 UX、交互或附属能力尚未完整落地为 MAS 默认体验。
- `not_equivalent_retired`: 旧能力不再作为 MAS 默认能力保留。
- `historical_fixture_only`: 只作为历史行为对照或回归 fixture。

当前汇总：

| class | count |
| --- | ---: |
| `behavior_equivalent` | 2 |
| `purpose_equivalent_with_different_timing` | 6 |
| `partially_equivalent` | 4 |
| `not_equivalent_retired` | 4 |
| `historical_fixture_only` | 1 |

## 关键行为差异

| behavior surface | classification | MDS behavior | MAS behavior | user impact |
| --- | --- | --- | --- | --- |
| daemon residency | `purpose_equivalent_with_different_timing` | resident HTTP/WebSocket daemon | Hermes gateway cron calls MAS-owned supervision tick script every 300s | drift detection and recovery can be scheduler-bound; no MAS resident daemon is claimed |
| supervision cadence | `purpose_equivalent_with_different_timing` | resident callbacks and worker/session loop | 300s scheduled tick script begins with `watch-runtime --max-ticks 1`, then runs supervisor scan / consume / execute-dispatch; turn-to-turn continuation is owned by the MAS kernel | acceptable for outer drift detection and stale recovery; normal continuation no longer waits for cron, but live interactive daemon response is still not claimed |
| turn completion continuation | `behavior_equivalent` | runner completion normalizes state, drains queued user messages, schedules auto continuation, stops at human/terminal gates | MAS Runtime Turn Lifecycle Kernel performs the same normalization and next-turn decision with runner monitor, delayed timer, worker lease, user queue and receipt |旧 MDS 的“一个 session 结束后怎么启动另一个 session”缺口已补齐为 MAS-owned runtime behavior |
| quest create/resume/pause/stop | `behavior_equivalent` | daemon API / quest service | MAS Runtime OS / study runtime router | daily lifecycle controls do not require external MDS |
| live worker/session tracking | `purpose_equivalent_with_different_timing` | in-memory session store and live session API | worker lease + runner monitor + durable runtime state/read model observed by ticks | fail-closed durable liveness is stronger than stale JSON; MDS in-memory session continuity remains retired |
| crash recovery / auto-resume | `purpose_equivalent_with_different_timing` | daemon startup resume | in-process turn continuation through kernel; stale/crash recovery through next Hermes tick or explicit watch/ensure runtime | normal continuation is low-latency; crash/stale recovery remains scheduler-bound but independent of MDS checkout |
| queued user messages/mailbox | `partially_equivalent` | daemon mailbox schedules turns | quest-local `user_message_queue` triggers turn scheduling; durable task intake / controller handoff handles broader work | queued messages during active worker execution are covered; chat-connector delivery is not default MAS behavior |
| progress visibility | `partially_equivalent` | Web/API status with project/quest-scoped workspace navigation | MAS Progress Portal / study-progress / cockpit, currently centered on workspace overview with study rows | fixed MAS-owned progress place exists, but multi-paper workspace UX still needs per-study/per-paper drilldown to avoid mixed interpretation |
| WebUI/WebSocket/terminal streaming | `purpose_equivalent_with_different_timing` | React WebUI, WebSocket terminal attach, bash log stream | Progress Portal for progress plus MAS-authored Live Console session read model, static shell, snapshot and loopback SSE stream | users get MAS-owned progress and read-only runtime observation; interactive terminal attach and UI-issued runtime control remain future parity candidates, not retired requirements |
| Portal / Live Console real-workspace evidence | `purpose_equivalent_with_different_timing` | WebUI observed live status from resident daemon surfaces | MAS `portal_console_soak` refreshes Portal and Live Console read models, checks multi-study/run disambiguation, terminal/log refs, source-ref cleanliness and MAS identity | users get auditable read-only evidence for the MAS-native visual surfaces; failed soak becomes blocker evidence rather than a hidden fallback to MDS WebUI |
| connector/channel background delivery | `not_equivalent_retired` | QQ/Slack/Discord/Telegram/Weixin/WhatsApp/Feishu background threads | durable handoff refs for external consumers | chat connector delivery is outside default MAS monolith operation |
| MCP surface | `purpose_equivalent_with_different_timing` | daemon-backed MCP | MAS MCP calls owner surfaces directly | MAS truth/status/progress surfaces covered without MDS daemon |
| GitOps state management | `not_equivalent_retired` | root Git / quest Git / diff reader | SQLite lifecycle + restore proof + plain quest dirs | intentional behavior change; Git no longer owns runtime lifecycle |
| memory / lesson store | `partially_equivalent` | memory service / lesson store | portfolio research memory / incident learning read models | lessons are evidence/calibration, not autonomous quality authority |
| team / multi-agent coordination | `historical_fixture_only` | MDS team service | MAS owner_route/controller coordination | team behavior is reference fixture only |
| artifact interaction handoff | `partially_equivalent` | daemon artifact interactions | Artifact OS locator / package handoff / controller refs | package discovery covered; interactive artifact mutation retired |
| daemon lifecycle controls | `not_equivalent_retired` | start/stop/restart MDS daemon | register/remove Hermes cron supervision | no MAS-native MDS daemon control path is needed |
| workspace-local host service | `not_equivalent_retired` | historical MAS launchd/systemd/cron bridge | retired cleanup evidence; canonical owner is Hermes gateway cron | old host services should be removed, not kept as active option |
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

- `outer_supervision_slo`: landed。它解释 outer supervision latency，默认仍由 Hermes gateway cron 300 秒 tick 承担；`due/stale/missing/blocked` 都会投影到用户入口，并给出 canonical one-shot reconcile dry-run 推荐。
- `portal_console_soak`: landed。它证明 MAS-native Portal / Live Console 的 read-only display surface 可在真实 workspace 上审阅；它只写 display evidence，不写 truth。
- `paper_autonomy_stability_evidence`: evidence read model landed。它把真实 workspace 只读证据收成单一 report；如果 evidence 有 blocker，状态应保持 `evidence_landed_with_blockers`，不能宣称真实论文自治稳定性 landed。

这三项让 MAS monolith 的“可解释、可查看、可审阅证据”更接近旧 MDS daemon/WebUI 给用户的信任感，但仍遵守本矩阵的核心结论：MAS 当前不把 MDS resident daemon 或旧 workspace-local service 恢复成默认依赖；交互式 terminal attach / UI control 若要补齐，必须走 MAS-native interactive parity lane，而不是重新启用旧 daemon 作为 owner。

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

- `outer supervision latency`: 仍是 300 秒 Hermes gateway cron one-shot；它只影响 drift detection、stale recovery 和周期性刷新，不再影响正常 turn-to-turn continuation。
- `progress visibility UX`: Progress Portal 已替代默认进度查看入口，并已有 per-study Portal page、Route/Decision Trail read-only helper、conversation read model 与 soak evidence keys。它仍保持 `partially_equivalent`，因为真实多论文 workspace 的长期用户体验、route input 完整性和交互深度仍需 evidence-gated polish。
- `interactive console`: 独立 Live Console UI shell、profile-level session read model、snapshot / loopback SSE stream 和 clean-room contract 已作为 `live-console-parity` landed。它是 read-only purpose equivalence，不是旧 MDS resident WebSocket terminal attach 的 1:1 复刻；terminal attach/input/resize/detach 与 UI-issued runtime control 是后续 interactive parity candidate。
- `connector background delivery`: 旧 MDS 的 QQ/Slack/Discord/Telegram/Weixin/WhatsApp/Feishu background delivery 仍不属于 MAS 默认 monolith；当前只保留 durable handoff refs。
- `in-memory session API`: MAS 选择 durable read model 与 receipt，不恢复旧 MDS in-memory session store。

## 2026-05-09 Remaining Semantic Gaps

下表只列仍可能影响用户感知或未来能力选择的差异；已明确退役且无默认产品价值的能力不进入 active implementation backlog。

| gap | current impact | why it is acceptable now | recommended improvement |
| --- | --- | --- | --- |
| Portal per-study/per-paper IA | 多论文 workspace 里，用户已能进入 per-study Portal page；真实 workspace 还需要验证长期刷新、attention queue、deep link 和 source refs 足够清晰。 | 默认进度入口、source refs、freshness、artifact locator、OPL handoff 和 per-study repo contract 已由 MAS 持有；不会回落到 MDS WebUI。 | P0 polish：继续真实 workspace user soak，修正混读、链接、source ref 可读性和 artifact grouping。 |
| Portal route / decision trail | Repo contract 已落地，但真实论文若缺 controller/evidence/runtime lineage 输入，会 fail-closed 显示 missing，用户仍看不到完整路线演进。 | `focused_lanes.portal-route-decision-trail` 与 `mas_progress_portal_route_decision_trail` 已固定 read-only contract，不让 Portal 重新裁决医学质量。 | P0 soak/polish：补真实 route inputs 与可读 source refs，持续验证 route node、decision rationale、blocked reason、superseded path、active/winning path。 |
| Live Console interactive terminal/control | 当前能看 session/run、terminal/log tail、SSE/snapshot 和 action intent；不能在 UI 里 attach terminal、输入命令、resize/detach 或直接 stop/resume/reconcile apply。 | read-only observation 已覆盖旧 WebUI 的“看状态/日志/终端尾部”目的；直接控制会触碰 runtime owner、authorization、idempotency 和审计边界。 | P1/P2：先做 authorized UI action lane（pause/resume/reconcile/stop intent apply），再单独评估 interactive terminal attach。 |
| outer supervision stale/crash latency | 正常 turn-to-turn continuation 不等 cron；但 worker crash、stale recovery、drift detection 和部分 read-model refresh 仍可能等到 300 秒 Hermes tick，或由 operator 触发 one-shot dry-run/reconcile。 | 这比旧 resident daemon 更可审计、fail-closed，且 `outer_supervision_slo` 已把 fresh/due/stale/blocked 和推荐命令投影给用户。 | P1：对真实 workspace 继续收集 SLO evidence，必要时用安全 one-shot reconcile 或更短受控 scheduler cadence，而不是恢复 resident MDS daemon。 |
| queued mailbox / conversation view | 运行中追加 user message 已有 queue；但用户还缺一个像旧 WebUI chat pane 那样的 executor conversation/timeline 视图。 | durable task intake、owner_route 和 runtime receipts 已能驱动研究，不依赖 chat connector。 | P1：从 turn receipts、user queue、tool/action refs 生成 conversation read model，并挂到 per-study Portal。 |
| artifact interactive mutation | package locator、artifact refs、current package discovery 已由 Artifact OS 持有；旧 MDS interactive artifact API 没有默认保留。 | MAS 选择 canonical-source-first，避免 UI 或 legacy artifact API 绕过 paper/package authority。 | P2：仅在 Artifact OS authority 下增加 file browser / pickup / rebuild proof view；不恢复任意 mutation API。 |
| memory/lesson service | MAS 有 incident learning、portfolio/research memory 和 calibration evidence，但不复刻 MDS autonomous memory service。 | 经验/记忆不能直接授权质量、投稿或 route。 | P2：把高价值 lessons 继续导入 Evaluation OS / research memory，保持 evidence-only。 |

后续完善顺序建议固定为：real-workspace `portal_console_soak` / source-ref polish -> route input completeness -> authorized UI action apply gate -> interactive terminal attach implementation gate。`portal-study-scoped-ia`、`portal-route-decision-trail`、`portal-stage-artifact-path`、`runtime-conversation-read-model` 和 study-scoped Live Console 已有 repo contract；下一步重点是让真实多论文 workspace 的用户体验稳定，同时不让 UI、connector 或旧 daemon 重新成为 runtime owner。

## 旧 Workspace-Local Service Policy

旧 workspace-local `systemd` / `cron` / `launchd` / `docker` service manager 不再是 active MAS runtime option。

当前规则：

- 新 workspace 不渲染 `watch-runtime-service-runner`。
- 新 workspace 不渲染 `ops/medautoscience/supervisor/systemd/*`。
- 新 workspace 不渲染 `ops/medautoscience/supervisor/cron/*`。
- 新 workspace 不渲染 `ops/medautoscience/supervisor/launchd/README.md`。
- `runtime-ensure-supervision --manager systemd|cron|launchd|docker` fail-closed 为 `retired_workspace_local_service_manager`。
- 检测到旧 service file 或 loaded state 时，只作为 `retired_cleanup_evidence`，由 `runtime-ensure-supervision` 清理后回到 Hermes gateway cron。

历史上这些 service 曾作为迁移桥和真实 workspace 排障证据存在。当前 active docs/code/scaffold 不应把它们写成可选 scheduler；历史记录只服务 debug。

## 使用规则

后续 Agent 回答 “MAS 是否完全吸收 MDS” 时，应使用下面口径：

- 可以说：MAS 默认 operation / diagnostic / progress / artifact / quality surfaces 不再要求外部 MDS repo、daemon、runtime root 或 WebUI。
- 可以说：MAS 以 capability supersede / rewrite / retire 方式完成 functional monolith closeout。
- 可以说：Live Console 提供旧 MDS WebUI 观察类能力的 MAS-owned read-only purpose equivalence。
- 可以说：旧 MDS WebUI 的 per-project/per-quest 信息架构是后续 Portal UX parity 的 clean-room oracle，当前 Portal 仍有 per-study/per-paper drilldown 缺口。
- 不能说：MAS 与旧 MDS resident daemon 行为完全等价。
- 不能说：MAS 复刻了 MDS resident WebSocket terminal attach、connector background delivery、team service 或 GitOps runtime lifecycle。
- 不能说：MDS resident WebSocket terminal attach 或 UI-issued runtime control 已经被放弃；准确口径是当前 read-only closeout 未落地这些能力，后续必须通过 MAS-native safety / owner / audit gate。
- 不能把旧 workspace-local launchd/systemd/cron/docker service 当成当前可选运行面。
