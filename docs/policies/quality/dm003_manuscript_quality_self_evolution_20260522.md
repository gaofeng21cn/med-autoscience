# DM003 Manuscript Quality Self-Evolution Patch Receipt

Owner: `MedAutoScience`
Purpose: `Define stable MAS quality, publication, evidence, and reviewer policy boundaries.`
State: `active_policy`
Machine boundary: Human-readable policy only; quality verdicts, publication truth, evidence state, and reviewer receipts remain in MAS authority functions, contracts, artifacts, ledgers, and owner receipts.

- Date: 2026-05-22
- Source Agent Lab suite: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/agent_lab/medical_manuscript_quality/latest_suite.json`
- Study quality target family: `observational_phenotype_treatment_gap`
- OPL Meta Agent developer work order owner: `opl-meta-agent`

## Scope

This patch updates MAS capability surfaces only: paper-repair owner receipt semantics, DM003 Agent Lab quality targets, regression tests, and this policy receipt.

## Addressed Gap Tokens

- `phenotype_derivation_transparency`
- `recorded_treatment_gap_terminology`
- `bp_and_data_quality_assessment`
- `baseline_characteristics_table`
- `formal_figures_and_tables`
- `numeric_abstract_results_with_uncertainty`
- `claim_evidence_alignment_without_runtime_language`
- `medical_prose_write_repair_requires_story_surface_delta`

## Authority Boundary

This patch does not write DM003 study truth, `publication_eval/latest.json`, `controller_decisions/latest.json`, canonical paper artifacts, `paper/submission_minimal`, `manuscript/current_package`, or any submission readiness verdict. DM003 quality closure remains owned by MAS AI reviewer and publication gate.

## Runtime Lesson

`medical_prose_write_repair` is a manuscript-facing work unit. If canonical paper inputs are sufficient, MAS must materialize a real story-surface delta in `paper/draft.md` and `paper/build/review_manuscript.md` from canonical `paper/` evidence surfaces. If those inputs are insufficient, `quality_repair_batch` or paper repair evidence must preserve `manuscript_story_surface_delta_missing` and route to the write owner. OPL queue success, Agent Lab transport success, or ledger-only updates cannot substitute for a canonical manuscript delta.

## 2026-05-21 Follow-up Landing

- `primary_care_gap` is now a supported manuscript family and resolves to STROBE rather than falling through an unsupported-family path.
- The clinical subtype reconstruction display shell admits `primary_care_gap` descriptive manuscripts, so DPCC phenotype / treatment-gap displays can be planned without pretending the paper is a prediction-model or generic clinical-observation manuscript.
- `medical_prose_write_repair` now shares the story-surface delta contract with `manuscript_story_repair`; the write owner must change `paper/draft.md` or `paper/build/review_manuscript.md`, and ledger-only repair remains blocked.
- `paper-mission-owner-surface` and `stage-outcome-authority` can materialize and execute persisted `run_quality_repair_batch` requests for this write route, preserving `manuscript_story_surface_delta_missing` as a typed blocker when the manuscript surface has not moved.
- `quality_repair_batch` now includes a writer-owner materializer for `medical_prose_write_repair` that writes canonical manuscript story surfaces from methods/cohort/display/treatment-gap/transition/table/evidence refs while avoiding current-package, delivery mirror, publication-eval, controller-decision, and submission-package writes.
- `paper_repair_executor` now targets `paper/draft.md` as the canonical text-repair surface and classifies `paper/draft.md` / `paper/build/review_manuscript.md` as `canonical_manuscript_story_surface`.

These changes intentionally do not declare DM003 quality ready. They make the MAS owner chain capable of materializing prose-quality repairs on canonical manuscript surfaces and then routing back to AI reviewer currentness after a manuscript delta exists.

## 2026-05-22 Round 2 Landing

The next AI reviewer pass confirmed that a manuscript story surface delta alone is not enough for this study family. For phenotype / treatment-gap observational manuscripts, `medical_prose_write_repair` must now materialize reproducibility-grade prose, not only a readable manuscript outline.

The writer materializer now requires the repaired story surface to include:

- index-visit construction using the first qualifying diabetes-coded visit after semantic-audit plausibility filtering;
- deterministic phenotype assignment that is reproducible without model fitting or post hoc label optimization;
- treatment-gap numerator and eligible-denominator rules, including severe-glycemia, uncontrolled-glycemia, hypertension-context, dyslipidemia-context, Not assessed, and recorded-medication source handling;
- missingness and plausibility-filter language that separates row-level, variable-level, and eligibility-level consequences without manuscript-only imputation;
- first-to-last transition construction and dominant-site deterministic site-support construction;
- explicit Table 1 relabeling as a cohort-assembly and data-quality summary, with Table 2 carrying phenotype-level baseline characteristics;
- Results callouts that state claim support, denominator scope, and absolute medication-coverage burden instead of only naming figures.

This is a MAS write-owner quality requirement. It does not transfer DM003 to data/stat owner unless the writer cannot recover these operational details from existing canonical evidence surfaces.

## 2026-05-22 Family-Specific Agent Lab Contract Landing

The DM003 Agent Lab manuscript-quality suite now projects a phenotype / treatment-gap first-draft quality contract rather than inheriting the prediction-model scorer and contract names. The suite-level scorer, promotion regression ref, developer work-order scope, and editable surface refs are derived from `study_quality_target_family`.

For `observational_phenotype_treatment_gap`, the contract refs are:

- `quality_contract_ref:phenotype_treatment_gap_first_draft_quality`
- `scorer:mas/phenotype-treatment-gap-first-draft-quality`
- `regression-suite:mas/phenotype-treatment-gap-first-draft-quality`
- `phenotype_treatment_gap_first_draft_quality_contract`

The regression now also locks the route target for each DM003 quality target, including phenotype derivation to `analysis-campaign`, BP/data quality to `analysis_harmonization_owner`, figure/table quality to `figure-polish`, journal reference style to `publication-gate`, and manuscript language/table/abstract repairs to `write` or `review` as appropriate.

This is still a refs-only Agent Lab capability. It does not mutate DM003 study truth, write `publication_eval/latest.json`, refresh `manuscript/current_package`, or authorize publication readiness.

## 2026-05-22 Internal Process Language Gate

DM003 exposed a writer-materializer leak where a Methods sentence described domains as selected "before manuscript repair". That phrase is internal repair chronology, not a medical methods statement.

The writer materializer now renders this as a study-design statement and treats `manuscript repair`, `quality repair`, `publication gate`, and `controller` as forbidden manuscript terms alongside existing runtime-authority language. The publication gate also redlines internal runtime or repair-process language in manuscript and managed submission surfaces, including `before manuscript repair`, `AI reviewer`, `quality repair`, `controller`, `publication gate`, and `submission readiness`.

This gate blocks leaked process language; it does not authorize readiness or mutate DM003 study truth.

## 2026-05-22 Eval-Bound Manuscript Currentness Guard

DM003 then exposed a deeper currentness bug: `run_quality_repair_batch` used the current AI reviewer eval for route authorization, but `medical_prose_write_repair` could still regenerate the manuscript from deterministic canonical templates and overwrite a more current manuscript that the AI reviewer had just assessed.

`medical_prose_write_repair` now treats `publication_eval/latest.json#reviewer_operating_system.currentness_checks.medical_prose_review` as a content identity guard when the check is current and route target is write. If both canonical story surfaces match the eval-bound manuscript digest, contain journal-routable medical prose, and avoid forbidden runtime language, the writer materializer preserves them and records the current story surfaces as the canonical manuscript delta. The source fingerprint includes this current manuscript basis, so a stale deterministic repair batch cannot share the same identity with the AI reviewer-bound manuscript.

This is still an owner-path guard, not a readiness verdict. A preserved current manuscript must return to AI reviewer / publication gate for quality authority.

## 2026-05-28 Structured Reporting Route Priority Landing

DM003 later exposed that the gate could identify the right medical-journal blockers while the work-unit selector still chose a generic story repair. When `reviewer_first_concerns_unresolved` appeared together with phenotype derivation, treatment-gap, baseline-characteristics, data-quality, or manuscript-voice blockers, the first selected work unit could become `manuscript_story_repair`, producing shallow prose changes instead of closing reproducibility and reporting gaps.

The publication work-unit selector now routes these structured medical reporting blockers to `medical_prose_write_repair` and keeps `treatment_gap_reporting_repair` in the blocking work-unit set. `treatment_gap_reporting_repair` is also registered as a story-surface write unit, so it cannot close on claim/evidence ledger updates alone. The writer handoff prompt contract now carries an explicit quality floor for:

- phenotype derivation method, clinical domains, thresholds, class-count rationale, and new-patient reproducibility;
- recorded medication-coverage / recorded treatment-review gap terminology with numerator, denominator, medication-source, and non-causal guardrails;
- BP semantic-field and broader data-quality assessment;
- true phenotype-level baseline characteristics table expectations;
- manuscript voice cleanup and forbidden runtime/meta-review language.

This route-priority repair does not authorize DM003 quality readiness. It only prevents MAS from converting specific medical-journal blockers into a generic prose-polish task before OPL writer execution.

## 2026-07-06 Reviewer Revision Backfeed Landing

The latest DM003 reviewer_revision exposed a first-draft quality gap that was broader than prose polish: the manuscript needed a structured medical finding argument before wording repair. For phenotype / treatment-gap manuscripts, MAS now treats these as first-draft and revision route-back targets:

- convert descriptive phenotype counts into a structured phenotype pattern and service-priority contrast, with rate and count separated;
- interpret recorded medication gaps through medication-record sensitivity when medication fields are incomplete, and preserve documentation-sensitive claim guardrails;
- route unsupported calendar-year, repeated-visit, and site-variance claims to analysis-campaign gaps or typed waivers instead of inventing Results;
- make Figure/Table terminology, rate/count labels, main/supplementary placement, and supplementary retention part of the quality-gate surface.

This backfeed is MAS repo capability only. It does not write DM003 study truth, paper body, publication eval, controller decisions, owner receipts, typed blockers, human gates, runtime queues, provider attempts, current package, or submission authority.

## 2026-07-06 Reviewer Revision Materialization Landing

DM003 then exposed the next boundary: accepted bounded-analysis reviewer-revision evidence is not useful enough if the write materializer leaves it outside the canonical manuscript and supplement. The DPCC phenotype / treatment-gap story materializer now consumes bounded-analysis rate-count and renal-risk calendar-year sensitivity tables when present, and projects them into manuscript-native Abstract, Methods, Results, Discussion, and Supplementary Tables without changing submission-readiness authority.

For this manuscript family, future first drafts and reviewer revisions should therefore materialize, not merely reference, these evidence surfaces when they exist:

- rate-count service-priority contrast as both prose logic and a supplementary table;
- renal-risk calendar-year medication-capture sensitivity as a bounded exploratory sensitivity, not as uptake, trend, guideline-adherence, or treatment-quality evidence;
- supplementary table numbering that preserves prior supplement content instead of silently dropping or overwriting it.

This is a write-surface materialization capability. It does not authorize publication quality, current-package readiness, owner receipts, typed blockers, human gates, runtime queues, provider attempts, or submission authority.

## 2026-07-06 Rate-Count Figure And Delivery Freshness Landing

DM003 then exposed a package-materialization bug: the reviewer-revision rate-count priority map could be copied into the canonical figure source, but the delivery sync could still prefer an older human-facing `submission/` mirror over the just-generated controller source at `manuscript/submission_minimal`. That made Figure 4 regress during delivery even though the canonical figure source had been updated.

The DPCC display repair now materializes the bounded-analysis rate-count priority map into the canonical Figure 4 generated source (`figures/generated/F4_treatment_gap_alignment_figure.*`), and delivery sync now prefers the newer controller-authorized submission source when both `manuscript/submission_minimal` and the existing `submission/` mirror are present. This prevents post-export sync from overwriting a freshly generated package with stale mirror content.

The latest pre-submission reviewer tightening exposed a narrower owner-callable gap: a `reviewer_revision` task intake can request abstract compression, renal-risk de-emphasis, a modest-effect-size caveat, and a Figure 4 rate-count title update without containing the older stale-story markers. The DM003 story refresh trigger now recognizes these reviewer-tightening intents and refreshes when the current story surface lacks the required compact renal-risk sentence or modest effect-size caveat, so minor but publication-facing reviewer advice is materialized through MAS rather than merely recorded as task intake.

Future reviewer-revision handling must treat package mirror freshness as part of the figure/table materialization check: current-package and legacy mirror roots are delivery projections, not evidence that the newly generated controller source was consumed. Supplementary retention must be verified from the generated package, not inferred from manuscript text alone.

## 2026-07-06 Delivery Role Currentness Readback Landing

DM003 then exposed a readback-level freshness bug after the package itself had been regenerated correctly: the delivery manifest could carry matching evaluated, authority, delivery, source-package, and human-package signatures, while an older `surface_roles.controller_authorized_package_source_root` value still pointed at the human-facing `submission/` root. The delivery inspector treated that role-path mismatch as `stale_source_mismatch` even when the content signatures and current-package freshness proof showed the package was current.

Delivery inspection now resolves the current package root and zip from the manifest's human-facing roles, and it does not let a role-path mismatch override matching source signatures. This keeps the freshness verdict tied to content identity and package proof, while still reporting the recorded source root as diagnostic context. It prevents MAS from telling the user a freshly synced package is stale solely because a legacy role label was stale.

This readback repair is still not a submission-authority decision. If the publication gate reports `authority_snapshot_missing`, the manuscript package can be current for review while `can_submit=false` remains the correct submission boundary.

## Regression Receipt

- `tests/test_cli_cases/owner_route_handoff_command/test_dispatch.py::test_domain_handler_dispatch_rejects_quality_repair_batch_without_manuscript_delta`
- `tests/test_agent_lab_medical_manuscript_quality.py::test_medical_manuscript_quality_agent_lab_suite_uses_dpcc_quality_targets` now also locks the structured phenotype pattern, medication-record sensitivity, unsupported temporal/visit/site gaps, and Figure/Table supplementary-retention targets.
- `tests/test_study_task_intake_cases/reviewer_revision_intake_cases.py::test_reviewer_revision_intake_is_detected_and_summarized` now locks the expanded reviewer_revision checklist.
- `tests/test_quality_repair_batch_cases/medical_prose_write_repair.py::test_medical_prose_write_repair_updates_canonical_story_surface`
- `tests/test_quality_repair_batch_cases/medical_prose_write_repair.py::test_medical_prose_write_repair_preserves_current_ai_reviewer_bound_story_surface`
- `tests/test_publication_work_units_cases/delivery_specificity_cases.py::test_current_delivery_reporting_checklist_blockers_route_to_write_repair`
- `tests/test_paper_repair_execution_evidence_cases/story_surface_delta_cases.py::test_treatment_gap_reporting_repair_requires_story_surface_delta`
- `tests/test_stage_outcome_authority_cases/quality_repair_writer_handoff_contract.py::test_quality_repair_writer_handoff_carries_structured_reporting_checklist`
- `tests/test_publication_gate_cases/supervisor_cases.py::test_build_gate_report_blocks_forbidden_manuscript_terminology`
- `tests/test_paper_repair_executor.py::test_paper_repair_executor_executes_text_repair_on_canonical_sources`
- `tests/test_medical_reporting_contract.py::test_resolve_medical_reporting_contract_for_primary_care_gap_manuscript`
- `tests/test_medical_startup_contract_support.py::test_reporting_contract_supports_primary_care_gap_manuscript_family`
- `tests/test_study_runtime_router_cases/publication_gate_recheck_lifecycle_cases.py::test_progress_projection_keeps_medical_prose_write_route_when_story_surface_delta_is_missing`
- `tests/test_stage_outcome_authority_owner_route.py::test_execute_quality_repair_batch_from_persisted_dispatch_and_owner_request`

Full verification commands and results are recorded in the implementation closeout for this patch.
