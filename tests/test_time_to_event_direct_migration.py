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
                "| Metric | Primary endpoint | Supportive endpoint |",
                "| --- | --- | --- |",
                "| Validation n | 7,408 | 7,408 |",
                "| C-index | 0.857 | 0.768 |",
                "| Role | Primary | Supportive |",
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

    assert report["status"] == "blocked"
    assert report["blockers"] == ["multicenter_generalizability_template_gap"]
    assert len(report["written_files"]) == 5

    assert f2["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert f2["displays"][0]["display_id"] == "discrimination_calibration"
    assert [item["label"] for item in f2["displays"][0]["discrimination_series"]] == ["CoxPH", "LassoCox"]
    assert [item["label"] for item in f2["displays"][0]["calibration_groups"]] == ["Decile 1", "Decile 5", "Decile 10"]

    assert f3["input_schema_id"] == "time_to_event_grouped_inputs_v1"
    assert f3["displays"][0]["display_id"] == "km_risk_stratification"
    assert [item["label"] for item in f3["displays"][0]["groups"]] == ["Low risk", "Intermediate risk", "High risk"]

    assert f4["input_schema_id"] == "time_to_event_decision_curve_inputs_v1"
    assert f4["displays"][0]["display_id"] == "decision_curve"
    assert [item["label"] for item in f4["displays"][0]["series"]] == ["Model", "Treat all"]
    assert f4["displays"][0]["reference_line"]["label"] == "Treat none"

    assert not (paper_root / "multicenter_generalizability_inputs.json").exists()

    assert t2["table_shell_id"] == "table2_time_to_event_performance_summary"
    assert t2["display_id"] == "time_to_event_performance_summary"
    assert [item["label"] for item in t2["columns"]] == ["Primary endpoint", "Supportive endpoint"]
    assert [item["label"] for item in t2["rows"]] == ["Validation n", "C-index", "Role"]


def test_run_time_to_event_direct_migration_rejects_missing_required_display_binding(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.time_to_event_direct_migration")
    study_root = tmp_path / "studies" / "001-dm"
    paper_root = tmp_path / "paper"
    registry = _display_registry_payload()
    registry["displays"] = [item for item in registry["displays"] if item["requirement_key"] != "multicenter_generalizability_overview"]
    write_json(paper_root / "display_registry.json", registry)

    with pytest.raises(ValueError, match="missing required display binding"):
        module.run_time_to_event_direct_migration(study_root=study_root, paper_root=paper_root)
