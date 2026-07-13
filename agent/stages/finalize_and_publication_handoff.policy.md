# Finalize And Publication Handoff Policy

This stage mechanically packages exact already-reviewed artifact bytes after current quality, Meta Review, source, artifact, and journal refs are available. It may produce an inspection archive, manifest, hashes, and refs-only handoff receipt, but it does not freeze or mutate canonical bytes and does not issue a quality, publication, submission, or ready claim. Downstream MAS and human owners retain acceptance and external-submission authority.

This Stage has one primary Attempt under
`contracts/stage_quality_cycle_policy.json`. Deterministic checking inside that
Attempt is `in_thread_refinement`, not Review. The Handoff consumes exact
artifact hashes and existing independent Stage Review and cross-Stage Meta
Review receipts; it creates no reviewer, repairer, or re-reviewer Attempt.

When any content or current-package byte must change, return a route-back to the
earliest owning Stage instead of repairing here. The changed bytes must complete
that Stage's fresh Review and re-enter cross-Stage Meta Review before returning
to this Handoff. A handoff packet only transports the resulting exact refs; it
cannot authorize acceptance or a quality/ready claim.

Stage throughput requires a reviewable delta or an evidence-backed blocker. Currentness-only, record-only, or provider-completed-only closeout cannot satisfy the stage unless it names the consumed no-op evidence and forced next target surface. Human gate requests must carry the decision boundary, evidence refs, blocking reason, and resume target surface.

A consumable internal handoff may close as `completed_with_quality_debt`; debt
blocks publication/submission-ready claims. External submission, credentials,
portal actions, and irreversible delivery always require the human authority
declared by the route.
