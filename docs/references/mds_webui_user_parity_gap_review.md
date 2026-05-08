# MDS WebUI User Parity Gap Review

Status: `active UX parity reference`
Owner: `MedAutoScience Product Projection + Runtime OS`
Date: `2026-05-08`
Related contracts: `live-console-parity`, `mds_behavior_equivalence_matrix`

## 结论

当前 MAS Progress Portal / Live Console 已经解决了“有 MAS-owned 地方看进度和只读运行证据”的问题，但从用户视角还没有达到旧 MDS WebUI 的完整体验等价。最明显的差距是信息架构：旧 MDS WebUI 的主路径是 project / quest scoped，用户按一篇论文或一个 quest 进入后看进度、stage、文件、执行对话和 terminal；当前 MAS Portal 默认是 workspace 固定入口，虽然有 `study_id` rows，但多篇论文会混在同一个 overview 叙事里，容易让用户误以为所有论文线属于同一条执行路径。

因此当前口径应改为：

- `progress_visibility`: `partially_equivalent`。MAS 有固定 Portal、study-progress、cockpit 和 source refs，但 per-study/per-paper drilldown 还不是首屏主模型。
- `live_console_parity`: `landed_read_only_purpose_parity`。MAS 有 session/run/terminal/log tail 的只读观察面；旧 MDS 的 resident WebSocket terminal attach、terminal input/resize/detach 和 UI-issued runtime control 不是当前 landed scope，但也不应写成 retired / abandoned。它们是后续 interactive parity lane，需要安全、owner、idempotency 和审计 gate。
- `old_mds_webui_code`: 仍不导入。可借鉴旧 MDS WebUI 的行为规格、信息架构和 UX oracle，不能复制旧 React/WebSocket 代码、bundle、历史或产品身份。

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

差距不在“有没有任何进度页”，而在“用户是否能以单篇论文为核心稳定理解系统正在做什么”。当前 Portal 的 study rows 是概览表，不是 per-study 工作台；Live Console 是运行证据页，不是论文进度主入口；执行器对话、terminal attach/control、stage/file path 还没有被整合成一个 per-study 用户路径。

## User-View Parity Matrix

| User capability | Old MDS WebUI behavior | Current MAS behavior | Gap | Priority |
| --- | --- | --- | --- | --- |
| 按论文/quest 进入 | `/projects/:projectId` 进入 project / quest workspace；之后的 canvas/stage/details/memory/terminal 都围绕同一 quest。 | `ops/mas/progress/index.html` 是 workspace 固定入口；study rows 可区分论文线，但默认叙事仍是 workspace overview。 | 需要 per-study/per-paper page、稳定 deep link 和默认选中逻辑，避免多论文混读。 | P0 |
| 当前实时进度 | WebUI 从 resident daemon/API/WebSocket 读 live 状态，用户感知接近即时。 | Portal 读 MAS durable projection；Live Console snapshot/SSE 提供只读运行观察；outer supervision freshness 可见。 | 需要在每个 study 页直接显示 refresh age、latency/SLO、last event 和 blocked reason；长期 soak 证明刷新体验。 | P0 |
| 论文路径 / stage | Stage surface 将 structured facts、history、files、download/open 与 quest selection 绑定。 | Portal 显示 paper/current stage 摘要和 artifact refs；没有完整 per-study path/stage/file workspace。 | 需要 study-scoped Path/Stage tab，把 stage、evidence、files、package refs 组织成单篇论文路线。 | P0 |
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
  - `Path / Stage`: 研究路线、stage history、evidence/review/proof refs。
  - `Runtime / Run`: active/last run、worker liveness、supervision SLO、receipts。
  - `Conversation`: user messages、assistant turns、tool calls、controller action intents。
  - `Terminal / Logs`: tail、source refs、stream health；未来可挂 authorized attach。
  - `Artifacts`: draft、tables/figures、current package、review records、rebuild proof。
  - `Source Refs`: durable refs，默认折叠给维护者。
- Live Console 从 Portal 进入时应默认带 `study_id`，profile-level Live Console 只作为 operator view。
- 静态路径可以继续保留 `ops/mas/progress/index.html`，但应提供 per-study deep link，例如 query `?study_id=<study_id>` 或 materialized `ops/mas/progress/studies/<study_id>/index.html`。

## Backlog Lanes

| Lane | Scope | Done criteria |
| --- | --- | --- |
| `portal-study-scoped-ia` | 把 Portal 默认 UX 改成 workspace shell + per-study detail/deep link。 | 多论文 workspace 打开后不会混读；单 study 页能回答状态、路径、阻塞、下一步、artifact。 |
| `portal-stage-artifact-path` | 做 study-scoped Path/Stage/Artifacts view。 | stage history、evidence/review/proof、draft/package/files 都按单篇论文组织。 |
| `runtime-conversation-read-model` | 从 MAS turn receipts、user queue、runner events、tool calls/source refs 生成 conversation/timeline read model。 | 用户能看到执行器“说了什么、做了什么、为什么停、下一步是什么”。 |
| `live-console-study-scope-polish` | Live Console 从 study deep link 进入，默认过滤单 study；显示 latency/SLO、stream source health、tail readability。 | Terminal/log tail 与 run identity 不再在多 study profile view 中混淆。 |
| `interactive-terminal-attach-design` | 设计 MAS-native authorized attach/control，不恢复旧 daemon 作为默认 owner。 | 有 threat model、owner gate、idempotency/audit、token/lease、input/resize/detach contract；默认仍 fail-closed。 |
| `authorized-ui-control` | UI action intent 到 controller-authorized apply 的最小安全链路。 | pause/resume/reconcile/stop 先可审计执行；terminal input 另行 gate。 |
| `real-workspace-user-soak` | 对真实多论文 workspace 做长期刷新和用户路径 soak。 | 记录 latency、freshness、confusion cases、source-ref readability 和 blocked reasons。 |

## Wording Rules

- 可以说：当前 MAS 已落地 read-only purpose parity，用户能通过 Portal / Live Console 看进度、study rows、session/run、terminal/log tail、runtime health、supervision freshness。
- 可以说：旧 MDS WebUI 的产品身份、代码、bundle、Git history 和 contributor footprint 不导入 MAS。
- 不能说：旧 resident WebSocket terminal attach、terminal input/resize、UI 控制 daemon 已经 retired / 不复刻。
- 应说：这些交互能力尚未落地在当前 read-only scope，属于后续 interactive parity candidate，落地前必须通过安全、owner、idempotency 和审计 gate。
- 不能说：当前 Progress Portal 的用户体验已经完整等价旧 MDS WebUI。当前它是固定入口和概览能力 landed；per-paper/per-study 工作台仍是 P0 gap。
