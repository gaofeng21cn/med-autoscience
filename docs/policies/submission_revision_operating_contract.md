# Submission / Revision Operating Contract

Status: `active contract`

This policy fixes the MAS authority boundary for manuscript revision and submission delivery. Reviewer/user revision, manual finishing, manuscript fast lane, bundle-only closeout, and submission package refresh must all start from controller-authorized `paper/` sources.

## Stable Rule

- `paper/` and `paper/submission_minimal/` are controller-authorized delivery sources.
- `manuscript/current_package/`, DOCX/PDF exports, ZIP files, and `manuscript_source.md` are projections.
- `manuscript_source.md` is an authority note when it is generated as an alias. It is not a second manuscript surface.
- Submission readiness requires an AI reviewer-backed quality record, a clear publication gate, a current source signature, and a fresh package projection.
- Mechanical QC and projection files may report blockers or freshness, but they must not claim scientific quality closure.

## Incident Guards

The platform must keep regression coverage for:

- duplicate figure legends
- study-specific hardcoding in platform package generation
- projection-as-authority drift
- stale submission source signatures
- wrong milestone claims from package existence alone
