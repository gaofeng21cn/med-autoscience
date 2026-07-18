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
