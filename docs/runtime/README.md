# Runtime Documentation Lifecycle

Status: `active runtime docs index`
Owner: `MedAutoScience Runtime OS`

`docs/runtime/` is organized by lifecycle role.

| directory | role |
| --- | --- |
| [contracts](./contracts/) | Runtime contracts, owner boundaries, durable surfaces, artifact authority, and backend/interface rules. |
| [control](./control/) | Controller, supervision, orchestration, outer-loop, scheduler, and runtime action surfaces. |
| [projections](./projections/) | Read models, user-visible status, observability, and non-authoritative summaries. |
| [display](./display/) | Progress Portal and Live Console display contracts. |
| [designs](./designs/) | Active designs that are not yet stable contracts. |

## Primary Entries

- [Runtime boundary](./contracts/runtime_boundary.md)
- [Agent runtime interface](./contracts/agent_runtime_interface.md)
- [Runtime handle and durable surface contract](./contracts/runtime_handle_and_durable_surface_contract.md)
- [Runtime supervision loop](./control/runtime_supervision_loop.md)
- [Supervision scheduler contract](./control/supervision_scheduler_contract.md)
- [Study runtime control surface](./control/study_runtime_control_surface.md)
- [Study progress projection](./projections/study_progress_projection.md)
- [Progress Portal](./display/progress_portal.md)
- [Live Console UI contract](./display/live_console_ui_contract.md)

## History

Completed runtime implementation plans are archived under
[history/runtime](../history/runtime/). They are provenance, not active backlog
or authority for reopening old MDS daemon, WebUI, or workspace-local service
paths.

## Rule

Contracts/control docs may describe authority. Projection/display docs may only
describe how existing truth is read or shown. New runtime docs must enter one of
the subdirectories above and state owner, purpose, state, and machine boundary.
