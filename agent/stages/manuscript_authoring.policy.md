# Manuscript Authoring Policy

This stage writes from MAS-owned evidence and source refs into canonical paper sources. Manuscript prose must carry current claim evidence faithfully and keep operational blockers outside the paper body. `current_package` is an output projection and cannot be edited as the authority source when canonical paper refs are stale.

Writing may proceed iteratively with analysis and may expose a source, evidence,
or claim-boundary repair. Canonical-source mutation requires the MAS authority
path; affected derived artifacts are rebuilt and bound to fresh proof before a
quality or ready claim. A manuscript packet is required before such a claim,
not as the first action of the stage.

First-draft authoring consumes `medical-manuscript-writing`. Registry, phenotype-
atlas, or treatment-gap studies also consume
`medical-registry-atlas-story-architect`; quantitative, table, and figure work
routes to matching specialist Skills. Templates may inform implementation but
never replace professional Skill consumption. The generation's existing medical,
statistical, reference, and display lanes are the cross-domain pre-review.
Missing or stale receipts are quality debt in Authoring and Review, and fail
closed only for quality/export/finalize/publication/submission claims.

First-draft scientific inputs follow
`contracts/manuscript_first_draft_quality_policy.json`. Current work uses
application schema v2 and one disposition for every canonical candidate ref:
`satisfied`, `route_back_required`, or `not_applicable_with_reason`. A v1
application remains readable but always creates
`first_draft_candidate_dispositions_missing` quality debt. Resolve dispositions
at the earliest canonical owner in baseline, analysis, authoring, then review
order; ref presence is checked only after no earlier route-back remains.

This Stage consumes its `initial_draft_evidence_integrity_requirements` entries
from the same policy: propagate analysis-scope qualifiers across every affected
reader and machine-readable surface, derive the manuscript/table/figure/claim
set from one generation-consistent structured source with renderer provenance,
write from the authors' position, distinguish scientific evidence gaps from
author-supplied objective facts, and bind all local `[AUTHOR INPUT: ...]`
annotations plus the derived To-Do projection through one
`author_stance_integrity_ref`, and freeze one immutable candidate snapshot
before independent review.

Clinical/registry data requires exact input-identity and data-freeze candidates;
non-clinical work records an explicit not-applicable reason. Prediction-model
work distinguishes development, internal, internal-external, and external
validation. Transportability review is external-validation-only. Triggered
fixed-horizon, competing-risk, DCA, Table 1, and reader-PDF work consumes its
specialist candidate and exact schema-v2 invocation, Scholar receipt, input,
and output bindings. PH evidence follows the explicit Scholar preflight
`ph_assessment_applicability` value and must not be inferred from model-family
text; nonlinearity evidence remains conditional on a positive continuous-
predictor count, while formal sample-size/overfitting evidence is not. DCA
binds calibration basis/status plus uncertainty method/interval. Missing or
unresolved evidence may produce a reviewable draft with quality debt, but it
cannot be replaced by a binary event fraction, stale render, template, or
successful renderer exit.

Reader-facing export follows `contracts/publication_layout_policy.json` and a
`medical-submission-prep` selection ref. A named journal consumes its local
ScholarSkills profile; no named journal consumes `general-medical-reader.v1`.
Unknown or stale profiles continue ordinary authoring with journal export marked
pending. Core reader outputs are exactly `paper.pdf` and
`paper_with_supplementary.pdf`; no third reader edition is created.

Derived-artifact iteration follows
`contracts/artifact_iteration_efficiency_policy.json`. The executor classifies
the change and computes a bounded impact plan before heavyweight side effects,
using the descriptor graph when declared and exact-input/canonical-role fallback
for legacy descriptors. Missing graph metadata does not block the hosted action,
but no cache hit may be claimed without complete input, code, tool, and
configuration closure. Iterative preview is component-scoped; full export,
complete render inspection, exact-byte inventory, and affected-lane review happen
only after one candidate freeze. Preview and cache evidence are not Review
receipts.

Canonical source and every derived manuscript, table, figure, and PDF byte
surface also pass `agent/quality_gates/artifact_source_authority_gate.md`.
File presence, a generation hash, or a professional candidate receipt cannot
promote a derived artifact into MAS source or publication authority.

Refs-only candidates enter canonical claims only through an exact MAS candidate
admission receipt. Candidate/evidence ref, size, hash, source-input digest,
generation, verdict, claim classes, permitted sections, disclosures, prohibited
claims, and sensitivity or supplementary constraints must match. Rejected,
waived, or route-back candidates remain non-authorizing provenance and cannot
leak into canonical outputs. The manuscript delta must extend one generation
manifest rather than mix denominator, catalog, display, or receipt generations.

A consumable manuscript delta may close as `completed_with_quality_debt`. Debt
blocks quality/publication/submission claims. No consumable delta becomes a
no-output/failure diagnostic and may route to any declared stage. Only an
unavailable executor, wrong-target identity/currentness, authority/safety/
permission boundary, irreversible action, or real human decision remains a
hard stop.
