# AI Reviewer Auditor Gate

Owner: MedAutoScience
Gate role: AI-first quality gate for publication quality, AI reviewer quality, and publication-route memory accept/reject
Machine boundary: this gate requires independent reviewer/auditor records. It is not satisfied by executor receipts, program exits, materializer outputs, generated surfaces, or package presence.

## Required Independent Record

The reviewer or auditor agent must run as a separate invocation from the executor whose work is being judged. The record must include:

- reviewer/auditor role and invocation or task record id.
- separate context summary and refs reviewed.
- manuscript, source, evidence, artifact, review, runtime, controller, and memory refs considered.
- hypothesis portfolio candidate, assumption, support/contradiction, novelty/provenance, testability/safety, negative failed-path, advisory ranking/proximity, and human gate receipt refs when the route depends on a hypothesis portfolio.
- medical judgment findings, not only checklist status.
- verdict or route-back recommendation with typed blocker when not ready.
- receipt proving currentness relative to task intake, controller decisions, manuscript/source refs, and artifact rebuild proof.

Codex CLI may serve as reviewer/auditor only when invoked as this separate task with its own context, task record, and receipt.

## Judgment Floor

Rubrics and quality packs define the traceable floor. The reviewer/auditor must also exercise AI-native medical publication judgment over:

- claim restraint and clinical interpretation.
- statistical rigor and methodology fit.
- source grounding and provenance currentness.
- citation integrity and reporting guideline fit.
- display-to-claim consistency.
- limitations, failed paths, reader risk, contribution logic, and journal fit.
- route memory relevance and memory writeback safety.
- hypothesis novelty, evidence balance, failed-path handling, advisory ranking limits, testability, safety, and human/independent-review boundary.

The journal-family floor must be explicitly consumed when the route touches manuscript, review, finalization, or journal resolution:

- `journal_response_pack`: stable comment ids, response tracker, action mapping, missing author-input flags, readiness state, response output refs, and unresolved-comment blocker.
- `data_availability_fair_pack`: dataset-to-location mapping, restricted data access route, repository identifier, dataset citation, FAIR metadata, Data Availability output ref, and source-readiness blocker.
- `citation_integrity_pack`: claim segment ids, candidate citation refs, support grade, metadata-only review flags, reference-manager/export notes, citation output refs, and citation blocker.
- `figure_evidence_contract_pack`: core claim, evidence chain, panel role, source-data refs, statistics refs, export contract, QA risks, figure output refs, and artifact/evidence blocker.
- `paper_reader_grounding_pack`: source map, page/block anchors, figure-near-claim refs, source-grounded follow-up refs, reader output refs, and grounding blocker.
- `paper_presentation_pack`: evidence spine, selected figure assets, speaker-notes context, presentation output refs, and presentation-grounding blocker.

These packs are quality floors and reviewer rubrics absorbed from nature-skills as MAS-native patterns. They are not publication authority, submission authorization, artifact authority, or a replacement for reviewer/auditor judgment.

## Gate Outcomes

Valid gate outputs are:

- independent reviewer/auditor record with current refs and no blocker.
- `publication_quality_blocker` routed to review or revision.
- `ai_reviewer_quality_blocker` routed to AI reviewer repair.
- `publication_route_memory_writeback_blocker` routed to memory writeback repair.
- human gate request when PI, scope, journal strategy, or external action is required.

## Program And Materializer Boundary

Programs, validators, materializers, scaffold checks, and generated OPL surfaces may emit provenance/currentness receipts or typed blockers. They cannot emit pass/ready verdicts for publication quality, AI reviewer quality, memory acceptance, submission readiness, source readiness, or artifact mutation.

## Fail-Closed Cases

Fail closed or route back when:

- the reviewer/auditor record is missing, stale, or from the same executor invocation.
- required source, evidence, manuscript, review, memory, or artifact refs are stale or missing.
- hypothesis portfolio refs are used for route selection but lack assumption/sub-assumption decomposition, supporting and contradicting evidence refs, novelty/source provenance refs, testability/safety refs, negative failed-path refs, or required reviewer/human gate receipt refs.
- required journal-family pack refs, output refs, typed blocker refs, or owner receipts are missing for an in-scope route.
- publication eval says ready but reviewer operating-system trace or manuscript refs are not current.
- only mechanical checks, test pass, provider completion, generated interface readiness, package presence, prose completeness, template completion, or pack presence support the ready claim.

## Receipt Requirements

A passing gate must cite the independent record, quality pack evidence refs, journal-family pack refs when in scope, review ledger refs, publication eval refs if updated, output refs reviewed, and owner receipt. A blocking gate must cite the typed blocker, route-back owner, missing refs, stale refs, forbidden shortcut avoided, and required repair condition.
