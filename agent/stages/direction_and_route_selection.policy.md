# Direction And Route Selection Policy

This stage owns medical route selection semantics. It must read study charter, source readiness refs, literature coverage, publication-route memory refs, and controller state before recommending a route. It may produce candidate routes, rejected routes, stop or pivot recommendations, and owner-route evidence. It cannot authorize publication quality, source readiness, artifact mutation, or submission readiness.

Formal Stage Review follows `contracts/stage_quality_cycle_policy.json`: the
reviewer is a new StageAttempt and execution session in this StageRun, consumes
only declared artifact/source/rubric refs, and inherits no producer conversation.
Checking inside the producer thread is `in_thread_refinement`, not Review.

Data-feasibility exploration may inform and revise direction selection; the
professional method is iterative rather than a fixed tool sequence. Before
claim-bearing work begins, the accepted route must still state the study and
claim boundary. Rejected and negative routes are recorded before a replacement
route is launched.

When a hypothesis portfolio is present, candidate selection must inspect assumption and sub-assumption decomposition, support and contradiction refs, novelty and source-provenance refs, testability and safety refs, negative failed-path refs, and independent reviewer or human-gate receipt refs. Ranking, tournament, proximity, debate, or evolution signals are advisory ordering signals only; route authority remains MAS owner route plus reviewer/human receipts where required.

Stage throughput requires a reviewable delta or an evidence-backed blocker. Currentness-only, record-only, or provider-completed-only closeout cannot satisfy the stage unless it names the consumed no-op evidence and forced next target surface. Human gate requests must carry the decision boundary, evidence refs, blocking reason, and resume target surface.
