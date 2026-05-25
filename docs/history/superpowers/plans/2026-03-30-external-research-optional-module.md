# External Research Optional Module Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 workspace 级外部 AI deep research 脚手架上升为 MedAutoScience 的显性可选模块，并在当前糖尿病 workspace 落地 prompt 与 external report 目录。

**Architecture:** 复用现有“建议层与 gate 层分离”的平台模式，新增独立 `external_research` controller 管理 `portfolio/research_memory/prompts/`、`external_reports/` 和 workspace-level prompt 生成；CLI/MCP 只暴露准备与状态查询入口；controller-first 与 scout 文案明确它是 optional enrichment，不参与 startup gate。

**Tech Stack:** Python 3.11+, Markdown, JSON, MedAutoScience CLI/controllers/MCP/tests

---

### Task 1: 新增 external research controller

**Files:**
- Create: `src/med_autoscience/controllers/external_research.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Test: `tests/test_external_research.py`

- [ ] 定义 `prompts/` 与 `external_reports/` 路径 helper
- [ ] 实现 workspace-level prompt 渲染
- [ ] 实现 `prepare_external_research(...)`
- [ ] 实现 `external_research_status(...)`
- [ ] 补测试覆盖初始化、幂等、状态建议

### Task 2: 暴露 CLI、MCP 与 workspace init 默认入口

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/mcp_server.py`
- Modify: `src/med_autoscience/controllers/workspace_init.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `tests/test_workspace_init.py`

- [ ] 增加 CLI 命令 `prepare-external-research`
- [ ] 增加 CLI 命令 `external-research-status`
- [ ] MCP 暴露对应工具
- [ ] `init-workspace` 默认创建 `prompts/` 与 `external_reports/`
- [ ] 生成 workspace wrapper scripts
- [ ] 补测试覆盖入口与脚手架

### Task 3: 升级 controller-first 与 scout 文案

**Files:**
- Modify: `src/med_autoscience/policies/controller_first.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Modify: `tests/test_controller_first_policy.py`

- [ ] 明确 `prepare-external-research` 是可选增强，不是 gate
- [ ] 明确外部报告原始落盘位置与稳定结论写回规则
- [ ] 补 policy 测试

### Task 4: 在当前 workspace 落地 prompt 与 external report 目录

**Files:**
- Modify: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/README.md`
- Modify: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/registry.yaml`
- Create: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/prompts/2026-03-30-workspace-topic-opportunity-deep-research-prompt.md`
- Create: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/external_reports/.gitkeep`

- [ ] 把 prompt 文件落到标准目录
- [ ] 建好 external_reports 目录
- [ ] 在 README / registry 里说明这层 optional enrichment 的角色

### Task 5: 验证与提交

**Files:**
- Verify: `tests/test_external_research.py`
- Verify: `tests/test_cli.py`
- Verify: `tests/test_mcp_server.py`
- Verify: `tests/test_workspace_init.py`
- Verify: `tests/test_controller_first_policy.py`

- [ ] 运行新增与相关回归测试
- [ ] 在当前 workspace 运行 `prepare-external-research` / `external-research-status`
- [ ] 检查 diff，确认没有把模块误接入 startup gate
- [ ] 按要求提交 `med-autoscience`
