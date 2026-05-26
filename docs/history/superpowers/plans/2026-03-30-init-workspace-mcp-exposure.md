# Init Workspace MCP Exposure Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `init-workspace` 暴露为 MCP tool，并在 Codex plugin / guide 文档里同步为新病种 workspace 的推荐入口。

**Architecture:** MCP 只做参数校验和 controller 转发，不复制初始化逻辑。文档层只前移入口说明，不改变 plugin 的薄包装定位。

**Tech Stack:** Python, JSON-RPC/MCP, Markdown, pytest

---

### Task 1: 为 MCP 增加 init_workspace tool

**Files:**
- Modify: `src/med_autoscience/mcp_server.py`
- Test: `tests/test_mcp_server.py`

- [ ] **Step 1: 写失败测试，要求 tool 列表中出现 `init_workspace`**

- [ ] **Step 2: 写失败测试，要求 `call_tool("init_workspace", ...)` 能把参数转发到 controller**

- [ ] **Step 3: 实现 MCP tool schema 与 handler**

- [ ] **Step 4: 运行定向测试**

Run: `PYTHONPATH=src pytest -q tests/test_mcp_server.py -k init_workspace`
Expected: 通过。

### Task 2: 同步 plugin / guide 入口说明

**Files:**
- Modify: `guides/codex_plugin.md`
- Modify: `README.md`
- Optional Modify: `plugins/med-autoscience/skills/med-autoscience/SKILL.md`

- [ ] **Step 1: 在 Codex plugin guide 中明确推荐入口**

- [ ] **Step 2: 在 README 的 Codex / Agent 执行者入口里补一句优先用 MCP init_workspace**

- [ ] **Step 3: 如果 plugin skill 已经显式列出推荐操作顺序，则同步更新**

### Task 3: 回归验证

**Files:**
- Modify: `src/med_autoscience/mcp_server.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `guides/codex_plugin.md`
- Modify: `README.md`

- [ ] **Step 1: 跑 MCP 定向测试**

Run: `PYTHONPATH=src pytest -q tests/test_mcp_server.py`
Expected: 通过。

- [ ] **Step 2: 复跑 workspace 初始化相关测试，确认没有引入第二套逻辑**

Run: `PYTHONPATH=src pytest -q tests/test_workspace_init.py tests/test_cli.py tests/test_mcp_server.py`
Expected: 通过。

- [ ] **Step 3: 手动调用 MCP handler 进行一次 dry-run 验证**

以 Python 直接调用 `call_tool("init_workspace", {...})`，确认输出包含 `structuredContent.workspace_root` 与 `created_files`。
