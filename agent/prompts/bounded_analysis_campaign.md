# Bounded Analysis Campaign Prompt

Owner: MedAutoScience
Stage id: bounded_analysis_campaign
Default forward stage: manuscript_authoring
Machine boundary: this prompt directs bounded scientific analysis. Evidence
ledgers, study truth, runtime events, and owner receipts remain MAS-owned.

## Objective

Close the evidence gaps that matter to the active claim, reviewer concern, or
methodology route. Return reviewable evidence and its claim impact without
expanding the accepted study boundary.

## Quality Cycle

Produce the best analysis artifact for this attempt role. Same-thread checking
is `in_thread_refinement` only. Formal Review, repair, and re-review are separate
StageAttempts with fresh execution sessions under the declared quality-cycle
policy; never claim a Review receipt from this conversation.

## Good Work

- Before claim-bearing analysis, state the question, estimand or target quantity,
  accepted cohort/source/endpoint/comparator boundary, expected evidence gain,
  and stop or route-back condition.
- Choose the statistical, data-governance, literature, table, and figure methods
  that best answer the question. `medical_research_execution.md` owns specialist
  routing; the executor may iterate or parallelize where dependencies allow.
- Bind accepted results to current source, run, code/provenance, evidence, and
  claim-impact refs. Classify impact as confirm, weaken, refute, narrow,
  downgrade, stop, or route-back.
- Record weak, negative, failed, stale, or duplicate paths before retrying or
  selecting a replacement analysis, so unsuccessful routes remain reproducible
  evidence rather than disappearing from the campaign.
- Methods drafting and evidence interpretation may proceed iteratively. No
  substantive claim may outrun its accepted evidence refs.

## Boundaries

Do not add a primary claim, cohort, endpoint, comparator, validation target, or
methodology route without decision or human authority. Compute completion,
specialist candidates, prose, package freshness, and tests cannot close source,
methodology, evidence, or quality gates.

## Research Trajectory

Follow `research_trajectory_medical_narrative.md`. When a claim-relevant
validation completes, a positive, negative, null, mixed, or inconclusive result
is interpreted, or the hypothesis, route, or next research step changes, the
current MAS Attempt immediately updates
`artifacts/research_trajectory/TRAJECTORY.md` and
`artifacts/research_trajectory/snapshot.json` together. A failed execution is
recorded only when it materially changes the validation boundary, route, or next
step. Keep execution outcome, evidence interpretation, and route decision
separate; an execution failure does not negate the hypothesis.

Use medical Results and Discussion wording, preserve unsuccessful routes and
their pivot reasons, and make no inference beyond the cited evidence. Do not
update for tool calls, heartbeats, retries, or runtime activity without
scientific change. The write neither starts nor waits for independent review.
`research_trajectory_delta_ref` remains nullable v1 read compatibility and is
not the v2 write gate; the current v2 Stage output returns it as `null`.

## Immutable Review Input

This Stage has a MAS-fixed review binding: `manifest_scope=analysis_generation`
and `review_lane=statistical`. Once a producer has one complete frozen artifact
inventory, resolve the selected MAS checkout through the OPL-generated
interface and call
`finalize_bounded_analysis_producer_snapshot_closeout(...)`. Supply the
producer closeout candidate, exact analysis artifact records, generation id and
ref, and an explicit transport locator for every statistical-scope `member_id`.
Emit the returned `closeout_packet`; the finalizer verifies the
locator bytes, calls `build_stage_review_input_snapshot_bundle(...)`, and
injects both required transport surfaces. Do not recreate its authority record,
scope logic, or closeout injection in ad hoc JSON. A repairer uses the stage
bundle builder directly with its own fresh Attempt bindings.

Use the exact five `OPL_*` Attempt bindings supplied by Framework as
`authority_issuer`. Return the generated request at
`route_impact.stage_quality_cycle.review_input_snapshot_materialization_request`
and add its MAS owner-authority exact ref to
`closeout_packet.closeout_ref_metadata[]`. Generic `artifact_refs` are not the
member locator map. If any required manifest member, exact locator, or Attempt
binding is unavailable, omit the request and carry statistical-lane quality
debt; do not claim formal review or readiness. A zero-artifact or hard-boundary producer
must not call the finalizer or fabricate a snapshot.

## Handoff

Return `bounded_analysis_evidence_ready` with result, evidence-ledger,
claim-impact, failed-path, specialist-candidate, and next-owner refs. A usable
analysis delta may advance as `completed_with_quality_debt`; record the debt and
block promotion or ready claims. Route back to baseline for source/provenance
repair or to direction for claim or method changes. When no consumable delta is
produced, preserve the failed/negative path as a diagnostic and return an
evidence-backed route recommendation. Because this Stage uses formal Review,
only a terminal reviewer or re-reviewer selects the next declared Stage. A
reviewer may terminally route back before budget exhaustion only when the
narrowest canonical owner of required work is a different declared Stage;
same-Stage repair continues the quality loop. Typed blockers and human gates are
reserved for real hard boundaries.
