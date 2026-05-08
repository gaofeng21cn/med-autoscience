# MDS Behavior Equivalence Gap Matrix

Status: `active behavior-audit reference`
Owner: `MedAutoScience Runtime OS`
Date: `2026-05-08`

## 结论

MAS 已经做到默认 operation、默认诊断、进度可视化、artifact/quality/status/progress/cockpit/OPL handoff 不要求外部 `med-deepscientist` repo、daemon、runtime root 或 WebUI。

2026-05-08 Runtime Continuity closeout 补齐了 daemon 退役后最影响用户信任的两类行为：durable session/worker tracking 和 crash-recovery intent。MAS 现在用 `runtime_session` read model 投影 worker/last seen/run/freshness，用 `recovery_intent` ledger 记录恢复原因、next owner、retry budget 与 current action，用 `runtime_reconcile_trigger` 给读入口展示一次 safe reconcile 的幂等推荐。这些能力仍是 scheduler-bound / controller-owned，不表示 MAS 变成 resident MDS daemon。

这不等于旧 MDS resident daemon 的行为被 1:1 复刻。正确完成口径是：

- `default_independence`: landed
- `full_mds_daemon_behavior_equivalence`: false
- `default_supervision_owner`: `hermes_gateway_cron`
- `default_tick_interval_seconds`: `300`
- `default_tick_max_ticks`: `1`
- `default_tick_command`: `ops/medautoscience/bin/watch-runtime --interval-seconds 300 --max-ticks 1`

旧 MDS daemon 的关键事实是 resident `ThreadingHTTPServer` + WebSocket + session store + background connector / worker / recovery loop。MAS 默认运行是 Hermes gateway cron 调 MAS one-shot tick。二者在“能否独立完成日常研究推进和恢复投影”上可以达到目的等价；在 resident process、低延迟交互、WebSocket terminal、connector background delivery 和 in-memory session continuity 上并不完全等价。

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
| `behavior_equivalent` | 2 |
| `purpose_equivalent_with_different_timing` | 5 |
| `partially_equivalent` | 3 |
| `not_equivalent_retired` | 5 |
| `historical_fixture_only` | 1 |

## 关键行为差异

| behavior surface | classification | MDS behavior | MAS behavior | user impact |
| --- | --- | --- | --- | --- |
| daemon residency | `purpose_equivalent_with_different_timing` | resident HTTP/WebSocket daemon | Hermes gateway cron calls one-shot MAS tick every 300s | drift detection and recovery can be scheduler-bound; no MAS resident daemon is claimed |
| supervision cadence | `purpose_equivalent_with_different_timing` | resident callbacks and worker/session loop | 300s scheduled tick with `max_ticks=1` | acceptable for paper runtime recovery, not equivalent to live interactive daemon response |
| quest create/resume/pause/stop | `behavior_equivalent` | daemon API / quest service | MAS Runtime OS / study runtime router | daily lifecycle controls do not require external MDS |
| live worker/session tracking | `purpose_equivalent_with_different_timing` | in-memory session store and live session API | durable runtime state/read model observed by ticks | fail-closed durable liveness, no MDS in-memory session continuity |
| crash recovery / auto-resume | `purpose_equivalent_with_different_timing` | daemon startup resume | next Hermes tick or explicit watch/ensure runtime | independent of MDS checkout, but scheduler-bound latency |
| queued user messages/mailbox | `partially_equivalent` | daemon mailbox schedules turns | durable task intake / controller handoff | research task intake covered; chat-connector mailbox is not default MAS behavior |
| progress visibility | `behavior_equivalent` | Web/API status | MAS Progress Portal / study-progress / cockpit | fixed MAS-owned progress place replaces MDS WebUI for default users |
| WebUI/WebSocket/terminal streaming | `not_equivalent_retired` | React WebUI, WebSocket terminal attach, bash log stream | read-only Portal snapshot / optional read-only refresh service; MAS Live Console parity planned | current Progress Portal is not an interactive console; parity plan is tracked in `docs/runtime/mas_live_console_mds_webui_parity_plan.md` |
| connector/channel background delivery | `not_equivalent_retired` | QQ/Slack/Discord/Telegram/Weixin/WhatsApp/Feishu background threads | durable handoff refs for external consumers | chat connector delivery is outside default MAS monolith operation |
| MCP surface | `purpose_equivalent_with_different_timing` | daemon-backed MCP | MAS MCP calls owner surfaces directly | MAS truth/status/progress surfaces covered without MDS daemon |
| GitOps state management | `not_equivalent_retired` | root Git / quest Git / diff reader | SQLite lifecycle + restore proof + plain quest dirs | intentional behavior change; Git no longer owns runtime lifecycle |
| memory / lesson store | `partially_equivalent` | memory service / lesson store | portfolio research memory / incident learning read models | lessons are evidence/calibration, not autonomous quality authority |
| team / multi-agent coordination | `historical_fixture_only` | MDS team service | MAS owner_route/controller coordination | team behavior is reference fixture only |
| artifact interaction handoff | `partially_equivalent` | daemon artifact interactions | Artifact OS locator / package handoff / controller refs | package discovery covered; interactive artifact mutation retired |
| daemon lifecycle controls | `not_equivalent_retired` | start/stop/restart MDS daemon | register/remove Hermes cron supervision | no MAS-native MDS daemon control path is needed |
| workspace-local host service | `not_equivalent_retired` | historical MAS launchd/systemd/cron bridge | retired cleanup evidence; canonical owner is Hermes gateway cron | old host services should be removed, not kept as active option |

## Runtime Continuity Completion

本轮 landed surface 固定为：

- `runtime_session_read_model`：只读投影 `study_id`、`quest_id`、`active_run_id`、`last_known_run_id`、`worker_state`、`worker_running`、`runtime_liveness_status`、`started_at`、`last_seen_at`、`last_event_cursor`、`last_stdout_ref`、freshness 与 evidence refs。
- `runtime_recovery_intent`：supervisor-owned ledger，记录恢复原因、next owner、retry budget、dedupe fingerprint、last attempt/result、next eligible tick 与 `current_action`。
- `runtime_reconcile_trigger_projection`：读入口只展示 safe reconcile 推荐与 blocked reasons；它不执行 reconcile，不写 runtime truth。
- `mas_runtime_continuity_projection`：投影到 `study-progress`、workspace cockpit、product-entry status、Progress Portal、MCP compact projection 和 OPL handoff。

这组 surface 的完成口径是“用户能看清有没有 worker、上次看到什么时候、为什么没继续、下一次怎么恢复”。它不复刻 MDS in-memory session API，也不复刻 WebSocket terminal。质量、投稿、交付授权继续由 MAS quality/publication/artifact owner surface 持有。

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
- 不能说：MAS 与旧 MDS resident daemon 行为完全等价。
- 不能说：MAS 复刻了 MDS WebSocket terminal、connector background delivery、team service 或 GitOps runtime lifecycle。
- 不能把旧 workspace-local launchd/systemd/cron/docker service 当成当前可选运行面。
