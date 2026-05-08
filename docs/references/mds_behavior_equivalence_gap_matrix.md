# MDS Behavior Equivalence Gap Matrix

Status: `active behavior-audit reference`
Owner: `MedAutoScience Runtime OS`
Date: `2026-05-08`
Related contract: `live-console-parity`

## 结论

MAS 已经做到默认 operation、默认诊断、进度可视化、artifact/quality/status/progress/cockpit/OPL handoff 不要求外部 `med-deepscientist` repo、daemon、runtime root 或 WebUI。

2026-05-08 Runtime Turn Lifecycle correction 已解决旧审计中最关键的“连续跑”缺口：runner completion 不再等外部 cron 触发下一轮，而是在 MAS-owned `mas_runtime_core` 内通过 `complete_turn_and_normalize` 清理 `active_run_id` / `worker_running`，按 queued user messages、human gate、terminal status 与 `continuation_policy` 决定下一 turn；`auto_continue` 仍保持约 `0.2s` 的低延迟 kernel timer。

2026-05-08 Runtime Continuity closeout 补齐了 daemon 退役后另一个影响用户信任的外层行为：durable session/worker tracking 和 crash-recovery intent。MAS 现在用 `runtime_session` read model 投影 worker/last seen/run/freshness，用 `recovery_intent` ledger 记录恢复原因、next owner、retry budget 与 current action，用 `runtime_reconcile_trigger` 给读入口展示一次 safe reconcile 的幂等推荐。这些能力仍是 scheduler-bound / controller-owned，不表示 MAS 变成 resident MDS daemon。

2026-05-08 Runtime Evidence closeout 又把剩余用户感知缺口压成三组可审阅 evidence：`outer_supervision_slo` 解释 300 秒外环是否 fresh/due/stale/missing/blocked，并给出 safe one-shot reconcile dry-run；`portal_console_soak` 在真实 workspace 上证明 MAS Progress Portal / Live Console 可刷新、可区分多 study/run、source refs 不回流旧 MDS identity；`paper_autonomy_stability_evidence` 把真实 profile inventory、supervisor reconcile dry-run、workspace migration dry-run 和 real workspace soak monitor 合成单一 read model。这些 surface 解决“用户怎么看监管是否还在、页面是否可信、真实论文自治证据是否足够”的问题，不声明旧 resident daemon 低延迟交互或 connector threads 1:1 等价。

这不等于旧 MDS resident daemon 的行为被 1:1 复刻。正确完成口径是：

- `default_independence`: landed
- `full_mds_daemon_behavior_equivalence`: false
- `default_supervision_owner`: `hermes_gateway_cron`
- `default_tick_interval_seconds`: `300`
- `default_tick_max_ticks`: `1`
- `default_tick_command`: `ops/medautoscience/bin/watch-runtime --interval-seconds 300 --max-ticks 1`

旧 MDS daemon 的关键事实是 resident `ThreadingHTTPServer` + WebSocket + session store + background connector / worker / recovery loop。MAS 当前拆成两层：内层 turn lifecycle kernel 已承担 runner 返回后的连续科研主循环；外层 Hermes gateway cron 仍承担 drift detection、stale recovery、read-model refresh 与 supervision tick。二者在“日常研究推进、turn-to-turn continuation、恢复投影和进度查看”上已经解决主要运行目的问题；在 resident process、低延迟交互、WebSocket terminal、connector background delivery 和 in-memory session continuity 上仍不完全等价。

## 行为分类

机器可读矩阵在 `med_autoscience.controllers.mds_capability_parity.build_mds_behavior_equivalence_matrix()`。

允许分类只有：

- `behavior_equivalent`: 行为目标和默认用户影响等价。
- `purpose_equivalent_with_different_timing`: 目标等价，但节奏、延迟或实现方式有显著差异。
- `partially_equivalent`: MAS 覆盖研究主流程，但旧 MDS 的某些交互或附属能力已不作为默认能力。
- `not_equivalent_retired`: 旧能力不再作为 MAS 默认能力保留。
- `historical_fixture_only`: 只作为历史行为对照或回归 fixture。

当前汇总：

| class | count |
| --- | ---: |
| `behavior_equivalent` | 3 |
| `purpose_equivalent_with_different_timing` | 6 |
| `partially_equivalent` | 3 |
| `not_equivalent_retired` | 4 |
| `historical_fixture_only` | 1 |

## 关键行为差异

| behavior surface | classification | MDS behavior | MAS behavior | user impact |
| --- | --- | --- | --- | --- |
| daemon residency | `purpose_equivalent_with_different_timing` | resident HTTP/WebSocket daemon | Hermes gateway cron calls one-shot MAS tick every 300s | drift detection and recovery can be scheduler-bound; no MAS resident daemon is claimed |
| supervision cadence | `purpose_equivalent_with_different_timing` | resident callbacks and worker/session loop | 300s scheduled tick with `max_ticks=1`, with turn-to-turn continuation owned by the MAS kernel | acceptable for outer drift detection and stale recovery; normal continuation no longer waits for cron, but live interactive daemon response is still not claimed |
| turn completion continuation | `behavior_equivalent` | runner completion normalizes state, drains queued user messages, schedules auto continuation, stops at human/terminal gates | MAS Runtime Turn Lifecycle Kernel performs the same normalization and next-turn decision with runner monitor, delayed timer, worker lease, user queue and receipt |旧 MDS 的“一个 session 结束后怎么启动另一个 session”缺口已补齐为 MAS-owned runtime behavior |
| quest create/resume/pause/stop | `behavior_equivalent` | daemon API / quest service | MAS Runtime OS / study runtime router | daily lifecycle controls do not require external MDS |
| live worker/session tracking | `purpose_equivalent_with_different_timing` | in-memory session store and live session API | worker lease + runner monitor + durable runtime state/read model observed by ticks | fail-closed durable liveness is stronger than stale JSON; MDS in-memory session continuity remains retired |
| crash recovery / auto-resume | `purpose_equivalent_with_different_timing` | daemon startup resume | in-process turn continuation through kernel; stale/crash recovery through next Hermes tick or explicit watch/ensure runtime | normal continuation is low-latency; crash/stale recovery remains scheduler-bound but independent of MDS checkout |
| queued user messages/mailbox | `partially_equivalent` | daemon mailbox schedules turns | quest-local `user_message_queue` triggers turn scheduling; durable task intake / controller handoff handles broader work | queued messages during active worker execution are covered; chat-connector delivery is not default MAS behavior |
| progress visibility | `behavior_equivalent` | Web/API status | MAS Progress Portal / study-progress / cockpit | fixed MAS-owned progress place replaces MDS WebUI for default users |
| WebUI/WebSocket/terminal streaming | `purpose_equivalent_with_different_timing` | React WebUI, WebSocket terminal attach, bash log stream | Progress Portal for progress plus MAS-authored Live Console session read model, static shell, snapshot and loopback SSE stream | users get MAS-owned progress and read-only runtime observation; old resident WebSocket terminal attach is not restored |
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

这三项让 MAS monolith 的“可解释、可查看、可审阅证据”更接近旧 MDS daemon/WebUI 给用户的信任感，但仍遵守本矩阵的核心结论：MAS 不恢复 MDS resident daemon，也不恢复旧 workspace-local service。

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
- `interactive console`: Progress Portal 已替代默认进度查看；独立 Live Console UI shell、profile-level session read model、snapshot / loopback SSE stream 和 clean-room contract 已作为 `live-console-parity` landed。它是 read-only purpose equivalence，不是旧 MDS resident WebSocket terminal attach 的 1:1 复刻。
- `connector background delivery`: 旧 MDS 的 QQ/Slack/Discord/Telegram/Weixin/WhatsApp/Feishu background delivery 仍不属于 MAS 默认 monolith；当前只保留 durable handoff refs。
- `in-memory session API`: MAS 选择 durable read model 与 receipt，不恢复旧 MDS in-memory session store。

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
- 不能说：MAS 与旧 MDS resident daemon 行为完全等价。
- 不能说：MAS 复刻了 MDS resident WebSocket terminal attach、connector background delivery、team service 或 GitOps runtime lifecycle。
- 不能把旧 workspace-local launchd/systemd/cron/docker service 当成当前可选运行面。
