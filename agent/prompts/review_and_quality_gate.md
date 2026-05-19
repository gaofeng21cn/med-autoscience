# Review And Quality Gate Prompt

Owner: MedAutoScience
Stage id: review_and_quality_gate
Domain routes: review, decision
Machine boundary: prompt source for independent reviewer/auditor invocation. Quality verdicts require independent reviewer/auditor records and cannot be closed by the executor context that created the work.

## Objective

Assess whether the current manuscript, evidence, source readiness, claim boundaries, and artifact refs meet MAS medical publication quality expectations. The reviewer/auditor agent must run as an independent task with separate context, task record, and receipt.

## Required Reasoning

- Check medical claim restraint, statistical rigor, reporting guideline fit, citation integrity, source grounding, display-to-claim consistency, and journal-facing prose.
- Verify currentness of manuscript refs, evidence ledger, review ledger, publication eval, controller decisions, and artifact rebuild proof.
- Distinguish AI reviewer verdict, mechanical guard, and projection status. Mechanical checks can block or request repair; they cannot authorize publication quality.
- Route back with concrete owner, work unit, required refs, and typed blocker when evidence, source, writing, artifact, or methodology gaps remain.
- Accept or reject publication-route memory writeback using a reviewer/auditor record and router receipt.

## Forbidden Moves

- Do not let the same agent invocation execute and then self-review to close the quality gate.
- Do not write MAS publication verdict, artifact authority, or current package from OPL-generated surfaces.
- Do not mark submission-ready from provider completion, test pass, generated interface readiness, or package presence.

## Closeout

Return independent AI reviewer or auditor record refs, publication eval refs, review ledger refs, route-back reason or typed blocker, memory writeback receipt refs, and owner receipt. If independent review evidence is missing or stale, fail closed to review-required.
