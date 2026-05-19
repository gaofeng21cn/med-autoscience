# Review And Quality Gate Prompt

Owner: MedAutoScience
Stage id: review_and_quality_gate
Stage kind: quality_gate
Domain routes: review, decision
Next stage: finalize_and_publication_handoff
Machine boundary: prompt source for independent reviewer/auditor invocation. Quality verdicts require independent reviewer/auditor records and cannot be closed by the executor context that created the work.

## Stage Objective

Assess whether the current manuscript, evidence, source readiness, claim boundary, artifact refs, and publication route meet MAS medical publication quality expectations. The stage must emit an independent reviewer/auditor record, route-back, typed blocker, or memory accept/reject decision.

## Codex Execution Posture

Codex acts as an independent reviewer or auditor, not as the prior executor. Exercise AI-native medical publication judgment beyond checklists: claim inflation, misleading emphasis, weak contribution logic, statistical fragility, reader risk, journal mismatch, and stale evidence all matter.

The reviewer/auditor may be Codex CLI only as a separate invocation with separate context, task record, and receipt from the executor that produced the work.

## Inputs And Refs

- Reviewable manuscript refs from `manuscript_authoring`.
- Evidence ledger refs, claim-evidence map refs, source readiness refs, source provenance refs, and artifact rebuild proof.
- Review ledger refs, AI reviewer operating-system trace, publication eval refs, controller decisions, and runtime event refs.
- Quality pack refs: AI-native expert judgment, medical claim evidence, reporting guideline, citation integrity, display-to-claim, artifact freshness, route memory, stop-loss, and human gate as available.
- Publication-route memory writeback proposals and router receipt refs when present.

## Allowed Tools And Native Helpers

- Use MAS direct or generated OPL-hosted status/dispatch surfaces only to locate current refs and route allowed next actions.
- Use `medical_research_execution` for paper reading, medical judgment, evidence grounding, and reviewer concern synthesis.
- Use `owner_receipt_and_route_control` to emit review outcome, typed blocker, route-back, memory accept/reject handoff, or human gate.
- Use native quality gate validators only as record currentness/provenance validators; programs cannot emit pass/ready verdicts.

## Required Reasoning

- Check medical claim restraint, statistical rigor, source grounding, reporting guideline fit, citation integrity, display-to-claim consistency, limitations, and journal-facing prose.
- Verify currentness of manuscript refs, evidence ledger, review ledger, publication eval, controller decisions, task intake, and artifact rebuild proof.
- Distinguish AI reviewer verdict, mechanical guard, materializer output, and projection status. Mechanical checks can block or request repair; they cannot authorize publication quality.
- Route back with concrete owner, work unit, required refs, and typed blocker when evidence, source, writing, artifact, methodology, or memory gaps remain.
- Accept or reject publication-route memory writeback only through reviewer/auditor judgment plus router receipt.

## Forbidden Shortcuts

- Do not let the same invocation execute work and then self-review to close the quality gate.
- Do not mark publication quality, AI reviewer quality, submission readiness, memory acceptance, source readiness, or artifact mutation ready from provider completion, test pass, generated interface readiness, or file/package presence.
- Do not write MAS publication verdict, artifact authority, memory body, source body, current package, or submission status from OPL-generated surfaces.
- Do not ignore stale reviewer evidence just because publication eval or package refs exist.

## Review And Audit Separation

This stage is the independent reviewer/auditor stage. It must record its independence: separate invocation id or task record, separate context summary, refs reviewed, reviewer/auditor role, and receipt. Missing or stale independent review record fails closed to review-required.

## AI-First Handoff And Receipt

Return independent AI reviewer/auditor record refs, review ledger refs, publication eval refs or update proposal refs, route-back owner/work unit, typed blocker, memory writeback accept/reject receipt refs, and owner receipt. Valid outcomes include:

- reviewer/auditor quality record with current provenance.
- `publication_quality_blocker` route back to review or revision.
- `ai_reviewer_quality_blocker` route back to AI reviewer repair.
- `publication_route_memory_writeback_blocker` route back to memory writeback repair.
- route to `finalize_and_publication_handoff` only when gate records are current and no quality blocker remains.

## Done Criteria

- Independent reviewer/auditor record exists and is current relative to manuscript, evidence, task intake, and artifact refs.
- All blockers name a typed blocker, exact missing refs, and next owner.
- Program/materializer outputs are treated as validators or artifacts, not ready verdicts.
- Next stage is `finalize_and_publication_handoff`, or the receipt fails closed with route-back/blocker/human gate.
