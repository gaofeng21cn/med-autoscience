# Runtime Event And Outer-Loop Input Implementation Plan

**Goal:** 让 managed runtime 端到端消费 native runtime truth，并把 study-owned supervision / escalation / decision truth 与 quest-owned runtime truth 清晰拼接。

**Architecture:** `MedDeepScientist` 负责 quest-owned native runtime event durable surface；`MedAutoScience` transport/status/outer-loop 透传并消费 `runtime_event_ref`，同时继续维护 study-owned `decision`、`reason`、`supervisor_tick_audit`、`runtime_escalation_ref`。禁止 controller 再覆盖 quest-owned `runtime_events/*`。

---

## 已完成

- [x] `GET /api/quests/{quest_id}/session` 已支持 `runtime_event_ref` / `runtime_event`
- [x] transport 已校验并透传 native runtime truth
- [x] `study_runtime_status` 已优先暴露 session-native `runtime_event_ref`
- [x] `study_runtime_execution` 已停止在 managed runtime 上重写 quest-owned transition event
- [x] `runtime_supervision` 已停止覆盖 quest-owned `runtime_events/latest.json`
- [x] `study_outer_loop_tick(...)` 已按 native runtime truth + study-owned supervision truth 组合输入运行

## 当前剩余 P2 任务

### Task 1: 收紧 parity gate

**Files:**
- Modify: `./runtime_core_convergence_and_controlled_cutover.md`
- Modify: `./runtime_core_convergence_and_controlled_cutover_implementation_plan.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 明确写下 cross-repo parity gate 的通过标准
- [ ] 明确切分“全局 P0/P1/P2”与“局部 runtime cutover gate”，避免编号冲突
- [ ] 冻结 physical cutover 之前必须保持 green 的验证矩阵

### Task 2: 扩大 transition matrix 验证

**Files:**
- Modify: `tests/test_runtime_transport_med_deepscientist.py`
- Modify: `tests/test_study_runtime_router.py`
- Modify: `tests/test_study_outer_loop.py`
- Modify: `tests/test_runtime_watch.py`

- [ ] 覆盖 `paused / stopped / waiting_for_user / stale / degraded / live`
- [ ] 覆盖 session-native `runtime_event_ref` 缺失、quest mismatch、artifact mismatch、schema mismatch
- [ ] 覆盖 managed outer-loop 在 `supervisor_tick_status != fresh` 下的 fail-closed

### Task 3: 进入 physical cutover 计划

**Files:**
- Modify: `./runtime_core_convergence_and_controlled_cutover.md`
- Modify: `./runtime_core_convergence_and_controlled_cutover_implementation_plan.md`
- Modify: `../program/project_repair_priority_map.md`

- [ ] 只围绕 `P2 controlled cutover -> physical monorepo migration` 写剩余计划
- [ ] 不重新打开已完成的 `P0` / `P1`
- [ ] 明确 absorb 的模块边界、删除条件和回归 gate
