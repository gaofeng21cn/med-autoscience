# MAS Progress Portal

Status: `planned runtime read-model surface`
Owner: `MedAutoScience Product Projection + Runtime OS`

## 入口结论

`MAS Progress Portal` 是面向医生、PI 和研究团队的固定进度入口。目标不是复制旧 MDS WebUI，而是给用户一个稳定位置：

```text
ops/mas/progress/index.html
```

用户应能直接打开这个入口，看到当前课题做到了哪里、系统下一步准备做什么、为什么卡住、是否需要医生/PI 判断、交付文件在哪里。Portal 只消费 MAS 现有 truth / read-model surface，不创建第二套状态系统。

## 形态决策

Progress Portal 采用双层形态：

1. 默认层：静态快照 HTML
   - 由 MAS CLI / controller-authorized refresh 生成 `ops/mas/progress/index.html`。
   - 不需要长期服务进程，不依赖外部 MDS checkout。
   - 适合医生直接打开、转发、归档或在断网/服务未启动时查看。
   - 页面必须显示 `generated_at`、`freshness`、`source_refs` 和 stale/missing 状态。

2. 可选层：本地只读实时服务
   - 由后续 `medautosci workspace progress-portal --serve --profile <profile>` 或同等 workspace helper 启动。
   - 服务只读取本地 MAS durable surfaces 和 portal payload；可以轮询刷新或使用文件变更通知。
   - 不写 study truth、publication truth、runtime authority、package authority 或 SQLite runtime lifecycle authority。
   - 实时体验应显示“最近刷新时间”和“下一次刷新/监听状态”，让用户知道页面是否仍在更新。

因此，Portal 不是二选一的静态网页或动态网站。默认必须有稳定静态入口；实时体验作为同一 read-model 的本地只读增强层实现。

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
- `workspace-cockpit`
- `study_runtime_status`
- `runtime_watch`
- `runtime_supervision/latest.json`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- delivery / package currentness projection
- `artifacts/runtime/runtime_lifecycle.sqlite` 里的 runtime lifecycle read model

Portal 只能生成 read-model payload 和展示文件，例如：

```text
artifacts/runtime/progress_portal/latest.json
ops/mas/progress/index.html
```

这些文件是展示产物，不是 study truth。任何启动、恢复、暂停、写作、质量裁决、投稿授权、交付重建或 runtime lifecycle 写入仍回到既有 owner surface。

## 静态快照合同

静态 HTML 应满足：

- 单文件可打开，默认不需要 Node、Python server 或前端构建链。
- 使用稳定 MAS branding：`Med Auto Science`。
- 顶部显示 study id、workspace name、当前状态、freshness、generated time。
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

## 旧 MDS WebUI 关系

旧 MDS WebUI 的可吸收价值是“可视化状态、进度和路线”，不是品牌、代码历史或产品入口身份。

迁移原则：

- 旧 `start-web` 语义后续应转向 MAS Progress Portal 或明确 legacy diagnostic。
- `DeepScientist`、`MDS`、`DS` 只允许出现在折叠的 legacy diagnostic / provenance / oracle 区域。
- 默认医生视图不得展示 MDS/DS 路径作为 workspace truth。
- 不把上游 WebUI 历史、contributor footprint 或 product semantics 导入 MAS main。

## 计划中的开发入口

后续实现应使用独立 lane，例如 `codex/mas-progress-portal`，并保持写集聚焦：

- `src/med_autoscience/controllers/progress_portal.py` 或自然子模块。
- `src/med_autoscience/cli_parts/` 中的 workspace command。
- workspace init helper / template，只指向 `ops/mas/progress/index.html`。
- `tests/test_progress_portal.py` 与必要的 workspace init / CLI / wording guard 测试。
- docs 中的 runtime projection、architecture/status 和 README 索引。

建议 CLI 形态：

```bash
medautosci workspace progress-portal --profile <profile>
medautosci workspace progress-portal --profile <profile> --open
medautosci workspace progress-portal --profile <profile> --serve
```

`--serve` 不应是默认必需路径；默认命令应能生成可打开的静态快照。

## 验收标准

- 新 workspace 有明确固定入口：`ops/mas/progress/index.html`。
- Portal payload 与 `study-progress`、`workspace-cockpit`、`product-entry-status` 对同一 study 的状态一致。
- Portal 不写 authority surface，只写 read-model / display artifact。
- 默认页面不出现 MDS/DeepScientist 产品语义。
- stale/missing/conflict 有明确可见状态。
- 本地实时服务可刷新页面，但停止服务后静态快照仍可打开。
- MCP/CLI/controller payload shape 不因 Portal 改动而破坏。

