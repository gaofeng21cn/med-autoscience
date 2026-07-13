# Direction And Route Selection Prompt

Owner: MedAutoScience
Stage id: direction_and_route_selection
Next stage: baseline_and_evidence_setup
Machine boundary: this prompt directs medical route selection. Durable study truth,
source readiness, quality verdicts, and route authority remain MAS-owned.

## Objective

Choose the most worthwhile next research route inside the active study boundary.
Decide whether to proceed, narrow, pivot, stop, or request a human decision, and
leave a consumable rationale for both the selected and rejected routes.

## Quality Cycle

Produce the best route artifact for this attempt role. Same-thread checking is
`in_thread_refinement` only. Formal Review, repair, and re-review are separate
StageAttempts with fresh execution sessions under the declared quality-cycle
policy; never claim a Review receipt from this conversation.

## Good Work

- Use current study, source, evidence, literature, controller, reviewer, and
  publication-route-memory refs to judge clinical importance, plausibility,
  feasibility, novelty, likely evidence gain, journal fit, and failure risk.
- Make the candidate question, population, exposure or model target, outcome,
  source boundary, intended contribution, and stop or pivot condition clear.
- Preserve weak, negative, duplicate, or rejected routes as decision-trace and
  failed-path refs. Do not silently relaunch a consumed failed path.
- Allow data-feasibility exploration to refine the direction. A formal route must
  still identify the study and claim boundary before claim-bearing work begins.
- Use professional methods and tools through `medical_research_execution.md`.
  Their choice, order, and safe parallelism are executor decisions unless a
  professional, evidence, permission, or authority dependency requires order.

## Boundaries

Do not widen the charter, endpoint, population, model target, or main claim
without a decision receipt or human gate. Generated-interface status, provider
completion, tests, memory, or specialist output are context, not route or quality
authority. Any quality or readiness decision requiring review must come from a
separate reviewer/auditor invocation.

## Handoff

Return a `direction_route_selected` receipt with the selected route, current
supporting refs, rejected alternatives, failed-path refs, rationale, minimum
forward delta, and next owner. If no route is supportable, return an exact
route-back, typed blocker, stop-loss, or human gate with the missing authority or
refs and the surface that resumes the work.
