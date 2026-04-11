# Runtime Core Convergence And Controlled Cutover Implementation Plan

**Goal:** 在 `P0` 与 `P1` 已完成的前提下，完成 `P2 controlled cutover -> physical monorepo migration` 中当前仍可在 repo 内推进的 gate、Hermes backend continuation，以及后续 physical migration readiness plan。

**Architecture:** 保持 quest-owned native runtime truth、study-owned supervision truth、workspace canonical knowledge truth 三层 owner 不变。`P2` 只处理 parity gate、模块边界、删除条件与 physical migration，不重新打开 `P0` / `P1`。

---

## 已完成前置项

- [x] runtime core 原生写出 quest-owned `runtime_events/*`
- [x] `GET /api/quests/{quest_id}/session` 暴露 `runtime_event_ref` / `runtime_event`
- [x] MAS transport/status/outer-loop 已消费 native runtime truth
- [x] MAS 已停止覆盖 quest-owned `runtime_events/latest.json`
- [x] workspace canonical literature / study reference context / quest materialization-only 已落地

## 当前 P2 任务

### Task 1: 冻结 Hermes continuation truth

**Files:**
- Modify: `../program/research_foundry_medical_mainline.md`
- Modify: `../program/research_foundry_medical_execution_map.md`
- Add: `../program/hermes_backend_continuation_board.md`
- Add: `../program/hermes_backend_activation_package.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 把 `Hermes` backend continuation 写成当前 repo-side 允许继续推进的 P2 子位置
- [ ] 写清目标、边界、验证、promotion invariants、excluded scope、真实 blocker
- [ ] 明确它不替代 external blocker package

### Task 2: 收紧 runtime backend registry 并接入 Hermes adapter

**Files:**
- Modify: `../../src/med_autoscience/runtime_backend.py`
- Add: `../../src/med_autoscience/runtime_transport/hermes.py`
- Modify: `../../src/med_autoscience/runtime_protocol/study_runtime.py`
- Test: `../../tests/test_runtime_backend.py`
- Test: `../../tests/test_runtime_transport_hermes.py`
- Test: `../../tests/test_runtime_protocol_study_runtime.py`

- [ ] registry fail-closed 校验 `BACKEND_ID` / `ENGINE_ID` / callable contract
- [ ] `Hermes` backend 显式注册
- [ ] `runtime_binding.yaml` 对 `Hermes` 继续写出 backend-generic durable fields

### Task 3: 对齐 blocker / cutover / preflight wording

**Files:**
- Modify: `./runtime_core_convergence_and_controlled_cutover.md`
- Modify: `../program/integration_harness_activation_package.md`
- Modify: `../program/external_runtime_dependency_gate.md`
- Modify: `../program/merge_and_cutover_gates.md`
- Modify: `../../src/med_autoscience/dev_preflight_contract.py`
- Test: `../../tests/test_dev_preflight_contract.py`
- Test: `../../tests/test_integration_harness_activation_package.py`

- [ ] 明确 repo-side `Hermes` continuation 与 broader cutover blocker 的关系
- [ ] 保证新增 docs / tests / transport file 不会在 preflight 中被误判为 unclassified
- [ ] 保持 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB` 只用于 broader cutover / physical migration blocker

### Task 4: 为 physical migration 保持 readiness，而不是越权执行

**Files:**
- Modify: cutover runbook / parity plan / monorepo topology truth（仅在 gate 需要时）
- Test: runtime native truth + workspace canonical truth + outer-loop contract

- [ ] 覆盖 runtime truth / knowledge truth / cutover gate 三条主线
- [ ] 保证 physical migration 前 contract 与测试都是 green
- [ ] 仅在 external runtime / workspace / human gate 全绿后进入 physical monorepo migration
