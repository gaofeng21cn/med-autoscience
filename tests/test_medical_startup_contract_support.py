from __future__ import annotations

import importlib
import json
from pathlib import Path
import runpy

import yaml


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_profile(tmp_path: Path, **overrides):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    payload = {
        "name": "diabetes",
        "workspace_root": workspace_root,
        "runtime_root": workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        "studies_root": workspace_root / "studies",
        "portfolio_root": workspace_root / "portfolio",
        "med_deepscientist_runtime_root": workspace_root / "ops" / "med-deepscientist" / "runtime",
        "med_deepscientist_repo_root": tmp_path / "med-deepscientist",
        "default_publication_profile": "general_medical_journal",
        "default_citation_style": "AMA",
        "enable_medical_overlay": True,
        "medical_overlay_scope": "workspace",
        "medical_overlay_skills": ("intake-audit", "baseline", "write", "finalize"),
        "research_route_bias_policy": "high_plasticity_medical",
        "preferred_study_archetypes": ("clinical_classifier",),
        "default_submission_targets": (),
        "default_startup_anchor_policy": "scout_first_for_continue_existing_state",
        "legacy_code_execution_policy": "forbid_without_user_approval",
        "startup_boundary_requirements": ("paper_framing", "journal_shortlist", "evidence_package"),
    }
    payload.update(overrides)
    return profiles.WorkspaceProfile(**payload)


def write_study(studies_root: Path, study_id: str, payload: dict[str, object]) -> Path:
    study_root = studies_root / study_id
    write_text(study_root / "study.yaml", yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))
    return study_root


def test_analysis_contract_for_study_marks_missing_endpoint_type_as_unsupported(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.studies_root,
        "001-risk",
        {
            "study_id": "001-risk",
            "preferred_study_archetype": "clinical_classifier",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "unsupported"
    assert result["reason_code"] == "missing_endpoint_type"


def test_analysis_contract_for_study_uses_primary_submission_target_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(
        tmp_path,
        default_submission_targets=(
            {
                "publication_profile": "frontiers_family_harvard",
                "primary": True,
                "package_required": True,
                "story_surface": "general_medical_journal",
            },
        ),
    )
    study_root = write_study(
        profile.studies_root,
        "001-risk",
        {
            "study_id": "001-risk",
            "preferred_study_archetype": "clinical_classifier",
            "endpoint_type": "binary",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["publication_profile"] == "frontiers_family_harvard"
    assert result["submission_target_family"] == "general_medical_journal"


def test_analysis_contract_for_study_rejects_unresolved_primary_publication_profile(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(
        tmp_path,
        default_submission_targets=(
            {
                "publication_profile": "unsupported_profile",
                "primary": True,
                "package_required": True,
                "story_surface": "general_medical_journal",
            },
        ),
    )
    study_root = write_study(
        profile.studies_root,
        "001-risk",
        {
            "study_id": "001-risk",
            "preferred_study_archetype": "clinical_classifier",
            "endpoint_type": "binary",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "unsupported"
    assert result["reason_code"] == "primary_submission_target_not_resolved_to_publication_profile"
    assert result["primary_target_resolution_status"] == "needs_journal_resolution"


def test_resolve_study_archetype_prioritizes_study_payload_study_archetype(tmp_path: Path) -> None:
    support = importlib.import_module("med_autoscience.controllers._medical_contract_support")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))

    study_archetype, issue = support.resolve_study_archetype(
        study_payload={
            "study_archetype": "clinical_classifier",
            "preferred_study_archetype": "clinical_subtype_reconstruction",
        },
        profile=profile,
    )

    assert issue is None
    assert study_archetype == "clinical_classifier"


def test_analysis_contract_for_study_uses_study_level_metadata_priority_and_survival_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-survival-risk",
        {
            "study_id": "001-survival-risk",
            "study_archetype": "clinical_classifier",
            "preferred_study_archetype": "gray_zone_triage",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "clinical_classifier"
    assert result["endpoint_type"] == "time_to_event"
    assert result["manuscript_family"] == "prediction_model"
    assert result["recommended_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]
    assert result["declared_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]


def test_analysis_contract_rejects_ambiguous_profile_fallback_without_explicit_study_archetype(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-ambiguous-risk",
        {
            "study_id": "001-ambiguous-risk",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "unsupported"
    assert result["reason_code"] == "ambiguous_study_archetype"


def test_analysis_contract_for_study_supports_survey_trend_analysis(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-survey-trend",
        {
            "study_id": "001-survey-trend",
            "study_archetype": "survey_trend_analysis",
            "endpoint_type": "descriptive",
            "manuscript_family": "clinical_observation",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "survey_trend_analysis"
    assert result["endpoint_type"] == "descriptive"
    assert result["manuscript_family"] == "clinical_observation"
    assert result["required_analysis_packages"] == [
        "descriptive_prevalence_estimation",
        "cross_survey_harmonization",
        "trend_shift_assessment",
        "guideline_correspondence_matrix",
        "subgroup_heterogeneity",
    ]
    assert result["required_reporting_items"] == [
        "paper_experiment_matrix",
        "derived_analysis_manifest",
        "harmonization_crosswalk",
    ]


def test_analysis_contract_for_study_supports_clinical_subtype_reconstruction(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(
        tmp_path,
        preferred_study_archetypes=("clinical_classifier", "clinical_subtype_reconstruction"),
    )
    study_root = write_study(
        profile.studies_root,
        "001-clinical-subtype",
        {
            "study_id": "001-clinical-subtype",
            "study_archetype": "clinical_subtype_reconstruction",
            "endpoint_type": "descriptive",
            "manuscript_family": "clinical_observation",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "clinical_subtype_reconstruction"
    assert result["endpoint_type"] == "descriptive"
    assert result["manuscript_family"] == "clinical_observation"
    assert result["required_analysis_packages"] == [
        "subtype_derivation",
        "subtype_stability_assessment",
        "clinical_characterization",
        "treatment_pattern_comparison",
        "site_held_out_validation",
        "subgroup_heterogeneity",
    ]
    assert result["required_reporting_items"] == [
        "paper_experiment_matrix",
        "derived_analysis_manifest",
        "subtype_variable_manifest",
        "subtype_assignment_contract",
    ]


def test_reporting_contract_summary_contains_recommended_explicit_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-survival-reporting",
        {
            "study_id": "001-survival-reporting",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )

    result = module.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "clinical_classifier"
    assert result["endpoint_type"] == "time_to_event"
    assert result["manuscript_family"] == "prediction_model"
    assert result["recommended_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]
    assert result["declared_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]
    assert result["display_registry_required"] is True
    assert result["required_illustration_shells"] == ["cohort_flow_figure"]
    assert result["required_table_shells"] == [
        "table1_baseline_characteristics",
        "table2_time_to_event_performance_summary",
    ]
    assert result["display_shell_plan"] == [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
            "story_role": "study_setup",
        },
        {
            "display_id": "discrimination_calibration",
            "display_kind": "figure",
            "requirement_key": "time_to_event_discrimination_calibration_panel",
            "catalog_id": "F2",
            "story_role": "result_evidence",
        },
        {
            "display_id": "km_risk_stratification",
            "display_kind": "figure",
            "requirement_key": "time_to_event_risk_group_summary",
            "catalog_id": "F3",
            "story_role": "result_evidence",
        },
        {
            "display_id": "decision_curve",
            "display_kind": "figure",
            "requirement_key": "time_to_event_decision_curve",
            "catalog_id": "F4",
            "story_role": "result_evidence",
        },
        {
            "display_id": "multicenter_generalizability",
            "display_kind": "figure",
            "requirement_key": "multicenter_generalizability_overview",
            "catalog_id": "F5",
            "story_role": "result_evidence",
        },
        {
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
            "story_role": "study_setup",
        },
        {
            "display_id": "time_to_event_performance_summary",
            "display_kind": "table",
            "requirement_key": "table2_time_to_event_performance_summary",
            "catalog_id": "T2",
            "story_role": "result_evidence",
        },
    ]


def test_reporting_contract_supports_survey_trend_analysis(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-survey-trend-reporting",
        {
            "study_id": "001-survey-trend-reporting",
            "study_archetype": "survey_trend_analysis",
            "endpoint_type": "descriptive",
            "manuscript_family": "clinical_observation",
        },
    )

    result = module.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "survey_trend_analysis"
    assert result["endpoint_type"] == "descriptive"
    assert result["manuscript_family"] == "clinical_observation"
    assert result["reporting_guideline_family"] == "STROBE"
    assert result["required_illustration_shells"] == ["cohort_flow_figure"]
    assert result["required_table_shells"] == ["table1_baseline_characteristics"]
    assert result["display_ambition"] == "strong"
    assert result["minimum_main_text_figures"] == 4
    assert result["recommended_main_text_figures"] == [
        {
            "catalog_id": "F2",
            "display_kind": "figure",
            "story_role": "result_primary",
            "narrative_purpose": "historical_to_current_patient_migration",
            "tier": "core",
        },
        {
            "catalog_id": "F3",
            "display_kind": "figure",
            "story_role": "result_alignment",
            "narrative_purpose": "clinician_surface_and_guideline_alignment",
            "tier": "core",
        },
        {
            "catalog_id": "F4",
            "display_kind": "figure",
            "story_role": "result_interpretive",
            "narrative_purpose": "divergence_decomposition_or_robustness",
            "tier": "core",
        },
    ]
    assert result["display_shell_plan"] == [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
            "story_role": "study_setup",
        },
        {
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
            "story_role": "study_setup",
        },
    ]


def test_reporting_contract_supports_clinical_subtype_reconstruction(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_contract")
    profile = make_profile(
        tmp_path,
        preferred_study_archetypes=("clinical_classifier", "clinical_subtype_reconstruction"),
    )
    study_root = write_study(
        profile.studies_root,
        "001-clinical-subtype-reporting",
        {
            "study_id": "001-clinical-subtype-reporting",
            "study_archetype": "clinical_subtype_reconstruction",
            "endpoint_type": "descriptive",
            "manuscript_family": "clinical_observation",
        },
    )

    result = module.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "clinical_subtype_reconstruction"
    assert result["endpoint_type"] == "descriptive"
    assert result["manuscript_family"] == "clinical_observation"
    assert result["reporting_guideline_family"] == "STROBE"
    assert result["required_illustration_shells"] == ["cohort_flow_figure"]
    assert result["required_table_shells"] == ["table1_baseline_characteristics"]
    assert result["display_ambition"] == "strong"
    assert result["minimum_main_text_figures"] == 4
    assert result["recommended_main_text_figures"] == [
        {
            "catalog_id": "F2",
            "display_kind": "figure",
            "story_role": "result_primary",
            "narrative_purpose": "phenotype_characterization_and_gap_structure",
            "tier": "core",
        },
        {
            "catalog_id": "F3",
            "display_kind": "figure",
            "story_role": "result_validation",
            "narrative_purpose": "site_held_out_reproducibility_or_assignment_stability",
            "tier": "core",
        },
        {
            "catalog_id": "F4",
            "display_kind": "figure",
            "story_role": "result_treatment",
            "narrative_purpose": "treatment_target_gap_alignment",
            "tier": "core",
        },
    ]
    assert result["display_shell_plan"] == [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
            "story_role": "study_setup",
        },
        {
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
            "story_role": "study_setup",
        },
    ]


def test_survival_reporting_contract_hydration_and_materialization_use_semantic_display_ids(
    tmp_path: Path,
    monkeypatch,
) -> None:
    reporting_module = importlib.import_module("med_autoscience.controllers.medical_reporting_contract")
    hydration_module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    materialization_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    test_helpers = runpy.run_path(str(Path(__file__).with_name("test_display_surface_materialization.py")))
    dump_json = test_helpers["dump_json"]
    minimal_layout_sidecar = test_helpers["_minimal_layout_sidecar_for_template"]

    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier",))
    study_root = write_study(
        profile.studies_root,
        "001-survival-reporting-e2e",
        {
            "study_id": "001-survival-reporting-e2e",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )
    reporting_contract = reporting_module.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )
    quest_root = tmp_path / "runtime" / "quests" / "001-survival-reporting-e2e"
    hydration_module.run_hydration(
        quest_root=quest_root,
        hydration_payload={
            "medical_analysis_contract": {"study_archetype": "clinical_classifier", "endpoint_type": "time_to_event"},
            "medical_reporting_contract": reporting_contract,
            "entry_state_summary": "Study root: /tmp/studies/001-survival-reporting-e2e",
            "literature_records": [],
        },
    )
    paper_root = quest_root / "paper"
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "title": "Study cohort flow",
            "steps": [
                {"step_id": "screened", "label": "Patients screened", "n": 186},
                {"step_id": "included", "label": "Included in analysis", "n": 128},
            ],
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "catalog_id": "T1",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "overall", "label": "Overall (n=128)"},
                {"group_id": "high_risk", "label": "High risk (n=55)"},
            ],
            "variables": [
                {"variable_id": "age", "label": "Age, median (IQR)", "values": ["52 (44-61)", "58 (50-66)"]},
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_performance_summary.json",
        {
            "schema_version": 1,
            "table_shell_id": "table2_time_to_event_performance_summary",
            "display_id": "time_to_event_performance_summary",
            "title": "Time-to-event model performance summary",
            "columns": [
                {"column_id": "development", "label": "Development"},
                {"column_id": "external", "label": "External validation"},
            ],
            "rows": [
                {"row_id": "c_index", "label": "Harrell C-index", "values": ["0.81", "0.77"]},
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_grouped_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [
                {
                    "display_id": "km_risk_stratification",
                    "template_id": "time_to_event_risk_group_summary",
                    "title": "Five-year risk-group summary",
                    "caption": "Predicted versus observed five-year risk across prespecified risk groups.",
                    "panel_a_title": "Predicted and observed five-year risk",
                    "panel_b_title": "Observed five-year events",
                    "x_label": "Risk group",
                    "y_label": "Five-year risk (%)",
                    "event_count_y_label": "Observed five-year events",
                    "risk_group_summaries": [
                        {
                            "label": "Low risk",
                            "sample_size": 64,
                            "events_5y": 3,
                            "mean_predicted_risk_5y": 0.06,
                            "observed_km_risk_5y": 0.05,
                        },
                        {
                            "label": "High risk",
                            "sample_size": 64,
                            "events_5y": 18,
                            "mean_predicted_risk_5y": 0.24,
                            "observed_km_risk_5y": 0.28,
                        },
                    ],
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_discrimination_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
            "displays": [
                {
                    "display_id": "discrimination_calibration",
                    "template_id": "time_to_event_discrimination_calibration_panel",
                    "title": "Time-to-event discrimination and grouped calibration",
                    "caption": "Validation discrimination and grouped 5-year calibration structure.",
                    "panel_a_title": "Validation discrimination",
                    "panel_b_title": "Grouped 5-year calibration",
                    "discrimination_x_label": "Validation C-index",
                    "calibration_x_label": "Risk decile",
                    "calibration_y_label": "5-year risk (%)",
                    "discrimination_points": [
                        {"label": "Ridge Cox", "c_index": 0.81},
                        {"label": "Lasso Cox", "c_index": 0.78},
                    ],
                    "calibration_summary": [
                        {"group_label": "Decile 1", "group_order": 1, "n": 24, "events_5y": 0, "predicted_risk_5y": 0.010, "observed_risk_5y": 0.009},
                        {"group_label": "Decile 10", "group_order": 10, "n": 24, "events_5y": 4, "predicted_risk_5y": 0.058, "observed_risk_5y": 0.081},
                    ],
                    "calibration_callout": {"group_label": "Decile 10", "predicted_risk_5y": 0.058, "observed_risk_5y": 0.081},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_decision_curve_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_decision_curve_inputs_v1",
            "displays": [
                {
                    "display_id": "decision_curve",
                    "template_id": "time_to_event_decision_curve",
                    "title": "Time-to-event decision curve",
                    "caption": "Net benefit for the survival model at the 24-month horizon.",
                    "panel_a_title": "Decision-curve net benefit",
                    "panel_b_title": "Model-treated fraction",
                    "x_label": "Threshold probability",
                    "y_label": "Net benefit",
                    "treated_fraction_y_label": "Patients classified above threshold (%)",
                    "reference_line": {"x": [0.05, 0.45], "y": [0.0, 0.0], "label": "Treat none"},
                    "series": [
                        {"label": "Locked survival model", "x": [0.05, 0.10, 0.20, 0.40], "y": [0.18, 0.17, 0.15, 0.08]}
                    ],
                    "treated_fraction_series": {
                        "label": "Locked survival model",
                        "x": [0.05, 0.10, 0.20, 0.40],
                        "y": [62.0, 49.0, 31.0, 12.0],
                    },
                }
            ],
        },
    )
    dump_json(
        paper_root / "multicenter_generalizability_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "multicenter_generalizability_inputs_v1",
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "template_id": "multicenter_generalizability_overview",
                    "title": "Internal multicenter generalizability overview",
                    "caption": "Center-level event support and coverage context under the frozen split.",
                    "overview_mode": "center_support_counts",
                    "center_event_y_label": "5-year events",
                    "coverage_y_label": "Patient count",
                    "center_event_counts": [
                        {
                            "center_label": "Center A",
                            "split_bucket": "train",
                            "event_count": 7,
                        },
                        {
                            "center_label": "Center B",
                            "split_bucket": "validation",
                            "event_count": 5,
                        },
                    ],
                    "coverage_panels": [
                        {
                            "panel_id": "region",
                            "title": "Region coverage",
                            "layout_role": "wide_left",
                            "bars": [{"label": "Central", "count": 420}, {"label": "East", "count": 395}],
                        },
                        {
                            "panel_id": "north_south",
                            "title": "North vs South",
                            "layout_role": "top_right",
                            "bars": [{"label": "North", "count": 380}, {"label": "South", "count": 435}],
                        },
                        {
                            "panel_id": "urban_rural",
                            "title": "Urban/rural",
                            "layout_role": "bottom_right",
                            "bars": [{"label": "Urban", "count": 520}, {"label": "Missing", "count": 295}],
                        },
                    ],
                }
            ],
        },
    )

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(minimal_layout_sidecar(template_id), ensure_ascii=False),
            encoding="utf-8",
        )

    def fake_render_python_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(minimal_layout_sidecar(template_id), ensure_ascii=False),
            encoding="utf-8",
        )

    monkeypatch.setattr(materialization_module, "_render_r_evidence_figure", fake_render_r_evidence_figure, raising=False)
    monkeypatch.setattr(
        materialization_module,
        "_render_python_evidence_figure",
        fake_render_python_evidence_figure,
        raising=False,
    )

    result = materialization_module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5"]
    assert result["tables_materialized"] == ["T1", "T2"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert {item["figure_id"] for item in figure_catalog["figures"]} == {"F1", "F2", "F3", "F4", "F5"}
    assert {item["table_id"] for item in table_catalog["tables"]} == {"T1", "T2"}
