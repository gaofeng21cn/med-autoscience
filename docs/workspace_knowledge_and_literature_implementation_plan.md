# Workspace Knowledge And Literature Implementation Plan

**Goal:** 把 workspace 级 research memory 扩展为 workspace 级 canonical knowledge / literature layer，并把 study / quest 的文献职责收回到清晰边界内。

**Architecture:** 保留现有 `portfolio/research_memory` 作为 workspace-first knowledge layer，在其下引入 canonical literature registry；study 增加 reference context artifact；quest hydration 只做受控 materialization。先冻结 owner contract，再迁移 controller 与 hydration 路径。

---

## Task 1: 冻结 knowledge / literature owner contract

**Files:**
- Create: `docs/workspace_knowledge_and_literature_contract.md`
- Modify: `docs/project_repair_priority_map.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 明确 workspace / study / quest 三层 authority 边界。
- [ ] 明确 workspace canonical literature registry 与 study reference context 的目标 surface。
- [ ] 在文档测试中冻结“quest 只做 materialization，不做 canonical truth”的结论。

## Task 2: 引入 workspace literature registry controller

**Files:**
- Create: `src/med_autoscience/controllers/workspace_literature.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/mcp_server.py`
- Test: `tests/test_workspace_literature.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_mcp_server.py`

- [ ] 新增 workspace literature 初始化与状态检查入口。
- [ ] 定义 canonical registry、bibliography、coverage 的稳定路径。
- [ ] 让 workspace 能显式报告 canonical literature layer 是否存在以及当前覆盖度。

## Task 3: 引入 study reference context artifact

**Files:**
- Create: `src/med_autoscience/study_reference_context.py`
- Modify: `src/med_autoscience/controllers/reference_papers.py`
- Modify: `src/med_autoscience/runtime_protocol/study_runtime.py`
- Test: `tests/test_study_reference_context.py`
- Test: `tests/test_reference_papers_controller.py`

- [ ] 把 `paper_urls`、`reference_papers`、workspace registry 选集收敛到 study-owned artifact。
- [ ] 区分 `framing anchor`、`claim support`、`journal fit neighbor`、`adjacent inspiration` 等角色。
- [ ] 保持 study charter / startup contract 仍是 authority ingress，而不是直接把 quest cache 升格。

## Task 4: 让 quest hydration 改为 materialization-only

**Files:**
- Modify: `src/med_autoscience/controllers/quest_hydration.py`
- Modify: `src/med_autoscience/controllers/literature_hydration.py`
- Modify: `src/med_autoscience/startup_literature.py`
- Test: `tests/test_quest_hydration.py`
- Test: `tests/test_literature_hydration.py`
- Test: `tests/test_runtime_protocol_study_runtime.py`

- [ ] 让 quest hydration 优先读取 workspace canonical literature 与 study reference context。
- [ ] quest-root 下保留 local literature outputs，但只作为 runtime local materialization。
- [ ] 去掉 quest-local literature surface 的长期 owner 语义。

## Task 5: 接回 portfolio memory / external research

**Files:**
- Modify: `src/med_autoscience/controllers/portfolio_memory.py`
- Modify: `src/med_autoscience/controllers/external_research.py`
- Modify: `docs/README.md`
- Modify: `docs/README.zh-CN.md`
- Test: `tests/test_portfolio_memory.py`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 让 workspace literature registry 成为 `portfolio/research_memory` 的正式组成部分。
- [ ] 明确 external research 报告只能沉淀回 workspace canonical layer，不能直接变成 study / quest truth。
- [ ] 更新 operator docs，固定 workspace-first 的读取顺序。
