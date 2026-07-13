# Artifact Source Authority Gate

Owner: MedAutoScience
Gate role: AI-first record validator for source readiness and artifact mutation authority
Machine boundary: this gate protects canonical paper sources, source readiness, current package, delivery package, and publication handoff. It cannot be closed by file presence, program success, generated surfaces, or package freshness.

## Source Readiness Record

A source-readiness decision requires current refs for:

- study charter and active claim boundary.
- source locator, source provenance, and source body ownership.
- cohort, endpoint, exposure/model target, comparator, measurement window, and missingness assumptions.
- hypothesis candidate assumptions, sub-assumptions, support/contradiction evidence refs, novelty/source provenance refs, testability/safety refs, and negative failed-path refs when source readiness depends on a hypothesis portfolio.
- evidence or baseline refs that depend on the source.
- reviewer/auditor or authority receipt when the gate contract requires independent review.

Missing or stale refs prevent a source-ready claim and route the gap to source intake, study design, baseline/evidence setup, or methodology reframe. Zero consumable delta emits a progress diagnostic. Emit `source_readiness_blocker` only for wrong-target identity/currentness, authority/safety, irreversible-action, unavailable-executor, or explicit human-decision boundaries; ordinary gaps remain quality debt.

## Artifact Mutation Record

Artifact mutation authorization requires current refs for:

- canonical manuscript/source refs.
- figure/table/supplement/response refs affected by the mutation.
- artifact rebuild proof current relative to source, evidence, review, and task intake.
- artifact authority owner receipt.
- package/materialization refs produced from canonical sources.

Missing or stale refs prevent artifact authorization and route the gap to artifact rebuild, source revision, manuscript authoring, review, or human gate. Emit `artifact_mutation_blocker` when mutation cannot proceed safely; a non-mutating consumable delta may still advance with quality debt.

## AI-First Authority Boundary

Artifact and source authority gates are provenance floors plus medical judgment boundaries. A complete checklist may request review, rebuild, or handoff; it cannot suppress unresolved concerns about claim support, scientific meaning, reader interpretation, source limitations, or publication quality.

## Program And Materializer Boundary

Programs and materializers may validate schema/currentness, materialize artifacts, rebuild packages, and emit receipts or blockers. They cannot mark source-ready, artifact-authorized, publication-ready, medical-ready, or submission-ready. Materializer success without an authority receipt is only a materialization ref.

## OPL Projection Boundary

OPL generated surfaces may carry locator metadata, status projections, dispatch receipts, and body-free refs. They cannot read source body as truth, accept memory body, authorize artifact mutation, write `current_package`, mark source-ready, or mark submission-ready.

## Required Blocker Shape

Every blocker must include blocker type, missing refs, stale refs, affected source or artifact, route-back owner, required repair, and forbidden shortcut avoided. If the authority record is missing, fail the ready or mutation claim rather than projecting ready state. Do not convert that claim failure into a stage blocker when a safe, non-authoritative, consumable delta with explicit debt can still be handed forward.
