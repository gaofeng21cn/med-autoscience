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
            "requirement_key": "kaplan_meier_grouped",
            "catalog_id": "F3",
        },
        {
            "display_id": "decision_curve",
            "display_kind": "figure",
            "requirement_key": "time_to_event_decision_curve",
            "catalog_id": "F4",
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
                    "template_id": "kaplan_meier_grouped",
                    "title": "Kaplan-Meier risk stratification",
                    "caption": "Time-to-event separation across prespecified risk groups.",
                    "x_label": "Months from surgery",
                    "y_label": "Survival probability",
                    "groups": [
                        {"label": "Low risk", "times": [0, 6, 12, 24], "values": [1.0, 0.96, 0.93, 0.88]},
                        {"label": "High risk", "times": [0, 6, 12, 24], "values": [1.0, 0.88, 0.77, 0.62]},
                    ],
                    "annotation": "Log-rank P < .001",
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
                    "caption": "Horizon-specific discrimination and calibration structure.",
                    "discrimination_x_label": "1 - Specificity",
                    "discrimination_y_label": "Sensitivity",
                    "calibration_x_label": "Months from surgery",
                    "calibration_y_label": "Observed event-free probability",
                    "discrimination_reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
                    "calibration_reference_line": {"x": [0.0, 24.0], "y": [1.0, 0.60], "label": "Expected"},
                    "discrimination_series": [
                        {"label": "24-month horizon", "x": [0.0, 0.15, 0.30, 1.0], "y": [0.0, 0.66, 0.81, 1.0]}
                    ],
                    "calibration_groups": [
                        {"label": "Predicted low risk", "times": [0, 6, 12, 24], "values": [1.0, 0.96, 0.92, 0.87]},
                        {"label": "Predicted high risk", "times": [0, 6, 12, 24], "values": [1.0, 0.86, 0.75, 0.58]},
                    ],
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
                    "x_label": "Threshold probability",
                    "y_label": "Net benefit",
                    "reference_line": {"x": [0.05, 0.45], "y": [0.0, 0.0], "label": "Treat none"},
                    "series": [
                        {"label": "Locked survival model", "x": [0.05, 0.10, 0.20, 0.40], "y": [0.18, 0.17, 0.15, 0.08]}
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

    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4"]
    assert result["tables_materialized"] == ["T1", "T2"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert {item["figure_id"] for item in figure_catalog["figures"]} == {"F1", "F2", "F3", "F4"}
    assert {item["table_id"] for item in table_catalog["tables"]} == {"T1", "T2"}
