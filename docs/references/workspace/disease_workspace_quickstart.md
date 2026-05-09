# Disease Workspace Quickstart

这份指南写给要新建疾病项目 workspace 的 Agent 或技术同事。

目标不是复制一个旧项目，而是用最小骨架快速建立一个病种级研究 workspace，并接入 `MedAutoScience`。controlled backend / oracle 只在 legacy diagnostic、backend audit 或 parity proof 需要时配置。

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

`MAS Runtime OS` 在某个 study 下的受管运行状态。

它更像运行过程和任务执行面，不是病种级目录，也不是外部 `MedDeepScientist` daemon 的默认入口。

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

这个命令默认 no root Git / no quest Git。新 workspace 的 runtime lifecycle 由 `artifacts/runtime/runtime_lifecycle.sqlite`、`artifacts/runtime/lifecycle_migration` ledger、`runtime/quests` manifest 与 `runtime/restore_index` 承接；workspace 根目录 Git、quest `.git`、Git diff/log 和 worktree list 都不是 active truth。

这个命令会生成下面这套 MAS-first 最小骨架：

```text
<workspace>/
├── datasets/
├── contracts/
├── studies/
├── portfolio/
│   └── data_assets/
├── refs/
├── artifacts/
│   └── runtime/
├── runtime/
│   ├── quests/
│   ├── archives/
│   └── restore_index/
└── ops/
    ├── mas/
    └── medautoscience/
        ├── bin/
        ├── profiles/
        ├── config.env
        └── README.md
```

旧 workspace 中的 `ops/med-deepscientist/runtime/quests/`、quest-local `.ds/`、`.ds/worktrees/` 和 quest `.git` 只作为 legacy diagnostic / restore / enrichment / reference surface 被识别；新 quest active path 不再由 MDS Git 或 Git worktree 维护。quest materializer 应在 repo-level guard 中阻断既有 quest `.git` 回流：materialize 出来的 active quest root 必须是普通目录，manifest 记录 `git_runtime_used=false` 与 `quest_git_active_path_retired=true`。

当前维护口径是 current workspaces 的 root Git 已完成 restore-proof full retirement。未来如果接入外部或旧 workspace 时发现 root `.git`，它只属于 legacy maintenance diagnostic，不是论文审计仓库，也不是可选日常状态面；不得提交 generated artifacts、PDF/DOCX/ZIP 投稿包、runtime ledgers、SQLite sidecar、archive payload 或 quest runtime 目录。有提交或 dirty 的 root Git 必须先完成 inventory、authority classification、restore archive、sha256 和 restore command，再决定是否 remove。
如果旧 workspace 已经因为误 `git add` 产生很大的 `.git/objects`，先运行：

```bash
ops/medautoscience/bin/storage-audit --git-only
```

确认报告里 `categories.git.health.recommended_action` 后，再运行低风险 hardening：

```bash
ops/medautoscience/bin/storage-audit --git-only --apply
```

只有当报告显示外层 Git 没有 commits、remotes、stashes、linked worktrees 和 locks，且 lifecycle ledger 已记录 restore-proof inventory/archive/remove 计划时，才允许进入 root Git remove 步骤。root Git 退役后不得通过 bootstrap 重新初始化。历史命令形态如下，仅用于维护者诊断：

```bash
ops/medautoscience/bin/storage-audit --git-only --apply --reinitialize-empty-workspace-git
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
- `artifacts/runtime/`
  - SQLite runtime lifecycle DB、lifecycle migration ledger、status projection 和 restore proof
- `runtime/quests/`
  - 普通 quest 执行目录和 manifest，不是 Git repo
- `runtime/archives/`、`runtime/restore_index/`
  - runtime archive 与恢复索引

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
3. 编辑 `ops/medautoscience/config.env`；旧 workspace 如仍保留 controlled backend 诊断入口，再只读核对旧 `ops/med-deepscientist/config.env`
4. 审阅生成的 `ops/medautoscience/profiles/*.local.toml`
5. 运行 `ops/medautoscience/bin/show-profile`
6. 运行 `ops/medautoscience/bin/bootstrap`
7. 再在 `studies/` 下创建首个 `study-id`
8. 从 `ops/medautoscience/bin/enter-study` 或受管入口进入 intake、scout、idea、write 等阶段

## Runtime Boundary

- `MedAutoScience` 是正式研究入口，单一 MAS app skill 负责承接其稳定 callable surface
- `MAS Runtime OS` 是默认 runtime owner；`MAS supervision scheduler contract` 是默认 supervision scheduler owner，当前 active adapter 是 `Hermes gateway cron`
- `MedDeepScientist` 只保留为 frozen source archive / historical fixture / explicit legacy diagnostic / provenance reference，不是默认 workspace runtime 依赖
- 不要直接通过 `MedDeepScientist` UI、CLI 或 daemon HTTP API 发起研究流程
- 旧 `ops/med-deepscientist/bin/*` 如果在历史 workspace 中出现，只作为 historical/debug evidence 或 cleanup target；新 workspace 不生成，也不作为 active runtime 运维入口
- `OPL` handoff、product-entry manifest 与其他机器可读桥接只保留在集成或参考层
- Agent 查状态或做 lifecycle 操作时，读 file authority、SQLite runtime lifecycle、lifecycle ledger、quest manifest 和 restore index；不查 Git

## 常见误区

- 不要复制整个 legacy workspace 当模板
- 不要在每个病种 workspace 里再 clone 一份上游 `DeepScientist`；只有 backend audit / parity oracle / source provenance 需要时才配置外部 MDS reference repo
- 不要把单篇论文目录当成 workspace 顶层
- 不要在每个 study 下各自维护一份未经登记的数据真相源

## 接下来读什么

- [Workspace Architecture](workspace_architecture.md)
- [Runtime Boundary](../../runtime/contracts/runtime_boundary.md)
- [Bootstrap](../../../bootstrap/README.md)
- [workspace.profile.template.toml](../../../profiles/workspace.profile.template.toml)
