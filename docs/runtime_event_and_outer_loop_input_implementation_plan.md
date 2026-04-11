# Runtime Event And Outer-Loop Input Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 runtime 状态迁移收敛成 quest-owned event surface，并让 outer loop 直接消费该输入合同，消除 MAS 对停车/降级的系统性失感。

**Architecture:** 新增 `runtime_event` durable artifact，统一由 `study_runtime_status`、`study_runtime_execution`、`runtime_supervision` 物化；outer loop 从 `runtime_event_ref` 读取正式 runtime 输入，而不是继续把 `decision/reason` 当成完整输入。`runtime_watch` 同时扩大扫描面，保证非 live quest 仍可见。

**Tech Stack:** Python 3.12, pytest, repository-tracked docs, existing runtime protocol helpers.

---

### Task 1: 冻结文档合同

**Files:**
- Create: `docs/runtime_event_and_outer_loop_input_contract.md`
- Create: `docs/runtime_event_and_outer_loop_input_implementation_plan.md`
- Modify: `docs/README.md`
- Modify: `docs/README.zh-CN.md`
- Test: `tests/test_runtime_contract_docs.py`

- [ ] 把 runtime event 与 outer-loop input contract 写入 repo-tracked 文档，并加入中英文 docs 索引。
- [ ] 给文档测试增加索引断言，冻结新合同文档入口。

### Task 2: 引入 runtime event artifact

**Files:**
- Create: `src/med_autoscience/runtime_event_record.py`
- Modify: `src/med_autoscience/runtime_protocol/study_runtime.py`
- Modify: `src/med_autoscience/runtime_protocol/__init__.py`
- Test: `tests/test_runtime_event_record.py`

- [ ] 先写失败测试，固定 `RuntimeEventRecord` / `RuntimeEventRecordRef` 的 schema、序列化和 latest alias 行为。
- [ ] 增加 write/read helper：
  - timestamped event artifact
  - `latest.json`
  - ref round-trip

### Task 3: 把 runtime event 接到 `study_runtime_status`

**Files:**
- Modify: `src/med_autoscience/controllers/study_runtime_status.py`
- Modify: `src/med_autoscience/controllers/study_runtime_types.py`
- Modify: `src/med_autoscience/controllers/study_runtime_decision.py`
- Test: `tests/test_study_runtime_typed_surface.py`
- Test: `tests/test_study_runtime_router.py`

- [ ] 先写失败测试，要求 managed runtime 的 `study_runtime_status(...)` 暴露 `runtime_event_ref`。
- [ ] 在 `_finalize_result()` 里物化 `status_observed` event。
- [ ] 让 `outer_loop_input` 包含至少：
  - `quest_status`
  - `decision`
  - `reason`
  - `active_run_id`
  - `runtime_liveness_status`
  - `worker_running`
  - `supervisor_tick_status`
  - `controller_owned_finalize_parking`
  - `interaction_action`
  - `interaction_requires_user_input`
  - `runtime_escalation_ref`

### Task 4: 把 runtime event 接到执行与监管

**Files:**
- Modify: `src/med_autoscience/controllers/study_runtime_execution.py`
- Modify: `src/med_autoscience/controllers/runtime_supervision.py`
- Test: `tests/test_study_runtime_router.py`
- Test: `tests/test_runtime_watch.py`

- [ ] 先写失败测试，要求 `ensure_study_runtime(...)` 在动作后写 `transition_applied` event。
- [ ] 先写失败测试，要求 `runtime_supervision` 在健康态变化时写 `supervision_changed` event，并保留原始原因，不再只落 `runtime_supervision_escalated`。
- [ ] 最小实现完成后，验证现有 escalation surface 继续存在，但不再承担全部状态语义。

### Task 5: 让 outer loop 直接消费 runtime event

**Files:**
- Modify: `src/med_autoscience/controllers/study_outer_loop.py`
- Test: `tests/test_study_outer_loop.py`

- [ ] 先写失败测试，要求 managed runtime 缺少 `runtime_event_ref` 时 `study_outer_loop_tick(...)` fail-closed。
- [ ] 删除“status 缺 escalation ref 就 synthesize escalation”这条路径。
- [ ] outer loop 读取 event artifact，并使用 `outer_loop_input` 做 runtime 输入验证。

### Task 6: 扩大 watch 可见面并收紧 summary alignment

**Files:**
- Modify: `src/med_autoscience/runtime_protocol/quest_state.py`
- Modify: `src/med_autoscience/controllers/runtime_watch.py`
- Modify: `src/med_autoscience/controllers/study_runtime_decision.py`
- Test: `tests/test_runtime_protocol_quest_state.py`
- Test: `tests/test_runtime_watch.py`

- [ ] 先写失败测试，要求 watch 不再天然漏掉 `paused / stopped / idle / created`。
- [ ] 先写失败测试，要求 runtime summary alignment 至少比较：
  - `quest_status`
  - `active_run_id`
  - `runtime_liveness_status`
  - `supervisor_tick_status`

### Task 7: 补 transition matrix 测试

**Files:**
- Modify: `tests/test_runtime_watch.py`
- Modify: `tests/test_study_progress.py`
- Modify: `tests/test_study_outer_loop.py`
- Modify: `tests/test_study_runtime_router.py`

- [ ] 增加 parked 负例：停车存在但不允许自动恢复时，仍需保持前台可见。
- [ ] 增加 invisible / cross-surface conflict 用例。
- [ ] 增加 `fresh -> stale`、`degraded -> live` 序列用例。

### Task 8: 全量验证

**Files:**
- Test only

- [ ] 运行本次改动直接覆盖的测试集合。
- [ ] 运行更大一圈 runtime/controller 回归集合。
- [ ] 检查 worktree 中的最终 diff，只保留本次合同收紧所需变更。
