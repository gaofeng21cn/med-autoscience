# OPL App MAS Runtime Workbench Program

Purpose: `program_history_record`
State: `history_provenance`

Archive note: this is the 2026-05-11 full record of the P1 workbench plan.
Current content-level owner: [OPL App MAS Runtime Workbench Program](../../active/opl_app_mas_runtime_workbench_program.md).
Current development map: [MAS Current Development Lines](../../active/current-development-lines.md).
Do not treat every section in this file as current mandatory scope.

Status: `archived full record; current owner doc is active`
Date: `2026-05-11`
Owner: `MedAutoScience Product Projection + OPL Runtime Manager integration boundary`
Machine boundary: `human-readable program plan; implementation must promote stable JSON/API contracts before UI code consumes new fields`
Content lifecycle role: archived P1 full record. The current content-level owner document owns the active App/workbench implementation path.

## 结论

MAS 的 Progress Portal、Live Console、conversation read model 和 terminal attach gate 不应继续以 CLI 或 workspace-local HTML 作为主要用户体验。最合理的目标形态是接入 `OPL App`，由 OPL App 提供统一运行工作台，把 OPL 自身运行状态、family-runtime queue、domain attention queue、MAS 单篇论文运行状态和 terminal/log 交互放到同一产品界面里。

本文是 P1。P1 的任务是把 P0 论文自治目标做成用户可理解、可审阅、可控制的产品界面；P0 继续定义论文自治的质量验收，P2 继续提供 OPL stage-led framework 和 provider runtime 依托。

当前确定状态：

- MAS 已经有 Progress Portal、Live Console、conversation read model、terminal attach gate、OPL handoff 和 owner action receipt 等 repo surface。
- 当前缺口是产品入口：医生、PI 或普通用户仍需要跨 CLI、workspace-local HTML、loopback service 和文件面理解系统状态。
- OPL App Runtime Workbench 是 P1 的目标用户界面；MAS local Portal / Live Console 保留为 fallback、debug 和 evidence surface。
- P1 的完成证据是 App 中稳定呈现 MAS study progress、route decision、executor conversation、terminal/log、artifact refs 和 safe action receipts。

边界固定为：

- `OPL App` / `OPL Runtime Manager` 持有产品级工作台、导航、通知、queue、approval transport、窗口与 WebView/terminal 组件。
- `MAS` 持有 study truth、publication judgment、paper/package authority、runtime owner surface、terminal attach owner gate、action receipt 和 source refs。
- OPL family runtime provider 负责长期在线、stage attempt、唤醒、delivery、approval transport 和 family queue tick；Temporal 是目标生产 provider，Hermes-Agent 只作为迁移期 legacy/optional provider 或 executor/proof lane。
- OPL App 消费 MAS domain-owned projection 并调用 MAS owner endpoint；医学状态、质量裁决、投稿 readiness 和 current package authority 仍由 MAS owner surfaces 持有。

## 为什么接到 OPL App

旧 MDS WebUI 的用户价值是“一个自然的运行工作台”，不是 daemon 本身。用户关心的是：

- 哪篇论文正在跑；
- 当前路线和决策为什么这样走；
- 执行器最近说了什么、做了什么；
- terminal/log 是否还活着；
- 能不能暂停、恢复、停止；
- terminal 可交互时能不能像普通 Web terminal 一样输入；
- 产物在哪里。

如果 MAS 自己继续做一套完整 WebUI，而 OPL App 又已有 OPL 运行状态、provider readiness、family queue、domain task dispatch 和 App-first 首启路径，就会形成两套状态入口和两套操作体验。更稳定的设计是把 MAS 的 domain projection 接到 OPL App 的运行工作台，MAS 保留 workspace-local Portal / Live Console 作为 fallback、debug 和 no-App 环境入口。

## 外部工程参照

本方案参考的成熟模式只采纳模式，不引入这些项目作为 MAS runtime dependency：

- Electron 官方安全建议强调：Electron 不是普通浏览器；加载本地/远端内容时必须限制 Node integration、启用 context isolation / sandbox，IPC 只暴露必要 API，避免把 Electron API 暴露给不可信内容。OPL App 内嵌 MAS 面板时应走 allowlisted IPC / local service bridge，不把 arbitrary file URL 当成高权限页面。参考：Electron [Security](https://www.electronjs.org/docs/latest/tutorial/security)、[Context Isolation](https://www.electronjs.org/docs/latest/tutorial/context-isolation) 和 [contextBridge](https://www.electronjs.org/docs/latest/api/context-bridge)。
- VS Code Webview 模式适合“产品 shell 内嵌 domain-specific view”：Webview 可以显示自定义 UI，但脚本、资源和消息通道要受 CSP、message passing 和 local resource boundary 限制。OPL App 可以用同类思路承载 MAS workbench panel。参考：VS Code [Webview API](https://code.visualstudio.com/api/extension-guides/webview) 与 [Webview UX guidelines](https://code.visualstudio.com/api/ux-guidelines/webviews)。
- xterm.js 是浏览器终端组件的事实标准；terminal 输入应走 `onData` / addon / fit 等浏览器终端模式，再转成 MAS terminal attach API 的 token/lease/idempotency/audit 请求，而不是在 UI 里暴露命令行。参考：xterm.js [Documentation](https://xtermjs.org/docs/) 和 [Using addons](https://xtermjs.org/docs/guides/using-addons/)。
- Temporal / Cloudflare Durable Objects 的共同经验是：长运行任务要靠 durable identity、durable state、queue、checkpoint、schedule、recovery 和 human gate，而不是靠 UI 常驻进程。OPL App 是操作台，不能成为 MAS runtime truth；真正的恢复与执行仍要走 MAS owner surface 与 OPL provider-backed runtime surface。参考：Temporal [Docs](https://docs.temporal.io/) 与 Cloudflare Durable Objects [overview](https://developers.cloudflare.com/durable-objects/) / [SQLite-backed storage](https://developers.cloudflare.com/durable-objects/api/sqlite-storage-api/)。
- Kubernetes Operator 模式的核心是 controller 把 desired state 与 actual state 收敛。对应到本方案，OPL App 只展示 desired/current/reconcile hint 和触发受控 action；MAS controller 才能执行 domain reconcile。参考：Kubernetes [Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)。

## 当前事实

MAS 侧已经具备这些 repo contract：

- Progress Portal：workspace / per-study / per-paper 进度入口，含 route/decision、stage、runtime、conversation、artifact 和 source refs。
- Live Console：session/run、terminal tail、log tail、runtime health、supervision freshness 和 stream snapshot。
- Progress Portal actions：显式 `--enable-actions` 下可调用 MAS runtime owner 的 pause/resume/stop，并写 action receipt。
- Terminal attach gate：有 attach/input/resize/detach owner gate，默认 fail closed；当存在 attach-capable live run 时，可暴露 loopback attach/input/resize/detach API。
- OPL handoff：Progress Portal payload 已投影 `opl_handoff`，OPL runtime tray 已消费 `portal_path`、`portal_url`、`portal_payload_ref`、`portal_freshness` 和 `portal_source_refs`。

缺口是产品形态：这些能力仍散在 CLI、workspace-local HTML、loopback service 和 read-model 文件中。对医生/PI 或普通用户来说，当前入口仍像维护者工具；P1 把这些 read model 和 action receipt 组合成自然的 App 体验。

## 目标信息架构

OPL App 增加一个统一的 `Runtime Workbench`，在现有 OPL Runtime Manager / runtime tray 之上分三层：

1. `Family Runtime Overview`
   展示 OPL provider readiness、family-runtime queue、running / attention / recent 三类 item、domain filter、通知和 approval 状态。

2. `Domain Workspace Panel`
   选择 MAS/MAG/RCA 等 domain 后显示该 domain 的 workspace 列表、profile、health、freshness、source refs 和 attention queue。MAS workspace item 继续由 MAS `opl_handoff` / sidecar export / product-entry manifest 提供。

3. `MAS Study Workbench`
   进入某篇 MAS study 后显示：
   - 概览：study macro state、user next、当前 blocker、next action。
   - 路线/决策：route/decision trail、采用路线、失败路线、切换理由、source refs。
   - 执行器对话：用户消息、turn receipt、latest turn、controller action intent、tool/source refs。
   - 运行：active run、worker state、last seen、runtime continuity、recovery intent、SLO freshness。
   - Terminal / Logs：terminal transcript tail、worker log tail、stream freshness、run identity。
   - 控制：pause/resume/stop/reconcile request，均显示 owner、risk、receipt 和 idempotency。
   - Artifacts：current package、draft、figures/tables、review proof、submission mirror、open/download/path reveal。

默认视图面向医生/PI，先显示“论文现在在哪里、系统下一步是什么、是否需要我”。维护者信息进入折叠的 source/ref/debug drawer。

## 交互设计

### 进度与执行器对话

OPL App 不应打开 CLI 输出。它应直接消费 MAS read models：

```text
artifacts/runtime/progress_portal/latest.json
artifacts/runtime/conversation_read_model/latest.json
artifacts/runtime/live_console/session_read_model/latest.json
artifacts/runtime/terminal_attach/read_model/latest.json
```

App 侧以 native React/Electron 组件渲染这些 payload。workspace-local HTML 只保留为 fallback 和证据文件，不能作为 App 内主体验的唯一载体。

### Terminal / log tail

终端显示分两种模式：

- `read-only tail`：默认可用，展示 MAS terminal/log tail refs 和 transcript 摘要；没有 live run 时显示 no-live-run 原因。
- `interactive attach`：仅当 MAS terminal attach status 为 `available` 且 live run 为 attach-capable 时启用。

OPL App 的 terminal 组件应采用 xterm-like component，输入流转如下：

```text
User keypress
-> OPL App terminal component
-> OPL allowlisted IPC / local service bridge
-> MAS terminal attach endpoint
-> MAS token + lease + idempotency + audit validation
-> per-run terminal_commands.jsonl
-> MAS controlled PTY wrapper
-> transcript/log read model
-> OPL App refresh/SSE update
```

禁止路径：

- App 直接写 `terminal_commands.jsonl`。
- App 直接写 MAS runtime state、runtime SQLite、publication eval、controller decisions 或 current package。
- App 用 `chat_quest` 伪装 terminal input。
- App 把旧 MDS WebSocket owner 作为 fallback。

### 控制按钮

Pause / Resume / Stop / Reconcile 统一表现为按钮和确认 sheet：

- 按钮必须显示 owner：`MAS runtime owner` 或 `OPL family queue`。
- destructive 或 interrupting action 必须要求确认。
- 所有 action 必须带 idempotency key。
- 成功或拒绝都显示 receipt、source refs 和下一步。
- Reconcile 默认先 dry-run；apply 只有在 MAS owner route 明确允许时出现。

## Contract Plan

### MAS 输出给 OPL App

新增或扩展一个 `mas_opl_runtime_workbench_projection`，可以先作为 `progress_portal.latest.json` / product-entry manifest / sidecar export 的子结构落地，字段固定为：

```text
surface_kind: mas_opl_runtime_workbench_projection
schema_version: 1
workspace:
  workspace_root
  profile_ref
  profile_name
studies[]:
  study_id
  display_title
  macro_state
  user_next
  current_stage
  active_run_id
  worker_state
  last_seen_at
  freshness
  blocker_summary
  next_action_summary
  source_refs[]
  links:
    progress_payload_ref
    conversation_read_model_ref
    live_console_read_model_ref
    terminal_attach_status_ref
    artifact_refs[]
  actions:
    pause/resume/stop/reconcile_dry_run/reconcile_apply
    allowed
    owner
    endpoint_ref
    idempotency_required
    confirmation_required
terminal:
  mode: read_only_tail | attach_available | unavailable
  reason
  endpoints?
  token_required
  lease_required
  audit_ref
authority:
  opl_role: projection_consumer_and_action_transport_only
  mas_truth_owner: true
  forbidden_writes[]
```

这个 projection 只做 App 消费入口，不成为 study truth。

### OPL App 输入给 MAS

OPL App 只能向 MAS 发送 typed action request：

```text
surface_kind: opl_app_domain_action_request
domain: medautoscience
workspace_root
profile_ref
study_id
quest_id?
action: pause | resume | stop | reconcile_dry_run | reconcile_apply | terminal_attach | terminal_input | terminal_resize | terminal_detach
idempotency_key
requested_by: user | opl_runtime_manager
source: opl_app_runtime_workbench
payload
```

MAS 返回 typed receipt。OPL App 存储 App-level history 只作为 UI/audit cache，不能替代 MAS receipt。

## App Embedding Strategy

推荐分两阶段，避免一次性把 Electron WebView、terminal、SSE 和 domain actions 全部塞进一个大改动。

### Phase 1: App-native read-only workbench

- OPL App runtime tray 增加 MAS study drilldown。
- 直接读取 MAS projection JSON，渲染 App-native tabs。
- 显示 terminal/log read-only tail、conversation timeline、route/decision 和 artifacts。
- 保留“打开 workspace-local Portal/Live Console”作为 fallback 链接。
- 不启用 terminal input。

验收：用户不再需要命令行就能在 OPL App 内看 MAS study 进度、执行器对话和 terminal/log tail。

### Phase 2: Controlled actions

- OPL App 为 pause/resume/stop/reconcile-dry-run 接入 allowlisted IPC。
- MAS 侧保持 action receipt 和 idempotency。
- OPL App 显示 receipt、failure reason、source refs。
- Reconcile apply 继续受 MAS owner route / human gate / publication gate / retry budget 限制。

验收：用户能在 OPL App 内安全暂停/恢复/停止 MAS runtime，且所有动作有 receipt。

### Phase 3: Interactive terminal attach

- OPL App 内置 terminal component。
- MAS projection 暴露 terminal status 和 endpoints；App 只在 `attach_available` 时显示连接按钮。
- Attach 产生 MAS token/lease；input/resize/detach 走 MAS endpoint。
- transcript 通过 Live Console SSE 或 polling 刷新。
- 所有输入、resize、detach 均审计。

验收：存在 attach-capable live run 时，用户在 OPL App 中可像旧 MDS WebUI 一样查看和输入 terminal；无 owner 或无 live run 时显示明确原因。

### Phase 4: OPL provider online workbench

- OPL Runtime Manager 把 MAS pending family tasks、provider readiness、family queue、notification、approval 和 MAS study workbench 合并为一个运行面。
- OPL family runtime provider wakeup / tick 负责长期在线；MAS 继续持有 domain dispatch 和 paper truth。
- OPL App 显示 queue item 与对应 MAS study 的关联。

验收：一个 OPL App 页面回答“OPL 在线 substrate 是否健康、MAS 哪篇论文在跑、为什么停、下一步谁负责、我能点什么”。

## Implementation Lanes

| lane | repo | write scope | output |
| --- | --- | --- | --- |
| `mas-workbench-projection` | `med-autoscience` | progress portal / product-entry / sidecar projection contract and tests | `mas_opl_runtime_workbench_projection` |
| `opl-runtime-tray-drilldown` | `one-person-lab` | runtime tray types, snapshot builder, App projection contract | MAS study rows and drilldown data |
| `opl-aion-runtime-workbench-ui` | `opl-aion-shell` | renderer route/panel, IPC bridge, terminal/log components | App-native Runtime Workbench |
| `mas-action-transport` | `med-autoscience` | action receipt endpoints / tests | pause/resume/stop/reconcile receipts exposed for App |
| `terminal-attach-app-bridge` | `med-autoscience` + `opl-aion-shell` | terminal status projection, IPC allowlist, xterm-like panel | attach/input/resize/detach in App |
| `real-workspace-soak` | `med-autoscience` + `one-person-lab` + `opl-aion-shell` | tests and evidence only | DM/NF/PitNET profile read-only and action receipt soak |

各 lane 必须使用 disjoint write set；OPL main 当前若有 unrelated dirty docs，不得在 MAS lane 中修改或吸收。

## UX Rules

- 第一屏是运行工作台，不是说明页。
- 中文优先，技术字段只在 source/ref drawer 中出现。
- 使用密集、克制、状态优先的 dashboard 风格。
- 运行状态、阻塞、下一步和人类 gate 必须在首屏可见。
- Terminal 组件只能在可交互时启用输入；不可用时按钮 disabled 并显示真实 blocker。
- destructive action 采用确认 sheet，并显示 owner、影响范围和 receipt path。
- 所有 source refs 可展开，但默认不把长路径塞满主 UI。

## Verification

MAS 侧：

- `uv run pytest tests/test_runtime_live_console_ui.py tests/test_terminal_attach_contract.py -q`
- `make test-meta`
- `scripts/verify.sh`
- projection contract focused tests

OPL 侧：

- `npm run build`
- runtime tray focused tests
- family-runtime / Runtime Manager contract tests
- line-budget / typecheck

OPL App 侧：

- renderer unit tests for workbench tabs and disabled/enabled terminal states
- IPC allowlist tests
- browser/Electron screenshot tests for desktop widths
- action receipt integration fixture

Real workspace soak：

- 至少一个 no-live-run workspace；
- 一个 running or attach-capable fixture；
- 一个 human gate / publication gate blocked case；
- 一个 action receipt case；
- 一个 stale/freshness warning case。

## Boundary

- 旧 MDS WebUI / React bundle / WebSocket owner 留在历史和 provenance 语境。
- OPL App 通过 MAS typed projection 和 owner endpoint 工作，MAS truth surface 仍由 MAS 写入。
- MAS workspace-local Portal 保留为 fallback 和 evidence。
- Terminal input 保持 terminal attach owner gate，不并入 generic chat。
- P1 使用既有 MAS runtime owner surface，不新增 MAS runtime daemon。
- Phase 1 先把人类可见读面接到 App，交互 terminal 进入 Phase 3。

## Open Decisions

1. OPL App 内部用 `WebContentsView` / sandboxed iframe / native React panel 哪个承载 MAS workbench。推荐 native React panel；WebView 只用于 fallback HTML preview。
2. Terminal component 采用 `@xterm/xterm` 还是复用 OPL App 已有 terminal/panel 基础。推荐先评估 App bundle 和 CSP，再决定依赖。
3. Live Console stream 在 App 内优先走 SSE、polling 还是 OPL native helper state index。推荐 Phase 1 polling JSON，Phase 3 再接 SSE。
4. OPL Runtime Manager 的 queue item 与 MAS study workbench 的关联 key 使用 `study_id + workspace_root + profile_ref`，还是引入 family-level `domain_run_id`。推荐先用现有 triple，等跨 domain run ledger 稳定后再推广 `domain_run_id`。

## Done Definition

这个 program 到 MVP 完成时，用户路径应变为：

```text
Open OPL App
-> Runtime Workbench
-> MAS
-> Select study
-> See progress / route / executor conversation / terminal-log / artifacts
-> Click safe actions when available
-> See receipt and next state
```

用户不需要知道 `medautosci runtime live-console --serve`、`--enable-terminal-attach` 或 workspace-local HTML 路径。命令行只保留给维护者诊断和 fallback。
