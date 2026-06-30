# Legacy Active Path Tombstones

Status: `tombstoned`
Owner: `MedAutoScience documentation`
Purpose: preserve tombstone context for retired active-path wording and default-caller claims.
Machine boundary: machine truth lives in `contracts/runtime/legacy-active-path-tombstones.json`, product-entry manifest tombstone proofs, sidecar receipts, OPL current-control-state / provider attempt refs, and MAS runtime/controller surfaces.
State: `history_provenance`

Current read rule: this file is a tombstone/provenance guard. It does not define a MAS `Runtime OS`, hosted runtime owner, scheduler owner, product surface, runnable CLI path, default next-action selector, provider admission authority, paper progress proof, publication-ready proof, or submission-ready proof. Current runtime ownership is OPL/Temporal hosted runtime plus MAS domain authority refs, owner receipts and typed blockers; current next-action authority is `StageOutcome -> NextActionEnvelope`.

## Hermes Scheduler Hosted Runtime

The Hermes scheduler / hosted runtime path is no longer a MAS default active path. It is retained only as explicit diagnostic cleanup, historical provider proof, or provenance context. OPL Temporal provider readiness and MAS sidecar dispatch are the replacement active-path contract.

## Hosted Runtime Binding Wording

Generic hosted-runtime binding wording is tombstoned unless it explicitly refers to provider-readiness provenance or an optional adapter context. It must not be used as evidence that MAS paper progress, publication quality, or submission readiness has been closed.

## Workspace Local Scheduler

The workspace-local scheduler is degraded to standalone diagnostics. It is not the OPL-hosted online target and cannot authorize study truth, paper progress, artifact mutation, or publication readiness.

## Legacy Next-Action And Current-Owner Surfaces

The following names are tombstoned as default authority surfaces:

- `current_executable_owner_action`
- `current_work_unit`
- `current_execution_envelope`
- PaperRecovery / `paper_recovery_state`
- provider admission / provider-admission candidates
- domain transition successor projections
- OPL queue / attempt / StageAttempt observations
- exact work-unit route tables or allowlists

Allowed read contexts:

- historical provenance;
- migration diagnostic;
- observability-only drilldown;
- receipt/readback evidence for the same canonical identity;
- no-resurrection guard.

Forbidden current uses:

- selecting the default next action;
- authorizing provider admission or dispatch;
- declaring paper progress, runtime-ready, publication-ready, submission-ready, current package authority, owner receipt, typed blocker, or human gate.

Exact work-unit id remains an identity binding only when carried by canonical `StageOutcome -> NextActionEnvelope` or by same-identity MAS owner consumption. It is not a selector by itself.
