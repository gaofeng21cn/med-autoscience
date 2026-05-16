# Runtime 历史归档

Status: `history archive`
Owner: `MedAutoScience Runtime OS`

本目录保存运行时 implementation plan、legacy boundary 记录和不再拥有当前运行行为的 provenance。

当前运行时真相从 [runtime 文档入口](../../runtime/README.md) 开始：

- `docs/runtime/contracts/`：稳定合同与 owner boundary。
- `docs/runtime/control/`：controller、supervision、orchestration 与 runtime action surface。
- `docs/runtime/projections/`：读模型和用户可见投影。
- `docs/runtime/display/`：Progress Portal 与 Live Console 展示合同。
- `docs/runtime/designs/`：尚未提升为稳定合同的活跃设计。

| file | historical role | current owner surface |
| --- | --- | --- |
| [legacy runtime boundary](legacy_runtime_boundary.md) | 早期 runtime boundary 快照与迁移参考。 | [runtime boundary](../../runtime/contracts/runtime_boundary.md) |
| [runtime event and outer-loop input implementation plan](runtime_event_and_outer_loop_input_implementation_plan.md) | 已完成的 native runtime truth / outer-loop input 实施计划。 | [runtime event and outer-loop input contract](../../runtime/contracts/runtime_event_and_outer_loop_input_contract.md) |
| [runtime core convergence and controlled cutover implementation plan](runtime_core_convergence_and_controlled_cutover_implementation_plan.md) | 已完成的 runtime core convergence / cutover 实施计划。 | [runtime core convergence contract](../../runtime/contracts/runtime_core_convergence_and_controlled_cutover.md) |
| [workspace knowledge and literature implementation plan](workspace_knowledge_and_literature_implementation_plan.md) | 已完成的 workspace knowledge / literature 实施计划。 | [workspace knowledge and literature contract](../../runtime/contracts/workspace_knowledge_and_literature_contract.md) |
| [outer-loop wakeup and decision loop](outer_loop_wakeup_and_decision_loop.md) | 旧 outer-loop wakeup 设计说明；保留术语 provenance。 | [study runtime control surface](../../runtime/control/study_runtime_control_surface.md) 与 [runtime event and outer-loop input contract](../../runtime/contracts/runtime_event_and_outer_loop_input_contract.md) |

Runtime 历史只保留 provenance。它可以解释当前合同为什么这样设计，但不能重开旧 MDS daemon、WebUI、workspace-local service 或已退役 scheduler 路径。活跃 runtime 变更必须先更新当前 contract / control / projection / display 层。
