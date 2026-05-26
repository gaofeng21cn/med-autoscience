# MDS WebUI User Parity Gap Review

Status: `active UX parity reference`
Owner: `MedAutoScience Product Projection + OPL Runtime Manager integration boundary`
Date: `2026-05-09`
Purpose: `Preserve MDS parity, backend-audit, and historical fixture reference context for MAS.`
State: `support_reference`
Machine boundary: Human-readable parity reference only; current MAS and MDS-source truth remains in explicit archive imports, source provenance, contracts, tests, diagnostics, and receipts.

Related contracts: `live-console-parity`, `mds_behavior_equivalence_matrix`

## 结论

当前 MAS Progress Portal 已经解决了“有 MAS-owned 地方看论文进度、study rows、route / decision trail 和 evidence refs”的问题；repo contract 已把 per-study 工作台、研究路线地图、route-decision read-only helper、artifact/source refs 与 OPL owner-route handoff refs 纳入 MAS-owned progress/domain projection。2026-05-26 校准后，MAS private Live Console、conversation/session read model、terminal attach gate 和 Portal action endpoint 已从当前控制面物理退役，只保留 history/provenance；运行对话、terminal/log/provider drilldown 必须来自 OPL `current_control_state` 或 provider attempt projection。旧 MDS WebUI 的主路径是 project / quest scoped，用户按一篇论文或一个 quest 进入后看进度、stage、文件、执行对话和 terminal；MAS 现在应继续沿 per-study/per-paper progress shell 与 OPL runtime drilldown join 收敛，而不是恢复旧 WebUI、旧 daemon 或 MAS 私有 terminal owner 作为 owner。

因此当前口径应改为：

- `progress_visibility`: `partially_equivalent`，但 repo contract 已前进。MAS 有固定 Portal、study-progress、cockpit、per-study page、source refs、`mas_progress_portal_route_decision_trail` 和 `mas_progress_portal_route_map` read-only helper；真实 workspace 用户等价仍取决于多论文 workspace soak、route inputs 完整性和 UI polish。
- `live_console_parity`: `retired_mas_private_runtime_surface_with_opl_runtime_drilldown_join`。MAS 只保留 Progress Portal payload / per-study static page / route-decision read-only projection 和 domain refs；Progress Portal 本地 action endpoint 已退役；pause/resume/stop 意图走 domain-handler / OPL owner-route handoff refs。Terminal attach/input/resize/detach 不由 MAS terminal attach owner gate 管理，也不在 MAS Portal 暴露；运行 terminal/log/provider drilldown 的 owner 是 OPL `current_control_state` / provider attempt projection。旧 MDS 的 resident WebSocket owner 仍不进入 MAS 默认运行。
- `old_mds_webui_code`: 仍不导入。可借鉴旧 MDS WebUI 的行为规格、信息架构和 UX oracle，不能复制旧 React/WebSocket 代码、bundle、历史或产品身份。

2026-05-26 fresh assessment：这个 gap review 仍然成立，但它的含义需要更精确。MAS Progress Portal 的 repo 能力已经 landed，真实 workspace evidence 以 read-model / refs projection 形式存在；当前缺口是 per-study 用户路径 polish、route input 完整性和 OPL runtime drilldown join，不是 MAS 默认还需要 MDS WebUI、MAS private Live Console 或 MAS terminal attach gate。对用户影响最大的是“真实多论文 workspace 中每篇论文是否稳定走 per-study 工作台”、“研究路线地图是否有足够 controller/evidence/runtime lineage 输入”、“OPL `current_control_state` 能否在 App/workbench 中和 MAS study projection 并列展示运行状态、终端/log/provider refs”。这些应作为 MAS progress projection + OPL App/runtime workbench lane 处理，不应通过重新启用旧 MDS daemon、旧 WebUI 或 MAS 私有 terminal owner 解决。

## Evidence

旧 MDS WebUI / daemon 的可观察能力：

- `src/ui/src/App.tsx` 把 `/projects/:projectId` 路由到 `ProjectWorkspacePage`，用户入口天然按 project / quest 切分。
- `ProjectWorkspacePage` 将 project id 传给 `WorkspaceLayout`；`WorkspaceLayout` 支持 quest workspace view，包括 `canvas`、`stage`、`details`、`memory`、`terminal`、`settings`。
- `QuestWorkspaceSurface` 聚合 quest runtime、文件、stage、memory、terminal、copilot/chat 相关 pane。
- `QuestStageSurface` 提供 stage-scoped structured facts、history、files、download/open 入口。
- `QuestConnectorChatView` 提供 quest transcript、streaming assistant message、user composer、stop run 和 older history。
- `QuestBashExecOperation` 提供 bash execution status、progress、command/workdir、tool call/result 展示。
- `daemon/app.py` 的 terminal attach path 使用 WebSocket token，支持 active runtime snapshot replay、logged terminal replay、input、binary input、resize、detach、ping/pong 和 terminal exit/error event。

当前 MAS 落地能力：

- `src/med_autoscience/controllers/progress_portal.py` 能生成 `ops/mas/progress/index.html` 和 payload，默认 workspace overview 下会解析 cockpit studies，并选择一个 active study 或 `workspace-overview`。
- `progress_portal_parts/workspace_overview.py` 已生成 study table，包含 `study_id`、状态、`active_run_id`、runtime health、supervisor、freshness、paper/current stage、焦点/下一步。
- `progress_portal_parts/workspace_carrier.py` 只作为 read-model materializer 写 `artifacts/runtime/progress_portal/*` 与 `ops/mas/progress/*` display/read-model evidence；hosted package 暴露 `mas_progress_portal_read_model_materializer_boundary`，active callers 为空。
- `progress_portal_parts/study_workbench.py`、`route_decision_trail.py` 和 `route_map.py` 提供 per-study workbench、route-decision trail 与路线地图 read-only projection，不重新解释 study truth、runtime truth 或 medical quality。
- MAS private Live Console / conversation/session read model / terminal attach gate 已从当前控制面物理退役；terminal/log/provider drilldown 归 OPL `current_control_state`。

差距不在“有没有任何进度页”，而在“用户是否能以单篇论文为核心稳定理解系统正在做什么”。当前 MAS 已有 per-study workbench repo contract；Progress Portal 是论文/domain progress 与 evidence refs 入口，不是运行控制面或 terminal owner。terminal/log/provider drilldown、live execution drilldown 和 attach/control 必须并列展示 OPL `current_control_state` 或 provider attempt projection。另一个原 P0 语义缺口已经有机器合同承接：旧 MDS WebUI 能让用户看到类似研究路线的演进，MAS 现在用 `focused_lanes.portal-route-decision-trail`、`mas_progress_portal_route_decision_trail` 和 `mas_progress_portal_route_map` helper 固定 read-only projection，展示先尝试哪条分析/写作路径，哪一步因为证据、质量、数据或运行 blocker 走不通，为什么切换到另一条路线，以及最终哪条路线仍是 active / winning path。真实 workspace 若缺 controller decision、evidence/review ledger 或 runtime lineage 输入，页面必须显示 missing，不得编造路线。

## User-View Parity Matrix

| User capability | Old MDS WebUI behavior | Current MAS behavior | Gap | Priority |
| --- | --- | --- | --- | --- |
| 按论文/quest 进入 | `/projects/:projectId` 进入 project / quest workspace；之后的 canvas/stage/details/memory/terminal 都围绕同一 quest。 | `ops/mas/progress/index.html` 是 workspace 固定入口；study rows 可区分论文线，但默认叙事仍是 workspace overview。 | 需要 per-study/per-paper page、稳定 deep link 和默认选中逻辑，避免多论文混读。 | P0 |
| 当前实时进度 | WebUI 从 resident daemon/API/WebSocket 读 live 状态，用户感知接近即时。 | Portal 读 MAS durable projection；运行 freshness / provider state 从 OPL `current_control_state` 或 provider attempt projection 并列进入 App/workbench。 | 需要在每个 study 页直接显示 refresh age、latency/SLO、last event、blocked reason 和 OPL runtime handoff state；长期 soak 证明刷新体验。 | P0 |
| 论文路径 / stage | Stage surface 将 structured facts、history、files、download/open 与 quest selection 绑定。 | Portal 显示 paper/current stage 摘要和 artifact refs；没有完整 per-study path/stage/file workspace。 | 需要 study-scoped Path/Stage tab，把 stage、evidence、files、package refs 组织成单篇论文路线。 | P0 |
| 研究路线 / 决策轨迹 | Canvas / stage / history 能体现路线演进、分叉、失败路径和后续转向。 | MAS 已有 `focused_lanes.portal-route-decision-trail`、`mas_progress_portal_route_decision_trail` 与 `mas_progress_portal_route_map` read-only helper，消费 controller/evidence/runtime lineage/source refs，并把 `intervention_lane` 投影成用户可读路线地图。 | 需要真实 workspace soak/polish，确保每篇论文都有足够 route inputs 和可读 source refs。 | P0 landed visualization / soak pending |
| 执行器实时对话 | Quest connector/chat pane 有 transcript、streaming assistant message、user composer、stop run、older history。 | MAS per-study Portal 不持有运行对话 truth；App/workbench 应从 OPL `current_control_state` / provider attempt refs 并列展示执行器回合、typed blocker 和 owner handoff。 | 真实 workspace 长时间 soak 仍需验证 MAS study projection 与 OPL runtime drilldown join 的覆盖度和 source ref 可读性。 | P1 OPL join pending |
| terminal/log 观察 | WebUI 可以看 bash tool operation、progress、logs，并通过 xterm/WebSocket attach 到 terminal。 | MAS Portal 不暴露 terminal/log runtime owner；OPL `current_control_state` / provider attempt projection 持有 terminal/log/provider drilldown。 | 需要 OPL runtime workbench drilldown join；MAS 只展示 progress/domain refs、owner receipt 或 typed blocker。 | P1 |
| UI 控制运行 | WebUI 可发消息、stop run、terminal input、部分 daemon/system 操作。 | MAS Progress Portal 不再提供 `--serve --enable-actions`；pause/resume/stop、inspect、reconcile 意图应显示为 domain-handler / OPL owner-route handoff refs，不由 Portal action endpoint 执行。 | terminal input/resize/detach 不属于 MAS Portal 默认能力；runtime apply / terminal command 必须由 OPL runtime owner surface 和审计 gate 承担。 | P2 OPL owner |
| 多论文 workspace | 旧 WebUI 的 project/quest route 减少混淆；用户通常在单 quest 上操作。 | MAS workspace overview 会把所有 studies 放到同一表和同一页面上下文。 | 需要左侧 study list / attention queue + 单 study detail 主面；workspace overview 只作入口，不作主要解释页。 | P0 |
| artifact/file discoverability | 文件树、open/download、stage files 与 quest workspace 在同一 UI 中。 | Progress Portal 有 artifact/source refs；OPL runtime drilldown 可并列展示 provider / terminal / log refs；不是集成文件浏览体验。 | 需要 artifact/file tab，按 current package、draft、tables/figures、review/proof 分组。 | P1 |

## Target Information Architecture

Progress Portal 后续应从“一个 workspace 大页面”调整为“workspace shell + per-study detail”：

- Workspace shell：左侧或顶部是 study list / attention queue，默认只回答“哪些论文线需要看”。每个 item 显示 `study_id`、短题名、状态、last seen、blocker、next action、live/run badge。
- Study detail：选中一个 study 后，主区域只解释这篇论文。首屏应显示研究标题/问题、当前阶段、正在做什么、下一步、阻塞、freshness、active run 和交付入口。
- Study tabs：
  - `Overview`: 人话状态、blocker、next action、quality/publication status。
  - `路线/决策`: 研究路线、分支、失败/阻塞原因、转向理由、superseded path、active/winning path 和 controller/evidence/review/runtime source refs。
  - `Path / Stage`: 当前 stage、stage history、evidence/review/proof refs。
  - `Runtime / Run`: active/last run、worker liveness、supervision SLO、receipts，并标明 OPL `current_control_state` / provider attempt refs。
  - `执行器对话`: OPL runtime drilldown refs、typed blocker、owner handoff、tool/action/source refs；MAS 不持有 runtime conversation truth。
  - `Terminal / Logs`: OPL terminal/log/provider refs 与 stream health；MAS 不挂 terminal attach owner gate。
  - `Artifacts`: draft、tables/figures、current package、review records、rebuild proof。
  - `Source Refs`: durable refs，默认折叠给维护者。
- Runtime drilldown 从 Portal / App 进入时应默认带 `study_id`，并跳到 OPL `current_control_state` / provider attempt projection；旧 MAS Live Console 只作为 history/provenance 读取。
- 静态路径可以继续保留 `ops/mas/progress/index.html`，但应提供 per-study deep link，例如 query `?study_id=<study_id>` 或 materialized `ops/mas/progress/studies/<study_id>/index.html`。

## Backlog Lanes

| Lane | Machine contract | Scope | Done criteria |
| --- | --- | --- |
| `portal-study-scoped-ia` | Progress Portal materialization / real-workspace progress evidence keys | 把 Portal 默认 UX 改成 workspace shell + per-study detail/deep link。 | 多论文 workspace 打开后不会混读；单 study 页能回答状态、路径、阻塞、下一步、artifact。 |
| `portal-route-decision-trail` | `focused_lanes.portal-route-decision-trail` | 把 controller decisions、evidence/review ledgers 和 runtime lifecycle lineage/canvas 投影成单篇论文路线图。 | 用户能看到尝试过的路线、失败或阻塞原因、转向理由、superseded path、active/winning path、route map node/edge 和对应 source refs；Portal 不重新解释医学质量。 |
| `portal-stage-artifact-path` | Progress Portal materialization / artifact refs evidence keys | 做 study-scoped Path/Stage/Artifacts view。 | stage history、evidence/review/proof、draft/package/files 都按单篇论文组织。 |
| `runtime-drilldown-join` | OPL `current_control_state` / provider attempt projection refs | 从 per-study Portal / App workbench 并列展示 OPL runtime state、attempt refs、terminal/log/provider refs、typed blockers 和 owner handoff。 | 用户能在单篇论文页看清 MAS domain progress 与 OPL runtime 状态的 join，不把 MAS Portal 写成 runtime owner。 |
| `live-console-study-scope-polish` | retired MAS Live Console provenance | 旧 study-scoped Live Console 只保留 history/provenance；当前实现目标是 OPL runtime drilldown join。 | Terminal/log tail 与 run identity 不再在 MAS profile view 中混淆，统一来自 OPL runtime owner。 |
| `interactive-terminal-attach-design` | retired MAS terminal attach gate provenance | MAS 不再维护 terminal attach/control owner；旧设计只作为 history/provenance。 | 运行 terminal/log/provider drilldown 必须来自 OPL `current_control_state` 或 provider attempt projection；MAS 只暴露 progress/domain refs、owner receipt 或 typed blocker。 |
| `authorized-ui-control` | domain-handler / OPL owner-route handoff refs | UI action intent 到 OPL runtime owner 的最小安全链路。 | `pause`、`resume`、`stop` 意图只展示 handoff refs；terminal input 另行 gate。 |
| `real-workspace-user-soak` | Progress Portal + OPL runtime drilldown join evidence keys | 对真实多论文 workspace 做长期刷新和用户路径 soak。 | 记录 latency、freshness、confusion cases、source-ref readability 和 blocked reasons。 |

## Current Impact And Priority

| priority | gap | current user impact | next implementation shape |
| --- | --- | --- | --- |
| P0 landed contract / soak pending | `portal-study-scoped-ia` | 用户能打开一个固定 Portal；真实多论文 workspace 仍需验证默认路径不会混读。 | 继续真实 workspace user soak、source ref polish 和 IA 细节修正。 |
| P0 landed visualization / soak pending | `portal-route-decision-trail` | 用户能看到 repo contract 中的路线图 projection 和 SVG 研究路线地图；真实论文若缺 route inputs 会显示 missing。 | 补真实 controller/evidence/runtime lineage 输入质量，持续 soak Route / Decision Trail 与 route map 可读性。 |
| P0 landed contract / polish pending | `portal-stage-artifact-path` | 用户能看到 artifact refs 和 per-study grouping；真实 workspace 还需要路径可读性 polish。 | 在 per-study detail 里继续打磨 Path/Stage 与 Artifacts tabs。 |
| P1 OPL join pending | `runtime-drilldown-join` | 用户需要在 App/workbench 中同时看到 MAS study progress 与 OPL current_control_state / provider attempt drilldown。 | 从 OPL runtime owner refs 持续增强只读 runtime drilldown join。 |
| P1 retired MAS surface / OPL owner | `live-console-study-scope-polish` | 旧 MAS Live Console 不再是当前 surface；terminal/log/provider drilldown 统一归 OPL。 | 继续验证 App/workbench 默认按 study 过滤 OPL run/log/terminal refs。 |
| P2 OPL owner | `authorized-ui-control` | 用户可看到 pause/resume/stop 的 owner-route handoff refs；terminal input 与 reconcile apply 不在 MAS Portal 默认能力内。 | 继续真实 workspace owner-route handoff soak；runtime apply / terminal command 只由 OPL runtime owner surface 承担。 |
| P2 | `interactive-terminal-attach-design` | 不能复刻旧 MDS WebSocket terminal attach 的交互体验。 | 先由 OPL runtime owner 完成 threat model 与 audit gate，再决定是否实现 terminal input/resize/detach。 |

当前不建议把 connector background delivery、旧 GitOps runtime lifecycle、MDS daemon start/stop/update control 或 workspace-local launchd/systemd/cron/docker service 写入此 backlog；这些已按 MAS monolith 目标退役。

## Wording Rules

- 可以说：当前 MAS 已落地 progress read-only purpose parity，用户能通过 Progress Portal 看进度、study rows、route/decision trail、source/artifact refs、owner receipt 或 typed blocker；运行 drilldown 归 OPL `current_control_state`。
- 可以说：研究路线 / decision trail 的 MAS read-only contract 已落地为 `focused_lanes.portal-route-decision-trail`、`mas_progress_portal_route_decision_trail` 和 `mas_progress_portal_route_map`；真实 workspace route input 完整性、长期刷新和 UI 可读性仍是 P0 soak/polish。
- 可以说：旧 MDS WebUI 的产品身份、代码、bundle、Git history 和 contributor footprint 不导入 MAS。
- 不能说：旧 resident WebSocket terminal attach、terminal input/resize 或 UI 控制 daemon 已被 MAS Portal 吸收、复刻或成为 MAS-owned runtime control。
- 应说：这些交互能力不属于 MAS Portal 当前 read-only scope，若未来补齐必须由 OPL runtime owner surface 通过安全、owner、idempotency 和审计 gate 承担。
- 不能说：当前 Progress Portal 的用户体验已经完整等价旧 MDS WebUI。当前 repo contract 已覆盖 per-paper/per-study 工作台和 Route / Decision Trail，但真实 workspace 长时间用户体验、交互控制和 terminal attach 仍需 gated polish/soak。
- 不能说：Path/Stage 只要列出当前 stage 和 artifact refs 就已经覆盖旧 MDS 的研究路线视图；必须显式展示路线分支、失败/阻塞原因、转向理由和 active/winning path。
