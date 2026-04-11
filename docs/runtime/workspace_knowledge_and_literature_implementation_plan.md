# Workspace Knowledge And Literature Implementation Plan

**Goal:** 守住已经完成的 workspace-first canonical knowledge / literature contract，并把剩余工作收口到 `P2 controlled cutover -> physical monorepo migration`。

**Architecture:** workspace 持有 canonical literature / research memory，study 持有 reference context，quest 只做 materialization。`P1` 已完成，当前不再重新打开 owner 设计，而是保证 cutover 期间不回退。

---

## 已完成

- [x] workspace canonical literature registry 已进入 `portfolio/research_memory/literature/*`
- [x] study-owned `artifacts/reference_context/latest.json` 已进入主线
- [x] `build_hydration_payload(...)` 已提供 `workspace_literature + study_reference_context`
- [x] quest hydration / literature hydration 已按 materialization-only 理解 quest literature surface

## 当前剩余 P2 任务

### Task 1: 守住 authority boundary

**Files:**
- Modify: `./workspace_knowledge_and_literature_contract.md`
- Modify: `../program/project_repair_priority_map.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 明确写下 `P1` 已完成，避免再次把它写成待办
- [ ] 明确 physical cutover 期间不得回退 workspace-first owner
- [ ] 明确 study / quest 只能消费 canonical layer，不能重新主写 authority truth

### Task 2: 补 cutover parity gate

**Files:**
- Modify: hydration / reference-context 相关测试
- Test: `tests/test_study_reference_context.py`
- Test: `tests/test_runtime_protocol_study_runtime.py`
- Test: `tests/test_quest_hydration.py`
- Test: `tests/test_literature_hydration.py`

- [ ] 覆盖 workspace registry、study reference context、quest materialization 三层一致性
- [ ] 覆盖 registry mismatch、empty selection、promotion path 等 fail-closed 场景
- [ ] 把 workspace-first contract 纳入最终 cutover regression suite
