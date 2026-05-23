---
name: review
description: Use when a MedAutoScience manuscript or manuscript-facing draft needs adversarial medical review, claim downgrade, citation repair, reviewer action matrix, or route-back closeout before finalize.
---

# Review

Use this skill when a manuscript-facing draft, claim-evidence package, or reviewer feedback needs strict medical review before the line can advance.

Review is not copyediting. It is a MAS-owned pressure test over claims, evidence, displays, citations, methods, limitations, and route readiness.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

## Stage card and route contract

- Stage card ref: `docs/runtime/contracts/stage_surfaces.md#review`
- Route contract ref: `agent/stages/stage_route_contract.yaml#/route_contracts/review`
- Knowledge contract: `src/med_autoscience/stage_knowledge_contract.py#/STAGE_OBLIGATIONS/review`
- Quality pack contract: `src/med_autoscience/stage_quality_contract.py`

Route key question:

- What should the strict AI reviewer send back before the line can advance?

The success condition is a reviewer action matrix that maps each concern to evidence, citation, text repair, analysis-campaign, route decision, or human gate work. Unsupported claims must be downgraded or routed back before finalize.

## MAS Ownership

MedAutoScience owns the review judgment, claim downgrade, citation repair routing, publication evaluation, review ledger, evidence ledger, controller decision, and artifact authority.

Allowed MAS owner tools and surfaces:

- controller-authorized MAS CLI / MCP / product-entry domain handler surfaces
- `artifacts/publication_eval/latest.json`
- `artifacts/controller_decisions/latest.json`
- `paper/review/review_ledger.json` and reviewer action matrix surfaces
- `paper/evidence/evidence_ledger.json` and claim-evidence map
- citation ledger, reference context, literature intelligence read models, and source provenance surfaces
- `paper/display_registry.json`, display-to-claim map, and figure semantics surfaces
- stage knowledge packet and stage memory closeout packet
- publication gate and AI reviewer publication eval surfaces

Quality verdicts, publication readiness, and submission readiness must close through MAS owner surfaces. A contradiction flag, rubric note, external review artifact, or provider completion is only an input until MAS records the owner decision.

## AI-Native Reviewer Judgment

The reviewer is an expert medical publication judge first and a rubric user second.
Use quality packs, contracts, and checklists as the minimum floor for traceability, coverage, and route-back language.
They must not limit review to enumerated checklist failures or allow a mechanically complete matrix to stand in for scientific judgment.

Name material concerns even when no existing rubric item names them, including:

- misleading emphasis or weak contribution logic
- clinically implausible interpretation
- journal-fit or audience-risk problems
- hidden negative or equivocal results
- reviewer skepticism that follows from the whole paper rather than one isolated field

When open-ended judgment adds a concern, still bind it back to MAS owner surfaces through evidence refs, citation refs, affected text or display locations, route decision, typed blocker, or human gate.

## Knowledge Obligations

Before reviewing, recover the stage knowledge packet and make these inputs explicit:

- manuscript or manuscript-facing draft under review
- active study charter and locked claim boundary
- claim-evidence map and evidence ledger refs
- display-to-claim map, figure/table registry, and display freshness refs
- study reference context and citation ledger refs
- prior reviewer findings and unresolved reviewer concerns
- AI reviewer calibration memory, if present
- current publication eval and controller decision refs
- known contradiction flags and their provenance

If reference context or citation ledger refs are missing, record that as a review blocker and create a citation repair request. Do not fill the gap with memory-only claims.

## Quality Pack Refs

Use quality packs as reviewer rubrics and quality inputs. They do not authorize readiness by themselves.

Required packs for this stage:

- `medical_claim_evidence_pack`: every claim must map to direct evidence or be downgraded / routed back.
- `reporting_guideline_pack`: methods, results, limitations, and reporting checklist obligations must match the study type.
- `display_to_claim_pack`: each figure and table must support the stated claim without overclaiming.
- `route_memory_pack`: recurring reviewer lessons and prior failed repairs should inform routing without replacing study truth.
- `stop_loss_pack`: irreparable, weak, contradictory, or high-risk lines must become route decisions instead of prose smoothing.
- `human_gate_pack`: boundary-changing review conclusions must be carried as human-gate signals.

Related packs:

- `artifact_freshness_pack` when review findings depend on regenerated current package, delivery manifest, or display exports.
- `statistical_analysis_pack` when the review finding routes back to analysis-campaign.

## Adversarial Review

Run review with an adversarial mindset:

- assume each central claim may be too broad until evidence proves otherwise
- check whether the cohort, endpoint, comparator, time horizon, and missing-data strategy are explicit
- verify that statistics, sample sizes, confidence intervals, p-values, calibration, subgroup claims, and external validation claims match their evidence
- inspect whether every figure, table, and caption has a defensible display-to-claim mapping
- check whether methods labels such as `knowledge-guided`, `causal`, `mechanistic`, `calibration-first`, or `AI-assisted` have operational definitions
- look for orphan claims, inflated novelty, missing limitations, weak citation support, hidden negative results, and contradictions
- separate manuscript repair from route-level repair

A strict review should produce repairable findings. Do not write vague criticism that cannot be mapped to a claim, evidence ref, citation ref, text location, route decision, or human gate.

## Contradiction Flags

Contradiction flags are `review_signal_only`.

Use contradiction flags to prioritize review work, citation repair, and route-back decisions, but never as direct publication authority.

For every contradiction flag used in review, record:

- source and provenance
- affected claim, method, result, or citation
- whether the contradiction is factual, methodological, population-specific, endpoint-specific, temporal, or interpretive
- required disposition: citation repair, claim downgrade, analysis-campaign, write repair, decision, or human gate
- why the flag is or is not blocking

If a contradiction cannot be resolved within the current charter, route through `decision` or human gate rather than forcing a manuscript-safe sentence around it.

## Claim Downgrade

Unsupported claims must be narrowed immediately or routed back.

Use claim downgrade when:

- evidence is internally valid but narrower than the draft claim
- validation is internal only and the draft implies external validation or deployment readiness
- subgroup, threshold, calibration, or clinical utility evidence is insufficient
- a figure or table supports association, not causality or mechanism
- a citation supports background plausibility but not the paper's direct result

For each downgrade:

- update the draft or write-repair request
- update the review ledger with the old claim, new claim, evidence ref, and reason
- update the claim-evidence map or mark the needed repair
- state whether the downgraded claim still permits `write`, `finalize`, or needs `decision`

Do not let a downgraded claim remain contradicted by figure titles, captions, abstracts, highlights, or conclusions.

## Citation Repair

Review must treat citation quality as part of medical rigor.

Open a citation repair request when:

- a claim has no citation or only a weak background citation
- a citation does not match the population, endpoint, method, or time horizon
- a guideline, reporting standard, or validation claim needs a primary or official source
- a cited source is stale where recency matters
- a citation is contradicted by a newer or stronger source
- source metadata, DOI, PMID, journal, year, or full-text provenance is incomplete

Citation repair output must include:

- affected claim or section
- existing citation and why it is insufficient
- required source type, such as primary study, guideline, systematic review, reporting standard, dataset documentation, or official registry
- blocking status and next route

Do not fabricate citations, infer guideline requirements from memory, or use third-party summaries as authority when official or primary sources are required.

## Reviewer Action Matrix

Write findings as an action matrix. Each row should include:

- concern id
- affected claim, section, figure, table, or citation
- evidence path or missing evidence path
- citation path or missing citation path
- severity: blocker, major, minor, or note
- disposition: `accept_as_is`, `downgrade_claim`, `repair_citation`, `route_back_write`, `route_back_analysis`, `route_back_decision`, `human_gate`, or `stop`
- readiness label blocked: `draft-ready`, `paper-ready`, or `submission-ready`
- owner surface that must record closure

The matrix should be tied to `publication_eval/latest.json`, `review_ledger`, or the equivalent MAS review surface. It should be specific enough for another executor to continue without reading transient chat.

## Route-Back Closeout

Review is complete only after it names the narrowest honest next route.

Route to `analysis-campaign` when:

- the claim may be supportable but needs a bounded analysis slice
- display-to-claim repair depends on new or regenerated evidence
- a statistical, subgroup, calibration, utility, or sensitivity gap blocks review

Route to `write` when:

- evidence is adequate but wording, structure, caveats, limitations, or citation placement need repair

Route to `finalize` when:

- review finds no blocker and the remaining work is package readiness, declarations, freshness, or export audit

Route to `decision` when:

- novelty, rigor, citation, evidence, or contradiction gaps cannot be closed within writing
- a reviewer finding requests a different baseline, study line, or route-level judgment
- claim downgrade changes the paper's central contribution

Escalate a human gate when review would change study boundary, external release, submission authorization, journal direction, or non-public data usage.

## Reusable Critique Lessons

Write a reusable critique lesson only when the finding should change future stage defaults across studies.

Good reusable lessons:

- a recurring claim overreach pattern
- a citation provenance failure mode
- a display-to-claim mismatch pattern
- a statistical reporting omission that should be checked earlier
- a reviewer concern ordering rule

Keep reusable lessons separate from study-specific truth. Memory can inform future route selection, but it cannot replace review ledger closure, evidence ledger updates, publication eval, or controller decision.

## Research Harness Clean-Room Lessons

Research Harness is only a clean-room pattern source here.

Useful absorbed patterns:

- adversarial resolution artifacts
- contradiction-aware review signals
- claim-evidence coverage posture
- numeric trace checks
- typed review closeout

Forbidden imports from Research Harness:

- no RH dependency, runner, checkpoint engine, database, dashboard, MCP server, parser backend, or verdict authority
- no RH paper-ready, citation, number-quality, or route verdict may replace MAS `publication_eval/latest.json`, review ledger, evidence ledger, controller decision, publication gate, or artifact proof

If an RH-inspired critique is useful, write it as MAS-owned review ledger, citation repair, evidence repair, route-back, or memory closeout material.

## Forbidden Actions

- Do not review as a friendly copyedit while leaving unsupported claims intact.
- Do not treat contradiction flags as publication verdicts; they are `review_signal_only`.
- Do not advance to finalize with orphan claims, missing evidence refs, unresolved citation gaps, or unclosed reviewer blockers.
- Do not fix citation gaps by inventing sources, guessing official requirements, or relying on memory alone.
- Do not directly edit `manuscript/current_package` as the final repair when canonical paper sources or OPL runtime-control refs are stale.
- Do not convert an external harness result, provider completion, or dashboard state into MAS quality authority.
- Do not bury negative, weak, contradictory, or blocked findings in prose.
- Do not let OPL own review truth, publication readiness, or memory writeback.

## Closeout Packet

Before leaving this stage, write or refresh a stage memory closeout packet and review route artifact with:

- reviewer action matrix
- evidence repair requests and citation repair requests
- claim downgrades with old claim, new claim, evidence refs, and affected text / display locations
- contradiction flags used, each marked `review_signal_only`
- remaining blockers and blocked readiness label
- reusable critique lesson, if any
- route-back recommendation with the narrowest next route
- human-gate request if the review changes boundary, release, submission, or data-use authority
- MAS owner surface refs that must prove closure

Closeout should leave enough context for another executor to continue from the MAS owner surfaces without relying on transient chat.

## OPL Boundary

OPL may index, display, dispatch, and check freshness for MAS-exported review descriptors, task refs, route recommendations, and owner receipts.

OPL must not:

- write MAS review truth, evidence truth, citation truth, or manuscript authority
- authorize quality verdicts, publication readiness, submission readiness, or claim downgrades
- own review ledgers, evidence ledgers, controller decisions, publication eval, or canonical artifacts
- accept memory writeback without MAS memory router receipt
- turn provider-hosted or external-harness completion into paper closure

The valid family path is `OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker`.
