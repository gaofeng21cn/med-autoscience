# Owner Receipt And Route Control Skill Policy

Owner: MedAutoScience
Skill role: receipt, route-back, typed blocker, and human gate policy for MAS stage packets
Machine boundary: generated OPL surfaces may dispatch allowlisted MAS tasks and display refs. They cannot interpret medical quality, write domain truth, accept memory bodies, authorize artifact mutation, or mark submission readiness.

## Receipt Contract

Every mutating or decision-bearing path must emit a durable owner receipt. The receipt must identify:

- program_id, study_id, quest_id, and active_run_id when available.
- stage id, owner route, executor role, and whether the invocation was executor or reviewer/auditor.
- input refs read and output refs produced.
- source, evidence, review, artifact, publication, memory, and runtime refs affected or intentionally left unchanged.
- currentness basis relative to task intake, controller decision, manuscript/source refs, and artifact rebuild refs.
- next owner, next stage, or terminal blocker.

## Valid Route Outcomes

- `owner_receipt`: work produced current refs and a next owner or next stage.
- `typed_blocker`: work cannot proceed until a named authority gap is repaired.
- `route_back_request`: the current stage exposed a better owner or previous-stage repair.
- `human_gate_request`: PI, external source, journal strategy, scope expansion, or submission action is required.
- `no_op_with_currentness_proof`: all required refs were already current and no mutation was authorized.

## Typed Blocker Requirements

A typed blocker must name the blocker semantics, route-back owner, missing refs, stale refs if any, forbidden shortcut avoided, and repair condition. Use MAS gate vocabulary where applicable:

- `source_readiness_blocker`
- `artifact_mutation_blocker`
- `publication_quality_blocker`
- `ai_reviewer_quality_blocker`
- `publication_route_memory_writeback_blocker`
- methodology, claim-boundary, provenance, citation, journal-fit, or human-gate blocker when the stage contract needs a more specific repair.

## Route Control Rules

- Follow `owner_route`, controller decisions, and stage handoff refs; do not route by local convenience.
- Route back when a stage exposes source, evidence, method, claim, writing, artifact, memory, or review currentness gaps.
- Route forward only when the receipt contains current refs required by the next stage.
- Preserve failed-path and stop-loss evidence so later stages do not repeat invalid routes.
- Human gate blocks auto-advance only when the stage or authority boundary says external decision is required.

## Program And Materializer Boundary

Programs, validators, materializers, generated surfaces, and OPL-hosted descriptors may emit provenance/currentness receipts, artifact refs, schema validation results, or typed blockers. They must not emit pass/ready verdicts for publication quality, AI reviewer quality, source readiness, publication-route memory acceptance, artifact mutation, or submission readiness.

## Independence Boundary

Execution receipts and review/audit receipts are separate artifacts. The same invocation cannot execute work and then close the AI-first quality gate for that work. Missing independent reviewer/auditor record fails closed or routes back.
