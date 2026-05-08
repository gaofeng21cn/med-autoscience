# Runtime Documentation Lifecycle

Status: `active runtime docs index`
Owner: `MedAutoScience`

## 入口结论

`docs/runtime/` 是 MAS 运行时合同、控制面、读模型和历史 implementation plan 的工作层。默认阅读顺序是先读 active contracts，再读 control surfaces，随后读 read models / projection contracts；implementation plans 只作为 historical / closeout reference，不能绕过 active contracts 或 behavior-equivalence matrix 重新打开旧 MDS backend / workspace-local service 计划。projection / generated-human docs 只作为人类展示或派生物合同；deprecated/history candidates 在确认 inbound links 后再迁入 `docs/history/runtime/`。

本目录不承载公开产品介绍、program board、capability board 或 references。跨目录叙事入口仍以 `docs/README.md`、`docs/docs_portfolio_consolidation.md` 和 core five 为准。

MAS 保留 domain-owned runtime truth：OPL family 文档生命周期只提供分层治理口径，不把 OPL 的模型、命名或 owner route 强套到 MAS。MAS 的 study truth、publication readiness、controller authority 和 runtime durable surfaces 仍以本仓 contracts、schemas、controllers 与 durable JSON 为准。

## Lifecycle Layers

### Active Contracts

这些文件定义当前 runtime 行为、owner boundary、durable surface、artifact authority 或 delivery plane 的稳定合同。修改 runtime 语义、authority boundary 或 durable identity 时先读这一层。

| file | current handling |
| --- | --- |
| [agent_runtime_interface.md](agent_runtime_interface.md) | Runtime 总接口和入口分层；保持 active。 |
| [agent_entry_modes.md](agent_entry_modes.md) | Agent route / mode contract；保持 active。 |
| [runtime_boundary.md](runtime_boundary.md) | MAS-first runtime 边界；保持 active。 |
| [runtime_handle_and_durable_surface_contract.md](runtime_handle_and_durable_surface_contract.md) | `program_id`、`study_id`、`quest_id`、`active_run_id` 与 durable surface 合同；保持 active。 |
| [runtime_backend_interface_contract.md](runtime_backend_interface_contract.md) | Backend 选择、registry、binding durable surface；保持 active。 |
| [runtime_event_and_outer_loop_input_contract.md](runtime_event_and_outer_loop_input_contract.md) | Quest-owned native runtime truth 与 MAS outer-loop 输入拼接；保持 active。 |
| [runtime_core_convergence_and_controlled_cutover.md](runtime_core_convergence_and_controlled_cutover.md) | Runtime core convergence / controlled cutover 当前事实与 gate；保持 active。 |
| [durable_workflow_contract.md](durable_workflow_contract.md) | Durable workflow state, replay, idempotent tick, human gate 和 retry budget；保持 active。 |
| [workspace_knowledge_and_literature_contract.md](workspace_knowledge_and_literature_contract.md) | Workspace / study / quest 三层知识与文献 authority boundary；保持 active。 |
| [baseline_refresh_contract.md](baseline_refresh_contract.md) | Baseline refresh 允许/禁止场景；保持 active。 |
| [delivery_plane_contract_map.md](delivery_plane_contract_map.md) | Delivery authority、projection / shell / consumer surface 与 fail-closed rules；保持 active。 |
| [canonical_artifact_contract.md](canonical_artifact_contract.md) | Canonical source 与派生产物边界；保持 active。 |
| [artifact_retention_operations_contract.md](artifact_retention_operations_contract.md) | Retention plan、终局止损生命周期、SQLite / file authority；保持 active。 |

### Active Control Surfaces

这些文件定义 controller、supervision loop、outer-loop 或 operator action surface。修改启动、恢复、暂停、重跑、supervision 或控制动作时先读这一层。

| file | current handling |
| --- | --- |
| [runtime_supervision_loop.md](runtime_supervision_loop.md) | Supervision loop、owner route、dispatch 和 fail-closed live 语义；保持 active。 |
| [study_runtime_control_surface.md](study_runtime_control_surface.md) | `study_runtime_status`、`ensure_study_runtime`、outer-loop tick、stop/pause/rerun 语义；保持 active。 |
| [study_runtime_orchestration.md](study_runtime_orchestration.md) | Study runtime orchestration、typed surface、preflight/execution/artifact contracts；保持 active。 |
| [outer_loop_wakeup_and_decision_loop.md](outer_loop_wakeup_and_decision_loop.md) | Outer-loop wakeup 与 decision loop 设计；当前作为 active control-loop contract 使用。 |

### Active Read Models And Projection Contracts

这些文件定义读取、聚合或人类展示层。它们不能回写 study truth、quality truth 或 publication authority。

| file | current handling |
| --- | --- |
| [study_truth_kernel.md](study_truth_kernel.md) | Study truth reducer contract；保持 active read-model contract。 |
| [runtime_health_kernel.md](runtime_health_kernel.md) | Runtime health reducer contract；保持 active read-model contract。 |
| [study_macro_state_and_owner_route.md](study_macro_state_and_owner_route.md) | 用户宏观状态与 executable owner route；保持 active read-model / routing contract。 |
| [study_progress_projection.md](study_progress_projection.md) | Physician-friendly progress projection；作为 projection contract 保持 active。 |
| [progress_portal.md](progress_portal.md) | MAS-native fixed progress entrance：静态快照 + 可选本地只读实时服务；作为 implementation-ready read-model / display artifact contract 保持 active。 |
| [progress_projection_history_contract.md](progress_projection_history_contract.md) | Progress lazy-history / detail-load contract；作为 projection contract 保持 active。 |
| [artifact_inventory_projection.md](artifact_inventory_projection.md) | Artifact inventory projection 字段和展示规则；作为 projection contract 保持 active。 |
| [ai_first_observability.md](ai_first_observability.md) | AI-first operator / user observability signals；作为 observability projection 保持 active。 |
| [runtime_capability_matrix.md](runtime_capability_matrix.md) | Backend capability / doctor / timeout matrix；作为 runtime capability read model 保持 active。 |

### Implementation Plans / Closeout References

这些文件记录旧 P2 / cutover / migration 过程。当前 default runtime closeout 以 MAS Runtime OS + Hermes gateway cron + behavior-equivalence matrix 为准；这些 plan 不是默认真相入口，也不得作为重开外部 MDS runtime dependency 或 workspace-local service 的依据。后续做 inbound link 检查后可迁入 `docs/history/runtime/`。

| file | current handling |
| --- | --- |
| [runtime_event_and_outer_loop_input_implementation_plan.md](runtime_event_and_outer_loop_input_implementation_plan.md) | Native runtime truth 消费主线的 historical closeout reference；当前不作为 active P2 plan。 |
| [runtime_core_convergence_and_controlled_cutover_implementation_plan.md](runtime_core_convergence_and_controlled_cutover_implementation_plan.md) | Runtime core cutover historical closeout reference；当前不作为 active Hermes/MDS migration plan。 |
| [workspace_knowledge_and_literature_implementation_plan.md](workspace_knowledge_and_literature_implementation_plan.md) | Workspace-first knowledge/literature closeout reference；当前不作为 active cutover plan。 |

### History Candidates / Designs Pending Implementation

这些文件是设计或方案比较材料，也是后续 history candidates。只要对应 controller / CLI / contract / gate 尚未完整落地并通过 repo 验证，就留在 `docs/runtime/`；落地后按 history candidate 流程迁入 `docs/history/runtime/`。

| file | current handling |
| --- | --- |
| [journal_package_builtins_upgrade_design.md](journal_package_builtins_upgrade_design.md) | Journal shortlist -> requirements -> target-specific package 的待执行设计；当前不归档。落地后应拆出 active contract 或迁入 `docs/history/runtime/`。 |

## Deprecated / History Candidates

当前不在本 lane 移动文件。以下规则用于后续归档：

1. `*_implementation_plan.md` 只有在对应 contract、代码、测试和 migration gate 均完成后，才可迁入 `docs/history/runtime/`。
2. `*_design.md` 只有在设计已被 active contract 取代，或明确放弃且保留历史价值时，才可迁入 `docs/history/runtime/`。
3. 迁移前必须运行 inbound link spot-check，例如 `rg -n "runtime_event_and_outer_loop_input_implementation_plan|journal_package_builtins_upgrade_design" docs src tests`，并在同一 lane 内更新链接。
4. 叙述性 runtime docs 不能作为 machine-readable authority；代码与行为测试应依赖 stable id、schema、contract surface 或 durable JSON。

## Maintenance Rules

- 新增 runtime 文档时先归入 active contract、control surface、read model / projection contract、implementation plan 或 history candidate 之一，并在本 README 添加 current handling。
- 新增 active contract 应说明 owner boundary、durable surface、fail-closed rule 和与 read model / projection 的关系。
- 新增 control surface 应说明允许的操作、拒绝条件、durable write surface 和与 read model 的关系。
- 新增 implementation plan 应写清已完成前置项、当前待办、受影响文件和完成后归档条件。
- Projection / generated-human docs 只描述如何展示已有 truth，不应创建新的 study truth、quality truth 或 delivery authority。
- 归档动作只在 inbound links 可同步更新时执行；否则文件先留在 `docs/runtime/`，并在 current handling 中标注原因。
