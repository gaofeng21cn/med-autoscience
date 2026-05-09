# Runtime Core Convergence And Controlled Cutover Implementation Plan

**Status:** `historical closeout reference`

**Goal:** 本文件记录旧 `P2 controlled cutover -> physical monorepo migration` 的历史执行计划。当前默认运行 closeout 已由 MAS Runtime OS + MAS supervision scheduler contract + behavior-equivalence matrix 接管；Hermes gateway cron 只是当前 active adapter。不得把本文作为重开 Hermes/MDS backend migration 或 workspace-local service 的 active plan。

**Architecture:** 当前 active architecture 以 `runtime_core_convergence_and_controlled_cutover.md`、`runtime_supervision_loop.md` 和 `mds_behavior_equivalence_gap_matrix.md` 为准。

---

## 已完成前置项

- [x] runtime core 原生写出 quest-owned `runtime_events/*`
- [x] `GET /api/quests/{quest_id}/session` 暴露 `runtime_event_ref` / `runtime_event`
- [x] MAS transport/status/outer-loop 已消费 native runtime truth
- [x] MAS 已停止覆盖 quest-owned `runtime_events/latest.json`
- [x] workspace canonical literature / study reference context / quest materialization-only 已落地

## 历史 P2 任务

以下清单保留为历史记录；当前不得作为 active checklist 执行。

### Task 1: 冻结 Hermes continuation truth

**Files:**
- Modify: `../history/program/research_foundry_medical_mainline.md`
- Modify: `../history/program/research_foundry_medical_execution_map.md`
- Add: `../history/program/hermes_backend_continuation_board.md`
- Add: `../history/program/hermes_backend_activation_package.md`
- Test: `../../tests/test_runtime_protocol_study_runtime.py`
- Test: `../../tests/test_study_runtime_router.py`

- [historical] 把 `Hermes` backend continuation 写成当前 repo-side 允许继续推进的 P2 子位置
- [historical] 写清目标、边界、验证、promotion invariants、excluded scope、真实 blocker
- [historical] 明确它不替代 external blocker package

### Task 2: 收紧 runtime backend registry 并接入 Hermes adapter

**Files:**
- Modify: `../../src/med_autoscience/runtime_backend.py`
- Add: `../../src/med_autoscience/runtime_transport/hermes.py`
- Modify: `../../src/med_autoscience/runtime_protocol/study_runtime.py`
- Test: `../../tests/test_runtime_backend.py`
- Test: `../../tests/test_runtime_transport_hermes.py`
- Test: `../../tests/test_runtime_protocol_study_runtime.py`

- [historical] registry fail-closed 校验 `BACKEND_ID` / `ENGINE_ID` / callable contract
- [historical] `Hermes` backend 显式注册
- [historical] `runtime_binding.yaml` 对 `Hermes` 继续写出 backend-generic durable fields

### Task 3: 对齐 blocker / cutover / preflight wording

**Files:**
- Modify: `./runtime_core_convergence_and_controlled_cutover.md`
- Modify: `../history/program/integration_harness_activation_package.md`
- Modify: `../../policies/runtime-governance/external_runtime_dependency_gate.md`
- Modify: `../../policies/repo-ops/merge_and_cutover_gates.md`
- Modify: `../../src/med_autoscience/dev_preflight_contract.py`
- Test: `../../tests/test_dev_preflight_contract.py`
- Review: integration-harness Markdown wording by human/Agent documentation review only; do not add pytest wording anchors.

- [historical] 明确 repo-side `Hermes` continuation 与 broader cutover blocker 的关系
- [historical] 保证新增 docs / tests / transport file 不会在 preflight 中被误判为 unclassified
- [historical] 保持 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB` 只用于 broader cutover / physical migration blocker

### Task 4: 为 physical migration 保持 readiness，而不是越权执行

**Files:**
- Modify: cutover runbook / parity plan / monorepo topology truth（仅在 gate 需要时）
- Test: runtime native truth + workspace canonical truth + outer-loop contract

- [historical] 覆盖 runtime truth / knowledge truth / cutover gate 三条主线
- [historical] 保证 physical migration 前 contract 与测试都是 green
- [historical] 仅在 external runtime / workspace / human gate 全绿后进入 physical monorepo migration
