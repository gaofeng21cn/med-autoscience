# Finalize And Publication Handoff Policy

This stage performs publication handoff after current quality, artifact, source, and journal refs are available. It distinguishes internal handoff readiness from external submission. Artifact mutation needs MAS artifact authority and rebuild proof; external journal submission remains under human supervision.

Formal Stage Review follows `contracts/stage_quality_cycle_policy.json`: the
reviewer is a new StageAttempt and execution session in this StageRun, consumes
only declared artifact/source/rubric refs, and inherits no producer conversation.
Checking inside the producer thread is `in_thread_refinement`, not Review.

When a change is required, preserve the professional dependency: obtain MAS
mutation authority, mutate canonical source, rebuild derived artifacts/package,
obtain fresh proof and risk-matched independent review for the rebuilt bytes,
then issue the internal handoff. Already-current refs may be reused. A handoff
packet is required before a quality or ready claim, not as the first stage action.

Stage throughput requires a reviewable delta or an evidence-backed blocker. Currentness-only, record-only, or provider-completed-only closeout cannot satisfy the stage unless it names the consumed no-op evidence and forced next target surface. Human gate requests must carry the decision boundary, evidence refs, blocking reason, and resume target surface.

A consumable internal handoff may close as `completed_with_quality_debt`; debt
blocks publication/submission-ready claims. External submission, credentials,
portal actions, and irreversible delivery always require the human authority
declared by the route.
