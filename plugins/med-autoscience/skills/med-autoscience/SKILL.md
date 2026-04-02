# MedAutoScience Plugin

当 Codex 需要通过稳定运行面操作 `MedAutoScience`，而不是把仓库当成临时脚本集合来直接拼装时，使用这个 plugin。

## 这个 plugin 是什么

- `MedAutoScience` 面向 Codex 的薄入口层
- 叠加在现有 Python package、CLI、controller、overlay 与 workspace profile 之上
- 不替代 `medautosci` CLI、controller contract，也不替代非 Codex 集成

## 核心规则

优先走已有的 `MedAutoScience` 运行时 contract：

- 如果 workspace 还不存在，优先调用 MCP tool `init_workspace`
- `medautosci init-workspace`
- `medautosci doctor --profile <profile>`
- `medautosci show-profile --profile <profile>`
- `medautosci bootstrap --profile <profile>`
- `medautosci watch --runtime-root <runtime-root>`
- `medautosci overlay-status --profile <profile>`
- `medautosci install-medical-overlay --profile <profile>`
- `medautosci med-deepscientist-upgrade-check --profile <profile> --refresh`
- `medautosci-mcp`

如果 `medautosci` 不在 `PATH` 上，用模块入口：

```bash
uv run python -m med_autoscience.cli doctor --profile <profile>
```

## 操作约束

- 任何写操作之前，先读 workspace 当前状态
- 数据资产变更要走 controller 命令和结构化 payload，不直接手改 registry
- 保持 `MedAutoScience` 作为运行层，不要把 controller、profile、overlay、workspace 逻辑塌缩进 plugin 私有文件
- 保持 CLI 和 controller 入口稳定，避免破坏其他 Agent 的兼容性
- plugin-local MCP 依赖 `medautosci-mcp` 在 `PATH` 上可用

## 首先应读的文件

- `bootstrap/README.md`
- `controllers/README.md`
- `guides/codex_plugin.md`

## 典型任务

- 审核某个 workspace profile 是否接对
- 为新的病种 workspace 建立骨架并接入 Codex 驱动执行
- 检查 overlay 是否漂移，必要时重覆写
- 运行 runtime watch 并归纳阻塞点
- 通过可审计命令驱动数据资产和投稿交付 controller
