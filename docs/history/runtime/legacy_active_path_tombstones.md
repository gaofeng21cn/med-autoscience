# Legacy Active Path Tombstones

Status: `tombstoned`
Owner: `MedAutoScience documentation`
Purpose: preserve tombstone context for retired active-path wording and default-caller claims.
Machine boundary: machine truth lives in `contracts/runtime/legacy-active-path-tombstones.json`, product-entry manifest tombstone proofs, sidecar receipts, OPL current-control-state / provider attempt refs, and MAS runtime/controller surfaces.
State: `history_provenance`

Current read rule: this file is a tombstone/provenance guard. It does not define a MAS `Runtime OS`, hosted runtime owner, scheduler owner, product surface, or runnable CLI path. Current runtime ownership is OPL/Temporal hosted runtime plus MAS domain authority refs, owner receipts and typed blockers.

## Hermes Scheduler Hosted Runtime

The Hermes scheduler / hosted runtime path is no longer a MAS default active path. It is retained only as explicit diagnostic cleanup, historical provider proof, or provenance context. OPL Temporal provider readiness and MAS sidecar dispatch are the replacement active-path contract.

## Hosted Runtime Binding Wording

Generic hosted-runtime binding wording is tombstoned unless it explicitly refers to provider-readiness provenance or an optional adapter context. It must not be used as evidence that MAS paper progress, publication quality, or submission readiness has been closed.

## Workspace Local Scheduler

The workspace-local scheduler is degraded to standalone diagnostics. It is not the OPL-hosted online target and cannot authorize study truth, paper progress, artifact mutation, or publication readiness.
