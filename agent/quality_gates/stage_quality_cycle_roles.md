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

Use the controller-provided `quality_round_index`, `max_repair_rounds`, current
`stage_id`, declared Stage targets, and exact artifact identity to choose one
branch:

- `same_stage_repair_required`: when the current Stage is the narrowest
  canonical owner of the required repair and another repair round remains, a
  reviewer or re-reviewer returns outcome `repair_required` and at most
  `route_impact.stage_route_recommendation`. This branch is non-terminal; the
  controller creates the next fresh repairer Attempt.
- `cross_stage_route_back_before_budget_exhaustion`: when the narrowest canonical
  owner of required work is a different declared Stage, a reviewer or
  re-reviewer may end the current StageRun before budget exhaustion. Return outcome
  `repair_required` plus exactly one `route_impact.stage_route_decision` with
  `decision_kind=route_back`, a `target_stage_id` different from the current
  Stage, and non-empty `evidence_refs` binding the finding and owner diagnosis.
  This is the only terminal route allowed before repair-budget exhaustion for
  outcome `repair_required`; the controller validates and materializes the
  route-back instead of creating an in-Stage repairer.
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

Review transport uses that same quality-cycle envelope. A producer or repairer
with a normalized v2 generation manifest, one controller-bound MAS review lane,
and an explicit `source_refs_by_member_id` map covering exactly that lane's
MAS-owned scope returns
`route_impact.stage_quality_cycle.review_input_snapshot_materialization_request`.
Build it with
`build_review_input_snapshot_materialization_request(...)`; never infer the map
from generic artifact refs or choose a different lane. Pass
`authority_issuer` from the exact `OPL_STAGE_ATTEMPT_REF`,
`OPL_EXECUTION_CONTENT_BINDING_SHA256`, `OPL_PACKAGE_USE_BOUNDARY_ID`,
`OPL_ROOT_PACKAGE_ID`, and `OPL_ROOT_PACKAGE_CONTENT_DIGEST` Attempt
environment bindings; never synthesize or reuse them across Attempts. The
request carries only the canonical MAS `owner_authority_ref`, producer Attempt
binding, explicit transport locators, hashes, and sizes. Lane, scope, role, and
owner refs remain in MAS-owned records and are opaque to Framework. Copy the
same four-field `owner_authority_ref` object into
`closeout_packet.closeout_ref_metadata[]`; use `ref`, not the legacy `uri` spelling.
If the exact
map is unavailable, do not invent a request: record lane quality debt and
continue the hosted action without a quality, publication, export, submission,
or ready claim. Once you return a request, every member identity, locator, hash,
and size is an exact claim. An invalid,
out-of-workspace, mismatched, or unmaterializable present request fails closed
as a transport contract error; never relabel it as ordinary quality debt or
forge a MAS typed blocker. A reviewer or re-reviewer that receives a
`scholarskills_page_hash_evidence_candidate` returns it unchanged at
`route_impact.stage_quality_cycle.page_hash_evidence_candidate`, declares
`page_hash_evidence_candidate_package_id=mas-scholar-skills`, and returns the
candidate's exact origin ref as `page_hash_evidence_origin_ref`. Framework
persists the opaque candidate and may issue only a generic artifact receipt;
the same four-field origin exact ref must also appear in
`closeout_packet.closeout_ref_metadata[]`. Neither object is a MAS verdict or
authority.

## Producer

Use the Stage goal, policy, sources, and quality definition to produce the best
consumable artifact. You may check and improve your work in this thread, but that
is `in_thread_refinement`; return artifact refs/hashes and never a Review receipt.
The producer is decisive only in a primary-only StageRun when the result is
progress-terminal. In a StageRun with
formal Review, return at most an evidence-backed route recommendation and leave
the terminal decision to the reviewer or re-reviewer. Under
`hard_boundary_or_zero_artifact`, return no route output.

For formal Review, use the stage-bound MAS manifest scope and review lane. When
the Stage declares a producer attempt-local snapshot finalizer, call that
finalizer with the closeout candidate, frozen artifact inventory, and explicit
`source_refs_by_member_id` map; emit its returned closeout packet. Otherwise,
call `build_stage_review_input_snapshot_bundle(...)` directly.
Never derive that map from generic artifact refs or choose an unbound lane.
Bind snapshot authority to the exact
`OPL_STAGE_ATTEMPT_REF`, `OPL_EXECUTION_CONTENT_BINDING_SHA256`,
`OPL_PACKAGE_USE_BOUNDARY_ID`, `OPL_ROOT_PACKAGE_ID`, and
`OPL_ROOT_PACKAGE_CONTENT_DIGEST` values supplied to this Attempt. Return the
resulting request at
`route_impact.stage_quality_cycle.review_input_snapshot_materialization_request`
and append its owner-authority exact-ref entry to
`closeout_packet.closeout_ref_metadata[]`. If the exact manifest inventory,
locator map, or controller-bound lane is unavailable, omit the request, record
lane quality debt, and make no quality or readiness claim. Never call a
snapshot finalizer for a zero-artifact or hard-boundary producer.

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

When ScholarSkills returns a page-hash evidence candidate, pass the exact
candidate through at the declared quality-cycle path without rewriting it or
turning it into a finding, verdict, blocker, or readiness claim. Declare the
candidate package and origin exact ref in the sibling fields above so Framework
does not parse the ScholarSkills payload.

While repair budget remains and the repair belongs to this Stage, an outcome of
`repair_required` is non-terminal and returns at most a route recommendation.
This is `same_stage_repair_required`. If the narrowest canonical owner is a
different declared Stage, follow
`cross_stage_route_back_before_budget_exhaustion`; this reviewer becomes the
decisive Attempt for that terminal route-back. At final consumable budget, keep
outcome `repair_required` and follow `final_budget_consumable`. A hard-boundary
reviewer returns no route output.

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

When the repaired generation will enter formal re-review, rebuild its v2
generation manifest and call `build_stage_review_input_snapshot_bundle(...)`
with the inherited controller-bound lane, an explicit exact
`source_refs_by_member_id` map, and this repair Attempt's five `OPL_*` authority
bindings. Return the new snapshot materialization request at the canonical
quality-cycle path and append its `required_closeout_ref_metadata` entry to
`closeout_packet.closeout_ref_metadata[]`. Never reuse the producer request or
authority issuer. Missing exact inputs remain lane quality debt; do not guess or
forge a request.

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

When ScholarSkills returns a page-hash evidence candidate, pass the exact
candidate through at the declared quality-cycle path under the same
non-authority and fresh-review requirements as the initial reviewer.

When another repair round is required, remains available, and belongs to this
Stage, return only a route recommendation. This is
`same_stage_repair_required`. If the narrowest canonical owner is a different
declared Stage, follow `cross_stage_route_back_before_budget_exhaustion`; this
re-reviewer becomes the decisive Attempt for that terminal route-back. On the
final consumable round, keep outcome `repair_required` and return the route
decision for controller-classified terminal quality debt. A hard-boundary
re-reviewer returns no route output.
