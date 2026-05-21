# DM003 Manuscript Quality Self-Evolution Patch Receipt

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

`medical_prose_write_repair` is a manuscript-facing work unit. If `quality_repair_batch` or paper repair evidence reports `manuscript_story_surface_delta_missing`, sidecar dispatch must preserve the typed blocker and return a blocked receipt. OPL queue success, Agent Lab transport success, or ledger-only updates cannot substitute for a canonical `paper/draft.md` or `paper/build/review_manuscript.md` delta.

## 2026-05-21 Follow-up Landing

- `primary_care_gap` is now a supported manuscript family and resolves to STROBE rather than falling through an unsupported-family path.
- The clinical subtype reconstruction display shell admits `primary_care_gap` descriptive manuscripts, so DPCC phenotype / treatment-gap displays can be planned without pretending the paper is a prediction-model or generic clinical-observation manuscript.
- `medical_prose_write_repair` now shares the story-surface delta contract with `manuscript_story_repair`; the write owner must change `paper/draft.md` or `paper/build/review_manuscript.md`, and ledger-only repair remains blocked.
- `domain-route-scan` and `domain-owner-action-dispatch` can materialize and execute persisted `run_quality_repair_batch` requests for this write route, preserving `manuscript_story_surface_delta_missing` as a typed blocker when the manuscript surface has not moved.

These changes intentionally do not generate DM003 prose. They make the MAS owner chain capable of routing the prose-quality blocker to the correct write owner and then back to AI reviewer currentness after a canonical manuscript delta exists.

## Regression Receipt

- `tests/test_cli_cases/sidecar_family_adapter_command.py::test_sidecar_dispatch_rejects_quality_repair_batch_without_manuscript_delta`
- `tests/test_agent_lab_medical_manuscript_quality.py::test_medical_manuscript_quality_agent_lab_suite_uses_dpcc_quality_targets`
- `tests/test_medical_reporting_contract.py::test_resolve_medical_reporting_contract_for_primary_care_gap_manuscript`
- `tests/test_medical_startup_contract_support.py::test_reporting_contract_supports_primary_care_gap_manuscript_family`
- `tests/test_study_runtime_router_cases/publication_gate_recheck_lifecycle_cases.py::test_study_runtime_status_keeps_medical_prose_write_route_when_story_surface_delta_is_missing`
- `tests/test_domain_owner_action_dispatch_owner_route.py::test_execute_quality_repair_batch_from_persisted_dispatch_and_owner_request`

Full verification commands and results are recorded in the implementation closeout for this patch.
