# MAS Live Console 与 MDS WebUI Parity 落地计划

Status: `active implementation plan`
Owner: `MedAutoScience Runtime OS + Product Projection`
Date: `2026-05-08`

## 目标

补齐 `mds_behavior_equivalence_gap_matrix.md` 中 `WebUI/WebSocket/terminal streaming` 的显著差异。目标不是把 Progress Portal 改成旧 WebUI，也不是导入 MDS React/WebSocket 代码历史；目标是在 MAS monolith 中提供一个 MAS-authored live console，承接旧 MDS WebUI 对用户有价值的能力：

- workspace / study 当前状态实时更新；
- runtime run/session 可见；
- terminal / bash stream 可读；
- runtime supervision、worker log、artifact delta、recent events 可读；
- 明确区分 read-only 观察、controller-authorized action、legacy diagnostic。

## 当前事实

`MAS Progress Portal` 已经是 workspace 固定进度入口，适合看当前阶段、路线、阻塞、artifact 和质量状态。它是 read-model display artifact，不持有 runtime authority。

旧 MDS WebUI 的用户价值不止是进度摘要，还包括 resident WebUI / WebSocket 的低延迟观察能力：状态、terminal stream、日志流、session/run 细节。这个能力在 MAS 中当前没有等价默认入口，不能继续用“Progress Portal 已替代旧 WebUI”一笔带过。

## 设计边界

- 不导入旧 MDS WebUI 代码、git history、assets、package lock 或 contributor footprint。
- 可以复用旧 MDS 的行为规格、UI 信息架构、字段语义和验收样例，作为 clean-room spec / oracle fixture。
- Console 默认只读；任何 pause/resume/relaunch/repair 仍必须走 MAS controller/runtime surface。
- Console 不写 `study_truth`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`runtime_lifecycle.sqlite` 或论文内容。
- Progress Portal 保持医生/PI 默认进度页；Live Console 是维护者/高级用户实时观察入口，可以从 Portal 深链进入。

## 目标架构

### Layer 1: Runtime Session Read Model

新增 MAS-owned `runtime_session_read_model`：

- 输入：`runtime_lifecycle.sqlite`、`artifacts/runtime/health/latest.json`、`runtime_supervision/latest.json`、`runtime_status_summary.json`、`.ds/bash_exec/summary.json`、MAS Runtime OS run refs。
- 输出：`artifacts/runtime/live_console/session_read_model/latest.json`。
- 字段：workspace、study_id、active_run_id、worker_running、runtime_health_status、supervisor_tick_status、last_event_at、log_sources、terminal_sources、artifact_delta、controller_allowed_actions。
- 只读聚合，不重新解释 truth。

### Layer 2: Stream Bridge

新增 MAS stream bridge：

- `medautosci runtime live-console --profile <profile> --serve`
- 本地绑定 `127.0.0.1`。
- Server-Sent Events 或 WebSocket 二选一；优先 SSE，因为 terminal/log 只读流更简单、浏览器兼容好、无需引入重前端依赖。
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

新增 MAS-authored static UI shell：

- 默认路径：`ops/mas/live-console/index.html`。
- 不使用旧 MDS 代码。
- 信息架构复用旧 MDS WebUI 能力：
  - 左侧 workspace/study/run 列表；
  - 中部状态时间线；
  - 右侧 terminal/log stream；
  - 底部 artifact/event refs；
  - 明确只读 badge 与 controller action deep links。
- Progress Portal header 增加 live console link；Console header 增加返回 Progress Portal link。

### Layer 4: Controller Action Links

Console 只生成 action intent link，不直接执行：

- `inspect progress`
- `open study runtime status`
- `request reconcile`
- `pause/resume/relaunch` 仅显示 controller-required command / deep link，并标明权限。

## 并行实施 Lane

### Lane A: Spec / Oracle Inventory

- 从旧 MDS WebUI 行为整理 clean-room spec：页面区域、terminal/log stream、session/run 状态字段、事件类型。
- 输出 `docs/references/mds_webui_cleanroom_behavior_spec.md` 和 fixture JSON。
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
- 验收：Playwright 打开本地服务能看到 DM002/DPCC003 两条 live run 和 terminal/log 区。

### Lane E: Portal Integration

- Progress Portal payload/HTML 加 `live_console` refs。
- `hosted_package.json` 增加 live console entrypoint，但 authority 仍为 read-only。
- docs/status/runtime/progress_portal 更新：Portal 是 progress page，Live Console 是 MDS WebUI streaming capability replacement。

### Lane F: Real Workspace Soak

- 对 DM-CVD workspace 刷新 Portal + Live Console。
- 验收：
  - Portal H1 是 workspace；
  - 时间显示本机时区；
  - Live Console 能分辨 DM002/DPCC003；
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
