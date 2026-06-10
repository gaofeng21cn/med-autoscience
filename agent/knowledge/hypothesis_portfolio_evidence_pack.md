# Hypothesis Portfolio Evidence Pack

Owner: MedAutoScience
Knowledge role: MAS-owned hypothesis portfolio and evidence-pack consumption model
Machine boundary: this file defines semantic requirements for stage packs and generated descriptors. It is not a hypothesis ledger, evidence ledger, quality verdict, publication authority, or artifact authority surface.

## Portfolio Object

A MAS hypothesis portfolio is a refs-first research object for choosing and auditing study directions. It may include Co-Scientist-inspired generation, reflection, ranking, evolution, proximity, and meta-review signals, but those signals are advisory inputs only.

Each hypothesis candidate must carry:

- candidate id, study or quest scope, route stage, and currentness basis.
- explicit assumption and sub-assumption decomposition.
- supporting evidence refs and contradicting evidence refs.
- novelty refs, source provenance refs, and prior-art boundary.
- testability plan refs, safety or risk refs, and feasibility constraints.
- negative or failed-path refs when an idea has already failed, narrowed, or been rejected.
- ranking, proximity, debate, or tournament refs marked as advisory.
- independent reviewer, auditor, human gate, or owner receipt refs when the candidate is promoted, rejected, paused, or routed.

## Authority Rules

MAS owns hypothesis semantics, evidence interpretation, novelty/provenance acceptance, testability and safety judgment, failed-path ledger interpretation, route selection, quality verdict, publication readiness, artifact authority, owner receipts, and typed blockers.

OPL may index, transport, display, and project hypothesis candidate refs, evidence refs, advisory ranking refs, proximity refs, receipt refs, and blocker refs. OPL cannot write hypothesis truth, promote evidence, accept novelty, declare testability/safety, rank a candidate as a route authority, close an independent review gate, authorize publication quality, or mutate artifacts.

## Ranking And Proximity

Ranking, tournament, Elo-like, proximity, debate, and evolution signals are useful for exploration ordering and reviewer workload shaping. They never replace:

- current study charter and route decision authority.
- source readiness and evidence ledger currentness.
- independent reviewer/auditor gate record.
- human gate receipt when PI, safety, scope, or irreversible choice is involved.
- MAS owner receipt or typed blocker.

If a ranked candidate lacks supporting or contradicting evidence refs, provenance refs, failed-path refs, or reviewer/human gate refs required by the route, fail closed with a typed blocker naming the missing ref family.

## Progress-First JIT Affordance Strategy

Co-Scientist-inspired portfolio work is a current-owner-native JIT affordance, not a standing progress enhancement layer and not a new admission or gate authority. It may rank the next owner delta, generate reviewer repair hints, or write one reusable refs-only lesson only when the current owner action, owner route, route-back, typed blocker, reviewer/publication gate, human gate, or stop-loss decision explicitly requests that ref family, briefing, repair question, or arbitration need.

The JIT mechanisms are:

- next-delta tournament: compare candidate next-owner deltas once per attempt and return advisory ordering refs.
- bounded micro-candidate generation: generate at most three candidates for the immediate next delta, repair hint, or reusable lesson.
- critique-as-repair-hint: turn critique into actionable repair-hint refs for the next executor or independent reviewer.
- reusable lesson extraction: preserve at most one reusable lesson ref for the explicitly invoked current-owner need, with no evidence, memory, artifact, or manuscript body copied into the handoff.
- triggered meta-review: run only for stop-loss, repeated failure, human gate, claim-boundary drift, or exhausted no-loop budget.
- opportunistic knowledge prefetch: prefetch source, evidence, failed-path, reviewer concern, or journal-neighbor refs only when it does not delay the declared owner dispatch.

These signals cannot admit a route, close an AI reviewer or artifact/source gate, promote a stage, authorize publication/submission readiness, generate a default next owner, or mutate study truth, artifacts, memory, or current package state. Missing JIT affordance refs should be skipped unless the route-required evidence refs are actually absent, in which case the route emits the normal typed blocker.

## Stage Use

Direction and baseline stages may generate or consume hypothesis portfolios to compare candidate study lines. Analysis, writing, review, and finalization stages may consume portfolio refs to explain why a path was selected, narrowed, rejected, or routed back.

Codex should cite candidate refs and evidence-pack refs it read, state whether ranking/proximity is advisory, and return an owner receipt, route-back request, human gate request, or typed blocker when the portfolio lacks required refs.
