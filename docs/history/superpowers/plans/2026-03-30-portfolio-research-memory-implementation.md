# Portfolio Research Memory Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `portfolio research memory` 上升为 MedAutoScience 的显性能力，并在当前糖尿病 workspace 落地首轮种子资产。

**Architecture:** 新增独立 `portfolio_memory` controller 管理 `portfolio/research_memory/` 目录、registry 和状态检查；workspace 初始化默认创建这层资产；controller-first 与 scout 文案升级为优先读取 portfolio 研究记忆。当前 workspace 再用这套骨架写入 disease topic landscape、dataset question map 与 venue intelligence。

**Tech Stack:** Python 3.11+, YAML/JSON, Markdown, MedAutoScience CLI/controllers/tests

---

### Task 1: 新增 portfolio memory controller

**Files:**
- Create: `src/med_autoscience/controllers/portfolio_memory.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Test: `tests/test_portfolio_memory.py`

- [ ] 实现 root / registry / asset path helpers
- [ ] 实现默认骨架渲染：`README.md`、`registry.yaml`、`topic_landscape.md`、`dataset_question_map.md`、`venue_intelligence.md`
- [ ] 实现 `init_portfolio_memory(...)`
- [ ] 实现 `portfolio_memory_status(...)`
- [ ] 补测试：初始化、幂等、状态读取

### Task 2: 暴露 CLI 与 workspace init 默认入口

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/controllers/workspace_init.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_workspace_init.py`

- [ ] 增加 CLI 命令 `init-portfolio-memory`
- [ ] 增加 CLI 命令 `portfolio-memory-status`
- [ ] 让 `init-workspace` 默认创建 `portfolio/research_memory/`
- [ ] 生成 wrapper scripts
- [ ] 更新 workspace README / rules 文案
- [ ] 补测试覆盖新目录与脚本

### Task 3: 升级 controller-first 与 scout 文案

**Files:**
- Modify: `src/med_autoscience/policies/controller_first.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Test: `tests/test_controller_first_policy.py`

- [ ] 在 controller-first summary 中加入 portfolio research memory 优先级
- [ ] 在 scout 模板中加入“先读 portfolio research memory，再做 quest/global memory，再决定是否外部调研”
- [ ] 补相应测试或断言

### Task 4: 在当前 DM-CVD-Mortality-Risk workspace 落地种子资产

**Files:**
- Modify: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/README.md`
- Create: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/README.md`
- Create: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/registry.yaml`
- Create: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/topic_landscape.md`
- Create: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/dataset_question_map.md`
- Create: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/venue_intelligence.md`

- [ ] 用新骨架初始化当前 workspace
- [ ] 写入 diabetes 当前高信号研究方向
- [ ] 写入同一批数据可做课题图谱
- [ ] 写入 venue intelligence，并与 study 001 的 shortlist evidence 保持一致
- [ ] 保留并链接既有 `topic_backlog.md`

### Task 5: 验证

**Files:**
- Modify: `tests/test_mcp_server.py`（如需要）

- [ ] 运行新增 controller / CLI / workspace init 测试
- [ ] 运行既有 controller-first / overlay / workspace init 回归测试
- [ ] 在当前 workspace 运行 `portfolio-memory-status`
- [ ] 确认当前 workspace 的 seeded assets 状态正确
