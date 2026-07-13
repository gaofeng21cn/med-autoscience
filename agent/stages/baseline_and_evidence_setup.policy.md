# Baseline And Evidence Setup Policy

This stage establishes source, cohort, endpoint, comparator, and baseline support for the selected study line. Source readiness is a MAS authority verdict backed by study charter, source provenance, and evidence refs. OPL may consume locator metadata only. A baseline that changes the claim boundary must route to decision or human gate.

Formal Stage Review follows `contracts/stage_quality_cycle_policy.json`: the
reviewer is a new StageAttempt and execution session in this StageRun, consumes
only declared artifact/source/rubric refs, and inherits no producer conversation.
Checking inside the producer thread is `in_thread_refinement`, not Review.

A versioned baseline and accepted source/claim boundary are required before an
analysis result is accepted as claim-bearing evidence. Exploratory feasibility
work may happen earlier and may revise the route, but it does not satisfy this
dependency by itself.

For hypothesis portfolio inputs, this stage must preserve candidate assumptions, sub-assumptions, supporting and contradicting evidence refs, novelty/source provenance refs, testability/safety refs, and negative failed-path refs as body-free evidence-pack refs. Advisory ranking or proximity cannot suppress failed evidence, missing source readiness, independent reviewer requirements, or human gate boundaries.

Stage throughput requires a reviewable delta or an evidence-backed blocker. Currentness-only, record-only, or provider-completed-only closeout cannot satisfy the stage unless it names the consumed no-op evidence and forced next target surface. Human gate requests must carry the decision boundary, evidence refs, blocking reason, and resume target surface.
