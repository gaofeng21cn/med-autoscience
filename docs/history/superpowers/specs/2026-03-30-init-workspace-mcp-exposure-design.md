# Init Workspace MCP Exposure Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

## 背景

`init-workspace` 已经作为 CLI/controller 落地，可以让 Agent 通过 `medautosci init-workspace` 初始化病种级 workspace。

但从平台定位看，这还差最后一步：

- 对 `Codex` 这类 Agent，最理想的不是让它再拼 shell 命令，而是直接调用结构化 tool
- 对 `MedAutoScience` 的 plugin/guide 而言，也需要把这个新入口前移到“推荐做法”

因此需要把 `init-workspace` 同时暴露到：

- `med_autoscience.mcp_server`
- Codex plugin / guide 文档

## 目标

新增一个 MCP tool，使 Agent 可以直接通过结构化参数初始化新病种 workspace，并在 plugin 文档层同步说明这是新项目推荐入口。

## 非目标

- 不新增第二套初始化逻辑
- 不改变 `init-workspace` controller 的语义
- 不把 plugin 做成独占入口
- 不修改发布流程或安装流程

## 设计决定

### 1. MCP 直接复用现有 controller

MCP tool 不应重新实现 workspace 初始化逻辑。

它只负责：

- 参数校验
- 调用 `controllers.workspace_init.init_workspace(...)`
- 以文字 + structuredContent 返回结果

这样可以保证：

- CLI 与 MCP 行为一致
- 新功能只有一个真相源

### 2. Tool 命名与参数

建议新增 MCP tool：

- `init_workspace`

输入参数与 CLI 对齐：

- `workspace_root: string` 必填
- `workspace_name: string` 必填
- `dry_run: boolean` 可选
- `force: boolean` 可选
- `default_publication_profile: string` 可选
- `default_citation_style: string` 可选

### 3. 返回形态

返回形态沿用现有 MCP 风格：

- `content[0].text` 放 JSON 文本
- `structuredContent` 放 controller 原始结构

同时在 `structuredContent` 中保留：

- `workspace_root`
- `workspace_name`
- `dry_run`
- `created_directories`
- `created_files`
- `profile_path`
- `next_steps`

### 4. Plugin / guide 只做入口提示

不改 plugin 架构，不加新的 plugin 内部逻辑。

只在现有文档与 skill 说明中前移一句：

- 新病种 workspace 优先通过 `init_workspace` MCP tool 或 `init-workspace` CLI 初始化

这样做的原因是：

- plugin 仍保持“薄入口”
- 结构化能力以 MCP 为主
- 文档只负责告诉 Agent 应该优先走哪条路

## 涉及文件

- `src/med_autoscience/mcp_server.py`
- `tests/test_mcp_server.py`
- `guides/codex_plugin.md`
- `README.md` 或 plugin 相关入口文档
- 如有必要：`plugins/med-autoscience/skills/med-autoscience/SKILL.md`

## 成功标准

- Agent 可直接通过 MCP 调 `init_workspace`
- MCP 与 CLI 对同一输入产生同一类初始化结果
- Codex plugin / guide 明确把该能力暴露为新病种项目推荐入口
- 不引入第二套初始化实现
