# Source Readiness And Artifact Authority Knowledge

Owner: MedAutoScience
Knowledge role: executable rules for source readiness, artifact authority, and canonical delivery
Machine boundary: this file describes authority semantics. It does not authorize source readiness or artifact mutation by itself.

## Source Readiness

Source readiness asks whether the current data/source/provenance package can support the active study claim. A ready source must have current refs for:

- study charter and claim boundary.
- source locator, source provenance, and source body ownership.
- cohort, inclusion/exclusion, endpoint, exposure or model target, comparator, measurement window, and missingness assumptions.
- data version, transformation or model provenance, run context, and reproducibility notes.
- known source limitations and route impact.

Missing provenance, moved-home drift, stale task intake, incompatible units, hidden cohort changes, or incomplete canonical bundle must route back with `source_readiness_blocker` or a more specific methodology/provenance blocker.

## Artifact Authority

Artifact authority asks whether manuscript, figures, tables, supplement, response, package, and delivery outputs are current, rebuildable, and authorized by MAS owner surfaces. Artifact mutation requires:

- canonical source refs for the artifact.
- rebuild proof current relative to source, evidence, review, and task intake.
- artifact authority refs or owner receipt.
- package refs that are materialized from canonical sources, not edited as the truth source.
- route-back or human gate state when external submission or PI strategy is involved.

## Canonical-Source-First Rule

The canonical paper/source refs are the edit authority. `current_package`, exported bundles, delivery manifests, PDFs, DOCX files, or portal-ready packages are materializations. They may be checked, rebuilt, or blocked, but they do not become the source of truth merely because they exist.

## Forbidden Readiness Signals

These signals can support diagnostics or blockers, but cannot close source or artifact authority:

- file presence.
- script exit code.
- queue or provider completion.
- generated interface readiness.
- local test pass.
- package freshness.
- upload readiness.
- OPL descriptor or scaffold validation.

## Required Blocker Shape

When readiness or authority cannot be established, return a typed blocker with missing refs, stale refs, affected claim or artifact, required owner, and route-back stage. Source problems route to source intake, study design, baseline/evidence setup, methodology reframe, or human gate. Artifact problems route to artifact rebuild, source revision, manuscript authoring, review, or human gate.
