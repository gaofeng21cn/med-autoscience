# Disease Workspace Quickstart

这份指南写给要新建疾病项目 workspace 的 Agent 或技术同事。

目标不是复制一个旧项目，而是用最小骨架快速建立一个病种级研究 workspace，并接入外部共享的 `MedAutoScience` 与 `MedDeepScientist`（仓库名 `med-deepscientist`）。

## 先记住一句话

一个 workspace 默认对应一个病种，或一个稳定的专病研究主题。

它不是单篇论文目录，而是：

- 共享数据底座
- 多条研究线的组合面
- 多篇论文的持续产出面

## 先分清 5 个对象

### 1. `workspace`

病种级长期资产层。

它负责管理：

- 私有数据与公开数据
- 数据版本与合同
- 选题池与跨 study 积累
- 本地运行状态与入口脚本

### 2. `dataset family / version`

workspace 级数据版本层。

例如：

- 主分析数据 `master/v2026-03-28`
- 补充随访版本
- 多中心追加版本

这些版本属于 workspace，而不是某个单独 study。

### 3. `study`

单条具体研究线。

通常一个 `study` 对应：

- 一篇主稿
- 或一组强关联投稿产物

例如：

- 临床分类器研究
- 亚型重构研究
- 外部验证与模型更新研究

### 4. `quest`

`MedDeepScientist` 在某个 study 下的运行状态。

它更像运行过程和任务执行面，不是病种级目录。

### 5. `paper bundle / submission package`

某个 study 收敛出来的投稿交付物。

它属于 study-local 结果，不属于 workspace 顶层。

## 推荐最小骨架

如果 Agent 已接入 `medautosci-mcp`，优先直接调用 MCP tool `init_workspace`。

如果当前环境还没有接 MCP，再用 CLI：

```bash
uv run python -m med_autoscience.cli init-workspace \
  --workspace-root /ABS/PATH/TO/NEW-WORKSPACE \
  --workspace-name my-disease
```

如果你想先让 Agent 看计划，再决定是否创建，可以先加 `--dry-run`。

这个命令会生成下面这套最小骨架：

```text
<workspace>/
├── datasets/
├── contracts/
├── studies/
├── portfolio/
│   └── data_assets/
├── refs/
└── ops/
    ├── medautoscience/
    │   ├── bin/
    │   ├── profiles/
    │   ├── config.env
    │   └── README.md
    └── deepscientist/
        ├── bin/
        ├── config.env
        ├── runtime/
        ├── startup_briefs/
        └── startup_payloads/
```

## 每个目录大致做什么

- `datasets/`
  - 冻结后的分析数据版本
- `contracts/`
  - 变量定义、终点定义、纳排标准等稳定语义
- `studies/`
  - 每个 `study-id` 的独立研究工作区
- `portfolio/`
  - 选题池、公开数据扩展、数据资产登记、跨 study 方法学积累
- `refs/`
  - 参考文章与文献提取稿
- `ops/`
  - 本地入口、配置和运行状态

## 私有数据、公开数据与 study 的关系

默认关系如下：

- 私有数据版本登记在 workspace 级数据资产层
- 公开数据扩展线索也登记在 workspace 级数据资产层
- `study` 只消费这些已登记的数据版本
- 同一数据版本可以被多个 study 复用

不要让每个 study 都维护一份自己的“真相数据副本”。

## 新项目推荐启动顺序

1. 建立病种级 workspace 骨架
2. 放入原始数据、数据说明、变量定义、终点定义和参考资料
3. 编辑 `ops/medautoscience/config.env` 与 `ops/deepscientist/config.env`
4. 审阅生成的 `ops/medautoscience/profiles/*.local.toml`
5. 运行 `ops/medautoscience/bin/show-profile`
6. 运行 `ops/medautoscience/bin/bootstrap`
7. 再在 `studies/` 下创建首个 `study-id`
8. 从 `ops/medautoscience/bin/enter-study` 或受管入口进入 intake、scout、idea、write 等阶段

## Runtime Boundary

- `MedAutoScience` 是正式研究入口
- `MedDeepScientist` 是默认受控 runtime
- 不要直接通过 `MedDeepScientist` UI、CLI 或 daemon HTTP API 发起研究流程
- `ops/deepscientist/bin/*` 只用于启动、查看、停止 runtime，不用于研究治理

## 常见误区

- 不要复制整个 legacy workspace 当模板
- 不要在每个病种 workspace 里再 clone 一份上游 `DeepScientist`；统一使用外部共享的 `med-deepscientist`
- 不要把单篇论文目录当成 workspace 顶层
- 不要在每个 study 下各自维护一份未经登记的数据真相源

## 接下来读什么

- [Workspace Architecture](workspace_architecture.md)
- [Runtime Boundary](runtime_boundary.md)
- [Bootstrap](../bootstrap/README.md)
- [workspace.profile.template.toml](../profiles/workspace.profile.template.toml)
