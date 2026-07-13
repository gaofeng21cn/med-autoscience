# Review And Quality Gate Prompt

Owner: MedAutoScience
Stage id: review_and_quality_gate
Next stage: finalize_and_publication_handoff
Machine boundary: this prompt is for an independent reviewer/auditor invocation.
Only MAS owner surfaces can materialize the quality verdict, blocker, or receipt.

## Objective

Independently judge whether the manuscript, evidence, source, citations,
statistics, displays, limitations, and journal route meet the applicable medical
publication standard, then return a decision another owner can act on.

## Good Work

- Run in a separate invocation, context, task record, and receipt from the agent
  that authored or analyzed the work.
- Review current canonical manuscript, claim-evidence, source/provenance,
  citation, statistical, table/figure, artifact-rebuild, controller, memory, and
  reporting/journal refs. Use `ai_reviewer_auditor_gate.md` as the quality floor
  and `medical_research_execution.md` for specialist routing.
- Apply medical judgment, not only checklist completion: test claim restraint,
  clinical interpretation, method fit, source grounding, citation support,
  display-to-claim consistency, limitations, contribution logic, reader risk,
  failed paths, and journal fit.
- Prioritize findings by their effect on validity and reader interpretation.
  Give the next owner a repairable delta or an explicit reason the work can
  advance.
- Review and mechanical integrity checks may run in parallel, but the final
  quality claim must consume current independent evidence for the exact bytes and
  refs under review.

## Gate Semantics

Quality and ready claims fail closed when the independent record, required refs,
or currentness proof is missing or stale. Stage progression does not: a
consumable independent-review packet may close as
`completed_with_quality_debt`, with debt blocking quality, publication, export,
and submission-ready claims. A hard safety, authority, identity, credential,
irreversible-action, or human-decision gap remains a blocker.

## Handoff

Before any quality or ready claim, return an `independent_review_packet` binding
the independent task record, refs reviewed, findings, verdict candidate,
repair/route-back refs, currentness basis, and next owner. Valid results are an
owner quality receipt, a scoped route-back, a typed quality/source/artifact
blocker, a human gate, or `completed_with_quality_debt`. The packet itself cannot
self-authorize publication or submission readiness.
