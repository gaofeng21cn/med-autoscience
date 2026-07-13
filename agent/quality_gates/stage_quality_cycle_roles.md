# Stage Quality Cycle Role Supplement

Owner: MedAutoScience
Machine boundary: OPL selects one role for one new StageAttempt. This supplement
does not create a StageRun, session, receipt, quality verdict, or MAS authority.

Cross-Stage route output has one machine shape. A progress-terminal decisive Attempt returns
`route_impact.stage_route_decision` with `decision_kind`, a declared
`target_stage_id` except for `complete`, and non-empty `evidence_refs`. A
non-decisive Attempt may return `route_impact.stage_route_recommendation` with
the same fields plus `reason`. Never return both or use
`route_back_stage_ref`, `selected_next_stage_ref`, `next_stage_ref`, or
`workflow_complete`.

## Quality Budget And Hard Boundaries

Use the controller-provided `quality_round_index`, `max_repair_rounds`, and exact
artifact identity to choose one branch:

- `repair_budget_remaining`: when required defects still need repair and another
  repair round remains, a reviewer or re-reviewer returns outcome
  `repair_required` and at most `route_impact.stage_route_recommendation`. This
  branch is non-terminal; the controller creates the next fresh repairer Attempt.
- `final_budget_consumable`: when required findings remain, no repair round
  remains, and the exact artifact refs and hashes are consumable, the current
  reviewer or re-reviewer is the terminal decisive Attempt. Required findings
  keep outcome `repair_required`; do not relabel them `quality_debt`. Return
  exactly one `route_impact.stage_route_decision` whose `evidence_refs` bind the
  remaining required finding refs and quality-debt refs. The controller
  classifies this branch as `terminal_quality_debt`, projects
  `completed_with_quality_debt`, and follows the selected route. That debt still
  forbids quality, publication, export, submission, or ready claims. Use outcome
  `quality_debt` only when no required finding remains and ordinary non-required
  debt is carried forward.
- `hard_boundary_or_zero_artifact`: an authority, safety, identity, currentness,
  credential, irreversible-action, or human-decision gate, or literal zero
  consumable exact artifact is not a Stage-routing judgment. A reviewer or
  re-reviewer returns outcome `blocked` or `human_gate` with the applicable
  boundary evidence; every Attempt returns neither
  `route_impact.stage_route_decision` nor
  `route_impact.stage_route_recommendation`. Literal zero consumable artifact
  uses `blocked`. The controller terminalizes the StageRun as blocked or
  human-gated.

Reviewer and re-reviewer quality output also has one machine shape. Return
`route_impact.stage_quality_cycle.outcome` as exactly one of `pass`,
`repair_required`, `quality_debt`, `blocked`, or `human_gate`. An Attempt must
not return receipt `verdict` or use `hard_stop` as an outcome. The OPL StageRun
controller materializes `opl_stage_review_receipt.verdict`, mapping the first
three values directly and mapping `blocked` or `human_gate` to receipt-only
`hard_stop`.

## Producer

Use the Stage goal, policy, sources, and quality definition to produce the best
consumable artifact. You may check and improve your work in this thread, but that
is `in_thread_refinement`; return artifact refs/hashes and never a Review receipt.
The producer is decisive only in a primary-only StageRun when the result is
progress-terminal. In a StageRun with
formal Review, return at most an evidence-backed route recommendation and leave
the terminal decision to the reviewer or re-reviewer. Under
`hard_boundary_or_zero_artifact`, return no route output.

## Reviewer

Independently inspect the exact artifact hashes against the declared rubric and
source refs. Do not inherit the producer conversation and do not mutate the
artifact. Return `route_impact.stage_quality_cycle.outcome` and findings with
stable `finding_id`, severity,
required/optional status, evidence refs, repair expectations, acceptance
criteria, and the narrowest canonical defect-owner Stage. Do not create a
Review receipt or repair map. The OPL StageRun controller materializes the
`opl_stage_review_receipt` from this Attempt's identity, session, exact reviewed
hashes, rubric, and outcome.

While repair budget remains, an outcome of `repair_required` is non-terminal;
return at most a route recommendation when the defect belongs elsewhere and let
the controller continue the quality loop. At final consumable budget, keep
outcome `repair_required` and follow `final_budget_consumable`. When this reviewer
progress-terminalizes the StageRun, it is the decisive Attempt and returns the
route decision. A hard-boundary reviewer returns no route output.

## Repairer

Consume the exact reviewed artifact, finding refs, repair expectations,
acceptance criteria, source/rubric refs, and necessary lineage. Produce a new
artifact generation plus a repair map keyed by every accepted `finding_id`;
each entry records repair status, changed artifact refs, and repair evidence.
Do not reuse the reviewer session, close findings, or claim that the repair
passed. A repairer never makes a terminal route decision; when no hard boundary
applies and repair cannot stay inside the inherited Stage boundary, return only
a route recommendation for the fresh re-reviewer to judge. Under
`hard_boundary_or_zero_artifact`, return no route output.

## Re Reviewer

In a fresh session, review the exact repaired artifact hashes against the prior
findings, repair map, original source/rubric refs, and unresolved acceptance
criteria. Return `closed`, `partially_closed`, or `still_open` for every stable
`finding_id`, plus `route_impact.stage_quality_cycle.outcome`, evidence, and
remaining quality debt. Only an
unclosed required finding, repair regression, or critical new finding may
trigger another repair round; ordinary new suggestions are optional observations
or quality debt and cannot reopen the loop. Never inherit the repairer
conversation or create the controller-owned Review receipt.

When another repair round is required and remains available, return only a route
recommendation. On the final consumable round, keep outcome `repair_required`
and return the route decision for controller-classified terminal quality debt.
When this re-reviewer progress-terminalizes the StageRun, it is the decisive
Attempt and returns the route decision. A hard-boundary re-reviewer returns no
route output.
