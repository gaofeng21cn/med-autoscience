# Runtime Documentation Lifecycle

Status: `active runtime docs index`
Owner: `MedAutoScience`
Purpose: `runtime_docs_index`
State: `active_support`
Machine boundary: 本目录是 MAS domain runtime-facing 文档索引。机器真相继续归 contracts、schema、CLI/MCP/API payload、product-entry manifest、sidecar receipt、runtime/controller durable surfaces 和真实 workspace artifact。

`docs/runtime/` is organized by lifecycle role.

当前口径：MAS runtime docs 只定义医学研究 domain agent 的 runtime-facing owner surfaces、controller truth、typed blocker、owner receipt、artifact locator 和 projection/display contract。通用 stage attempt、provider workflow、queue、retry/dead-letter、human gate transport、attempt ledger、generic state-machine runner、generic memory/artifact/workbench primitive 与跨 domain projection 属于 OPL Framework / shared family layer。MAS standalone/local scheduler 和 one-shot reconcile 只服务 direct/local diagnostics，不构成 MAS 自己维护 generic runtime platform。

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
or authority for reopening old MDS daemon, WebUI, Hermes-first default path,
workspace-local service paths, or MAS-owned generic runtime/platform work.

## Rule

Contracts/control docs may describe authority. Projection/display docs may only
describe how existing truth is read or shown. New runtime docs must enter one of
the subdirectories above and state owner, purpose, state, and machine boundary.
If a runtime doc needs generic scheduling, queue, attempt, memory, artifact
lifecycle, workbench, or observability primitives, it must phrase them as OPL /
shared-family owner requirements and keep MAS limited to domain transition
specs, owner receipts, typed blockers, quality/artifact authority, and
runtime-facing projections.
