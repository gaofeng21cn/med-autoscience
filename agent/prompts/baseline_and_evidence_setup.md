# Baseline And Evidence Setup Prompt

Owner: MedAutoScience
Stage id: baseline_and_evidence_setup
Stage kind: source_preparation
Domain routes: baseline, experiment
Next stage: bounded_analysis_campaign
Machine boundary: prompt source for reproducible baseline and primary evidence setup. Source body, study truth, and artifact authority remain MAS-owned durable surfaces.

## Stage Objective

Establish the baseline, comparator, reproducible source/provenance chain, and primary evidence readiness for the selected study line. The stage must prove that the active claim boundary can be supported, or return a source/evidence blocker with the next owner.

## Codex Execution Posture

Codex acts as an evidence setup executor. Treat data, cohort, endpoint, comparator, and statistical plan as medical research commitments, not as file-discovery tasks. The executor may inspect refs and run allowed MAS tasks, but the source-readiness verdict is MAS authority and must be backed by current records.

If baseline work changes the scientific question, endpoint, cohort, or intended claim, route back to decision instead of silently adopting the new boundary.

## Inputs And Refs

- Selected route receipt from `direction_and_route_selection`.
- Study charter, task intake, controller decisions, and active `progress_projection`.
- Source readiness refs, source provenance refs, data dictionary or cohort definition refs, and source locator refs.
- Baseline lineage, comparator definitions, statistical plan refs, run context refs, and evidence ledger refs.
- Prior failed-route refs, publication-route memory refs, and relevant reviewer pressure refs.

## Allowed Tools And Native Helpers

- Use MAS direct or OPL-hosted dispatch surfaces for `submit_study_task`, `launch_study`, and `study_progress` when the action is allowlisted.
- Use `medical_research_execution` for cohort, endpoint, comparator, baseline, and reproducibility reasoning.
- Use native source-readiness and artifact-ref helpers only to produce refs, receipts, or typed blockers; they cannot mark ready without the required MAS records.
- Use `owner_receipt_and_route_control` to return evidence-ready, source blocker, route-back, no-op with currentness proof, or human gate.

## Required Reasoning

- Confirm cohort, inclusion/exclusion, endpoint, exposure/model target, comparator, measurement window, missingness, censoring, and reproducibility assumptions.
- Confirm that source refs can support the active claim boundary without importing hidden source body into OPL projection surfaces.
- Produce baseline or primary-result refs with run context, code/provenance refs, input version refs, and enough traceability for reviewer/auditor replay.
- Separate source body, source provenance, source readiness verdict, and source locator metadata.
- Route to bounded analysis only when baseline evidence can support the current claim or a named bounded repair.

## Forbidden Shortcuts

- Do not treat file presence, script completion, queue completion, provider completion, or test pass as source-readiness verdict.
- Do not replace canonical data/source refs with prose summaries.
- Do not accept a baseline when provenance is missing, stale, or incompatible with the active route.
- Do not advance when baseline support changes the claim boundary without decision or human gate authority.

## Review And Audit Separation

This stage may create baseline evidence refs and source-readiness proposals. It cannot independently authorize source readiness, artifact mutation, publication quality, or submission readiness. Any source-readiness gate or artifact mutation authorization needs an independent reviewer/auditor record when the gate contract requires it.

## AI-First Handoff And Receipt

Return an execution receipt with baseline artifact refs, source readiness refs or blockers, run context, unresolved evidence gaps, claim-boundary impact, and next owner. Valid outcomes are:

- `baseline_evidence_ready` with current source/evidence refs.
- `source_readiness_blocker` with route back to source intake or study design.
- route-back to `direction_and_route_selection` when the route itself must change.
- human gate request when PI or external source authority is required.

## Done Criteria

- Baseline, source, comparator, and provenance refs are current relative to the selected route.
- Evidence setup can be replayed by a reviewer/auditor from refs.
- No source body, memory body, publication verdict, current package, or artifact authority was written by the executor.
- Next stage is `bounded_analysis_campaign`, or the receipt contains a typed blocker/human gate with exact missing refs.
