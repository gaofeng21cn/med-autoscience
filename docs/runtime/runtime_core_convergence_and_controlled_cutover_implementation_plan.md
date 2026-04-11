# Runtime Core Convergence And Controlled Cutover Implementation Plan

**Goal:** 在 `P0` 与 `P1` 已完成的前提下，完成 `P2 controlled cutover -> physical monorepo migration` 的剩余 gate 与实施计划。

**Architecture:** 保持 quest-owned native runtime truth、study-owned supervision truth、workspace canonical knowledge truth 三层 owner 不变。`P2` 只处理 parity gate、模块边界、删除条件与 physical migration，不重新打开 `P0` / `P1`。

---

## 已完成前置项

- [x] runtime core 原生写出 quest-owned `runtime_events/*`
- [x] `GET /api/quests/{quest_id}/session` 暴露 `runtime_event_ref` / `runtime_event`
- [x] MAS transport/status/outer-loop 已消费 native runtime truth
- [x] MAS 已停止覆盖 quest-owned `runtime_events/latest.json`
- [x] workspace canonical literature / study reference context / quest materialization-only 已落地

## 当前 P2 任务

### Task 1: 写清 cutover gate

**Files:**
- Modify: `./runtime_core_convergence_and_controlled_cutover.md`
- Modify: `../program/project_repair_priority_map.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 把 `P2` 明确写成当前唯一 active tranche
- [ ] 明确 cross-repo parity suite 的放行标准
- [ ] 明确 physical migration 的阻断条件与退出条件

### Task 2: 锁定 absorb 边界

**Files:**
- Modify: monorepo 拓扑说明
- Modify: cutover runbook
- Test: repo-level integration checks

- [ ] 明确哪些模块被吸收
- [ ] 明确哪些过渡期 glue 必须删除
- [ ] 明确 absorb 后 authority surface 不得发生混叠

### Task 3: 做 final cutover verification

**Files:**
- Modify: cross-repo regression suite
- Test: runtime native truth + workspace canonical truth + outer-loop contract

- [ ] 覆盖 runtime truth / knowledge truth / cutover gate 三条主线
- [ ] 保证 physical migration 前 contract 与测试都是 green
- [ ] 仅在验证通过后进入 physical monorepo migration
