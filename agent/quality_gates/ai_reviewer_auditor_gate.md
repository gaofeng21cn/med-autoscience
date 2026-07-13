# AI Reviewer Auditor Gate

Owner: MedAutoScience
Gate role: AI-first quality gate for publication quality, AI reviewer quality, and publication-route memory accept/reject
Machine boundary: this gate requires independent reviewer/auditor records. It is not satisfied by executor receipts, program exits, materializer outputs, generated surfaces, or package presence.

## Required Independent Record

The reviewer or auditor agent must run as a new StageAttempt and execution
session from the executor whose work is being judged. It must not resume or
inherit the executor conversation. Same-thread checking is
`in_thread_refinement` and cannot emit this gate's receipt. The record must
include:

- reviewer/auditor role and invocation or task record id.
- producer and reviewer attempt/session refs, with distinct session identities
  and `no_context_inheritance=true`.
- separate context summary and refs reviewed.
- manuscript, source, evidence, artifact, review, runtime, controller, and memory refs considered.
- hypothesis portfolio candidate, assumption, support/contradiction, novelty/provenance, testability/safety, negative failed-path, advisory ranking/proximity, and human gate receipt refs when the route depends on a hypothesis portfolio.
- JIT progress-affordance refs when explicitly requested and consumed, including next-delta tournament, bounded micro-candidate, critique-as-repair-hint, strategy retrospective, prefetch, and reusable refs-only lesson refs.
- medical judgment findings, not only checklist status.
- verdict or route-back recommendation with typed blocker when not ready.
- receipt proving currentness relative to task intake, controller decisions, manuscript/source refs, and artifact rebuild proof.

Codex CLI may serve as reviewer/auditor only when invoked as this separate task
with its own new thread/context, task record, and receipt. Re-review after repair
must also use a new session distinct from the repairer.

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
- progress-first use of JIT affordances: when explicitly requested by the current owner or gate, tournaments may order next owner deltas, critique may become repair hints, strategy retrospective may explain stop-loss/repeated failure/human gate/claim-boundary drift/no-loop budget, and reusable lesson extraction may write one refs-only lesson.
- registry, phenotype-atlas, and treatment-gap manuscript floors: clinical discovery contract before Results drafting, Methods reconstructability before prose polish, finding-led Results paragraphs, recorded-care review terminology, medication-capture sensitivity before headline claims, and current-evidence-bounded revision scope.

The journal-family floor must be explicitly consumed when the route touches manuscript, review, finalization, or journal resolution:

- `journal_response_pack`: stable comment ids, response tracker, action mapping, missing author-input flags, readiness state, response output refs, and unresolved-comment blocker.
- `manuscript_argument_pack`: one-sentence argument, contribution, reader risk, novelty boundary, argument skeleton output ref, and route-back blocker.
- `data_availability_fair_pack`: dataset-to-location mapping, restricted data access route, repository identifier, dataset citation, FAIR metadata, Data Availability output ref, and source-readiness blocker.
- `citation_integrity_pack`: claim segment ids, candidate citation refs, citation support grades, metadata-only review flags, reference-manager/export notes, citation output refs, and citation blocker.
- `figure_evidence_contract_pack`: core claim, evidence chain, panel role, figure source-data/statistics/export QA, source-data refs, statistics refs, export contract, QA risks, figure output refs, and artifact/evidence blocker.
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

## Quality-Claim Fail-Closed Cases

Do not issue a quality, publication, export, or submission-ready claim when:

- the reviewer/auditor record is missing, stale, or from the same executor invocation.
- required source, evidence, manuscript, review, memory, or artifact refs are stale or missing.
- hypothesis portfolio refs are used for route selection but lack assumption/sub-assumption decomposition, supporting and contradicting evidence refs, novelty/source provenance refs, testability/safety refs, negative failed-path refs, or required reviewer/human gate receipt refs.
- required journal-family pack refs, output refs, typed blocker refs, or owner receipts are missing for an in-scope route.
- publication eval says ready but reviewer operating-system trace or manuscript refs are not current.
- only mechanical checks, test pass, provider completion, generated interface readiness, package presence, prose completeness, template completion, or pack presence support the ready claim.
- next-delta tournament, micro-candidate generation, critique-as-repair-hint, reusable lesson extraction, strategy retrospective, or opportunistic prefetch is used to admit a route, close this gate, promote a stage, or authorize publication/submission readiness.

This fail-closed rule protects the claim, not ordinary stage progression. When a
current, consumable independent-review packet exists but bounded repair budget is
exhausted, return `completed_with_quality_debt` with exact debt and next-owner
refs. The debt blocks ready claims. When there is no consumable packet, emit a
no-output/failure diagnostic and let Codex continue or route back. Use a typed
blocker only when authority, safety, wrong-target identity/currentness,
credential, irreversible-action, unavailable-executor, or explicit
human-decision requirements prevent safe progress.

## Receipt Requirements

A passing gate must cite the independent record, quality pack evidence refs, journal-family pack refs when in scope, review ledger refs, publication eval refs if updated, output refs reviewed, owner receipt, and any explicitly requested JIT affordance refs consumed as non-authoritative context. A debt result must cite the consumable packet, unresolved findings, blocked claim classes, and next owner. A blocking gate must cite the typed blocker, route-back owner, missing refs, stale refs, forbidden shortcut avoided, and required repair condition.
