from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path

import pytest


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _display_registry_payload() -> dict:
    return {
        "schema_version": 1,
        "source_contract_path": "paper/medical_reporting_contract.json",
        "displays": [
            {
                "display_id": "discrimination_calibration",
                "display_kind": "figure",
                "requirement_key": "time_to_event_discrimination_calibration_panel",
                "catalog_id": "F2",
                "shell_path": "paper/figures/discrimination_calibration.shell.json",
            },
            {
                "display_id": "km_risk_stratification",
                "display_kind": "figure",
                "requirement_key": "kaplan_meier_grouped",
                "catalog_id": "F3",
                "shell_path": "paper/figures/km_risk_stratification.shell.json",
            },
            {
                "display_id": "decision_curve",
                "display_kind": "figure",
                "requirement_key": "time_to_event_decision_curve",
                "catalog_id": "F4",
                "shell_path": "paper/figures/decision_curve.shell.json",
            },
            {
                "display_id": "multicenter_generalizability",
                "display_kind": "figure",
                "requirement_key": "multicenter_generalizability_overview",
                "catalog_id": "F5",
                "shell_path": "paper/figures/multicenter_generalizability.shell.json",
            },
            {
                "display_id": "time_to_event_performance_summary",
                "display_kind": "table",
                "requirement_key": "table2_time_to_event_performance_summary",
                "catalog_id": "T2",
                "shell_path": "paper/tables/time_to_event_performance_summary.shell.json",
            },
        ],
    }


def test_run_time_to_event_direct_migration_writes_complete_inputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.time_to_event_direct_migration")
    study_root = tmp_path / "studies" / "001-dm"
    paper_root = tmp_path / "paper"

    write_json(paper_root / "display_registry.json", _display_registry_payload())
    write_text(
        paper_root / "tables" / "table2_performance_summary.md",
        "\n".join(
            [
                "# Table 2. Performance summary",
                "",
                "| Endpoint | C-index | Stratification / utility |",
                "| --- | --- | --- |",
                "| Cardiovascular mortality | Ridge 0.857; lasso 0.768 | High-risk tertile: 11 / 17 events; positive DCA at 0.5%-2.0% thresholds |",
                "| All-cause mortality | Supportive Cox line 0.768 | Observed 5-year risk across tertiles: 0.5%, 2.0%, 5.5% |",
                "",
            ]
        )
        + "\n",
    )
    write_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "catalog_id": "F1",
            "title": "Study cohort flow",
            "steps": [
                {"step_id": "source", "label": "Source cohort", "n": 15787, "detail": "Frozen analysis cohort"},
                {"step_id": "evaluable", "label": "Evaluable at five years", "n": 14816, "detail": "Complete primary endpoint support"},
                {"step_id": "analysis", "label": "Validation cohort", "n": 7408, "detail": "Five-year cardiovascular mortality endpoint"},
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "cvd_mortality",
                    "label": "Five-year cardiovascular mortality",
                    "event_n": 121,
                    "detail": "Validation endpoint inventory",
                },
                {
                    "endpoint_id": "all_cause_mortality",
                    "label": "Five-year all-cause mortality",
                    "event_n": 388,
                    "detail": "Supportive endpoint inventory",
                }
            ],
        },
    )
    write_text(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "discrimination_report.md",
        "\n".join(
            [
                "# Validation discrimination",
                "",
                "| model | split | c_index |",
                "| --- | --- | --- |",
                "| CoxPH | validation | 0.857 |",
                "| LassoCox | validation | 0.768 |",
                "",
            ]
        )
        + "\n",
    )

    prediction_rows = [
        {"Sequnece": "1", "center": "1", "os_time": "1.0", "cvd_death": "1", "risk_score": "2.4", "predicted_risk_5y": "0.060", "calibration_decile": "10", "risk_tertile": "high"},
        {"Sequnece": "2", "center": "1", "os_time": "2.0", "cvd_death": "1", "risk_score": "2.1", "predicted_risk_5y": "0.050", "calibration_decile": "10", "risk_tertile": "high"},
        {"Sequnece": "3", "center": "2", "os_time": "6.0", "cvd_death": "0", "risk_score": "1.2", "predicted_risk_5y": "0.020", "calibration_decile": "5", "risk_tertile": "mid"},
        {"Sequnece": "4", "center": "2", "os_time": "7.0", "cvd_death": "0", "risk_score": "1.0", "predicted_risk_5y": "0.018", "calibration_decile": "5", "risk_tertile": "mid"},
        {"Sequnece": "5", "center": "3", "os_time": "4.0", "cvd_death": "0", "risk_score": "-0.5", "predicted_risk_5y": "0.005", "calibration_decile": "1", "risk_tertile": "low"},
        {"Sequnece": "6", "center": "3", "os_time": "8.0", "cvd_death": "0", "risk_score": "-0.7", "predicted_risk_5y": "0.004", "calibration_decile": "1", "risk_tertile": "low"},
        {"Sequnece": "7", "center": "4", "os_time": "3.0", "cvd_death": "1", "risk_score": "1.8", "predicted_risk_5y": "0.040", "calibration_decile": "10", "risk_tertile": "high"},
        {"Sequnece": "8", "center": "4", "os_time": "5.5", "cvd_death": "0", "risk_score": "0.9", "predicted_risk_5y": "0.015", "calibration_decile": "5", "risk_tertile": "mid"},
        {"Sequnece": "9", "center": "5", "os_time": "2.5", "cvd_death": "0", "risk_score": "-0.8", "predicted_risk_5y": "0.003", "calibration_decile": "1", "risk_tertile": "low"},
        {"Sequnece": "10", "center": "5", "os_time": "6.5", "cvd_death": "0", "risk_score": "-0.9", "predicted_risk_5y": "0.002", "calibration_decile": "1", "risk_tertile": "low"},
    ]
    lasso_rows = [
        {"Sequnece": row["Sequnece"], "center": row["center"], "os_time": row["os_time"], "cvd_death": row["cvd_death"], "risk_score": str(float(row["risk_score"]) - 0.2)}
        for row in prediction_rows
    ]
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "coxph_validation_predictions.csv",
        ["Sequnece", "center", "os_time", "cvd_death", "risk_score", "predicted_risk_5y", "calibration_decile", "risk_tertile"],
        prediction_rows,
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "lassocox_validation_predictions.csv",
        ["Sequnece", "center", "os_time", "cvd_death", "risk_score"],
        lasso_rows,
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "coxph_calibration_5y.csv",
        ["decile", "n", "events_5y", "mean_predicted_risk_5y", "observed_km_risk_5y"],
        [
            {"decile": "1", "n": "60", "events_5y": "1", "mean_predicted_risk_5y": "0.012", "observed_km_risk_5y": "0.010"},
            {"decile": "5", "n": "60", "events_5y": "3", "mean_predicted_risk_5y": "0.026", "observed_km_risk_5y": "0.032"},
            {"decile": "10", "n": "60", "events_5y": "8", "mean_predicted_risk_5y": "0.051", "observed_km_risk_5y": "0.074"},
        ],
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "coxph_km_risk_groups_5y.csv",
        ["risk_group", "n", "events_5y", "mean_predicted_risk_5y", "observed_km_risk_5y"],
        [
            {"risk_group": "low", "n": "120", "events_5y": "2", "mean_predicted_risk_5y": "0.004", "observed_km_risk_5y": "0.005"},
            {"risk_group": "mid", "n": "120", "events_5y": "4", "mean_predicted_risk_5y": "0.018", "observed_km_risk_5y": "0.020"},
            {"risk_group": "high", "n": "120", "events_5y": "11", "mean_predicted_risk_5y": "0.048", "observed_km_risk_5y": "0.055"},
        ],
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "coxph_dca_5y.csv",
        ["threshold", "net_benefit_model", "net_benefit_treat_all", "net_benefit_treat_none", "treated_fraction_model"],
        [
            {"threshold": "0.005", "net_benefit_model": "0.030", "net_benefit_treat_all": "0.010", "net_benefit_treat_none": "0.0", "treated_fraction_model": "0.40"},
            {"threshold": "0.010", "net_benefit_model": "0.024", "net_benefit_treat_all": "0.005", "net_benefit_treat_none": "0.0", "treated_fraction_model": "0.30"},
            {"threshold": "0.020", "net_benefit_model": "0.018", "net_benefit_treat_all": "-0.002", "net_benefit_treat_none": "0.0", "treated_fraction_model": "0.20"},
        ],
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "derived" / "center_event_distribution.csv",
        ["center", "split_bucket", "n_total", "n_allcause_events", "n_cvd_events"],
        [
            {"center": "1", "split_bucket": "validation", "n_total": "100", "n_allcause_events": "8", "n_cvd_events": "2"},
            {"center": "2", "split_bucket": "validation", "n_total": "120", "n_allcause_events": "10", "n_cvd_events": "1"},
            {"center": "3", "split_bucket": "validation", "n_total": "90", "n_allcause_events": "7", "n_cvd_events": "0"},
            {"center": "25", "split_bucket": "train", "n_total": "110", "n_allcause_events": "9", "n_cvd_events": "3"},
        ],
    )

    report = module.run_time_to_event_direct_migration(study_root=study_root, paper_root=paper_root)

    f2 = json.loads((paper_root / "time_to_event_discrimination_calibration_inputs.json").read_text(encoding="utf-8"))
    f3 = json.loads((paper_root / "time_to_event_grouped_inputs.json").read_text(encoding="utf-8"))
    f4 = json.loads((paper_root / "time_to_event_decision_curve_inputs.json").read_text(encoding="utf-8"))
    t2 = json.loads((paper_root / "time_to_event_performance_summary.json").read_text(encoding="utf-8"))
    ga = json.loads((paper_root / "submission_graphical_abstract.json").read_text(encoding="utf-8"))
    registry_after = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))

    assert report["status"] == "blocked"
    assert report["blockers"] == ["multicenter_generalizability_template_gap"]
    assert len(report["written_files"]) == 7
    assert report["authority_sync"]["status"] == "not_available"
    assert str(paper_root / "display_registry.json") in report["written_files"]

    assert f2["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert f2["displays"][0]["display_id"] == "discrimination_calibration"
    assert f2["displays"][0]["panel_a_title"] == "Validation discrimination"
    assert [item["label"] for item in f2["displays"][0]["discrimination_points"]] == ["CoxPH", "LassoCox"]
    assert [item["group_order"] for item in f2["displays"][0]["calibration_summary"]] == [1, 5, 10]
    assert f2["displays"][0]["calibration_callout"]["group_label"] == "Decile 10"

    assert f3["input_schema_id"] == "time_to_event_grouped_inputs_v1"
    assert f3["displays"][0]["display_id"] == "km_risk_stratification"
    assert f3["displays"][0]["template_id"] == "time_to_event_risk_group_summary"
    assert [item["label"] for item in f3["displays"][0]["risk_group_summaries"]] == [
        "Low risk",
        "Intermediate risk",
        "High risk",
    ]

    assert f4["input_schema_id"] == "time_to_event_decision_curve_inputs_v1"
    assert f4["displays"][0]["display_id"] == "decision_curve"
    assert [item["label"] for item in f4["displays"][0]["series"]] == ["Model", "Treat all"]
    assert f4["displays"][0]["reference_line"]["label"] == "Treat none"

    assert ga["shell_id"] == "submission_graphical_abstract"
    assert ga["catalog_id"] == "GA1"
    assert [item["panel_label"] for item in ga["panels"]] == ["A", "B", "C"]
    assert len(ga["footer_pills"]) == 3

    assert registry_after["displays"][1]["requirement_key"] == "time_to_event_risk_group_summary"

    assert not (paper_root / "multicenter_generalizability_inputs.json").exists()

    assert t2["table_shell_id"] == "table2_time_to_event_performance_summary"
    assert t2["display_id"] == "time_to_event_performance_summary"
    assert [item["label"] for item in t2["columns"]] == ["C-index", "Stratification / utility"]
    assert [item["label"] for item in t2["rows"]] == ["Cardiovascular mortality", "All-cause mortality"]


def test_run_time_to_event_direct_migration_syncs_authority_paper_truth_into_runtime_paper_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.time_to_event_direct_migration")
    study_root = tmp_path / "studies" / "001-dm"
    authority_paper_root = study_root / "paper"
    runtime_paper_root = tmp_path / "runtime" / "paper"

    write_json(authority_paper_root / "display_registry.json", _display_registry_payload())
    write_text(
        authority_paper_root / "tables" / "table2_performance_summary.md",
        "\n".join(
            [
                "# Table 2. Performance summary",
                "",
                "| Endpoint | C-index | Stratification / utility |",
                "| --- | --- | --- |",
                "| Cardiovascular mortality | Ridge 0.857; lasso 0.768 | High-risk tertile: 11 / 17 events; positive DCA at 0.5%-2.0% thresholds |",
                "| All-cause mortality | Supportive Cox line 0.768 | Observed 5-year risk across tertiles: 0.5%, 2.0%, 5.5% |",
                "",
            ]
        )
        + "\n",
    )
    write_json(
        authority_paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "catalog_id": "F1",
            "title": "Study cohort flow",
            "steps": [
                {"step_id": "source", "label": "Source cohort", "n": 15787, "detail": "Frozen analysis cohort"},
                {"step_id": "evaluable", "label": "Evaluable at five years", "n": 14816, "detail": "Complete primary endpoint support"},
                {"step_id": "analysis", "label": "Validation cohort", "n": 7408, "detail": "Five-year cardiovascular mortality endpoint"},
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "cvd_mortality",
                    "label": "Five-year cardiovascular mortality",
                    "event_n": 121,
                    "detail": "Validation endpoint inventory",
                },
                {
                    "endpoint_id": "all_cause_mortality",
                    "label": "Five-year all-cause mortality",
                    "event_n": 388,
                    "detail": "Supportive endpoint inventory",
                },
            ],
        },
    )
    write_json(
        authority_paper_root / "publication_style_profile.json",
        {
            "schema_version": 1,
            "style_profile_id": "authority-paper-style",
            "palette": {"primary": "#123456"},
            "semantic_roles": {"model_curve": "primary"},
            "typography": {"title_size": 12.0},
            "stroke": {"primary_linewidth": 2.0},
        },
    )
    write_json(authority_paper_root / "display_overrides.json", {"version": 1, "displays": []})
    write_json(
        authority_paper_root / "medical_reporting_contract.json",
        {
            "reporting_guideline_family": "TRIPOD",
            "display_registry_required": True,
            "figure_shell_requirements": [
                "cohort_flow_figure",
                "time_to_event_discrimination_calibration_panel",
                "kaplan_meier_grouped",
                "time_to_event_decision_curve",
                "multicenter_generalizability_overview",
            ],
            "required_evidence_templates": [
                "time_to_event_discrimination_calibration_panel",
                "kaplan_meier_grouped",
                "time_to_event_decision_curve",
                "multicenter_generalizability_overview",
            ],
            "display_shell_plan": [
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
            ],
        },
    )
    write_text(authority_paper_root / "draft.md", "# Draft\n")

    write_json(
        runtime_paper_root / "publication_style_profile.json",
        {
            "schema_version": 1,
            "style_profile_id": "stale-runtime-style",
            "palette": {"primary": "#000000"},
            "semantic_roles": {"model_curve": "primary"},
            "typography": {"title_size": 10.0},
            "stroke": {"primary_linewidth": 1.0},
        },
    )

    write_text(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "discrimination_report.md",
        "\n".join(
            [
                "# Validation discrimination",
                "",
                "| model | split | c_index |",
                "| --- | --- | --- |",
                "| CoxPH | validation | 0.857 |",
                "| LassoCox | validation | 0.768 |",
                "",
            ]
        )
        + "\n",
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "coxph_calibration_5y.csv",
        ["decile", "n", "events_5y", "mean_predicted_risk_5y", "observed_km_risk_5y"],
        [
            {"decile": "1", "n": "60", "events_5y": "1", "mean_predicted_risk_5y": "0.012", "observed_km_risk_5y": "0.010"},
            {"decile": "5", "n": "60", "events_5y": "3", "mean_predicted_risk_5y": "0.026", "observed_km_risk_5y": "0.032"},
            {"decile": "10", "n": "60", "events_5y": "8", "mean_predicted_risk_5y": "0.051", "observed_km_risk_5y": "0.074"},
        ],
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "coxph_km_risk_groups_5y.csv",
        ["risk_group", "n", "events_5y", "mean_predicted_risk_5y", "observed_km_risk_5y"],
        [
            {"risk_group": "low", "n": "120", "events_5y": "2", "mean_predicted_risk_5y": "0.004", "observed_km_risk_5y": "0.005"},
            {"risk_group": "mid", "n": "120", "events_5y": "4", "mean_predicted_risk_5y": "0.018", "observed_km_risk_5y": "0.020"},
            {"risk_group": "high", "n": "120", "events_5y": "11", "mean_predicted_risk_5y": "0.048", "observed_km_risk_5y": "0.055"},
        ],
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived" / "coxph_dca_5y.csv",
        ["threshold", "net_benefit_model", "net_benefit_treat_all", "net_benefit_treat_none", "treated_fraction_model"],
        [
            {"threshold": "0.005", "net_benefit_model": "0.030", "net_benefit_treat_all": "0.010", "net_benefit_treat_none": "0.0", "treated_fraction_model": "0.40"},
            {"threshold": "0.010", "net_benefit_model": "0.024", "net_benefit_treat_all": "0.005", "net_benefit_treat_none": "0.0", "treated_fraction_model": "0.30"},
            {"threshold": "0.020", "net_benefit_model": "0.018", "net_benefit_treat_all": "-0.002", "net_benefit_treat_none": "0.0", "treated_fraction_model": "0.20"},
        ],
    )
    write_csv(
        study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "derived" / "center_event_distribution.csv",
        ["center", "split_bucket", "n_total", "n_allcause_events", "n_cvd_events"],
        [
            {"center": "1", "split_bucket": "validation", "n_total": "100", "n_allcause_events": "8", "n_cvd_events": "2"},
            {"center": "2", "split_bucket": "validation", "n_total": "120", "n_allcause_events": "10", "n_cvd_events": "1"},
            {"center": "3", "split_bucket": "validation", "n_total": "90", "n_allcause_events": "7", "n_cvd_events": "0"},
            {"center": "25", "split_bucket": "train", "n_total": "110", "n_allcause_events": "9", "n_cvd_events": "3"},
        ],
    )

    report = module.run_time_to_event_direct_migration(study_root=study_root, paper_root=runtime_paper_root)

    synced_style_profile = json.loads((runtime_paper_root / "publication_style_profile.json").read_text(encoding="utf-8"))
    synced_reporting_contract = json.loads((runtime_paper_root / "medical_reporting_contract.json").read_text(encoding="utf-8"))

    assert report["authority_sync"]["status"] == "synced"
    assert report["authority_sync"]["source_paper_root"] == str(authority_paper_root)
    assert str(runtime_paper_root / "publication_style_profile.json") in report["authority_sync"]["synced_files"]
    assert synced_style_profile["style_profile_id"] == "authority-paper-style"
    assert "time_to_event_risk_group_summary" in synced_reporting_contract["figure_shell_requirements"]
    assert "kaplan_meier_grouped" not in synced_reporting_contract["figure_shell_requirements"]
    assert synced_reporting_contract["display_shell_plan"][2]["requirement_key"] == "time_to_event_risk_group_summary"
    assert (runtime_paper_root / "display_registry.json").exists()
    assert (runtime_paper_root / "cohort_flow.json").exists()
    assert (runtime_paper_root / "tables" / "table2_performance_summary.md").exists()


def test_run_time_to_event_direct_migration_rejects_missing_required_display_binding(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.time_to_event_direct_migration")
    study_root = tmp_path / "studies" / "001-dm"
    paper_root = tmp_path / "paper"
    registry = _display_registry_payload()
    registry["displays"] = [item for item in registry["displays"] if item["requirement_key"] != "multicenter_generalizability_overview"]
    write_json(paper_root / "display_registry.json", registry)

    with pytest.raises(ValueError, match="missing required display binding"):
        module.run_time_to_event_direct_migration(study_root=study_root, paper_root=paper_root)
