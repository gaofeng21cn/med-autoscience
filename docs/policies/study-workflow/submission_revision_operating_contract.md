# Submission / Revision Operating Contract

Status: `active contract`
Owner: `MedAutoScience`
Purpose: `submission_revision_operating_contract`
State: `active_policy`
Machine boundary: Human-readable study-workflow policy only; study truth remains in workspace artifacts, source contracts, runtime/controller outputs, generated artifacts, and owner receipts.

This policy fixes the MAS authority boundary for manuscript revision and submission delivery. Reviewer/user revision, manual finishing, manuscript fast lane, bundle-only closeout, and submission package refresh must all start from the workspace's controller-authorized `manuscript/` canonical editable source.

This policy is intentionally narrow: it governs same-line manuscript revision and submission delivery surfaces. It does not authorize new analysis, new claims, source readiness, quality verdicts, artifact mutation outside controller-approved paper/package flows, or OPL provider completion as submission readiness.

## Stable Rule

- Workspace `manuscript/` is the controller-authorized canonical editable source.
- Workspace `submission/`, including human-facing Markdown, DOCX/PDF exports, ZIP files, and submission-minimal bundles, is a generated projection.
- `manuscript_source.md`, when generated into a projection, records source lineage. It is not a second editable manuscript surface.
- `paper/`, when retained by an older workspace, is a legacy compatibility alias or provenance surface and must not be described as the canonical editable source.
- Submission readiness requires an AI reviewer-backed quality record, a clear publication gate, a current source signature, and a fresh package projection.
- Mechanical QC and projection files may report blockers or freshness, but they must not claim scientific quality closure.
- Explicit reviewer/user manuscript feedback after a stopped, submission-ready, or finalize milestone reactivates the same study line through durable revision intake and OPL runtime hydration/resume refs before MAS handlers edit canonical `manuscript/` sources.
- Foreground edits to `submission/`, DOCX/PDF exports, ZIP files, or package-visible Markdown are review overlays until reconciled into controller-authorized `manuscript/` and regenerated as fresh `submission/` projections.

## Revision Intake / Wake Action Decision

- Durable reviewer/user feedback is a revision intake ref consumed by the existing `manuscript_authoring` Stage action through `user_intent`, `input_refs`, and `route_context_refs`; it is not a new MAS action family.
- Attempt hydration, resume, signal, and wake lifecycle remain OPL-owned. MAS must not add a `revision_intake_wake` catalog action, repo-local runner, queue, or status shell.
- When OPL cannot bind a current durable revision intake ref to the existing Stage action, emit typed owner gap `revision_intake_wake_host_binding_missing` with owner `one-person-lab`, the study/revision refs, current StageRun identity, target existing action, and required host binding repair.
- Resolving that owner gap means adding or repairing the OPL host binding and readback while preserving the six public MAS Stage actions; it does not authorize a second MAS control plane.

## Incident Guards

The platform must keep regression coverage for:

- duplicate figure legends
- study-specific hardcoding in platform package generation
- projection-as-authority drift
- stale submission source signatures
- wrong milestone claims from package existence alone
