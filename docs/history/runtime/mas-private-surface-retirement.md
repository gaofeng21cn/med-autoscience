# MAS 私有控制面物理退役 tombstone

Owner: `MedAutoScience`
Purpose: `mas_private_surface_retirement_tombstone`
State: `history_tombstone_provenance`
Machine boundary: 本文只为 `contracts/runtime/mas-runtime-surface-retirement-inventory.json` 提供人读 provenance anchor。当前机器真相仍归 inventory、源码、tests、contracts 和 fresh runtime/readback evidence；本文不得作为 runtime readiness、provider running、paper progress、owner receipt、typed blocker 或 publication-ready 证据。

## 读法

MAS 私有控制面退役现在采用两栏口径：

- `repo-source retirement`: active callsites 已迁移或删除，旧 module / alias / wrapper / compat shim 已物理删除或降为合法最小 MAS adapter/projection，且 no-forbidden-authority guard、replacement parity、tombstone/provenance 和 focused/meta/default verification 通过后即可完成。
- `live-runtime readiness`: OPL live readback、provider admission/running proof、DM002/DM003 live paper-line outcome、production soak 和 long-running operator evidence。它不再阻塞 repo-source 删除，但仍是 runtime ready / production ready / paper progress 声明的前置。

以下条目是 tombstone，不是兼容入口。旧名称只能出现在 history、inventory、retired cleanup detector、negative tests 或 explicit provenance 语境；不得恢复 public CLI alias、workspace wrapper、fallback reader、compat shim 或 MAS-local queue/attempt/outbox/event/StageRun authority。

## runtime_transport_core_bridge

Disposition: `physically_retired`

Replacement: OPL owns runtime transport, queue, attempt ledger, retry/dead-letter, provider liveness and generic StageRun state.

Forbidden interpretation: MAS no longer owns a generic runtime transport bridge. Transport success, provider completion or queue state cannot imply MAS domain readiness, owner receipt, typed blocker, paper progress or publication readiness.

## runtime_turn_runner_closeout_adapter

Disposition: `physically_retired`

Replacement: OPL StageRun closeout / terminal readback is consumed by MAS only as owner-answer evidence, typed blocker evidence, route-back evidence or diagnostic provenance.

Forbidden interpretation: MAS must not keep a private turn runner, retry loop, closeout event log or worker residency adapter.

## worker_lease_residency_projection

Disposition: `physically_retired`

Replacement: OPL provider runtime owns lease, worker residency, attempt liveness and retry/dead-letter state.

Forbidden interpretation: MAS worker liveness hints are diagnostic only and cannot authorize provider admission, running proof, recovery action, retry or paper progress.

## domain_authority_refs_index

Disposition: `physically_retired`

Replacement: OPL `StateIndexKernel` / Vault consumes emitted MAS authority receipt refs. MAS may emit source adapter refs, but does not keep a private SQLite lifecycle substrate or runtime state index.

Forbidden interpretation: refs-only scans, sidecar refs, local replay helpers or source adapter manifests cannot become MAS private state/index authority or physical-runtime readiness proof.

## default_executor_dispatch_request

Disposition: `physically_retired`

Replacement: canonical carrier is `domain_progress_transition_requests`; executable body, command/event/outbox, provider admission and StageRun readback belong to OPL `DomainProgressTransitionRuntime`.

Forbidden interpretation: `default_executor_dispatches` / `task_kind=domain_owner/default-executor-dispatch` are provenance or OPL StageRun ABI only. They cannot authorize provider admission, attempt lease, event, outbox, StageRun, running proof or next action from MAS.

## domain_action_request_materializer_local_carrier_persistence_api

Disposition: `physically_retired`

Retired code path: `src/med_autoscience/controllers/domain_action_request_materializer_parts/persistence.py`

Retired symbols: `persist_default_executor_dispatches`, `persist_request_packets`, `persist_consumer_payload`, `request_packet_for_persistence`, `medical_paper_readiness_packet_for_persistence`, `source_workflow_ref_for_ai_reviewer_request`.

Replacement: MAS emits refs-only policy request projections; OPL persists durable command/event/outbox/StageRun state.

Forbidden interpretation: MAS materializer must not persist local request packets, local executor dispatches, private outbox records or queue-like carrier bodies.

## owner_callable_adapter_legacy_dispatch_projection_alias

Disposition: `physically_retired`

Replacement: `domain_progress_transition_requests` plus OPL readback. Body-free legacy diagnostics may expose identity refs only.

Forbidden interpretation: `owner_callable_adapters` must not be treated as active body carriers, readiness authority, provider admission, success outcome or fallback execution list.

## domain_action_request_materializer_current_default_executor_dispatches_api

Disposition: `physically_retired`

Replacement: current readers consume canonical transition request projections and OPL readback, not `current_default_executor_dispatches`.

Forbidden interpretation: legacy default-executor dispatch count, ready count or preview APIs cannot become controller readiness, current next action or provider admission proof.

## domain_action_request_materializer_owner_callable_adapter_projection

Disposition: `physically_retired`

Replacement: canonical `domain_progress_transition_requests` projection with body-free identity refs and OPL `DomainProgressTransitionRuntime` readback.

Forbidden interpretation: top-level `owner_callable_adapters` and `*_owner_callable_adapter_count` are legacy diagnostics only; public body reader is retired and must not return active carriers.

## domain_action_request_materializer_request_tasks_projection

Disposition: `physically_retired`

Replacement: `legacy_request_task_diagnostics.legacy_request_task_refs` may retain refs-only identity summaries; canonical requests are `domain_progress_transition_requests`.

Forbidden interpretation: `request_tasks` must not be exported or read as outbox, command, event, StageRun, provider admission, next action authority or executable handoff body.

## domain_action_request_materializer_canonical_transition_request_body_projection

Disposition: `physically_retired`

Replacement: MAS request projection contains identity refs and contract metadata only; full executable body, command/event/outbox and StageRun live readback belong to OPL.

Forbidden interpretation: `domain_progress_transition_requests` in MAS cannot carry or reconstruct executable bodies, operator payload bodies, provider admission, next action authority, command/event/outbox or StageRun state.

## default_executor_execution_latest_wire_projection

Disposition: `physically_retired`

Replacement: canonical latest receipt is `artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json`; legacy `default_executor_execution/latest.json` requires explicit opt-in for history replay/provenance.

Forbidden interpretation: legacy latest wire cannot be current provider admission, current owner handoff, recovery action, execution ledger, attempt lifecycle, provider running proof or StageRun authority.

## domain_owner_action_dispatch

Disposition: `opl_authorized_owner_callable_adapter`

Replacement: OPL `DomainProgressTransitionRuntime` execution authorization plus MAS owner callable adapter.

Retained MAS role: owner callable adapter policy boundary and typed blocker projection.

Forbidden interpretation: active dispatcher callers, closeout binding, provider completion, legacy default-executor carriers or owner-callable adapter lists cannot authorize execution, provider admission, running proof, next action or paper progress without trusted OPL authorization or bound OPL runtime readback.

## domain_health_diagnostic_obligation_actuator

Disposition: `obligation_readback_projection_consumer`

Replacement: OPL `RecoveryObligationStore` / `SupervisorDecisionEngine` readback plus MAS `PaperProgressPolicyAdapter` result.

Retained MAS role: consume-only obligation outcome projection and MAS typed-blocker authority result.

Forbidden interpretation: MAS must not run a private recovery-obligation store, supervisor decision engine, fixed-point reconciler, human-gate token store or request-projection-as-success path. Success requires OPL runtime readback, MAS owner answer readback or MAS domain authority readback.

## runtime_health_kernel

Disposition: `read_only_diagnostic_publisher`

Replacement: OPL Observability / StageRun / `DomainProgressTransitionRuntime` readback plus MAS owner answer projection.

Retained MAS role: body-free runtime health diagnostic projection.

Forbidden interpretation: runtime health epochs, diagnostic snapshots, worker liveness hints, canonical action labels or status payloads cannot become currentness authority, attempt ledger, retry/dead-letter state, provider running proof, next action or paper progress.

## progress_portal_study_workbench_overview_action_projection

Disposition: `read_only_workbench_projection`

Replacement: OPL Workbench Shell owns operator action transport; MAS only publishes inert `current_owner_delta` and `DomainProgressTransitionRuntime` readback refs.

Retained MAS role: body-free workbench read-model projection.

Forbidden interpretation: workbench summary, next-system-action text, operator focus refs or portal cleanliness cannot generate action, transport operator action, authorize provider admission, claim runtime readiness, paper progress or publication readiness.

## agent_tool_arsenal_scientific_capability_registry

Disposition: `opl_capability_runtime_projection`

Replacement: OPL Capability Runtime / Tool Arsenal selector and invocation runtime.

Retained MAS role: capability planning projection and owner-consumption evidence shape.

Forbidden interpretation: MAS capability registry, wildcard capabilities, sidecar refs or capability resolution cannot become a tool selector, always-on advisory pipeline, provider admission authority, current owner action blocker, paper progress proof or publication readiness claim.

## runtime_lifecycle_payload_retention

Disposition: `opl_authorized_maintenance_callable_adapter_live_takeover_tail_open`

Replacement: OPL runtime lifecycle cleanup / retention policy plus OPL maintenance authorization readback.

Retained MAS role: maintenance callable adapter and body-free receipt projection.

Forbidden interpretation: MAS maintenance dry-run plans, cleanup receipts, SQLite sidecar repair or apply authorization cannot become generic runtime lifecycle policy, persistence engine ownership, runtime readiness, provider admission or paper progress.

## runtime_storage_maintenance

Disposition: `opl_authorized_storage_maintenance_callable_adapter_live_takeover_tail_open`

Replacement: OPL runtime storage maintenance authorization / retention shell plus OPL `StateIndex` and restore/readback surfaces.

Retained MAS role: maintenance callable adapter and body-free diagnostic projection.

Forbidden interpretation: MAS storage maintenance checks, restore/retention helpers or apply results cannot become generic runtime storage shell, queue/attempt ownership, provider admission, runtime readiness, paper progress or publication readiness.
