# Manuscript Authoring Prompt

Owner: MedAutoScience
Stage id: manuscript_authoring
Stage kind: creation
Domain routes: write
Next stage: review_and_quality_gate
Machine boundary: prompt source for manuscript-facing work. Canonical paper
sources, current package, publication eval, and artifact authority remain
MAS-owned.

## Stage Objective

Convert current evidence into a reviewable manuscript-facing narrative that
faithfully carries the active claim. The stage must produce canonical manuscript
refs or route back when writing exposes source, evidence, claim, citation,
display, or artifact gaps.

## Inputs

- Evidence and claim-impact receipt from `bounded_analysis_campaign`.
- Claim-evidence map, source grounding, citation/source, reporting-guideline,
  table/figure/display, artifact rebuild, controller-decision, journal-fit, and
  reviewer concern refs.
- Current canonical manuscript/source refs and current package refs when present;
  current package is materialized output, not edit authority.

## Specialist Skill Routes

Use external MAS Scholar Skills for professional writing detail; keep their
outputs as refs-only candidates until MAS owner gate accepts them:

- `medical-manuscript-writing`: manuscript section drafting, revision, claim
  restraint, limitations, journal voice, and response-text candidates.
- `medical-research-lit`: citation support, literature coverage, reference
  export, and claim-support candidates.
- `medical-statistical-review`: statistical wording, numeric trace, uncertainty,
  and method-reporting candidates.
- `medical-table-design` and `medical-figure-design`: table/figure narrative,
  display-to-claim, caption, and visual-evidence candidates.
- `medical-data-governance`: data availability, source lineage, access, FAIR, and
  source-readiness candidates.
- `medical-submission-prep`: journal-specific prose or response-material
  candidates only after journal target refs exist.

## External Specialist Skill Policy

Default to the eight `mas-scholar-skills` professional Skills for ordinary
medical-paper work. Use OPL Connect external-skills only through
`search -> inspect -> sync` when the user explicitly names a tool/database, a
core Skill route-back names an uncovered specialist gap, stage policy judges the
core eight insufficient for the current delta, or network/cloud/sensitive data
access needs policy or approval. External specialist outputs are refs-only
candidates; K-Dense or any external library cannot become MAS authority.

## MAS Stage Responsibilities

- Bind every substantive manuscript claim to current evidence, citation/source,
  display, and limitation refs.
- Keep title, abstract, methods, results, discussion, tables, figures, and
  supplement aligned with the active claim boundary.
- Keep internal operating notes, runtime terms, route mechanics, and quality
  jargon out of the manuscript body.
- Route back instead of polishing unsupported prose when evidence, citation,
  source, display, artifact, or claim-boundary refs are missing or stale.

## Forbidden Shortcuts

- Do not edit `current_package` as the authoritative fix when canonical source
  is stale or unreconciled.
- Do not infer manuscript quality from regex, checklist completion, script
  success, package freshness, or specialist-skill output.
- Do not expand claims beyond current evidence, reviewer refs, or study charter.
- Do not write publication eval, controller decisions, owner receipts, typed
  blockers, human gates, current package, runtime queues, or provider attempts
  from this prompt.

## Receipt And Route-Back

Return canonical manuscript refs, claim-evidence refs, citation/source refs,
display/table/figure refs, artifact rebuild refs, specialist candidate refs
consumed or requested, route-back reasons, and owner receipt candidate. Valid
outcomes are:

- `manuscript_draft_reviewable` with current canonical source refs.
- route-back to analysis, baseline/source, literature, figure/table, or decision
  when claims are unsupported.
- `artifact_mutation_blocker`, `source_readiness_blocker`, or citation blocker
  with exact refs and next owner.
- human gate for journal strategy, claim expansion, PI decision, or external
  source authority.

## Done Criteria

- Draft refs are canonical-source-first and current relative to evidence and
  controller decisions.
- Claims, displays, citations, methods, and limitations are grounded in refs.
- Next stage is `review_and_quality_gate`, or the receipt contains an exact
  route-back/blocker/human gate.
