# Runtime Event And Outer-Loop Input Implementation Plan

Owner: `MedAutoScience`
Purpose: `runtime_history_record`
State: `history_provenance`
Machine boundary: 人读 runtime 历史/provenance 记录。当前 runtime truth 继续归 `docs/runtime/`、contracts、source、CLI/API payload、sidecar receipts、runtime/controller durable surfaces 和 owner receipts。

**Status:** `historical closeout reference`

**Goal:** 本文件记录 managed runtime native truth 消费链路的历史计划。当前默认 runtime owner 已收敛到 MAS Runtime OS；外部 `MedDeepScientist` 不再负责默认 quest-owned runtime truth，只能作为 historical fixture / explicit archive import reference / provenance reference。

**Architecture:** 当前 active architecture 以 `runtime_event_and_outer_loop_input_contract.md`、`runtime_handle_and_durable_surface_contract.md` 和 `mds_behavior_equivalence_gap_matrix.md` 为准。

---

## 已完成

- [x] `GET /api/quests/{quest_id}/session` 已支持 `runtime_event_ref` / `runtime_event`
- [x] transport 已校验并透传 native runtime truth
- [x] `study_runtime_status` 已优先暴露 session-native `runtime_event_ref`
- [x] `study_runtime_execution` 已停止在 managed runtime 上重写 quest-owned transition event
- [x] `runtime_supervision` 已停止覆盖 quest-owned `runtime_events/latest.json`
- [x] `study_outer_loop_tick(...)` 已按 native runtime truth + study-owned supervision truth 组合输入运行

## 历史剩余 P2 任务

以下任务保留为历史记录。不得把它们作为 active plan 重新打开外部 MDS daemon、MDS WebUI 或 workspace-local service。

### Task 1: 收紧 parity gate

**Files:**
- Modify: `./runtime_core_convergence_and_controlled_cutover.md`
- Modify: `./runtime_core_convergence_and_controlled_cutover_implementation_plan.md`
- Test: `tests/test_runtime_protocol_study_runtime.py`
- Test: `tests/test_study_runtime_router.py`

- [historical] 明确写下 cross-repo parity gate 的通过标准
- [historical] 明确切分“全局 P0/P1/P2”与“局部 runtime cutover gate”，避免编号冲突
- [historical] 冻结 physical cutover 之前必须保持 green 的验证矩阵

### Task 2: 扩大 transition matrix 验证

**Files:**
- Modify: `tests/test_runtime_transport_med_deepscientist.py`
- Modify: `tests/test_study_runtime_router.py`
- Modify: `tests/test_study_outer_loop.py`
- Modify: `tests/test_domain_health_diagnostic.py`

- [historical] 覆盖 `paused / stopped / waiting_for_user / stale / degraded / live`
- [historical] 覆盖 session-native `runtime_event_ref` 缺失、quest mismatch、artifact mismatch、schema mismatch
- [historical] 覆盖 managed outer-loop 在 `supervisor_tick_status != fresh` 下的 fail-closed

### Task 3: 进入 physical cutover 计划

**Files:**
- Modify: `./runtime_core_convergence_and_controlled_cutover.md`
- Modify: `./runtime_core_convergence_and_controlled_cutover_implementation_plan.md`
- Modify: `../../references/mainline/project_repair_priority_map.md`

- [historical] 只围绕 historical `P2 controlled cutover -> physical monorepo migration` 写剩余计划
- [historical] 不重新打开已完成的 `P0` / `P1`
- [historical] 明确 absorb 的模块边界、删除条件和回归 gate
