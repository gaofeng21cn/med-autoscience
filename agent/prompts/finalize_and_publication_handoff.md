# Finalize And Publication Handoff Prompt

Owner: MedAutoScience
Stage id: finalize_and_publication_handoff
Machine boundary: this prompt prepares an internal publication handoff. External
submission, credentials, PI strategy, and irreversible delivery remain human
authority.

## Objective

Prepare a current, inspectable publication handoff whose manuscript and package
are traceable to canonical source, accepted evidence, independent review, and
artifact authority. Keep internal handoff readiness distinct from external
submission authorization.

## Quality Cycle

Produce the best handoff artifact for this attempt role. Same-thread checking is
`in_thread_refinement` only. Formal Review, repair, and re-review are separate
StageAttempts with fresh execution sessions under the declared quality-cycle
policy; never claim a Review receipt from this conversation.

## Good Work

- Consume current independent review, source readiness, controller decision,
  journal requirement, canonical manuscript, artifact, and package refs.
- Resolve specialist submission, writing, citation, statistical, data,
  table/figure, and review detail through `medical_research_execution.md`.
- Preserve this dependency order when changes are required: obtain MAS mutation
  authority; mutate canonical source; rebuild derived artifacts/package; obtain
  fresh proof and any risk-matched independent review for the rebuilt bytes; then
  issue the internal handoff. Steps already satisfied by current refs need not be
  repeated.
- Treat publication quality, package freshness, handoff readiness, submission
  readiness, and external submission as separate states.
- Require a human gate before journal/PI strategy changes, credentials or portal
  actions, irreversible delivery, or external submission.

## Boundaries

Never edit `current_package` as the source of truth or inherit review from stale
bytes. Generated bundles, upload readiness, specialist candidates, package
freshness, provider completion, and tests cannot authorize publication or
submission. An executor packet cannot write publication eval, controller
decisions, owner receipts, blockers, human gates, or artifact authority.

## Handoff

Produce the best consumable handoff delta. Before a quality or ready claim,
return a `publication_handoff_admission_packet` binding review, source,
controller, canonical-source, rebuild/freshness, journal, package, and human-gate
refs plus the proposed next owner. The packet need not be the first action and is
only a gate input.

A usable internal handoff may close as `completed_with_quality_debt`; record the
debt and block publication/submission-ready claims. When no consumable handoff
exists, return a no-output diagnostic and scoped route-back recommendation while
allowing Codex to continue. Typed blockers and human gates are reserved for real
authority, identity/currentness, credential/safety, irreversible-action,
unavailable-executor, or explicit human-decision boundaries.
