# Finalize And Publication Handoff Prompt

Owner: MedAutoScience
Stage id: finalize_and_publication_handoff
Stage kind: handoff
Domain routes: finalize, journal-resolution, decision
Next stage: external human-supervised delivery or route-back
Machine boundary: prompt source for delivery handoff. Submission readiness,
artifact mutation authorization, and package authority remain MAS-owned.

## Stage Objective

Prepare a publication handoff only after independent quality review, canonical
artifact freshness, source grounding, and controller route state are current.
The stage must produce a handoff receipt or route back with the exact authority
gap; it must not treat bundle creation as submission authorization.

## Inputs

- Independent reviewer/auditor record from `review_and_quality_gate`.
- Publication eval refs, review ledger refs, controller decisions, route-back
  history, failed-path refs, and human gate state.
- Canonical manuscript, figure, table, supplement, response-material, delivery
  manifest, artifact rebuild, citation/export, journal-target, data/code
  availability, and package freshness refs.

## Specialist Skill Routes

Use external MAS Scholar Skills for professional preparation detail; keep their
outputs as refs-only candidates until MAS owner gate accepts them:

- `medical-submission-prep`: journal package, checklist, cover letter,
  highlights, supplement, response-material, and portal handoff candidates.
- `medical-manuscript-review`: final adversarial critique and route-back
  candidates before handoff.
- `medical-manuscript-writing`: last-mile candidate prose repairs requested by
  the reviewer/auditor.
- `medical-research-lit`: citation/export/source support candidates.
- `medical-statistical-review`: final statistical reporting and numeric trace
  candidates.
- `medical-table-design` and `medical-figure-design`: table/figure export,
  display-to-claim, visual QA, and rebuild candidates.
- `medical-data-governance`: Data Availability, FAIR metadata, access route,
  privacy/access, and source-readiness candidates.

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

- Confirm the handoff depends on current independent review, current source
  readiness, current artifact rebuild proof, and current controller decisions.
- Keep handoff readiness, package freshness, publication quality, submission
  readiness, and external submission as separate owner-gated states.
- Verify that all manuscript/package refs are canonical-source-first and
  traceable to source, evidence, review, display, citation, and rebuild refs.
- Route back when quality, source, artifact, journal-fit, package, memory, or
  human-gate evidence is missing or stale.
- Require human supervision for external submission, PI strategy, journal
  strategy, claim expansion, credentials, or portal actions.

## Forbidden Shortcuts

- Do not treat generated bundles, upload readiness, specialist package
  candidates, provider completion, or test pass as submission authorization.
- Do not mutate package/current-package artifacts without MAS artifact authority
  and rebuild proof.
- Do not mark publication-ready or submission-ready from stale reviewer records,
  stale source refs, stale artifact rebuild proof, or package freshness alone.
- Do not write publication eval, controller decisions, owner receipts, typed
  blockers, human gates, current package, runtime queues, or provider attempts
  from this prompt.

## Typed Packet And Admission Gate

Return a `publication_handoff_admission_packet` first. The packet must name
consumed refs (independent review packet, publication eval, controller decision,
artifact rebuild/freshness, journal requirements, human-gate state) and produced
refs (handoff receipt candidate, artifact authority, package freshness proof,
journal checklist, route-back/blocker/human-gate refs). MAS owner/gate decides
admission after the packet; the executor does not convert specialist output,
test pass, generated bundle, provider completion, upload readiness, or package
freshness into publication-ready or submission-ready.

Fail closed to route-back, typed blocker, or human gate when quality/source/
artifact/journal/package refs are missing or stale, handoff would change claim
or package authority, or external submission, credentials, PI/journal strategy,
or irreversible delivery requires human authorization.

## Receipt And Route-Back

Return publication handoff receipt refs, artifact authority refs, package
freshness proof, journal requirement refs, human gate state, specialist
candidate refs consumed or requested, and next owner. Valid outcomes are:

- publication handoff receipt with current review/source/artifact/package refs.
- `artifact_mutation_blocker` route-back for rebuild or source revision.
- `publication_quality_blocker` route-back to independent review or writing.
- `source_readiness_blocker`, `submission_package_blocker`, or human gate with
  exact missing refs and resume surface.
- route-back to `decision` when claim, journal, or external-authority strategy
  must change.

## Done Criteria

- Handoff refs are current against independent review, source readiness, artifact
  rebuild proof, and controller decisions.
- Package/materialized outputs remain traceable to canonical source refs and MAS
  artifact authority.
- No external submission or PI decision is implied without human gate state.
