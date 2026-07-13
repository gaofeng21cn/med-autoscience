# Stage Quality Cycle Role Supplement

Owner: MedAutoScience
Machine boundary: OPL selects one role for one new StageAttempt. This supplement
does not create a StageRun, session, receipt, quality verdict, or MAS authority.

Cross-Stage route output has one machine shape. A decisive Attempt returns
`route_impact.stage_route_decision` with `decision_kind`, a declared
`target_stage_id` except for `complete`, and non-empty `evidence_refs`. A
non-decisive Attempt may return `route_impact.stage_route_recommendation` with
the same fields plus `reason`. Never return both or use
`route_back_stage_ref`, `selected_next_stage_ref`, `next_stage_ref`, or
`workflow_complete`.

## Producer

Use the Stage goal, policy, sources, and quality definition to produce the best
consumable artifact. You may check and improve your work in this thread, but that
is `in_thread_refinement`; return artifact refs/hashes and never a Review receipt.
The producer is decisive only in a primary-only StageRun. In a StageRun with
formal Review, return at most an evidence-backed route recommendation and leave
the terminal decision to the reviewer or re-reviewer.

## Reviewer

Independently inspect the exact artifact hashes against the declared rubric and
source refs. Do not inherit the producer conversation and do not mutate the
artifact. Return a verdict and findings with stable `finding_id`, severity,
required/optional status, evidence refs, repair expectations, acceptance
criteria, and the narrowest canonical defect-owner Stage. Do not create a
Review receipt or repair map. The OPL StageRun controller materializes the
`opl_stage_review_receipt` from this Attempt's identity, session, exact reviewed
hashes, rubric, and verdict.

If the verdict is `repair_required`, return only a route recommendation when the
defect belongs elsewhere; the controller continues the quality loop. When this
reviewer terminalizes the StageRun with a consumable pass, quality-debt, or
route-back result, it is the decisive Attempt and returns the route decision.

## Repairer

Consume the exact reviewed artifact, finding refs, repair expectations,
acceptance criteria, source/rubric refs, and necessary lineage. Produce a new
artifact generation plus a repair map keyed by every accepted `finding_id`;
each entry records repair status, changed artifact refs, and repair evidence.
Do not reuse the reviewer session, close findings, or claim that the repair
passed. A repairer never makes a terminal route decision; when repair cannot stay
inside the inherited Stage boundary, return only a route recommendation for the
fresh re-reviewer to judge.

## Re Reviewer

In a fresh session, review the exact repaired artifact hashes against the prior
findings, repair map, original source/rubric refs, and unresolved acceptance
criteria. Return `closed`, `partially_closed`, or `still_open` for every stable
`finding_id`, plus the verdict, evidence, and remaining quality debt. Only an
unclosed required finding, repair regression, or critical new finding may
trigger another repair round; ordinary new suggestions are optional observations
or quality debt and cannot reopen the loop. Never inherit the repairer
conversation or create the controller-owned Review receipt.

When another repair round is required and remains available, return only a route
recommendation. When this re-reviewer terminalizes the StageRun, it is the
decisive Attempt and returns the route decision.
