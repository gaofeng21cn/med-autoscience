# MDS WebUI User Parity Gap Review

Status: `active UX parity reference`
Owner: `MedAutoScience Product Projection + Runtime OS`
Date: `2026-05-09`
Related contracts: `live-console-parity`, `mds_behavior_equivalence_matrix`

## 结论

当前 MAS Progress Portal / Live Console 已经解决了“有 MAS-owned 地方看进度和只读运行证据”的问题，并且 repo contract 已把 per-study 工作台、Route / Decision Trail、Conversation read model、study-scoped Live Console、authorized action receipts 和 terminal attach fail-closed gate 纳入 MAS-owned surface。用户视角的剩余差距主要转为真实 workspace polish、长期刷新 soak、source ref 可读性和交互控制安全门禁。旧 MDS WebUI 的主路径是 project / quest scoped，用户按一篇论文或一个 quest 进入后看进度、stage、文件、执行对话和 terminal；MAS 现在应继续沿 per-study/per-paper shell 收敛，而不是恢复旧 WebUI 或旧 daemon 作为 owner。

因此当前口径应改为：

- `progress_visibility`: `partially_equivalent`，但 repo contract 已前进。MAS 有固定 Portal、study-progress、cockpit、per-study page、source refs 和 `mas_progress_portal_route_decision_trail` read-only helper；真实 workspace 用户等价仍取决于多论文 workspace soak、route inputs 完整性和 UI polish。
- `live_console_parity`: `landed_read_only_purpose_parity`。MAS 有 session/run/terminal/log tail 的只读观察面；旧 MDS 的 resident WebSocket terminal attach、terminal input/resize/detach 和 UI-issued runtime control 不是当前 landed scope，但也不应写成 retired / abandoned。它们是后续 interactive parity lane，需要安全、owner、idempotency 和审计 gate。
- `old_mds_webui_code`: 仍不导入。可借鉴旧 MDS WebUI 的行为规格、信息架构和 UX oracle，不能复制旧 React/WebSocket 代码、bundle、历史或产品身份。

2026-05-09 fresh assessment：这个 gap review 仍然成立，但它的含义需要更精确。MAS Progress Portal / Live Console 的 repo 能力已经 landed，真实 workspace read-only soak 也有 evidence；当前缺口是用户路径 polish 和交互深度，不是 MAS 默认还需要 MDS WebUI。对用户影响最大的是“真实多论文 workspace 中每篇论文是否稳定走 per-study 工作台”、“Route / Decision Trail 是否有足够 controller/evidence/runtime lineage 输入”、“Conversation pane 是否覆盖真实执行器证据”和“Live Console 能否在安全门禁下执行授权控制”。这些应作为 MAS-native UX / control lane 处理，不应通过重新启用旧 MDS daemon 或旧 WebUI 解决。

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
- `runtime_live_console_ui.py` 能渲染 read-only Live Console HTML，展示 workspace/study/run 表、timeline、terminal stream tail、log stream tail、artifact/event refs。
- `progress_portal_parts/live_console_shell.py` 提供 Portal 到 Live Console 的 thin link/ref，authority 是 `read_only_runtime_observation`。

差距不在“有没有任何进度页”，而在“用户是否能以单篇论文为核心稳定理解系统正在做什么”。当前 MAS 已有 per-study workbench repo contract，Live Console 是运行证据页，不是论文进度主入口；执行器对话、terminal attach/control、stage/file path 仍需要真实 workspace polish 和更完整的用户路径。另一个原 P0 语义缺口已经有机器合同承接：旧 MDS WebUI 能让用户看到类似研究路线的演进，MAS 现在用 `focused_lanes.portal-route-decision-trail` 和 `mas_progress_portal_route_decision_trail` helper 固定 read-only projection，展示先尝试哪条分析/写作路径，哪一步因为证据、质量、数据或运行 blocker 走不通，为什么切换到另一条路线，以及最终哪条路线仍是 active / winning path。真实 workspace 若缺 controller decision、evidence/review ledger 或 runtime lifecycle lineage 输入，页面必须显示 missing，不得编造路线。

## User-View Parity Matrix

| User capability | Old MDS WebUI behavior | Current MAS behavior | Gap | Priority |
| --- | --- | --- | --- | --- |
| 按论文/quest 进入 | `/projects/:projectId` 进入 project / quest workspace；之后的 canvas/stage/details/memory/terminal 都围绕同一 quest。 | `ops/mas/progress/index.html` 是 workspace 固定入口；study rows 可区分论文线，但默认叙事仍是 workspace overview。 | 需要 per-study/per-paper page、稳定 deep link 和默认选中逻辑，避免多论文混读。 | P0 |
| 当前实时进度 | WebUI 从 resident daemon/API/WebSocket 读 live 状态，用户感知接近即时。 | Portal 读 MAS durable projection；Live Console snapshot/SSE 提供只读运行观察；outer supervision freshness 可见。 | 需要在每个 study 页直接显示 refresh age、latency/SLO、last event 和 blocked reason；长期 soak 证明刷新体验。 | P0 |
| 论文路径 / stage | Stage surface 将 structured facts、history、files、download/open 与 quest selection 绑定。 | Portal 显示 paper/current stage 摘要和 artifact refs；没有完整 per-study path/stage/file workspace。 | 需要 study-scoped Path/Stage tab，把 stage、evidence、files、package refs 组织成单篇论文路线。 | P0 |
| 研究路线 / 决策轨迹 | Canvas / stage / history 能体现路线演进、分叉、失败路径和后续转向。 | MAS 已有 `focused_lanes.portal-route-decision-trail` 与 `mas_progress_portal_route_decision_trail` read-only helper，消费 controller/evidence/runtime lineage/source refs 并 fail-closed。 | 需要真实 workspace soak/polish，确保每篇论文都有足够 route inputs 和可读 source refs。 | P0 landed contract / soak pending |
| 执行器实时对话 | Quest connector/chat pane 有 transcript、streaming assistant message、user composer、stop run、older history。 | MAS 主要暴露 progress events、source refs、runtime receipts；没有面向用户的 executor conversation pane。 | 需要 Runtime Conversation read model：按 study/run 汇总 user messages、assistant turns、tool calls、stop/replan/action intent。 | P1 |
| terminal/log 观察 | WebUI 可以看 bash tool operation、progress、logs，并通过 xterm/WebSocket attach 到 terminal。 | Live Console 展示 terminal/log tail refs 和 read-only tail；没有 interactive attach。 | read-only observation 已落地；interactive attach/input/resize/detach 需单独安全设计。 | P1 |
| UI 控制运行 | WebUI 可发消息、stop run、terminal input、部分 daemon/system 操作。 | MAS UI 只显示 action intent；apply 仍回 MAS controller/CLI/MCP。 | 需要 authorized UI action lane，先做 resume/reconcile/pause intent apply，再评估 terminal input。 | P2 |
| 多论文 workspace | 旧 WebUI 的 project/quest route 减少混淆；用户通常在单 quest 上操作。 | MAS workspace overview 会把所有 studies 放到同一表和同一页面上下文。 | 需要左侧 study list / attention queue + 单 study detail 主面；workspace overview 只作入口，不作主要解释页。 | P0 |
| artifact/file discoverability | 文件树、open/download、stage files 与 quest workspace 在同一 UI 中。 | Portal/Live Console 有 artifact/source refs；不是集成文件浏览体验。 | 需要 artifact/file tab，按 current package、draft、tables/figures、review/proof 分组。 | P1 |

## Target Information Architecture

Progress Portal 后续应从“一个 workspace 大页面”调整为“workspace shell + per-study detail”：

- Workspace shell：左侧或顶部是 study list / attention queue，默认只回答“哪些论文线需要看”。每个 item 显示 `study_id`、短题名、状态、last seen、blocker、next action、live/run badge。
- Study detail：选中一个 study 后，主区域只解释这篇论文。首屏应显示研究标题/问题、当前阶段、正在做什么、下一步、阻塞、freshness、active run 和交付入口。
- Study tabs：
  - `Overview`: 人话状态、blocker、next action、quality/publication status。
  - `Route / Decision Trail`: 研究路线、分支、失败/阻塞原因、转向理由、superseded path、active/winning path 和 controller/evidence/review/runtime source refs。
  - `Path / Stage`: 当前 stage、stage history、evidence/review/proof refs。
  - `Runtime / Run`: active/last run、worker liveness、supervision SLO、receipts。
  - `Conversation`: user messages、assistant turns、tool calls、controller action intents。
  - `Terminal / Logs`: tail、source refs、stream health；未来可挂 authorized attach。
  - `Artifacts`: draft、tables/figures、current package、review records、rebuild proof。
  - `Source Refs`: durable refs，默认折叠给维护者。
- Live Console 从 Portal 进入时应默认带 `study_id`，profile-level Live Console 只作为 operator view。
- 静态路径可以继续保留 `ops/mas/progress/index.html`，但应提供 per-study deep link，例如 query `?study_id=<study_id>` 或 materialized `ops/mas/progress/studies/<study_id>/index.html`。

## Backlog Lanes

| Lane | Machine contract | Scope | Done criteria |
| --- | --- | --- |
| `portal-study-scoped-ia` | `portal-console-soak` evidence keys | 把 Portal 默认 UX 改成 workspace shell + per-study detail/deep link。 | 多论文 workspace 打开后不会混读；单 study 页能回答状态、路径、阻塞、下一步、artifact。 |
| `portal-route-decision-trail` | `focused_lanes.portal-route-decision-trail` | 把 controller decisions、evidence/review ledgers 和 runtime lifecycle lineage/canvas 投影成单篇论文路线图。 | 用户能看到尝试过的路线、失败或阻塞原因、转向理由、superseded path、active/winning path 和对应 source refs；Portal 不重新解释医学质量。 |
| `portal-stage-artifact-path` | `portal-console-soak` evidence keys | 做 study-scoped Path/Stage/Artifacts view。 | stage history、evidence/review/proof、draft/package/files 都按单篇论文组织。 |
| `runtime-conversation-read-model` | `mas_runtime_conversation_read_model` | 从 MAS turn receipts、user queue、runner events、tool calls/source refs 生成 conversation/timeline read model。 | 用户能看到执行器“说了什么、做了什么、为什么停、下一步是什么”。 |
| `live-console-study-scope-polish` | `portal-console-soak.study_scoped_console` | Live Console 从 study deep link 进入，默认过滤单 study；显示 latency/SLO、stream source health、tail readability。 | Terminal/log tail 与 run identity 不再在多 study profile view 中混淆。 |
| `interactive-terminal-attach-design` | `focused_lanes.terminal-attach-gate` | 设计 MAS-native authorized attach/control，不恢复旧 daemon 作为默认 owner。 | 当前 gate fail-closed；未来实现需 threat model、owner gate、idempotency/audit、token/lease、input/resize/detach contract。 |
| `authorized-ui-control` | action receipts / enable-actions gate | UI action intent 到 controller-authorized apply 的最小安全链路。 | pause/resume/reconcile/stop 先可审计执行；terminal input 另行 gate。 |
| `real-workspace-user-soak` | `portal-console-soak.required_evidence_keys` | 对真实多论文 workspace 做长期刷新和用户路径 soak。 | 记录 latency、freshness、confusion cases、source-ref readability 和 blocked reasons。 |

## Current Impact And Priority

| priority | gap | current user impact | next implementation shape |
| --- | --- | --- | --- |
| P0 landed contract / soak pending | `portal-study-scoped-ia` | 用户能打开一个固定 Portal；真实多论文 workspace 仍需验证默认路径不会混读。 | 继续真实 workspace user soak、source ref polish 和 IA 细节修正。 |
| P0 landed read-only contract / soak pending | `portal-route-decision-trail` | 用户能看到 repo contract 中的路线图 projection；真实论文若缺 route inputs 会显示 missing。 | 补真实 controller/evidence/runtime lineage 输入质量，持续 soak Route / Decision Trail 可读性。 |
| P0 landed contract / polish pending | `portal-stage-artifact-path` | 用户能看到 artifact refs 和 per-study grouping；真实 workspace 还需要路径可读性 polish。 | 在 per-study detail 里继续打磨 Path/Stage 与 Artifacts tabs。 |
| P1 landed read-only contract / polish pending | `runtime-conversation-read-model` | 用户能看 conversation read model；真实执行器对话覆盖度仍需长期 soak。 | 从 user message queue、turn receipts、tool/action refs 持续增强只读 conversation timeline。 |
| P1 landed capability / polish pending | `live-console-study-scope-polish` | Live Console profile view 可区分 study/run；Portal 深链已携带 study scope，仍需 tail/readability polish。 | 继续验证 Live Console 默认只展示该 study 的 run/log/terminal refs。 |
| P2 | `authorized-ui-control` | 当前 UI 只展示 action intent；用户要执行 pause/resume/reconcile/stop 仍需 CLI/MCP/controller。 | 先做 controller-authorized action request/apply，带 idempotency、audit 和 fail-closed gate。 |
| P2 | `interactive-terminal-attach-design` | 不能复刻旧 MDS WebSocket terminal attach 的交互体验。 | 先完成 threat model 与 owner gate，再决定是否实现 terminal input/resize/detach。 |

当前不建议把 connector background delivery、旧 GitOps runtime lifecycle、MDS daemon start/stop/update control 或 workspace-local launchd/systemd/cron/docker service 写入此 backlog；这些已按 MAS monolith 目标退役。

## Wording Rules

- 可以说：当前 MAS 已落地 read-only purpose parity，用户能通过 Portal / Live Console 看进度、study rows、session/run、terminal/log tail、runtime health、supervision freshness。
- 可以说：研究路线 / decision trail 的 MAS read-only contract 已落地为 `focused_lanes.portal-route-decision-trail` 和 `mas_progress_portal_route_decision_trail`；真实 workspace route input 完整性、长期刷新和 UI 可读性仍是 P0 soak/polish。
- 可以说：旧 MDS WebUI 的产品身份、代码、bundle、Git history 和 contributor footprint 不导入 MAS。
- 不能说：旧 resident WebSocket terminal attach、terminal input/resize、UI 控制 daemon 已经 retired / 不复刻。
- 应说：这些交互能力尚未落地在当前 read-only scope，属于后续 interactive parity candidate，落地前必须通过安全、owner、idempotency 和审计 gate。
- 不能说：当前 Progress Portal 的用户体验已经完整等价旧 MDS WebUI。当前 repo contract 已覆盖 per-paper/per-study 工作台和 Route / Decision Trail，但真实 workspace 长时间用户体验、交互控制和 terminal attach 仍需 gated polish/soak。
- 不能说：Path/Stage 只要列出当前 stage 和 artifact refs 就已经覆盖旧 MDS 的研究路线视图；必须显式展示路线分支、失败/阻塞原因、转向理由和 active/winning path。
