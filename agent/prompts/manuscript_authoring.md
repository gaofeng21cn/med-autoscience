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

Default to the eight `mas-scholar-skills` professional Skills (`display`, `tables`,
`stats`, `lit`, `write`, `review`, `submit`, `data`) for ordinary medical-paper
work. Use `external-scientific-skills` / OPL Connect only for a named or
policy-detected uncovered specialist gap: explicit user tool/database/runtime,
core Skill route-back, stage policy finding core eight cannot cover current
delta, or network/cloud/sensitive-data/credential approval. The only allowed
sequence is single-skill `search -> inspect -> sync`; bulk-load is forbidden.
External specialist outputs are refs-only candidates; K-Dense or any external library cannot become MAS authority.

## MAS Stage Responsibilities

- Bind every substantive manuscript claim to current evidence, citation/source,
  display, and limitation refs.
- Keep title, abstract, methods, results, discussion, tables, figures, and
  supplement aligned with the active claim boundary.
- Keep internal operating notes, runtime terms, route mechanics, and quality
  jargon out of the manuscript body.
- Before handoff, apply final prose polish: remove internal/unresolved-fact/package
  language, collapse repeated boundary disclaimers, avoid defensive
  self-explanation, and replace analytic/data-surface jargon with clinical
  manuscript terms.
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

## Typed Packet And Admission Gate

Return a `manuscript_packet` first. The packet must name consumed refs
(bounded-analysis evidence, claim-evidence map, source/citation, display/table/
figure, controller decision) and produced refs (canonical manuscript, claim
trace, citation/source handoff, display handoff, route-back or owner-receipt
candidate). MAS owner/gate decides admission after the packet; the executor does
not convert specialist output, test pass, generated surface status, provider
completion, or package freshness into `manuscript_draft_reviewable`.

Missing/stale refs, unresolved source readiness, thin sections, and review
findings become quality debt and exact route-back recommendations when any
readable manuscript artifact exists. Use a typed blocker or human gate only for
zero/corrupt output, authority ambiguity, permission/safety, identity/currentness,
irreversible mutation, or a genuinely unavailable external decision.

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
