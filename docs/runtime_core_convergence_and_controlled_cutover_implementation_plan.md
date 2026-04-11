# Runtime Core Convergence And Controlled Cutover Implementation Plan

**Goal:** 把当前 repo-side `runtime_event` 合同推进到 runtime-native truth，并为 future monorepo 吸收准备可验证的 cutover gate。

**Architecture:** 保持现有 MAS-facing `runtime_event_ref + outer_loop_input` contract 不变，优先迁移 event owner，而不是同时重写 consumer surface。先完成 contract parity 与 transition matrix，再做 runtime repo 吸收与 physical monorepo cutover。

---

## Task 1: 冻结 runtime-native owner contract

**Files:**
- Create: `docs/runtime_core_convergence_and_controlled_cutover.md`
- Modify: `docs/project_repair_priority_map.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 明确写下 `runtime_event` 的 end-state owner 是 runtime core，而不是 repo-side controller。
- [ ] 明确写下 MAS cutover 后只做 consumer，不再承担 managed runtime event 的主要 writer 职责。
- [ ] 在文档测试中冻结这些结论，避免未来又把 projection 当 authority。

## Task 2: 补 runtime parity gate

**Files:**
- Modify: `docs/runtime_event_and_outer_loop_input_contract.md`
- Modify: `docs/runtime_core_convergence_and_controlled_cutover_implementation_plan.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 把 transition matrix 与 parity gate 文档化，覆盖 `paused / stopped / idle / created / waiting_for_user / parking / stale / degraded / live`。
- [ ] 明确 cutover 之前必须验证 runtime-native event 与当前 MAS-facing schema 完全对齐。
- [ ] 冻结“先校验 parity，再迁 owner，再做 cutover”的顺序。

## Task 3: 在 runtime repo 实现 native event writer

**Files:**
- Modify: `med-deepscientist` runtime core 对应 quest state / transition writer 模块
- Modify: `med-deepscientist` runtime tests
- Test: runtime repo transition matrix tests

- [ ] 让 runtime core 在 quest state 迁移时原生写 `runtime_events/*` durable surface。
- [ ] 保持 `status_snapshot / outer_loop_input / summary_ref` 与 MAS 现有 consumer schema 对齐。
- [ ] 为每类 transition 写显式失败测试，再补实现。

## Task 4: 让 MAS 改为 consumer-only

**Files:**
- Modify: `src/med_autoscience/controllers/study_runtime_decision.py`
- Modify: `src/med_autoscience/controllers/study_runtime_execution.py`
- Modify: `src/med_autoscience/controllers/runtime_supervision.py`
- Modify: `tests/test_study_runtime_router.py`
- Modify: `tests/test_runtime_watch.py`

- [ ] 去掉 MAS 作为 managed runtime event 主 writer 的职责。
- [ ] 保留对 native event 的严格校验与 fail-closed 行为。
- [ ] 确认 `study_outer_loop_tick(...)`、`runtime_watch`、`study_progress` 仍只消费 event plane，不退回 summary 推断。

## Task 5: 做 controlled monorepo cutover

**Files:**
- Modify: monorepo 拓扑文档与模块边界说明
- Modify: cutover runbook / absorb 文档
- Test: cross-repo contract regression suite

- [ ] 仅在 native event owner 与 consumer-only gate 全部通过后，才进入 physical cutover。
- [ ] 吸收 `controller_charter / runtime / eval_hygiene` 模块边界，不吸收过渡期 glue。
- [ ] 完成 absorb 后重新跑 cross-surface regression，确认 authority 没有混叠。
