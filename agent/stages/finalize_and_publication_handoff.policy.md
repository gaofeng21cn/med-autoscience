# Finalize And Publication Handoff Policy

This stage mechanically packages exact already-reviewed artifact bytes after current quality, Meta Review, source, artifact, and journal refs are available. It may produce an inspection archive, manifest, hashes, and refs-only handoff receipt, but it does not freeze or mutate canonical bytes and does not issue a quality, publication, submission, or ready claim. Downstream MAS and human owners retain acceptance and external-submission authority.

This Stage has one primary Attempt under
`contracts/stage_quality_cycle_policy.json`. Deterministic checking inside that
Attempt is `in_thread_refinement`, not Review. The Handoff consumes exact
artifact hashes and existing independent Stage Review and cross-Stage Meta
Review receipts; it creates no reviewer, repairer, or re-reviewer Attempt.
Its authority input is a `publication_generation` manifest, never a weaker
manuscript scope, and includes exact DOCX, PDF, supplement, ZIP allowlist, and
ZIP member records. Medical, statistical, reference, display, publication, and
exact-byte-package lane receipts must all be current and exact-byte bound.
The same generation must contain exactly one submission status, publication
evaluation, next-action envelope, and submission projection manifest. The
projection manifest binds the complete submission tree by relative path, byte
size, and SHA-256 and names `STATUS.json` plus
`audit/submission_manifest.json` as completion markers.

After MAS returns a generation-bound artifact projection authorization, OPL
must materialize the owner-prepared tree through
`opl_pack_materialize_artifact_projection`. It validates a sibling staging tree
before switching the canonical target and restores the prior target on
failure. Neither OPL nor the transport receipt may create or reinterpret MAS
status, publication evaluation, next action, quality, or submission authority.
Direct incremental writes into a preferred submission root are forbidden.

When any content or current-package byte must change, return a route-back to the
earliest owning Stage instead of repairing here. The new generation refreshes
every affected v2 lane; an unchanged lane carries forward only through a
MAS-owned currentness receipt with identical scope policy, rubric, identity, and
origin provenance. The resulting current cross-Stage Meta Review must return
before this Handoff consumes the generation. A handoff packet only transports
the resulting exact refs; it cannot authorize acceptance or a quality/ready
claim.

A consumable internal handoff may close as `completed_with_quality_debt`; debt
blocks publication/submission-ready claims. External submission, credentials,
portal actions, and irreversible delivery always require the human authority
declared by the route.
