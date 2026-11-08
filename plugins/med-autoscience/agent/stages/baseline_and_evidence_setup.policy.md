# Baseline And Evidence Setup Policy

This stage establishes source, cohort, endpoint, comparator, and baseline support for the selected study line. Source readiness is a MAS authority verdict backed by study charter, source provenance, and evidence refs. OPL may consume locator metadata only. A baseline that changes the claim boundary must route to decision or human gate.

A versioned baseline and accepted source/claim boundary are required before an
analysis result is accepted as claim-bearing evidence. Exploratory feasibility
work may happen earlier and may revise the route, but it does not satisfy this
dependency by itself.

This Stage consumes the baseline-owned entries in
`contracts/manuscript_first_draft_quality_policy.json`'s
`initial_draft_evidence_integrity_requirements`: fixed-horizon censoring-aware
estimand setup, analysis-scope qualifier boundaries, and construct-comparability
stop rules. An unresolved required construct mapping or identity-preserving
linkage is not estimable and cannot be replaced with a proxy.

For hypothesis portfolio inputs, this stage must preserve candidate assumptions, sub-assumptions, supporting and contradicting evidence refs, novelty/source provenance refs, testability/safety refs, and negative failed-path refs as body-free evidence-pack refs. Advisory ranking or proximity cannot suppress failed evidence, missing source readiness, independent reviewer requirements, or human gate boundaries.

When narrative clinical notes are in scope, this stage routes schema-bound,
one-note abstraction through Scholar Skills `medical-clinical-note-abstraction`.
The stage consumes `abstraction_schema_ref`, `note_level_candidate_refs`,
`span_provenance_ref`, `assertion_context_ref`,
`terminology_validation_ref`, `completeness_ref`, and
`chart_review_validation_candidate_ref` as refs-only candidates. Exact spans,
explicit nulls, and deterministic shape checks do not establish clinical truth,
terminology validity, cohort validity, source readiness, or analysis approval.
Data access and PHI handling stay with the data owner and data-governance route;
semantic disagreement, double-review sampling, agreement, adjudication, gold-set
maintenance, and error-stratified validation stay explicit before claim-bearing
use.
