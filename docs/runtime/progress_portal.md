# MAS Progress Portal

Status: `landed runtime read-model surface`
Owner: `MedAutoScience Product Projection + Runtime OS`
Related contract: `live-console-parity`

## 入口结论

`MAS Progress Portal` 是面向医生、PI 和研究团队的固定进度入口。它已经落成 MAS-owned payload、HTML materializer、workspace helper 和可选本地只读服务。它负责 progress / status / blocker / artifact pickup，不负责 terminal attach 或日志流；旧 MDS WebUI 的实时 console 能力由 [MAS Live Console 与 MDS WebUI Parity 落地计划](mas_live_console_mds_webui_parity_plan.md) 和 [MAS Live Console UI Contract](live_console_ui_contract.md) 承接。Progress Portal 给每个 MAS workspace 一个稳定位置：

```text
ops/mas/progress/index.html
```

用户应能直接打开这个入口，看到当前 workspace 与论文线做到了哪里、系统下一步准备做什么、为什么卡住、是否需要医生/PI 判断、交付文件在哪里。Portal 只消费 MAS 现有 truth / read-model surface，不创建第二套状态系统。

这个入口是 per-workspace fixed entrance。无论未来从 Codex、浏览器、OPL App 还是 OPL Runtime Manager 打开，页面和 payload 的 domain owner 都保持为 MAS。

新 workspace 中旧 `start-web` 目的的默认落点也固定到 MAS Progress Portal：`ops/mas/bin/start-web` 刷新并打开 `ops/mas/progress/index.html`。如果维护者需要外部 MDS WebUI，只能通过显式 explicit archive import reference / backend audit 路径启动；医生/PI 默认不再在旧 WebUI 与 MAS Portal 之间判断进度 truth。

Portal 现在是 MAS functional monolith completion 的默认进度可视化替代面。它不表示 MDS 被函数级 1:1 搬进 MAS；它表示日常研究进度、路线、阻塞、artifact pickup 和 OPL handoff 的用户可见入口已经由 MAS-owned read-model 承接，医生/PI 默认不再去 MDS WebUI 判断研究进度。旧 MDS WebUI 的 terminal/log streaming 属于 live console 能力，不应继续混进 Portal 的完成口径。

“替代旧 MDS WebUI”的产品验收是能力等价，不是导入旧 WebUI 模块或历史代码。最低可用形态必须同时显示 workspace 级概览和 study 级详情：同一 workspace 内多篇论文线要能按 `study_id` 区分，并展示各自的 `active_run_id`、runtime health、supervisor freshness、paper/current stage 和下一步/焦点。legacy runtime 或已停驻 study 的诊断噪声不能覆盖当前 live study 的主状态；这类信息只能保留在 diagnostics / source refs 中供维护者核查。

2026-05-08 user-view parity 校准：当前 Portal 已有固定入口和 study rows，但用户体验仍偏 workspace overview，多篇论文线会在同一页叙事中混合。旧 MDS WebUI 的 per-project/per-quest 工作台更接近用户视角；后续 P0 是把 Portal 改成 workspace shell + per-study/per-paper detail/deep link，而不是继续扩大一个混合 overview。详细调研见 [MDS WebUI User Parity Gap Review](../references/mds_webui_user_parity_gap_review.md)。

2026-05-09 fresh assessment：Portal 的 repo capability、workspace helper、OPL handoff、Live Console link 和 real-workspace read-only soak 已经可用；当前主要缺口是默认 IA 仍以 workspace overview 为中心。下一轮优化不应再讨论“是否恢复 MDS WebUI”，而应直接做 MAS-native per-study/per-paper 工作台：study selector、deep link、单篇论文 Overview、Path/Stage、Runtime/Run、Conversation、Terminal/Logs、Artifacts 和 Source Refs。

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

## Live Console Integration Boundary

Progress Portal 与 Live Console 分工如下：

- Progress Portal 负责 workspace/study overview、progress、blocker、artifact pickup、quality/publication projection 和 OPL handoff。
- Live Console 负责 runtime session、run、terminal tail、log tail、runtime health、supervision freshness、artifact delta 和 read-only event stream。
- Progress Portal 只暴露 `live_console` read-only link/ref、hosted package entrypoint 和返回关系；它不解释 Live Console 的 run state。
- Live Console 可以展示 pause / resume / relaunch / reconcile 的 controller action intent，但 UI 不直接执行 apply。
- 两个入口都不得修改 paper/package、publication gate、controller decisions、study truth 或 runtime authority；不得修改 paper/package 是共同硬边界。

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

多论文 workspace 的默认 IA 目标：

- workspace 首屏只负责 study list / attention queue / running-recent，不把所有论文线解释成同一条状态叙事。
- 选择一个 `study_id` 后，主视图必须只解释这一篇论文，并提供 Overview、Path/Stage、Runtime/Run、Conversation、Terminal/Logs、Artifacts 和 Source Refs 分区。
- 从 Portal 进入 Live Console 时应携带 study scope；profile-level Live Console 只作为维护者总览。
- 当前实现若只能生成 workspace overview，应显式显示这是概览页，并提供下一步 per-study deep link / refresh 计划。

当前优先级：

- P0：`portal-study-scoped-ia`，让 `ops/mas/progress/index.html` 进入后先看到 study list / attention queue，再选中单篇论文。
- P0：`portal-stage-artifact-path`，把 stage history、evidence/review/proof、draft/package/files 放到单篇论文视图。
- P1：`runtime-conversation-read-model`，让用户看到执行器消息、tool/action refs、停驻原因和下一步。
- P1：`live-console-study-scope-polish`，从 Portal 深链进入 Live Console 时默认带 study scope。

Portal 主 UI 标签默认使用中文。顶部必须同时显示本机时区时间和 UTC `generated_at`；本机时间要带 IANA timezone，例如 `Asia/Shanghai`，避免跨时区排障时把 stale / fresh 误判成时钟问题。

workspace overview 模式是多论文线入口，不是某一篇论文的详情页。该模式必须把 `workspace.studies` 作为首屏主体，显示每条 study 的 `study_id`、运行健康、监管心跳、进度新鲜度、论文阶段和下一步；不得把缺少单篇 `publication_eval` 或 `current_package` 的 fallback 文案渲染成 workspace 级问题。单篇质量门禁和交付包结论只在具体 study 视图中展示。

workspace alerts 必须保留解释层。每条可见告警或降级诊断都要说明：

- 来源：例如 `workspace_cockpit.workspace_alerts`、`workspace_supervision.service.summary`、`product_entry_preflight.medical_overlay_ready`。
- 用途：这条信息用来提醒运行、进度、质量还是诊断缺口。
- 当前输出：原始 read-model 当前给出的文本或状态。
- 期望输出：恢复后应该看到的具体状态或更具体 blocker。
- 修复/查看命令：如果已有受控 CLI，例如 `runtime-ensure-supervision` 或 `doctor --profile`，应显示命令；没有命令时保持为空。

`Hermes-hosted runtime supervision 尚未注册。` 是真实 workspace supervision blocker 时，应显示在“诊断与修复建议”里，并指向 `runtime-ensure-supervision`；`状态需要检查。` 这类泛化旧文案应标为低信息诊断，由具体 study 行和 runtime health blocker 取代。

如果 `runtime-supervision-status --profile <profile>` 显示 `status=loaded`、`job_exists=true`、`script_exists=true` 且最近一次运行成功，Portal 不应继续把 “Hermes-hosted runtime supervision 尚未注册。” 当作当前问题展示。若这条文案仍从旧 `workspace_cockpit.workspace_alerts` 传入，只能落入诊断表并携带来源/修复命令；若现场 supervision 已在线且具体 study 行已经给出 runtime health blocker，`状态需要检查。` 应完全隐藏，避免医生/PI 把低信息历史诊断误认为待处理任务。

当前 UI 采用简洁的 operational dashboard 形态：状态用 chip/tag 呈现，表格负责多 study 区分，告警表负责来源/用途/期望/命令。设计参考原则来自 `awesome-design-md` / GetDesign.md 一类 design-context-first 方法，以及 Material / Carbon / Atlassian 的状态 chip、tag、lozenge 和 data-table 模式：少装饰、强对齐、可扫描、状态含义不只靠颜色表达。

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

Outer supervision SLA 在 Portal 中只负责解释外环监管是否新鲜。页面应显示 `outer_supervision_slo.state`、最新 tick/reconcile 时间、监管年龄、blocked/missing reason，以及 canonical one-shot `runtime-supervisor-reconcile --dry-run` 推荐命令。`due` 或 `stale` 表示可以安全加速一次 reconcile；它不表示 Portal 拥有 runtime relaunch 权限。重复刷新必须通过 dedupe fingerprint 和 `runtime_reconcile_trigger` 去重，不能制造重复恢复动作。

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

## Portal / Console Soak Evidence

真实 workspace 上的 Portal / Live Console soak 由 `medautosci workspace portal-console-soak --profile <profile>` 生成。该 runner 复用现有 `workspace progress-portal` 与 `runtime live-console --snapshot`，输出 `artifacts/runtime/portal_console_soak/latest.json`，检查：

- Portal 是否能刷新并写出 payload / HTML；
- Live Console 是否能区分多 study / run；
- terminal/log refs 是否可读；
- source refs 是否没有把旧 MDS 路径冒充 truth；
- 页面是否保持 `Med Auto Science` identity，不把旧 MDS WebUI 作为产品入口。

该 soak 只允许写 display/read-model evidence：`artifacts/runtime/progress_portal/*`、`artifacts/runtime/live_console/*`、`artifacts/runtime/portal_console_soak/latest.json`、`ops/mas/progress/index.html` 与 `ops/mas/live-console/index.html`。它禁止写 paper/package、publication gate、controller decision、runtime SQLite 或 restore archive。soak 失败时应输出 blocker，不得伪造页面可用或 paper autonomy landed。

## 旧 MDS WebUI 关系

旧 MDS WebUI 的可吸收价值是“可视化状态、进度和路线”，不是品牌、代码历史或产品入口身份。

迁移原则：

- 旧 `start-web` 语义应转向 MAS Progress Portal 或明确 explicit archive import reference。
- `DeepScientist`、`MDS`、`DS` 只允许出现在折叠的 explicit archive import reference / provenance / oracle 区域。
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
