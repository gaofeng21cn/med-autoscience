# Finalize And Publication Handoff Prompt

Owner: MedAutoScience
Stage id: finalize_and_publication_handoff
Machine boundary: this prompt prepares an internal publication handoff. External
submission, credentials, PI strategy, and irreversible delivery remain human
authority.

## Objective

Mechanically package exact already-reviewed refs and hashes into a current,
inspectable handoff. Preserve byte identity from accepted evidence, independent
Stage Review, cross-Stage Meta Review, and artifact authority. Keep this
inspection handoff distinct from quality, ready, acceptance, and external
submission decisions.

## Quality Cycle

This Stage uses one primary Attempt. Same-thread deterministic checks are
`in_thread_refinement` only; this Stage does not start reviewer, repairer, or
re-reviewer Attempts and cannot emit a new Review receipt. Its inputs must
already carry exact independent Stage Review and Meta Review refs for the same
canonical bytes. The producer is therefore the decisive cross-Stage route owner
for a progress-terminal result in this StageRun; it may select any Stage declared
by the manifest, while OPL only validates role eligibility and target identity.
Under a hard boundary or literal zero consumable handoff artifact, return no
route output.

## Good Work

- Consume current independent review, source readiness, controller decision,
  journal requirement, canonical manuscript, artifact, and package refs.
- Use `medical_research_execution.md` only to interpret existing specialist,
  review, and submission refs; never start writing, analysis, table/figure, or
  citation repair inside this Handoff.
- Produce only deterministic inspection packaging, manifests, hashes, and
  refs-only handoff receipts over those exact already-reviewed bytes.
- When content, figure, table, analysis, citation, source, or current-package
  bytes need to change, route back to the earliest owning Stage. Any new bytes
  must complete that Stage's fresh Review and re-enter cross-Stage Meta Review
  before this Handoff can consume them.
- Treat publication quality, package freshness, handoff readiness, submission
  readiness, and external submission as separate states.
- Require a human gate before journal/PI strategy changes, credentials or portal
  actions, irreversible delivery, or external submission.

## Boundaries

This Stage never mutates canonical source, manuscript, figure, table, analysis,
or `current_package` bytes and never rebuilds a changed publication artifact.
It cannot inherit review from stale bytes. Generated bundles, upload readiness,
specialist candidates, package freshness, provider completion, and tests cannot
authorize publication, acceptance, or submission. An executor packet cannot
write publication eval, controller decisions, owner receipts, blockers, human
gates, or artifact authority.

## Handoff

Produce the best consumable inspection handoff delta. Return a
`publication_handoff_admission_packet` binding exact reviewed artifact hashes,
source, controller, canonical-source, freshness, journal, package, Meta Review,
and human-gate refs plus the proposed next owner. The packet is only a gate
input; downstream MAS/human owners retain acceptance and every quality,
publication, submission, or ready claim.

A usable internal handoff may close as `completed_with_quality_debt`; record the
debt and block publication/submission-ready claims. When no consumable handoff
exists, materialize an exact-ref-and-hash no-output diagnostic and select the
earliest owning declared Stage only when that diagnostic is itself consumable and
work can continue. Literal zero handoff and diagnostic artifact returns a typed
blocker and no route output. Return a progress-terminal selection as
`route_impact.stage_route_decision` with a declared `target_stage_id` and
non-empty `evidence_refs`, or use `decision_kind=complete` without a target when
the handoff legitimately closes the graph. Typed blockers and human gates are
reserved for real authority, identity/currentness, credential/safety,
irreversible-action, unavailable-executor, explicit human-decision, or literal
zero-consumable-artifact boundaries; they return no route output.
