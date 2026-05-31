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
- Re-consume journal-family quality pack refs as handoff floors, not authority: `journal_response_pack`, `data_availability_fair_pack`, `citation_integrity_pack`, `figure_evidence_contract_pack`, `paper_reader_grounding_pack`, and `paper_presentation_pack`. These floors remain MAS-native clean-room guidance, not vendor dependency, runtime dependency, default skill source, publication readiness authority, or quality verdict authority.
- Confirm reviewer response materials carry stable comment ids, action mapping, difficult-case routing, appeal-like routing, missing-author-input state, response readiness refs, and typed blocker refs for unresolved comments.
- Confirm Data Availability and FAIR outputs carry dataset-location mapping, restricted-access reason and access route, repository or persistent identifier, dataset citation, public metadata for restricted data when possible, licence / rights / provenance / README refs, output refs, and owner receipt.
- Confirm citation integrity outputs carry strict Nature / CNS scope decisions when requested, support grades, candidate citation refs, metadata-only flags, publisher or abstract verification refs, selected ENW / RIS / Zotero RDF export refs, and route-back blockers for unsupported claims.
- Confirm figure/table outputs carry backend selection, final size, source-data refs, statistics refs, export contract refs, image-integrity / reviewer-risk QA refs, rebuild proof, and artifact authority receipt.
- Confirm reader outputs carry full-paper source-map refs, stable page/block anchors, caption/table/figure anchors, figure-near-claim refs, source-grounded follow-up refs, and owner receipt.
- Confirm presentation outputs carry evidence-spine refs, selected figure asset refs, asset manifest, crop QA, PPTX package/reopen QA, slide overflow/readability QA, speaker-notes context, and owner receipt.
- Preserve distinction between handoff readiness and external submission. Human supervision controls journal submission and external system actions.
- Ensure route memory writeback and failed-path records are accepted, rejected, or blocked before closing the research line.
- If finalization exposes source, quality, artifact, journal-fit, or human-gate gaps, route back to the owning stage.

## Forbidden Shortcuts

- Do not treat bundle creation, upload readiness, generated surface status, provider completion, or test pass as submission authorization.
- Do not mutate package artifacts without artifact authority and rebuild proof.
- Do not bypass human gate when external submission, claim expansion, journal strategy, or PI decision is required.
- Do not mark publication-ready from stale AI reviewer records, stale artifact rebuild proof, or package freshness alone.
- Do not convert completed response/Data Availability/citation/figure/reader/presentation templates into submission authorization without independent reviewer/auditor quality authority and MAS owner receipts.

## Review And Audit Separation

This stage can prepare and validate handoff refs, but it cannot replace the independent quality gate. If quality evidence, source readiness, artifact authority, or memory writeback currentness is missing, route back to the independent reviewer/auditor or relevant owner rather than self-certifying.

## AI-First Handoff And Receipt

Return publication handoff receipt, artifact authority refs, package freshness proof, journal requirement refs, human gate state, route memory receipt refs, and next owner. Valid outcomes are:

The receipt must state the minimum forward delta and the next forced target surface. If no domain delta was possible, it must cite the consumed currentness, duplicate, failed-path, or forbidden-surface refs and close as typed blocker, human gate, stop-loss, or route-back. Record-only reviewer loops, currentness-only replay, and provider-completed-only closeout cannot satisfy this stage. Human gate requests must include the decision question, evidence refs, allowed choices or decision boundary, blocking reason, and the target surface that resumes after the human receipt.

- publication handoff receipt with current quality and artifact authority refs.
- `artifact_mutation_blocker` route back to artifact rebuild or source revision.
- `publication_quality_blocker` or reviewer route-back when quality evidence is stale.
- source-readiness blocker or human gate when external authority is required.

The handoff receipt must include current output refs and owner receipts for reviewer response difficult-case / appeal-like / author-input routing, Data Availability restricted-access / FAIR metadata, strict citation support and selected export, figure backend / source-data / statistics / export QA, source-grounded full-paper reader view with page/block anchors, and presentation PPTX QA / asset-manifest materials when present. Missing or stale refs must become typed blockers, not silent exclusions.

## Done Criteria

- Handoff refs are current against independent review, source readiness, artifact rebuild proof, and controller decisions.
- Package/materialized artifacts are traceable to canonical source refs and authorized by MAS artifact authority.
- No external submission or PI decision is implied without human gate state.
- The receipt either hands off with authority refs or routes back with typed blocker and exact missing refs.
