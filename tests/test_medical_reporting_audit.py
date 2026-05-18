from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_valid_medical_story_contracts(paper_root: Path, *, figure_required_exports: list[str] | None = None) -> None:
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "results_narrative_map.json").write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "study-population",
                        "section_title": "Study population",
                        "research_question": "Which cohort was analyzed?",
                        "direct_answer": "The analytic cohort is fully enumerated.",
                        "supporting_display_items": ["Figure1"],
                        "key_quantitative_findings": ["All exclusions are accounted for."],
                        "clinical_meaning": "Readers can interpret the cohort denominator.",
                        "boundary": "Descriptive cohort accounting only.",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "figure_semantics_manifest.json").write_text(
        json.dumps(
            {
                "figures": [
                    {
                        "figure_id": "Figure1",
                        "story_role": "study_setup",
                        "research_question": "How was the cohort assembled?",
                        "direct_message": "The flow chart documents cohort assembly and exclusions.",
                        "clinical_implication": "The denominator is transparent for clinical interpretation.",
                        "interpretation_boundary": "The figure does not make causal claims.",
                        "panel_messages": [{"panel_id": "A", "message": "Cohort inclusion and exclusion flow."}],
                        "legend_glossary": [{"term": "cohort", "explanation": "Eligible analytic population."}],
                        "threshold_semantics": "No clinical threshold is introduced.",
                        "stratification_basis": "Study inclusion and exclusion criteria.",
                        "recommendation_boundary": "No treatment recommendation is made.",
                        "renderer_contract": {
                            "figure_semantics": "illustration",
                            "renderer_family": "python",
                            "template_id": "cohort_flow_figure",
                            "selection_rationale": "The cohort-flow illustration shell is the registered Figure 1 contract.",
                            "layout_qc_profile": "publication_illustration_flow",
                            "required_exports": figure_required_exports or ["png", "svg", "pdf"],
                            "fallback_on_failure": False,
                            "failure_action": "block_and_fix_environment",
                        },
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "claim_evidence_map.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "cohort-accounting",
                        "statement": "The study cohort was assembled through auditable inclusion and exclusion steps.",
                        "status": "supported",
                        "paper_role": "main_text",
                        "display_bindings": ["Figure1"],
                        "sections": ["study-population"],
                        "evidence_items": [
                            {
                                "item_id": "cohort-flow",
                                "support_level": "direct",
                                "source_paths": ["paper/cohort_flow.json"],
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_valid_numeric_trace(paper_root, claim_id="cohort-accounting", trace_id="trace-cohort-n")


def _write_keyed_medical_story_contracts(paper_root: Path) -> None:
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "results_narrative_map.json").write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "transportability-results",
                        "section_title": "Transportability results",
                        "research_question": "What does external validation show?",
                        "direct_answer": "Risk ordering transfers only partially while calibration remains unstable.",
                        "supporting_display_items": ["F1"],
                        "key_quantitative_findings": ["External validation supports a bounded interpretation."],
                        "clinical_meaning": "External validation and recalibration are required before clinical use.",
                        "boundary": "The result does not support a deployable universal model.",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "figure_semantics_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "figures": {
                    "F1": {
                        "figure_id": "F1",
                        "title": "Study cohorts and external validation framework",
                        "research_question": "How large is the observed mortality difference?",
                        "direct_message": "The external validation cohort has a higher observed mortality rate.",
                        "clinical_implication": "Analysts should verify the outcome scale before transport.",
                        "interpretation_boundary": "This is an observed contrast, not a causal country-effect estimate.",
                        "panel_level_messages": [
                            {"panel": "overall", "message": "Cohort and endpoint context for external validation."}
                        ],
                        "glossary_terms": {
                            "transportability": "Whether model behavior remains valid in another population.",
                        },
                        "threshold_or_stratification_caveats": [
                            "Five-year all-cause mortality is the shared primary endpoint."
                        ],
                        "renderer_contract": {
                            "renderer": "python",
                            "allowed_renderers": ["python", "r_ggplot2"],
                            "template_id": "F1",
                            "layout_qc_profile": "F1",
                            "fallback_on_failure": False,
                            "failure_action": "block_and_fix_environment",
                            "source_kind": "evidence_figure",
                            "source_locked": True,
                            "locked": True,
                            "figure_kind": "evidence",
                            "source_catalog": "paper/figure_catalog.json",
                        },
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "claim_evidence_map.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "external-validation-boundary",
                        "statement": "External validation supports a bounded transportability claim.",
                        "status": "supported",
                        "paper_role": "main_text",
                        "display_bindings": ["F1"],
                        "sections": ["transportability-results"],
                        "evidence_items": [
                            {
                                "item_id": "external-validation-summary",
                                "support_level": "direct",
                                "source_paths": ["paper/results_narrative_map.json"],
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_valid_numeric_trace(paper_root, claim_id="external-validation-boundary", trace_id="trace-validation-n")


def _write_valid_numeric_trace(paper_root: Path, *, claim_id: str, trace_id: str) -> None:
    (paper_root / "numeric_trace.json").write_text(
        json.dumps(
            {
                "traces": [
                    {
                        "trace_id": trace_id,
                        "claim_id": claim_id,
                        "reported_value": "n=1,240",
                        "statistic_kind": "sample_size",
                        "source_paths": ["paper/tables/table1.json"],
                        "source_field": "analytic_n",
                        "rounding_rule": "integer_count_no_rounding",
                        "manuscript_refs": ["results:study-population"],
                        "verification_status": "verified",
                        "evidence_refs": ["cohort-flow"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_medical_reporting_audit_blocks_missing_population_accounting(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "medical_reporting_contract.json").write_text(
        '{"reporting_guideline_family": "TRIPOD"}',
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_cohort_flow" in report["blockers"]
    assert "missing_baseline_characteristics_schema" in report["blockers"]
    assert "missing_reporting_guideline_checklist" in report["blockers"]


def test_medical_reporting_audit_blocks_structured_publication_reporting_gaps(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "003-dpcc-phenotypes"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "STROBE",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
                "paper_archetype": "phenotype_real_world",
                "methods_completeness": {
                    "study_design": True,
                    "cohort": True,
                    "variables": True,
                    "model": True,
                },
                "statistical_reporting": {
                    "summary_format": True,
                    "p_values": True,
                },
                "table_figure_claim_map": [],
                "clinical_actionability": {
                    "treatment_gap": True,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "reporting_guideline_checklist.json").write_text("{}", encoding="utf-8")

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "methods_completeness_incomplete" in report["blockers"]
    assert "statistical_reporting_incomplete" in report["blockers"]
    assert "table_figure_claim_map_missing_or_incomplete" in report["blockers"]
    assert "clinical_actionability_incomplete" in report["blockers"]
    assert "treatment_gap_reporting_incomplete" in report["blockers"]
    report_payload = json.loads(Path(report["report_json"]).read_text(encoding="utf-8"))
    assert report_payload["structured_reporting_checklist"]["methods_completeness"]["missing_items"] == [
        "validation",
        "statistical_analysis",
    ]
    assert report_payload["structured_reporting_checklist"]["statistical_reporting"]["missing_items"] == [
        "subgroup_tests"
    ]
    assert report_payload["structured_reporting_checklist"]["clinical_actionability"]["missing_items"] == [
        "follow_up_or_outcome_relevance"
    ]
    assert report_payload["structured_reporting_checklist"]["treatment_gap_reporting"]["missing_items"] == [
        "explicit_numerator_denominator_rules",
        "overall_burden_and_group_rates",
        "table_role_consistency",
        "figure_legend_uniqueness",
        "non_causal_claim_guardrail",
        "numerator",
        "denominator",
        "eligibility",
        "time_window",
        "medication_data_source",
        "interpretation_label_or_guardrail",
    ]


def test_structured_reporting_checklist_blocks_prediction_model_reporting_gaps() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")
    complete = {"status": "complete"}

    checklist = policy.build_structured_reporting_checklist(
        {
            "manuscript_family": "prediction_model",
            "endpoint_type": "time_to_event",
            "methods_completeness": {key: complete for key in policy.METHODS_COMPLETENESS_ITEMS},
            "statistical_reporting": {key: complete for key in policy.STATISTICAL_REPORTING_ITEMS},
            "table_figure_claim_map": [{"claim_id": "primary-model", "table_figure_refs": ["T2", "F4"]}],
            "prediction_methods": {"data_source_years": "complete"},
            "time_to_event_prediction_reporting": {"competing_event_screen": "complete"},
            "decision_curve_clinical_utility": {"dca_threshold_range": "complete"},
            "prediction_performance_reporting": {"validation_n": "complete"},
            "baseline_balance_reporting": {"variable_level_missingness": "complete"},
        }
    )

    assert checklist["status"] == "blocked"
    assert "prediction_model_methods_reporting_incomplete" in checklist["blockers"]
    assert "time_to_event_prediction_reporting_incomplete" in checklist["blockers"]
    assert "decision_curve_clinical_utility_incomplete" in checklist["blockers"]
    assert "prediction_performance_reporting_incomplete" in checklist["blockers"]
    assert "baseline_balance_reporting_incomplete" in checklist["blockers"]
    assert "competing_risk_reporting_incomplete" not in checklist["blockers"]
    assert "linked_clinical_action_scenario" in checklist["decision_curve_clinical_utility"]["missing_items"]
    assert "standardized_mean_differences" in checklist["baseline_balance_reporting"]["missing_items"]


def test_structured_reporting_checklist_requires_competing_risk_details_when_events_present() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")

    def complete_section(items: tuple[str, ...]) -> dict[str, str]:
        return {item: "complete" for item in items}

    checklist = policy.build_structured_reporting_checklist(
        {
            "manuscript_family": "prediction_model",
            "endpoint_type": "time_to_event",
            "competing_risk_events_present": True,
            "methods_completeness": complete_section(policy.METHODS_COMPLETENESS_ITEMS),
            "statistical_reporting": complete_section(policy.STATISTICAL_REPORTING_ITEMS),
            "table_figure_claim_map": [{"claim_id": "primary-model", "table_figure_refs": ["T2", "F4"]}],
            "prediction_methods": complete_section(policy.PREDICTION_MODEL_METHODS_ITEMS),
            "prediction_model_reproducibility": complete_section(
                policy.PREDICTION_MODEL_REPRODUCIBILITY_ITEMS
            ),
            "variable_harmonization": complete_section(policy.VARIABLE_HARMONIZATION_ITEMS),
            "time_to_event_prediction_reporting": complete_section(policy.TIME_TO_EVENT_PREDICTION_ITEMS),
            "external_validation_reporting": complete_section(
                policy.EXTERNAL_VALIDATION_REPORTING_ITEMS
            ),
            "decision_curve_clinical_utility": complete_section(policy.DECISION_CURVE_CLINICAL_UTILITY_ITEMS),
            "prediction_performance_reporting": complete_section(
                policy.PREDICTION_PERFORMANCE_REPORTING_ITEMS
            ),
            "validation_uncertainty_reporting": complete_section(policy.VALIDATION_UNCERTAINTY_ITEMS),
            "prediction_display_reporting": complete_section(policy.PREDICTION_DISPLAY_REPORTING_ITEMS),
            "manuscript_voice_reporting": complete_section(policy.MANUSCRIPT_VOICE_REPORTING_ITEMS),
            "baseline_balance_reporting": complete_section(policy.BASELINE_BALANCE_REPORTING_ITEMS),
            "competing_risk_reporting": {
                "target_event_definition": "complete",
                "competing_event_definition": "complete",
            },
        }
    )

    assert checklist["status"] == "blocked"
    assert checklist["blockers"] == ["competing_risk_reporting_incomplete"]
    assert "non_target_death_handling" in checklist["competing_risk_reporting"]["missing_items"]
    assert "fine_gray_or_competing_risk_sensitivity" in checklist["competing_risk_reporting"]["missing_items"]


def test_default_structured_reporting_contract_for_time_to_event_prediction_sets_first_draft_gates() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")

    contract = policy.build_default_structured_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
        endpoint_type="time_to_event",
    )

    assert contract["prediction_model_reporting_required"] is True
    assert contract["competing_risk_reporting_required"] == "when_non_target_deaths_present"
    assert "model_tuning" in contract["prediction_methods"]
    assert "baseline_survival_or_absolute_risk_extraction" in contract["prediction_model_reproducibility"]
    assert "cross_cohort_unit_conversion" in contract["variable_harmonization"]
    assert "case_mix_and_covariate_support" in contract["external_validation_reporting"]
    assert "linked_clinical_action_scenario" in contract["decision_curve_clinical_utility"]
    assert "high_risk_predicted_observed" in contract["prediction_performance_reporting"]
    assert "observed_expected_ratio_confidence_interval" in contract["validation_uncertainty_reporting"]
    assert "calibration_curve_with_uncertainty" in contract["prediction_display_reporting"]
    assert "internal_quality_control_language_absent" in contract["manuscript_voice_reporting"]
    assert "standardized_mean_differences" in contract["baseline_balance_reporting"]
    assert "competing_event_screen" in contract["time_to_event_prediction_reporting"]


def test_write_audit_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return (
            quest_root / "artifacts" / "reports" / report_group / "latest.json",
            quest_root / "artifacts" / "reports" / report_group / "latest.md",
        )

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-04-03T10:00:00+00:00",
        "quest_root": str(quest_root),
        "status": "blocked",
        "blockers": ["missing_cohort_flow"],
        "action": "clear",
    }

    json_path, md_path = module.write_audit_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "medical_reporting_audit"
    assert seen["timestamp"] == "2026-04-03T10:00:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"


def test_medical_reporting_audit_reads_projected_paper_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk-reentry"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "paper_bundle_manifest.json").write_text("{}", encoding="utf-8")
    (paper_root / "medical_reporting_contract.json").write_text(
        '{"reporting_guideline_family": "TRIPOD"}',
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_medical_reporting_contract" not in report["blockers"]
    assert "missing_cohort_flow" in report["blockers"]


def test_medical_reporting_audit_blocks_missing_medical_story_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk-story"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
                {
                    "reporting_guideline_family": "STROBE",
                    "display_registry_required": False,
                    "cohort_flow_required": False,
                    "baseline_characteristics_required": False,
                    "display_shell_plan": [],
                },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "reporting_guideline_checklist.json").write_text(
        json.dumps({"schema_version": 1, "items": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_medical_story_contract" in report["blockers"]
    assert report["medical_story_contract_blockers"] == [
        "missing_results_narrative_map",
        "missing_figure_semantics_manifest",
        "missing_claim_evidence_map",
        "missing_numeric_trace",
    ]


def test_medical_reporting_audit_reports_figure_semantics_missing_pdf_export(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "002-dm-china-us-mortality-attribution"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "STROBE",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "reporting_guideline_checklist.json").write_text(
        json.dumps({"schema_version": 1, "items": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_valid_medical_story_contracts(paper_root, figure_required_exports=["png", "svg"])

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_medical_story_contract" in report["blockers"]
    assert "invalid_figure_semantics_manifest" in report["blockers"]
    assert "figure_semantics_manifest_missing_pdf_export" in report["blockers"]
    assert report["medical_story_contract_blockers"] == [
        "invalid_figure_semantics_manifest",
        "figure_semantics_manifest_missing_pdf_export",
    ]


def test_medical_reporting_audit_accepts_keyed_figure_semantics_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "002-dm-china-us-mortality-attribution"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "STROBE",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
                "quality_gate_expectation": {"gate_relaxation_allowed": True},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "review").mkdir(parents=True, exist_ok=True)
    (paper_root / "review" / "submission_checklist.json").write_text(
        json.dumps(
            {
                "overall_status": "submission_minimal_materialized_handoff_ready",
                "handoff_ready": True,
                "blocking_items": [],
                "package_status": "submission_minimal_ready",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_keyed_medical_story_contracts(paper_root)

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert "invalid_figure_semantics_manifest" not in report["blockers"]
    assert "missing_medical_story_contract" not in report["blockers"]
    assert report["medical_story_contract_valid"] is True
    assert report["medical_story_contract_blockers"] == []


def test_medical_reporting_audit_blocks_keyed_figure_semantics_missing_message(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "002-dm-china-us-mortality-attribution"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "STROBE",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "reporting_guideline_checklist.json").write_text(
        json.dumps({"schema_version": 1, "items": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_keyed_medical_story_contracts(paper_root)
    payload = json.loads((paper_root / "figure_semantics_manifest.json").read_text(encoding="utf-8"))
    del payload["figures"]["F1"]["direct_message"]
    (paper_root / "figure_semantics_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert "missing_medical_story_contract" in report["blockers"]
    assert "invalid_figure_semantics_manifest" in report["medical_story_contract_blockers"]


def test_medical_reporting_audit_downgrades_missing_reporting_guideline_checklist_when_handoff_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk-handoff-ready"
    paper_root = quest_root / "paper"
    review_root = paper_root / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "paper_bundle_manifest.json").write_text("{}", encoding="utf-8")
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "STROBE",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (review_root / "submission_checklist.json").write_text(
        json.dumps(
            {
                "overall_status": "submission_minimal_materialized_handoff_ready",
                "handoff_ready": True,
                "blocking_items": [],
                "package_status": "submission_minimal_ready",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "_medical_story_contract_blockers", lambda _: [])

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "advisory"
    assert report["blockers"] == []
    assert report["advisories"] == ["missing_reporting_guideline_checklist"]


def test_medical_reporting_audit_keeps_guideline_checklist_blocking_when_quality_gate_is_strict(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk-strict-gate"
    paper_root = quest_root / "paper"
    review_root = paper_root / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "paper_bundle_manifest.json").write_text("{}", encoding="utf-8")
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "STROBE",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
                "quality_gate_expectation": {
                    "guideline_family": "STROBE",
                    "gate_relaxation_allowed": False,
                    "required_before_accelerated_handoff": True,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (review_root / "submission_checklist.json").write_text(
        json.dumps(
            {
                "overall_status": "submission_minimal_materialized_handoff_ready",
                "handoff_ready": True,
                "blocking_items": [],
                "package_status": "submission_minimal_ready",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "_medical_story_contract_blockers", lambda _: [])

    report = module.run_controller(quest_root=quest_root, apply=False)

    report_payload = json.loads(Path(report["report_json"]).read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert "missing_reporting_guideline_checklist" in report["blockers"]
    assert report["advisories"] == []
    assert report_payload["quality_gate_expectation"]["gate_relaxation_allowed"] is False


def test_medical_reporting_audit_blocks_missing_direct_migration_stub(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    paper_root = quest_root / "paper"
    (paper_root / "figures").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)

    display_plan = [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
        {
            "display_id": "discrimination_calibration",
            "display_kind": "figure",
            "requirement_key": "time_to_event_discrimination_calibration_panel",
            "catalog_id": "F2",
        },
        {
            "display_id": "km_risk_stratification",
            "display_kind": "figure",
            "requirement_key": "time_to_event_risk_group_summary",
            "catalog_id": "F3",
        },
        {
            "display_id": "decision_curve",
            "display_kind": "figure",
            "requirement_key": "time_to_event_decision_curve",
            "catalog_id": "F4",
        },
        {
            "display_id": "multicenter_generalizability",
            "display_kind": "figure",
            "requirement_key": "multicenter_generalizability_overview",
            "catalog_id": "F5",
        },
        {
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
        {
            "display_id": "time_to_event_performance_summary",
            "display_kind": "table",
            "requirement_key": "table2_time_to_event_performance_summary",
            "catalog_id": "T2",
        },
    ]
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "TRIPOD",
                "display_registry_required": True,
                "display_shell_plan": display_plan,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "display_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_contract_path": "paper/medical_reporting_contract.json",
                "displays": [
                    {
                        **item,
                        "shell_path": (
                            f"paper/figures/{item['display_id']}.shell.json"
                            if item["display_kind"] == "figure"
                            else f"paper/tables/{item['display_id']}.shell.json"
                        ),
                    }
                    for item in display_plan
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    for item in display_plan:
        shell_path = (
            paper_root / "figures" / f"{item['display_id']}.shell.json"
            if item["display_kind"] == "figure"
            else paper_root / "tables" / f"{item['display_id']}.shell.json"
        )
        shell_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "source_contract_path": "paper/medical_reporting_contract.json",
                    "display_id": item["display_id"],
                    "display_kind": item["display_kind"],
                    "requirement_key": item["requirement_key"],
                    "catalog_id": item["catalog_id"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    (paper_root / "cohort_flow.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "shell_id": "cohort_flow_figure",
                "display_id": "cohort_flow",
                "catalog_id": "F1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_population_accounting",
                "population_accounting": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "baseline_characteristics_schema.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "table_shell_id": "table1_baseline_characteristics",
                "display_id": "baseline_characteristics",
                "catalog_id": "T1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_table_materialization",
                "group_columns": [],
                "variables": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_performance_summary.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "table_shell_id": "table2_time_to_event_performance_summary",
                "display_id": "time_to_event_performance_summary",
                "catalog_id": "T2",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_discrimination_calibration_inputs.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
                "displays": [
                    {
                        "display_id": "discrimination_calibration",
                        "catalog_id": "F2",
                        "template_id": "time_to_event_discrimination_calibration_panel",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_grouped_inputs.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_grouped_inputs_v1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
                "displays": [
                    {
                        "display_id": "km_risk_stratification",
                        "catalog_id": "F3",
                        "template_id": "time_to_event_risk_group_summary",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_decision_curve_inputs.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_decision_curve_inputs_v1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
                "displays": [
                    {
                        "display_id": "decision_curve",
                        "catalog_id": "F4",
                        "template_id": "time_to_event_decision_curve",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "reporting_guideline_checklist.json").write_text("{}", encoding="utf-8")

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_multicenter_generalizability_inputs" in report["blockers"]
    assert "missing_medical_story_contract" in report["blockers"]


def test_medical_reporting_audit_blocks_missing_transportability_governance_stub(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "002-dm-transportability"
    paper_root = quest_root / "paper"
    (paper_root / "figures").mkdir(parents=True, exist_ok=True)
    display_plan = [
        {
            "display_id": "transportability_governance",
            "display_kind": "figure",
            "requirement_key": "center_transportability_governance_summary_panel",
            "catalog_id": "F5",
        }
    ]
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "TRIPOD",
                "display_registry_required": True,
                "display_shell_plan": display_plan,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "display_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_contract_path": "paper/medical_reporting_contract.json",
                "displays": [
                    {
                        **display_plan[0],
                        "shell_path": "paper/figures/transportability_governance.shell.json",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "figures" / "transportability_governance.shell.json").write_text("{}", encoding="utf-8")

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_center_transportability_governance_summary_panel_inputs" in report["blockers"]
    assert "missing_multicenter_generalizability_inputs" not in report["blockers"]
