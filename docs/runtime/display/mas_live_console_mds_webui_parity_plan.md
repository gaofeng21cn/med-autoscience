# MAS Live Console 与 MDS WebUI Parity 落地计划

Status: `landed read-only parity contract`
Owner: `MedAutoScience runtime observation refs + Product Projection`
Date: `2026-05-08`
Contract ID: `live-console-parity`
Purpose: `live_console_clean_room_parity_provenance`
State: `history_supported_runtime_reference`
Machine boundary: 本文是人读 parity/provenance 记录。当前机器真相继续归 `contracts/test-lane-manifest.json` 的 `live-console-parity` / `terminal-attach-gate` lane、Live Console UI contract、MAS runtime/controller surfaces、Portal/Console generated artifacts 和真实 workspace evidence。

Lifecycle note: 当前 Live Console 展示合同从 [MAS Live Console UI Contract](live_console_ui_contract.md) 读取；本文保留 clean-room parity 背景、实施 lane 和验收脉络，不作为新的 active implementation queue。旧 MDS WebUI、resident daemon、WebSocket owner、bundle、assets 或 contributor footprint 只能作为 history/provenance/reference 读取。

## 目标

补齐 `mds_behavior_equivalence_gap_matrix.md` 中 `WebUI/WebSocket/terminal streaming` 的显著差异。目标不是把 Progress Portal 改成旧 WebUI，也不是导入 MDS React/WebSocket 代码历史；目标是在 MAS monolith 中提供一个 MAS-authored live console，承接旧 MDS WebUI 对用户有价值的能力：

- workspace / study 当前状态实时更新；
- runtime run/session 可见；
- terminal / bash stream 可读；
- runtime supervision、worker log、artifact delta、recent events 可读；
- 明确区分 read-only 观察、controller-authorized action、historical fixture / explicit archive import reference。

`live-console-parity` 已作为 focused lane 进入 `contracts/test-lane-manifest.json` 的 `focused_lanes.live-console-parity`。完成口径是 MAS-native purpose equivalence：MAS 提供 workspace overview、profile-level session snapshot、loopback SSE service shell、static Live Console HTML、Progress Portal deep link、clean-room oracle、forbidden authority writes，以及默认 fail-closed 的 terminal attach owner gate。它不声明旧 MDS resident daemon、old React bundle 或 WebSocket terminal attach 被 1:1 复刻。Terminal attach/input/resize/detach 的 MVP 已落到 MAS owner contract：无 owner 时 fail closed；owner available 时展示 attach/input/resize/detach UI/API。

## 当前事实

`MAS Progress Portal` 已经是 workspace 固定进度入口，适合看当前阶段、路线、阻塞、artifact 和质量状态。它是 read-model display artifact，不持有 runtime authority。

旧 MDS WebUI 的用户价值不止是进度摘要，还包括 resident WebUI / WebSocket 的低延迟观察能力：状态、terminal stream、日志流、session/run 细节。MAS 的落点是 Progress Portal + Live Console 分工：Portal 做默认进度入口，Live Console 做 read-only runtime observation。

2026-05-08 `live-console-parity` 更新：MAS 现在有 profile-level Live Console session read model、`runtime live-console --snapshot`、loopback `--serve`、`runtime_live_console_ui` helper 和 `ops/mas/live-console/index.html` shell。该 helper 只消费已经形成的 live-console snapshot/read-model payload，不读取、解释或改写 runtime stream/core read model，也不依赖旧 MDS bundle、旧 WebUI 代码或 CDN。Portal 集成边界保持为 thin link/ref：Progress Portal 可以暴露 Live Console entrypoint，Live Console header 可以返回 Progress Portal，但 Portal 会话不拥有 live-console 状态解释。

2026-05-08 user-view parity 校准：旧 MDS WebUI 的用户路径是 per-project/per-quest workspace；当前 MAS Portal 默认是 per-workspace fixed entry，虽然能列出多条 `study_id`，但多论文 workspace 仍容易混读。Progress Portal 的体验等价尚未完成，后续应优先落地 study-scoped Portal IA、per-study deep link、单篇论文 Path/Stage/Runtime/Conversation/Terminal/Artifacts 视图。详细 gap review 见 [MDS WebUI User Parity Gap Review](../../references/mds-parity/mds_webui_user_parity_gap_review.md)。

2026-05-08 UI polish 更新：Live Console 的可用性标准提升为“空状态也必须有信息”。当 DM002/DPCC003 等 study 没有 live run 时，页面仍要列出每条 study 的 runtime health、blocker、canonical runtime action、terminal/log missing source refs 和 controller action intent。`none`、`unknown`、`source`、`study.status`、`runtime.health` 等内部值不得直接作为主 UI 文案；它们只允许作为 payload 或 source-ref 审计值保留。

## 设计边界

- 不导入旧 MDS WebUI 代码、git history、assets、package lock 或 contributor footprint。
- 可以复用旧 MDS 的行为规格、UI 信息架构、字段语义和验收样例，作为 clean-room spec / oracle fixture。
- Console 默认只读；任何 pause/resume/relaunch/repair 仍必须走 MAS controller/runtime surface。
- Console 不写 `study_truth`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`runtime_lifecycle.sqlite` 或论文内容。
- Progress Portal 保持医生/PI 默认进度页；Live Console 是维护者/高级用户实时观察入口，可以从 Portal 深链进入。

## 目标架构

### Layer 1: Runtime Session Read Model

MAS-owned Live Console session read model：

- 输入：`study_runtime_status/latest.json`、`artifacts/runtime/health/latest.json`、`runtime_supervision/latest.json`、`runtime_status_summary.json`、runtime quest terminal/log summaries、MAS runtime observation refs、owner receipt refs 和 run evidence refs。
- 输出：`artifacts/runtime/live_console/session_read_model/latest.json`。
- 字段：workspace、studies、selected_study_id、runs、active_run_id、worker_running、runtime_health_status、supervisor_tick_status、events、log_sources、terminal_sources、artifact_delta、controller action intents。
- 只读聚合，不重新解释 truth。

### Layer 2: Stream Bridge

MAS stream bridge：

- `medautosci runtime live-console --profile <profile> --serve`
- 本地绑定 `127.0.0.1`。
- 当前 landed scope 使用 Server-Sent Events / snapshot 语义；不声称已复刻旧 MDS WebSocket attach。交互式 terminal attach/control 使用 MAS terminal attach owner gate；无 owner 时 fail closed，owner available 时仅展示 owner-provided attach/input/resize/detach endpoint contract。
- stream topics：
  - `workspace.status`
  - `study.status`
  - `runtime.health`
  - `runtime.supervision`
  - `terminal.tail`
  - `log.tail`
  - `artifact.delta`
- 每条 event 带 `source_ref`、`observed_at`、`local_time`、`sequence`。

### Layer 3: Web UI

MAS-authored static UI shell：

- 默认路径：`ops/mas/live-console/index.html`。
- 不使用旧 MDS 代码。
- 信息架构复用旧 MDS WebUI 能力：
  - 左侧 workspace/study/run 列表；
  - 中部状态时间线；
  - 右侧 terminal/log stream；
  - 底部 artifact/event refs；
  - 明确只读 badge 与 controller action deep links。
- Progress Portal header 增加 live console link；Console header 增加返回 Progress Portal link。
- 当前落地边界：`runtime_live_console_ui` 只提供静态 shell renderer 和 payload normalization；workspace/study/run、timeline、terminal/log tail、artifact/event refs 均来自传入 snapshot，不制造新的 runtime truth。
- 后续 Portal UX parity：Portal 应从 workspace overview 进一步拆出 per-study/per-paper detail，使旧 MDS per-quest 工作台语义以 MAS-owned clean-room IA 保留下来。

### Layer 4: Controller Action Links

Console 只生成 action intent link，不直接执行：

- `inspect progress`
- `open study runtime status`
- `request reconcile`
- `pause/resume/relaunch` 仅显示 controller-required command / deep link，并标明权限。

## Progress Portal 与 Live Console 分工

- Progress Portal：workspace / study overview、progress、blocker、artifact pickup、quality/publication projection、OPL handoff。
- Live Console：runtime session、run、terminal tail、log tail、runtime health、supervision freshness、artifact delta、read-only event stream。
- Portal 只暴露 Live Console link/ref 和 hosted package entrypoint；它不解释 Live Console run state。
- Live Console 只展示 controller action intent；pause / resume / relaunch / reconcile 必须回到 MAS controller/runtime surface，UI 不直接执行 apply。

## Authority Boundary

`live-console-parity` 禁止写入：

- `paper/current_package`
- `manuscript/current_package`
- `paper/submission_minimal`
- `manuscript/submission_minimal`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- `study_truth`
- `runtime_lifecycle.sqlite`

Live Console 只能写 MAS-owned read-model/display artifacts，例如 `artifacts/runtime/live_console/session_read_model/latest.json` 和 `ops/mas/live-console/index.html`。它不得修改 paper/package、不得生成医学结论、不得授权 publication/submission readiness。

## 并行实施 Lane

### Lane A: Spec / Oracle Inventory

- 从旧 MDS WebUI 行为整理 clean-room spec：页面区域、terminal/log stream、session/run 状态字段、事件类型。
- 输出 `docs/references/mds-parity/mds_webui_cleanroom_behavior_spec.md` 和 fixture JSON。
- 验收：文档不包含旧代码片段，不含上游 contributor metadata。

### Lane B: Session Read Model

- 新增 controller：`runtime_live_console.py` 或 `runtime_live_console_parts/`。
- 从现有 MAS durable surfaces 生成 session read model。
- 覆盖 DM002/DPCC003 fixture：active run、recovering、stale supervisor、terminal/log refs。
- 验收：没有 MDS repo/runtime root 依赖；legacy path 只能作为 source_ref/provenance。

### Lane C: Stream Server

- 新增 CLI：`medautosci runtime live-console --profile ... --serve`。
- 实现 read-only SSE stream；支持 once/snapshot 模式用于测试。
- 验收：连接后能收到 status/log/terminal delta；服务停止不影响 Progress Portal 静态页。

### Lane D: UI Shell

- 生成 `ops/mas/live-console/index.html`。
- 无构建链、无远程 CDN、无旧 MDS bundle。
- 支持 workspace/study/run 切换、日志 tail、terminal tail、event timeline。
- 验收：本地 static shell 能读取 session read model，展示 DM002/DPCC003 study/run 区分和 terminal/log 区。
- 代码边界：UI shell 可以有独立 payload helper / HTML renderer；不得调用或修改 stream server、runtime core read model、Portal controller action 或旧 MDS assets。

### Lane E: Portal Integration

- Progress Portal payload/HTML 加 `live_console` refs。
- `hosted_package.json` 增加 live console entrypoint，但 authority 仍为 read-only。
- docs/status/runtime/progress_portal 更新：Portal 是 progress page，Live Console 是 MDS WebUI streaming capability replacement。
- Thin-link 边界：Portal 只拥有入口发现、返回链接和 hosted package ref；Live Console 的 workspace/study/run、timeline、terminal/log 和 refs 解释权归 live-console snapshot/read model，不归 Portal 会话。

### Lane F: Real Workspace Soak

- 对 DM-CVD workspace 刷新 Portal + Live Console。
- 验收：
  - Portal H1 是 workspace；
  - 时间显示本机时区；
  - Portal / Live Console 主 UI 标签使用中文，英文只保留在技术值、命令或 source ref 中；
  - workspace alerts 显示来源、用途、当前输出、期望输出和可用修复命令；
  - workspace overview 不把单篇 publication/package 缺失文案渲染成 workspace 级阻塞；
  - Live Console 能分辨 DM002/DPCC003；
  - 没有 live run 时明确显示 no-live-run 空状态、blocker/action intent 和 terminal/log missing source refs；
  - terminal/log stream 可读；
  - controller action 不被 UI 直接执行；
  - 页面不出现旧 MDS product identity。

## 吸收顺序

1. A clean-room spec。
2. B session read model。
3. C stream server。
4. D UI shell。
5. E Portal integration。
6. F real workspace soak。

每条 lane 使用独立 worktree；合并前跑 focused tests，最后跑 `make test-meta`、`scripts/verify.sh`、`git diff --check`。

## 验收标准

- `mds_behavior_equivalence_gap_matrix.md` 中 `WebUI/WebSocket/terminal streaming` 从 `not_equivalent_retired` 更新为 `purpose_equivalent_with_different_timing` 或新增 `mas_live_console_equivalent` 分类。
- 用户默认打开 `ops/mas/progress/index.html` 看进度；需要实时日志/terminal 时打开 `ops/mas/live-console/index.html` 或本地 `--serve` URL。
- 没有新增外部 MDS checkout、daemon、WebUI、package 或 contributor footprint。
- 所有写操作仍通过 MAS controller/runtime owner surface。
