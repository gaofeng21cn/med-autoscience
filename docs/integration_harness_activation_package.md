# Integration Harness Activation Package

这份文档把 `real-study relaunch and verify` absorbed 到 `main` 之后，`Med Auto Science` 进入 `Phase 6 / Integration Harness And Cutover Readiness` 的正式 activation package 收口成 repo-tracked canonical surface。

它回答四个问题：

1. 为什么当前可以从 real-study absorbed truth 进入 integration harness
2. 当前只允许打开哪条最小 tranche
3. `controller / runtime / eval / delivery` chain 在这一阶段如何理解
4. 哪些 residual risk 与 external surface 仍然明确关闭

## 1. Activation verdict

截至 `2026-04-07`，当前 absorbed truth 已共同满足：

- `P0` outer-loop durable decision loop 已完成
- `P1` formal `stop / rerun / requires_human_confirmation` semantics 已完成
- `P2` delivery plane contract map and artifact-surface freeze 已完成
- `real-study relaunch and verify` 已在真实 anchor 上验证并 absorbed 到 `main`
- 当前 repo-side blocker=`none`
- 当前 remaining blocker 继续只属于 external workspace-side publication surface 与 pending human interaction

因此，当前正式打开的是：

- `Phase 6 / Integration Harness And Cutover Readiness`

但当前只打开到：

- `runtime-eval / delivery-report repo-native baseline`

当前仍然明确关闭：

- `end-to-end study harness`
- `runtime cutover`
- `behavior-equivalence claim`
- `med-deepscientist` 写入
- `cross-repo write`

## 2. Current active tranche

当前最小 coherent tranche 只负责两件事：

1. 把 repo-tracked mainline docs 从 pre-relaunch 叙事同步到 post-relaunch truth
2. 把 `runtime_watch -> publication_gate -> study_delivery_sync` 这一段最小 harness proof surface 编进 repo-native preflight / regression baseline

它不是：

- 新的 runtime feature tranche
- external workspace writer tranche
- end-to-end real-study harness tranche
- cutover tranche

## 3. Controller / runtime / eval / delivery chain

当前 `Phase 6` 只按下面这条链路理解 integration harness：

1. controller entry
   - `study_runtime_status(...)`
   - `ensure_study_runtime(...)`
2. runtime orchestration seam
   - `study_runtime_router`
   - `study_runtime_execution`
   - `runtime_protocol.study_runtime`
   - `runtime_transport.med_deepscientist`
3. durable runtime outputs
   - `launch_report`
   - `runtime_escalation_record`
4. downstream poll / report shell
   - `runtime_watch`
5. delivery / publication guard and projection
   - `medical_publication_surface`
   - `publication_gate`
   - `study_delivery_sync`

当前阶段的重点不是新增 authority root，而是：

- 让 repo 内已有 seam、proof surface、文档与 preflight contract 用同一口径指向这条链
- 保持 `runtime_watch` 只是 poll/report shell
- 保持 `paper/` 仍是 delivery authority source，`manuscript/` 仍只是 projection

## 4. Frozen semantics inherited from earlier phases

`Phase 6` 继续继承并保持以下 frozen truth：

- `pause_runtime = recoverable`
- `stop_runtime = terminal stop`
- `stop_after_current_step = unsupported / fail-closed`
- `rerun = unsupported executable action`
- `requires_human_confirmation = dispatch gate`

任何 integration harness tranche 都不得回退这些语义。

## 5. Repo-native proof surface for the current tranche

当前最小 tranche 的 repo-native proof surface 固定为：

- `tests/test_dev_preflight_contract.py`
- `tests/test_runtime_watch.py`
- `tests/test_study_delivery_sync.py`
- `tests/test_publication_gate.py`

更广但仍属于当前 closeout 的回归锚点包括：

- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_study_runtime_router.py`
- `tests/test_runtime_transport_med_deepscientist.py`
- `tests/test_study_outer_loop.py`

这里的含义是：

- 这是开发控制面的 integration baseline
- 不是“产品 runtime 已稳定 cutover”的声明

## 6. Residual risk list

当前仍必须显式保留的 residual risks：

1. `end-to-end study harness` 仍未打开
2. `runtime cutover gate` 仍未打开
3. `behavior-equivalence` 仍未声明
4. `med-deepscientist` 写入仍未获 repo-tracked contract 授权
5. `cross-repo write` 仍未获授权
6. `DM001` 的 `draft.md` / `endpoint_provenance_note.md` / pending interaction 仍属于 external workspace-side blocker

## 7. External surfaces genuinely needed beyond this tranche

如果要继续推进超出当前 tranche，真正需要的 external surface 只有：

1. external workspace writer / human review 去修 quest paper `Methods` 与 `endpoint_provenance_note.md`
2. pending human interaction resolution
3. 若未来真的进入 cutover，再单独打开 controlled runtime / behavior-equivalence gate

在这些 surface 未显式打开前，repo 内不得把当前 activation package 误写成：

- real-study fully recovered
- integration harness 已整体稳定
- cutover ready

## 8. Bridge to existing canonical docs

- [`docs/study_runtime_control_surface.md`](./study_runtime_control_surface.md)
  - formal control semantics
- [`docs/study_runtime_orchestration.md`](./study_runtime_orchestration.md)
  - runtime/controller seam
- [`docs/outer_loop_wakeup_and_decision_loop.md`](./outer_loop_wakeup_and_decision_loop.md)
  - outer-loop durable decision loop
- [`docs/delivery_plane_contract_map.md`](./delivery_plane_contract_map.md)
  - delivery/publication authority vs projection boundary
- [`docs/real_study_relaunch_verification.md`](./real_study_relaunch_verification.md)
  - absorbed real-study proof and external blocker classification
- `docs/integration_harness_activation_package.md`（本文）
  - real-study absorb 之后的 `Phase 6` activation package、current tranche、residual risks 与 external-surface boundary

若发生冲突：

1. formal control semantics 由 `study_runtime_control_surface.md` 裁定
2. runtime orchestration 由 `study_runtime_orchestration.md` 裁定
3. delivery plane authority boundary 由 `delivery_plane_contract_map.md` 裁定
4. 当前 `Phase 6` activation verdict 由本文裁定

