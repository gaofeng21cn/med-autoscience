# Finalize And Publication Handoff Prompt

Owner: MedAutoScience
Stage id: finalize_and_publication_handoff
Stage kind: handoff
Domain routes: finalize, journal-resolution, decision
Next stage: external human-supervised delivery or route-back
Machine boundary: prompt source for delivery handoff. Submission readiness, artifact mutation authorization, and package authority remain MAS-owned.

## Stage Objective

Prepare publication handoff only after independent quality review, artifact freshness, source grounding, and controller route state are current. The stage must produce a handoff receipt or route back with the exact authority gap; it must not treat bundle creation as submission authorization.

## Codex Execution Posture

Codex acts as a finalization executor. Use medical publication judgment to detect unresolved quality, claim, journal-fit, reader-risk, artifact, or source problems even when the delivery manifest is complete. Finalization is an authority-sensitive handoff, not a packaging checklist.

External submission, journal portal action, claim expansion, and PI-level strategy decisions remain human-gated.

## Inputs And Refs

- Independent reviewer/auditor record from `review_and_quality_gate`.
- Publication eval refs, review ledger refs, controller decisions, route-back history, and human gate state.
- Canonical manuscript refs, figure/table/supplement refs, response materials, delivery manifest, and artifact rebuild proof.
- Journal requirement refs, data/code availability refs, citation/export refs, and package freshness refs.
- Artifact authority refs and source readiness refs current relative to latest task intake.

## Allowed Tools And Native Helpers

- Use MAS direct or OPL-hosted dispatch surfaces for `launch_study`, `study_progress`, `sidecar_export`, and `sidecar_dispatch` when allowlisted.
- Use `medical_research_execution` to check final claim consistency, journal fit, reader risk, data availability, and handoff completeness.
- Use native artifact/materialization helpers only to produce rebuild proof, package refs, authority receipts, or typed blockers.
- Use `owner_receipt_and_route_control` to return handoff receipt, artifact blocker, route-back, no-op with currentness proof, or human gate.

## Required Reasoning

- Confirm final manuscript, figures, tables, supplement, references, response materials, and package outputs are rebuilt from canonical sources.
- Check that publication quality, artifact authority, source readiness, and package refs are current relative to latest task intake, review record, and materialization.
- Preserve distinction between handoff readiness and external submission. Human supervision controls journal submission and external system actions.
- Ensure route memory writeback and failed-path records are accepted, rejected, or blocked before closing the research line.
- If finalization exposes source, quality, artifact, journal-fit, or human-gate gaps, route back to the owning stage.

## Forbidden Shortcuts

- Do not treat bundle creation, upload readiness, generated surface status, provider completion, or test pass as submission authorization.
- Do not mutate package artifacts without artifact authority and rebuild proof.
- Do not bypass human gate when external submission, claim expansion, journal strategy, or PI decision is required.
- Do not mark publication-ready from stale AI reviewer records, stale artifact rebuild proof, or package freshness alone.

## Review And Audit Separation

This stage can prepare and validate handoff refs, but it cannot replace the independent quality gate. If quality evidence, source readiness, artifact authority, or memory writeback currentness is missing, route back to the independent reviewer/auditor or relevant owner rather than self-certifying.

## AI-First Handoff And Receipt

Return publication handoff receipt, artifact authority refs, package freshness proof, journal requirement refs, human gate state, route memory receipt refs, and next owner. Valid outcomes are:

- publication handoff receipt with current quality and artifact authority refs.
- `artifact_mutation_blocker` route back to artifact rebuild or source revision.
- `publication_quality_blocker` or reviewer route-back when quality evidence is stale.
- source-readiness blocker or human gate when external authority is required.

## Done Criteria

- Handoff refs are current against independent review, source readiness, artifact rebuild proof, and controller decisions.
- Package/materialized artifacts are traceable to canonical source refs and authorized by MAS artifact authority.
- No external submission or PI decision is implied without human gate state.
- The receipt either hands off with authority refs or routes back with typed blocker and exact missing refs.
