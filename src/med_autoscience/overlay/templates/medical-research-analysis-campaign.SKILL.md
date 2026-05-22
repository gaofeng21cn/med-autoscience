---
name: analysis-campaign
description: Use when a MedAutoScience study needs bounded follow-up analysis to close evidence gaps, repair claim-evidence or display-to-claim support, or route a weak result back without expanding the study boundary.
---

# Analysis Campaign

Use this skill when the current paper line already has a baseline or primary result and now needs a bounded, publication-relevant analysis campaign.

Do not use this skill for open-ended exploration, metric polishing, or a new study direction. If the active question would add a primary claim, change the cohort / endpoint / comparator contract, or require another budget window, route through `decision` or a human gate first.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

{{MED_AUTOSCIENCE_ROUTE_BIAS}}

{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}

{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

## Stage card and route contract

- Stage card ref: `docs/runtime/contracts/stage_surfaces.md#analysis-campaign`
- Route contract ref: `agent/stages/stage_route_contract.yaml#/route_contracts/analysis-campaign`
- Knowledge contract: `src/med_autoscience/stage_knowledge_contract.py#/STAGE_OBLIGATIONS/analysis-campaign`
- Quality pack contract: `src/med_autoscience/stage_quality_contract.py`

Route key question:

- Have the bounded evidence gaps been closed?

The success condition is narrow: every targeted gap must have a resolved result, an explicit weak / negative interpretation, or a stop / route-back decision. Added analyses must stay inside the active study charter and produce evidence that can support writing, review, finalize, or decision.

## MAS Ownership

MedAutoScience owns the study truth, controller authorization, evidence ledger, review ledger, route decision, publication evaluation, and artifact authority.

Allowed MAS owner tools and surfaces:

- controller-authorized MAS CLI / MCP / product-entry / runtime surfaces
- `progress_projection` and `domain_health_diagnostic`
- `artifacts/controller_decisions/latest.json`
- `artifacts/publication_eval/latest.json`
- `paper/evidence/evidence_ledger.json` and equivalent claim-evidence surfaces
- `paper/review/review_ledger.json` and reviewer concern surfaces
- `paper/display_registry.json`, `paper/figure_semantics_manifest.json`, and display materialization surfaces
- stage knowledge packet and stage memory closeout packet
- publication gate and AI reviewer publication eval surfaces

Do not treat chat text, provider completion, queue completion, an external harness result, or a local plot file as MAS truth until the corresponding MAS owner surface records it.

## Knowledge Obligations

Before running or interpreting follow-up analyses, recover the stage knowledge packet and make these inputs explicit:

- active `study_id`, `quest_id`, `active_run_id`, and active route when available
- current study charter boundary and locked cohort / endpoint / comparator / time horizon
- current route key question and bounded campaign scope
- failed path history and any prior stop-loss or weak-result notes
- evidence ledger and active claim-evidence map
- citation gaps that affect the targeted claims
- bounded frontier: possible analysis slices that still fit the charter
- reviewer concerns that triggered the campaign
- startup contract and compute boundary when present

If these inputs cannot be recovered, write the missing refs as blockers and route through `decision` rather than inventing a campaign.

## Quality Pack Refs

Use quality packs as reviewer rubrics and quality inputs. They do not authorize publication readiness.

Required packs for this stage:

- `statistical_analysis_pack`: analysis contract, cohort / endpoint lock, estimator or model choice, effect size, uncertainty, missing-data handling, multiplicity posture, and reproducibility refs.
- `display_to_claim_pack`: every updated table, figure, and display must map to a claim or a reviewer concern.
- `route_memory_pack`: failed paths, useful bounded repairs, and rejected expansion routes should be available for future routing.
- `stop_loss_pack`: weak, negative, unstable, or high-cost slices must become route decisions instead of hidden retries.
- `human_gate_pack`: any boundary-changing request must be carried as a human-gate signal, not as an analysis shortcut.

Optional related packs:

- `medical_claim_evidence_pack` when the analysis directly changes claim wording.
- `artifact_freshness_pack` when regenerated displays or package projections become downstream inputs.

## Bounded Analysis Candidate Board

Before running work, create or refresh a Bounded Analysis Candidate Board. The board must include at least one option in each category unless the category is explicitly not applicable:

- `explore`: low-cost check that clarifies whether a gap is real.
- `exploit`: strongest bounded slice that directly supports the active claim.
- `fusion`: combine existing evidence surfaces without changing the charter.
- `debug`: diagnose a weak, contradictory, missing, or stale evidence path.
- `stop`: stop-loss option with the route-back or human-gate reason.

For every candidate, record:

- target claim or reviewer concern
- expected evidence gain
- required input refs and output refs
- cost, runtime, and data risk
- statistical validity risk
- clinical interpretability
- display-to-claim impact
- decision reason: run, defer, reject, or stop

Run the smallest candidate set that can answer the route key question. Do not let the board become a backlog of attractive but non-blocking analyses.

## Statistical Discipline

Treat analysis-campaign work as manuscript evidence generation.

Before execution:

- name the estimand, comparison, or diagnostic question
- bind cohort, endpoint, time horizon, predictor set, and subgroup definitions to current truth surfaces
- state the model, test, or summary statistic and why it matches the question
- predeclare primary and secondary readouts for the slice
- define missing-data handling and exclusion handling
- decide whether multiplicity control, sensitivity framing, or descriptive labeling is required

During interpretation:

- report effect size and uncertainty before p-values or tiny score movements
- distinguish confirmatory, sensitivity, descriptive, and exploratory slices
- keep calibration, threshold behavior, clinical utility, subgroup heterogeneity, explainability, and external validation as claim-bound evidence, not decoration
- surface negative, weak, unstable, or contradictory results through claim downgrade, route-back, or stop-loss
- do not promote a tiny discrimination bump into a clinical claim without clinical interpretability and claim-evidence support

Every result that matters must leave a reproducible trace: source data ref, script or command ref, output artifact ref, result summary, affected claim, and route impact.

## Claim-Evidence And Display Repair

Analysis-campaign is often the right route for repairing a narrow evidence gap. It is not allowed to patch prose or figures around unsupported claims.

For each targeted gap:

- identify the exact claim, table, figure, caption, or reviewer concern
- link the existing supporting evidence or mark it missing
- run only the bounded analysis needed to close or falsify the gap
- update the evidence ledger or claim-evidence map with the result
- update display-to-claim mapping when figures or tables change
- materialize display surfaces through MAS-controlled display contracts when the display registry declares them
- downgrade or narrow claims immediately when the new evidence is weaker than the draft

If a display cannot honestly support the claim after repair, route to `write` for claim wording repair or `decision` for route-level judgment. Do not hide the mismatch in caption text.

## Route-Back Discipline

Use route-back as a normal outcome, not as failure.

Route to `write` when:

- evidence is sufficient but claim wording, limitations, or figure/table explanation must be repaired
- the campaign created a clean display-to-claim update that needs manuscript consolidation

Route to `review` when:

- the evidence package is complete enough for adversarial review but residual risks should be pressure-tested

Route to `finalize` when:

- the campaign closed the named blockers and the package only needs final audit / export checks

Route to `decision` when:

- new gaps exceed the bounded scope
- claim support weakens materially
- a reviewer-first scan requests a different baseline, study line, or stop-loss decision
- the next analysis would consume a new budget window

Escalate a human gate when the user must choose a new primary claim, external release, submission direction, dataset use, or compute budget boundary.

## Research Harness Clean-Room Lessons

Research Harness is only a clean-room pattern source here.

Useful absorbed patterns:

- typed research checkpoints
- numeric trace discipline
- claim-evidence coverage projection
- candidate path ranking
- explicit adverse / weak result resolution

Forbidden imports from Research Harness:

- no RH dependency, runner, checkpoint engine, database, dashboard, MCP server, parser backend, or verdict authority
- no RH paper-ready, citation, number-quality, or route verdict may replace MAS `publication_eval/latest.json`, review ledger, evidence ledger, controller decision, publication gate, or artifact proof

If a RH-inspired pattern is useful, write it as a MAS-owned evidence, review, quality-pack, or controller-readable artifact.

## Forbidden Actions

- Do not run unbounded grids or broad follow-up campaigns without a named route question.
- Do not continue compute when `startup_contract.startup_boundary_gate.allow_compute_stage` is not `true`.
- Do not execute legacy implementation code from `refs/` or history unless `startup_contract.legacy_code_execution_allowed` is `true`.
- Do not treat ablation-heavy work as a substitute for required calibration, transportability, cohort flow, baseline characteristics, or reporting-guideline evidence.
- Do not fabricate statistical significance, clinical utility, subgroup meaning, or mechanistic interpretation.
- Do not overwrite baseline, evidence, review, display, or package truth silently.
- Do not directly edit `manuscript/current_package` as the final repair for an analysis gap.
- Do not use OPL projection, provider completion, or external harness output to authorize MAS quality or publication readiness.

## Closeout Packet

Before leaving this stage, write or refresh a stage memory closeout packet and route artifact with:

- route outcome: continue, route-back, bounded analysis complete, write repair, finalize, human gate, or stop
- Bounded Analysis Candidate Board with run / reject / stop decisions
- slice ledger: each executed slice, input refs, output refs, and result interpretation
- evidence ledger and claim-evidence updates
- display-to-claim repairs or unresolved display blockers
- statistical discipline notes: estimand, model/test, uncertainty, sensitivity or multiplicity posture
- negative or weak result interpretation
- failed path lesson and why it should not be retried blindly
- route impact and exact next route
- reviewer/Codex revision handoff if this campaign was triggered by manuscript-change feedback

Reusable lessons may enter route memory only when they are separated from study-specific truth.

## OPL Boundary

OPL may index, display, dispatch, and check freshness for MAS-exported stage descriptors, task refs, and owner receipts.

OPL must not:

- write MAS domain truth
- authorize quality verdicts, publication readiness, submission readiness, or claim downgrades
- own canonical artifacts, evidence ledgers, review ledgers, or controller decisions
- accept memory writeback without MAS memory router receipt
- turn a provider-hosted completion into paper closure

The valid family path is `OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker`.
