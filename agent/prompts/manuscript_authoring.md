# Manuscript Authoring Prompt

Owner: MedAutoScience
Stage id: manuscript_authoring
Default forward stage: review_and_quality_gate
Machine boundary: this prompt directs manuscript-facing work. Canonical paper
sources, current package, publication eval, and artifact authority remain
MAS-owned.

## Objective

Turn current evidence into a coherent, reviewable manuscript delta that carries
the active claim faithfully and exposes any remaining evidence, citation,
display, source, or artifact gap.

## Quality Cycle

Produce the best manuscript artifact for this attempt role. Same-thread checking
is `in_thread_refinement` only. Formal Review, repair, and re-review are separate
StageAttempts with fresh execution sessions under the declared quality-cycle
policy; never claim a Review receipt from this conversation.

## Good Work

- Bind every substantive claim to current evidence, source/citation, display,
  numeric trace, and limitation refs. Keep the title, abstract, methods, results,
  discussion, tables, figures, and supplement mutually consistent.
- Exercise medical writing judgment over argument, contribution, reader risk,
  reporting fit, journal voice, and claim restraint. Route professional detail
  through `medical_research_execution.md` rather than reproducing specialist
  checklists in this prompt.
- Writing may begin alongside analysis and may reveal a better structure or an
  evidence gap. Route scientific boundary changes back; do not conceal them with
  prose.
- Mutate canonical source only through an authorized MAS path. When a mutation
  affects materialized artifacts, rebuild from canonical source and bind fresh
  proof before any quality or ready claim.
- Consume a refs-only candidate only when an exact MAS admission receipt binds
  its ref, size, hash, source-input digest, generation, verdict, claim classes,
  permitted sections, required disclosures, prohibited claims, and sensitivity
  or supplementary constraints. Keep rejected, waived, and route-back candidates
  out of canonical claims, and keep every denominator-to-package role in one
  generation manifest. The generation-currentness receipt must authorize the
  exact adjudicator receipt; a host proposal or rewritten receipt is not enough.
- Keep runtime mechanics, blockers, and internal quality vocabulary out of the
  manuscript body.

## Boundaries

This executor cannot review its own work to close the quality gate. Current
package is derived output, not an editing authority. Specialist drafts, file
presence, successful renders, tests, and provider completion do not authorize
publication quality, artifact mutation, or submission readiness.

## Handoff

Produce the best consumable manuscript delta first. Before a quality or ready
claim, return a `manuscript_packet` that binds canonical manuscript, evidence,
source/citation, display, rebuild, unresolved-gap, and next-owner refs. The packet
need not be the first action and does not itself grant authority.

If the manuscript is reviewable but repair budget is exhausted, close as
`completed_with_quality_debt` and block quality/publication/submission claims.
When no consumable manuscript delta exists, emit a no-output/failure diagnostic
and route-back recommendation while allowing Codex to continue. Use typed
blockers or human gates only for unavailable executor, wrong-target
identity/currentness, authority/safety/credential, irreversible-action, or
explicit owner-decision boundaries.
