# MAS Progress Portal

Status: `landed runtime read-model surface`
Owner: `MedAutoScience Product Projection + Runtime OS`

## 入口结论

`MAS Progress Portal` 是面向医生、PI 和研究团队的固定进度入口。它已经落成 MAS-owned payload、HTML materializer、workspace helper 和可选本地只读服务。它负责 progress / status / blocker / artifact pickup，不负责 terminal attach 或日志流；旧 MDS WebUI 的实时 console 能力由 [MAS Live Console 与 MDS WebUI Parity 落地计划](mas_live_console_mds_webui_parity_plan.md) 承接。Progress Portal 给每个 MAS workspace 一个稳定位置：

```text
ops/mas/progress/index.html
```

用户应能直接打开这个入口，看到当前 workspace 与论文线做到了哪里、系统下一步准备做什么、为什么卡住、是否需要医生/PI 判断、交付文件在哪里。Portal 只消费 MAS 现有 truth / read-model surface，不创建第二套状态系统。

这个入口是 per-workspace fixed entrance。无论未来从 Codex、浏览器、OPL App 还是 OPL Runtime Manager 打开，页面和 payload 的 domain owner 都保持为 MAS。

新 workspace 中旧 `start-web` 目的的默认落点也固定到 MAS Progress Portal：`ops/mas/bin/start-web` 刷新并打开 `ops/mas/progress/index.html`。如果维护者需要外部 MDS WebUI，只能通过显式 legacy diagnostic / backend audit 路径启动；医生/PI 默认不再在旧 WebUI 与 MAS Portal 之间判断进度 truth。

Portal 现在是 MAS functional monolith completion 的默认进度可视化替代面。它不表示 MDS 被函数级 1:1 搬进 MAS；它表示日常研究进度、路线、阻塞、artifact pickup 和 OPL handoff 的用户可见入口已经由 MAS-owned read-model 承接，医生/PI 默认不再去 MDS WebUI 判断研究进度。旧 MDS WebUI 的 terminal/log streaming 属于 live console 能力，不应继续混进 Portal 的完成口径。

“替代旧 MDS WebUI”的产品验收是能力等价，不是导入旧 WebUI 模块或历史代码。最低可用形态必须同时显示 workspace 级概览和 study 级详情：同一 workspace 内多篇论文线要能按 `study_id` 区分，并展示各自的 `active_run_id`、runtime health、supervisor freshness、paper/current stage 和下一步/焦点。legacy runtime 或已停驻 study 的诊断噪声不能覆盖当前 live study 的主状态；这类信息只能保留在 diagnostics / source refs 中供维护者核查。

## 形态决策

Progress Portal 采用双层形态：

1. 默认层：静态快照 HTML
   - 由 MAS CLI / controller-authorized refresh 生成 `ops/mas/progress/index.html`。
   - 不需要长期服务进程，不依赖外部 MDS checkout。
   - 适合医生直接打开、转发、归档或在断网/服务未启动时查看。
   - 页面必须显示 `generated_at`、`freshness`、`source_refs` 和 stale/missing 状态。

2. 可选层：本地只读实时服务
   - 由 `medautosci workspace progress-portal --serve --profile <profile>` 或同等 workspace helper 启动。
   - 服务只读取本地 MAS durable surfaces 和 portal payload；可以轮询刷新或使用文件变更通知。
   - 不写 study truth、publication truth、runtime authority、package authority 或 SQLite runtime lifecycle authority。
   - 实时体验应显示“最近刷新时间”和“下一次刷新/监听状态”，让用户知道页面是否仍在更新。

因此，Portal 不是二选一的静态网页或动态网站。默认必须有稳定静态入口；实时体验作为同一 read-model 的本地只读增强层实现。

## OPL App 集成结论

同一目的集成到 OPL App 进度看板的最优形态是分层消费，而不是把 MAS Portal 搬进 OPL 重新解释：

- `MAS` 负责 domain-owned progress portal payload 和 HTML，生成 `artifacts/runtime/progress_portal/latest.json` 与 `ops/mas/progress/index.html`。
- `MAS` 还负责 hosted packaging manifest，生成 `artifacts/runtime/progress_portal/hosted_package.json`。这个 manifest 只打包 MAS-owned workspace truth packaging，不消费 MDS WebUI，也不写任何 authority surface。
- 本地 MAS Portal 是每个 workspace 的固定入口，适合医生、PI 或维护者直接打开查看同一条研究线。
- `OPL App` / `OPL Runtime Manager` 只消费 MAS read-model / payload refs，把它们汇总到 family-level dashboard、attention queue、running/recent item 和 artifact locator。
- `latest.json` 固定暴露 `opl_handoff`：包含 payload refs、freshness、source refs、artifact locators、workspace-local Portal deep link 和 forbidden authority 列表，供 OPL family projection 直接索引。
- OPL 展示层可以打开或深链到 `ops/mas/progress/index.html`，也可以读取 `latest.json` 做跨 workspace 概览；它不能把 payload 文案升级成 OPL-owned readiness、submission-ready、publication verdict、quality verdict 或新的 study truth。
- OPL native helper 或 state indexer 只能加速文件发现、freshness、artifact index 和 source ref 汇总；它不能重算 MAS 的 study 状态、publication judgment、evidence ledger 或 controller next action。

详细评估记录见 [Progress Portal OPL App Integration](../references/progress_portal_opl_app_integration.md)。

## 用户体验合同

Portal 首屏必须回答这些问题：

- 当前论文线状态：自动运行、排队处理、质量修复、人工 gate、投稿包已交付、停驻、终止或异常。
- 当前正在做什么：一句医生/PI 能看懂的研究或论文动作。
- 下一步是什么：补文献、补统计、降级 claim、回到 AI reviewer、等待外部投稿信息、重建投稿包等。
- 为什么卡住：当前 blocker、owner、是否需要用户动作。
- 最近一次可见进展：带时间戳的人话事件。
- 质量/投稿状态：AI reviewer、publication gate、claim/statistics/writing readiness 的 projection。
- 文件与交付入口：draft、figures/tables、current package、review record、rebuild proof。
- 可信来源：默认折叠显示 durable refs，供维护者核查。

页面文案必须先讲研究含义，再讲技术细节。`quest`、`projection`、`fingerprint`、`runtime reentry`、legacy MDS path 等内部术语不能成为医生视图主句。

## 数据与 Authority 边界

Portal 的输入来自现有 MAS surface：

- `study_macro_state/latest.json`
- `study_progress.user_visible_projection`
- `study_progress.runtime_session`
- `study_progress.recovery_intent`
- `study_progress.runtime_reconcile_trigger`
- `study.runtime_continuity`
- `workspace-cockpit`
- `study_runtime_status`
- `runtime_watch`
- `runtime_supervision/latest.json`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- delivery / package currentness projection
- `artifacts/runtime/runtime_lifecycle.sqlite` 里的 runtime lifecycle read model

Runtime continuity 在 Portal 中只负责解释运行连续性，不负责执行动作。页面可以显示 worker state、last known run、last seen、freshness、recovery action、next owner、next eligible tick，以及 safe reconcile 是否 requestable；它不能直接重启 worker，不能修改 `current_package`，不能写 `publication_eval/latest.json` 或 `controller_decisions/latest.json`。

Portal 只能生成 read-model payload 和展示文件，例如：

```text
artifacts/runtime/progress_portal/latest.json
artifacts/runtime/progress_portal/hosted_package.json
ops/mas/progress/index.html
```

这些文件是展示产物，不是 study truth。任何启动、恢复、暂停、写作、质量裁决、投稿授权、交付重建或 runtime lifecycle 写入仍回到既有 owner surface。

`opl_handoff` 是同一 payload 内的 family-level projection，不是额外 truth surface。它只能引用本 payload、源 payload 摘要、freshness、source refs、artifact locators 与 Portal deep link；OPL 侧不能据此生成新的 study truth、publication judgment、quality verdict、runtime authority 或 artifact authority。

## 静态快照合同

静态 HTML 应满足：

- 单文件可打开，默认不需要 Node、Python server 或前端构建链。
- 使用稳定 MAS branding：`Med Auto Science`。
- 顶部主标题显示 workspace name；当前选择的 `study_id` 作为元信息显示，不能覆盖 workspace 级入口身份。
- 顶部时间同时显示本机本地时区时间和 UTC `generated_at`，避免跨时区排障时误判 freshness。
- 对 stale/missing/conflict 必须 fail-closed 显示，而不是隐藏。
- 页面内引用路径应来自 payload refs，不硬编码 docs prose path。
- 页面可以内联 CSS 和少量 JS 负责折叠、筛选、自动滚动到当前 blocker；不能依赖远程 CDN。

静态快照的刷新时机可以是：

- 用户手动运行 refresh 命令。
- controller-authorized sync / runtime watch tick 后刷新。
- 本地只读 serve 进程轮询刷新。
- workspace helper 被外部 scheduler 调用。

## 本地实时服务合同

实时服务应保持 lightweight：

- 绑定本机地址，默认 `127.0.0.1`。
- 只读本地文件与 SQLite read model。
- 不持有长期 workflow state；重启后可从 durable surfaces 重建。
- 不使用外部 MDS WebUI、外部 MDS runtime root 或 upstream DeepScientist UI state 作为默认输入。
- 如果 refresh 失败，页面显示上一版快照和明确错误，不写入 misleading current 状态。
- 适合后续接入 Codex App、OPL Runtime Manager 或浏览器自动打开，但这些集成不能成为 Portal 的 authority。

实时服务的价值是让用户看到页面持续更新，减少“是不是还在跑”的不确定感；工程上它只是 read-model refresh loop。

如果 read-model 给出 `runtime_reconcile_trigger.safe_to_request=true`，实时服务或页面刷新只能展示推荐命令或调用现有 controller/supervisor safe surface；重复刷新必须依赖 dedupe fingerprint，不能制造重复 relaunch。已 parked、completed、human gate、publication gate missing 或 retry exhausted 的 study 必须显示 blocked reason，而不是提示恢复。

## 旧 MDS WebUI 关系

旧 MDS WebUI 的可吸收价值是“可视化状态、进度和路线”，不是品牌、代码历史或产品入口身份。

迁移原则：

- 旧 `start-web` 语义应转向 MAS Progress Portal 或明确 legacy diagnostic。
- `DeepScientist`、`MDS`、`DS` 只允许出现在折叠的 legacy diagnostic / provenance / oracle 区域。
- 默认医生视图不得展示 MDS/DS 路径作为 workspace truth。
- 不把上游 WebUI 历史、contributor footprint 或 product semantics 导入 MAS main。

如果外部 MDS 仍因 backend audit、oracle fixture 或 upstream intake 被显式运行，MDS WebUI 也只能服务维护者诊断。它不能再作为医生默认进度面，也不能和 `ops/mas/progress/index.html` 并列解释同一个 study truth。

## Landed Implementation Surface

当前实现写集：

- `src/med_autoscience/controllers/progress_portal.py`
- `medautosci workspace progress-portal`
- `artifacts/runtime/progress_portal/hosted_package.json` MAS-owned hosted packaging manifest
- workspace init 生成 `ops/mas/progress/index.html` placeholder 和 `ops/medautoscience/bin/progress-portal`
- workspace init 生成 `ops/mas/bin/start-web`，默认刷新并打开 MAS Progress Portal
- `tests/test_progress_portal.py`
- `tests/test_cli_cases/progress_portal_commands.py`
- workspace init / README / architecture / status / OPL handoff docs

CLI 形态：

```bash
medautosci workspace progress-portal --profile <profile>
medautosci workspace progress-portal --profile <profile> --open
medautosci workspace progress-portal --profile <profile> --serve
```

`--serve` 不应是默认必需路径；默认命令应能生成可打开的静态快照。

实现时的最小合同：

- payload builder 从现有 MAS durable surfaces 组装 read-model，不从 Markdown 文档、OPL state cache 或旧 MDS WebUI 路径推导状态。
- HTML materializer 只渲染 payload，并把 stale/missing/conflict 显示成可见状态。
- workspace init 只需要提供固定入口位置和可刷新路径；不能把 OPL App、长期服务进程或外部 runtime substrate 变成 Portal 的必需依赖。
- OPL handoff 只暴露 payload refs、HTML path/deep link、freshness、source refs 和 artifact locators，供 family dashboard 消费。

## 验收标准

- 新 workspace 有明确固定入口：`ops/mas/progress/index.html`。
- Portal payload 与 `study-progress`、`workspace-cockpit`、`product-entry-status` 对同一 study 的状态一致。
- Portal 不写 authority surface，只写 read-model / display artifact。
- 默认页面不出现 MDS/DeepScientist 产品语义。
- stale/missing/conflict 有明确可见状态。
- 本地实时服务可刷新页面，但停止服务后静态快照仍可打开。
- MCP/CLI/controller payload shape 不因 Portal 改动而破坏。
