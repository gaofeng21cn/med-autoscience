# Manuscript Authoring Prompt

Owner: MedAutoScience
Stage id: manuscript_authoring
Next stage: review_and_quality_gate
Machine boundary: this prompt directs manuscript-facing work. Canonical paper
sources, current package, publication eval, and artifact authority remain
MAS-owned.

## Objective

Turn current evidence into a coherent, reviewable manuscript delta that carries
the active claim faithfully and exposes any remaining evidence, citation,
display, source, or artifact gap.

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
