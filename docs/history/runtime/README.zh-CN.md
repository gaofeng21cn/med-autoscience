# Runtime 历史归档

Status: `history archive`
Owner: `MedAutoScience Runtime OS`

本目录保存不再拥有当前 runtime 行为的 implementation plan 与 legacy boundary 记录。

| file | historical role | current owner surface |
| --- | --- | --- |
| [legacy runtime boundary](legacy_runtime_boundary.md) | 早期 runtime boundary 快照与迁移参考。 | [runtime boundary](../../runtime/contracts/runtime_boundary.md) |
| [runtime event and outer-loop input implementation plan](runtime_event_and_outer_loop_input_implementation_plan.md) | 已完成的 native runtime truth / outer-loop input 实施计划。 | [runtime event and outer-loop input contract](../../runtime/contracts/runtime_event_and_outer_loop_input_contract.md) |
| [runtime core convergence and controlled cutover implementation plan](runtime_core_convergence_and_controlled_cutover_implementation_plan.md) | 已完成的 runtime core convergence / cutover 实施计划。 | [runtime core convergence contract](../../runtime/contracts/runtime_core_convergence_and_controlled_cutover.md) |
| [workspace knowledge and literature implementation plan](workspace_knowledge_and_literature_implementation_plan.md) | 已完成的 workspace knowledge / literature 实施计划。 | [workspace knowledge and literature contract](../../runtime/contracts/workspace_knowledge_and_literature_contract.md) |

Runtime 历史只保留 provenance。活跃 runtime 变更必须先更新 `docs/runtime/contracts/`、`docs/runtime/control/`、`docs/runtime/projections/` 或 `docs/runtime/display/`。
