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

## Stage Use

Direction and baseline stages may generate or consume hypothesis portfolios to compare candidate study lines. Analysis, writing, review, and finalization stages may consume portfolio refs to explain why a path was selected, narrowed, rejected, or routed back.

Codex should cite candidate refs and evidence-pack refs it read, state whether ranking/proximity is advisory, and return an owner receipt, route-back request, human gate request, or typed blocker when the portfolio lacks required refs.
