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
- Accept only a `publication_generation` manifest. It must contain exact DOCX,
  PDF, supplementary output, ZIP allowlist, and ZIP member records, plus current
  medical, statistical, reference, display, publication, and exact-byte-package
  review receipts authorized by the same MAS review-currentness receipt.
- Require that the same `publication_generation` also binds exactly one
  `submission_status`, `publication_evaluation`, `next_action_envelope`, and
  `submission_projection_manifest`. These are one generation of user-visible
  state; a current package with stale status, evaluation, or next action is not
  a consumable handoff.
- After the MAS owner receipt authorizes artifact projection, publish the
  complete owner-prepared submission tree only through
  `opl_pack_materialize_artifact_projection`. The projection manifest must list
  every file by path, size, and SHA-256 and include `STATUS.json` and
  `audit/submission_manifest.json` as completion markers. Never populate the
  preferred root incrementally.
- When content, figure, table, analysis, citation, source, or current-package
  bytes need to change, route back to the earliest owning Stage. The new
  generation must refresh every affected v2 review lane and may reuse an
  unchanged lane only through the MAS-owned currentness receipt with identical
  scope policy, rubric, identity, and origin provenance. The resulting current
  cross-Stage Meta Review must be present before this Handoff can consume it.
- Treat publication quality, package freshness, handoff readiness, submission
  readiness, and external submission as separate states.
- Require a human gate before journal/PI strategy changes, credentials or portal
  actions, irreversible delivery, or external submission.

## Boundaries

This Stage never mutates canonical source, manuscript, figure, table, analysis,
or already-reviewed `current_package` bytes and never rebuilds a changed
publication artifact. MAS owner code may prepare generation-bound status,
evaluation, next-action, and projection-manifest bytes; OPL may only transport
those exact authorized bytes as one tree.
It cannot downgrade to a manuscript-generation scope or inherit review from
stale bytes. Generated bundles, upload readiness,
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
