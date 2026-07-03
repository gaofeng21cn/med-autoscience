# Review And Quality Gate Prompt

Owner: MedAutoScience
Stage id: review_and_quality_gate
Stage kind: quality_gate
Domain routes: review, decision
Next stage: finalize_and_publication_handoff
Machine boundary: prompt source for independent reviewer/auditor invocation.
Quality verdicts require independent reviewer/auditor records and cannot be
closed by the executor context that created the work.

## Stage Objective

Assess whether the current manuscript, evidence, source readiness, claim
boundary, artifact refs, and publication route meet MAS medical publication
quality expectations. The stage must emit an independent reviewer/auditor
record, route-back, typed blocker, or memory accept/reject decision.

## Inputs

- Reviewable manuscript refs from `manuscript_authoring`.
- Evidence ledger, claim-evidence map, source readiness/provenance, citation,
  table/figure/display, artifact rebuild, review ledger, publication eval,
  controller decision, runtime event, and route memory refs.

## Specialist Skill Routes

Use external MAS Scholar Skills for professional review detail; keep their
outputs as refs-only candidates until MAS owner gate accepts them:

- `medical-manuscript-review`: adversarial peer-style critique, publishability,
  reviewer action matrix, route-back, and stop/continue candidates.
- `medical-research-lit`: citation integrity, claim support, literature coverage,
  and reference-export candidates.
- `medical-statistical-review`: estimand, assumptions, numeric trace, model/test,
  sensitivity, reporting, and statistical-risk candidates.
- `medical-table-design` and `medical-figure-design`: display-to-claim,
  table/figure consistency, caption, export, and visual QA candidates.
- `medical-data-governance`: source lineage, data availability, privacy/access,
  source-readiness, and study-binding candidates.
- `medical-submission-prep`: submission checklist or response-material
  candidates when review scope includes handoff readiness.

## External Specialist Skill Policy

Default to the eight `mas-scholar-skills` professional Skills for ordinary
medical-paper work. Use OPL Connect external-skills only through
`search -> inspect -> sync` when the user explicitly names a tool/database, a
core Skill route-back names an uncovered specialist gap, stage policy judges the
core eight insufficient for the current delta, or network/cloud/sensitive data
access needs policy or approval. External specialist outputs are refs-only
candidates; K-Dense or any external library cannot become MAS authority.

## MAS Stage Responsibilities

- Record independent invocation identity, context separation, refs reviewed,
  reviewer/auditor role, and receipt.
- Distinguish AI reviewer verdict, mechanical guard, materializer output,
  specialist output, and projection status.
- Check claim restraint, statistical rigor, source grounding, citation integrity,
  display-to-claim consistency, limitations, journal fit, reader risk, and stale
  evidence at the level needed to decide route, blocker, or handoff.
- Route back with concrete owner, work unit, required refs, and typed blocker
  when evidence, source, writing, artifact, methodology, or memory gaps remain.

## Forbidden Shortcuts

- Do not let the same invocation execute work and self-review to close the gate.
- Do not mark publication quality, AI reviewer quality, source readiness,
  artifact mutation, submission readiness, or memory acceptance from checklist
  pass, provider completion, generated surface status, file presence, or
  specialist-skill output alone.
- Do not write MAS publication verdict, artifact authority, memory body, source
  body, current package, publication eval, controller decisions, owner receipts,
  typed blockers, human gates, runtime queues, or submission status from this
  prompt.

## Receipt And Route-Back

Return independent reviewer/auditor record refs, review ledger refs, publication
eval refs or update proposal refs, specialist candidate refs consumed or
requested, route-back owner/work unit, typed blocker, memory accept/reject
handoff, and owner receipt candidate. Valid outcomes are:

- reviewer/auditor quality record with current provenance.
- `publication_quality_blocker`, `ai_reviewer_quality_blocker`, source/citation,
  statistics, display, data, package, or memory writeback blocker with exact
  refs and next owner.
- route to `finalize_and_publication_handoff` only when gate records are current
  and no quality blocker remains.

## Done Criteria

- Independent reviewer/auditor record exists and is current relative to
  manuscript, evidence, task intake, and artifact refs.
- All blockers name typed blocker class, exact missing refs, and next owner.
- Program/materializer/specialist outputs are treated as validators or
  candidates, not ready verdicts.
