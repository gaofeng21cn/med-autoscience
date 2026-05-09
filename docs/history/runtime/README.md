# Runtime History

Status: `history archive`
Owner: `MedAutoScience Runtime OS`

This directory keeps runtime implementation plans, legacy boundary records, and
provenance notes that no longer own active runtime behavior.

Current runtime truth starts from the active [runtime docs index](../../runtime/README.md):

- `docs/runtime/contracts/`: stable contracts and owner boundaries.
- `docs/runtime/control/`: controllers, supervision, orchestration, and runtime action surfaces.
- `docs/runtime/projections/`: read models and user-visible projections.
- `docs/runtime/display/`: Progress Portal and Live Console display contracts.
- `docs/runtime/designs/`: active designs that have not yet become stable contracts.

| file | historical role | current owner surface |
| --- | --- | --- |
| [legacy runtime boundary](legacy_runtime_boundary.md) | Earlier runtime boundary snapshot and migration reference. | [runtime boundary](../../runtime/contracts/runtime_boundary.md) |
| [runtime event and outer-loop input implementation plan](runtime_event_and_outer_loop_input_implementation_plan.md) | Completed native runtime truth / outer-loop input implementation plan. | [runtime event and outer-loop input contract](../../runtime/contracts/runtime_event_and_outer_loop_input_contract.md) |
| [runtime core convergence and controlled cutover implementation plan](runtime_core_convergence_and_controlled_cutover_implementation_plan.md) | Completed runtime core convergence / cutover implementation plan. | [runtime core convergence contract](../../runtime/contracts/runtime_core_convergence_and_controlled_cutover.md) |
| [workspace knowledge and literature implementation plan](workspace_knowledge_and_literature_implementation_plan.md) | Completed workspace knowledge / literature implementation plan. | [workspace knowledge and literature contract](../../runtime/contracts/workspace_knowledge_and_literature_contract.md) |

Runtime history is provenance only. It can explain why the current contracts
look the way they do, but it cannot reopen old MDS daemon, WebUI,
workspace-local service, or retired scheduler paths. Active runtime changes must
update current contract, control, projection, or display docs first.
