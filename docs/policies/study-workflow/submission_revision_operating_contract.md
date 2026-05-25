# Submission / Revision Operating Contract

Status: `active contract`
Owner: `MedAutoScience`
Purpose: `submission_revision_operating_contract`
State: `active_policy`
Machine boundary: Human-readable study-workflow policy only; study truth remains in workspace artifacts, source contracts, runtime/controller outputs, generated artifacts, and owner receipts.

This policy fixes the MAS authority boundary for manuscript revision and submission delivery. Reviewer/user revision, manual finishing, manuscript fast lane, bundle-only closeout, and submission package refresh must all start from controller-authorized `paper/` sources.

This policy is intentionally narrow: it governs same-line manuscript revision and submission delivery surfaces. It does not authorize new analysis, new claims, source readiness, quality verdicts, artifact mutation outside controller-approved paper/package flows, or OPL provider completion as submission readiness.

## Stable Rule

- `paper/` and `paper/submission_minimal/` are controller-authorized delivery sources.
- `manuscript/current_package/`, DOCX/PDF exports, ZIP files, and `manuscript_source.md` are projections.
- `manuscript_source.md` is an authority note when it is generated as an alias. It is not a second manuscript surface.
- Submission readiness requires an AI reviewer-backed quality record, a clear publication gate, a current source signature, and a fresh package projection.
- Mechanical QC and projection files may report blockers or freshness, but they must not claim scientific quality closure.
- Explicit reviewer/user manuscript feedback after a stopped, submission-ready, or finalize milestone reactivates the same study line through durable revision intake and OPL runtime hydration/resume refs before MAS handlers edit canonical `paper/` sources.
- Foreground edits to `manuscript/current_package/`, DOCX/PDF exports, ZIP files, or package-visible Markdown are review overlays until reconciled into controller-authorized `paper/` and regenerated package projections.

## Incident Guards

The platform must keep regression coverage for:

- duplicate figure legends
- study-specific hardcoding in platform package generation
- projection-as-authority drift
- stale submission source signatures
- wrong milestone claims from package existence alone
