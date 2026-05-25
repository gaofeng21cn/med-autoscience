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
- `owner-route-reconcile` and `domain-owner-action-dispatch` can materialize and execute persisted `run_quality_repair_batch` requests for this write route, preserving `manuscript_story_surface_delta_missing` as a typed blocker when the manuscript surface has not moved.
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

## Regression Receipt

- `tests/test_cli_cases/owner_route_handoff_command.py::test_domain_handler_dispatch_rejects_quality_repair_batch_without_manuscript_delta`
- `tests/test_agent_lab_medical_manuscript_quality.py::test_medical_manuscript_quality_agent_lab_suite_uses_dpcc_quality_targets`
- `tests/test_quality_repair_batch_cases/medical_prose_write_repair.py::test_medical_prose_write_repair_updates_canonical_story_surface`
- `tests/test_quality_repair_batch_cases/medical_prose_write_repair.py::test_medical_prose_write_repair_preserves_current_ai_reviewer_bound_story_surface`
- `tests/test_publication_gate_cases/supervisor_cases.py::test_build_gate_report_blocks_forbidden_manuscript_terminology`
- `tests/test_paper_repair_executor.py::test_paper_repair_executor_executes_text_repair_on_canonical_sources`
- `tests/test_medical_reporting_contract.py::test_resolve_medical_reporting_contract_for_primary_care_gap_manuscript`
- `tests/test_medical_startup_contract_support.py::test_reporting_contract_supports_primary_care_gap_manuscript_family`
- `tests/test_study_runtime_router_cases/publication_gate_recheck_lifecycle_cases.py::test_progress_projection_keeps_medical_prose_write_route_when_story_surface_delta_is_missing`
- `tests/test_domain_owner_action_dispatch_owner_route.py::test_execute_quality_repair_batch_from_persisted_dispatch_and_owner_request`

Full verification commands and results are recorded in the implementation closeout for this patch.
