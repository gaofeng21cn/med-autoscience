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


def _registry_payload() -> dict:
    return {
        "schema_version": 1,
        "source_contract_path": "paper/medical_reporting_contract.json",
        "displays": [
            {
                "display_id": "cohort_flow",
                "display_kind": "figure",
                "requirement_key": "cohort_flow_figure",
                "catalog_id": "F1",
                "shell_path": "paper/figures/cohort_flow.shell.json",
            },
            {
                "display_id": "baseline_characteristics",
                "display_kind": "table",
                "requirement_key": "table1_baseline_characteristics",
                "catalog_id": "T1",
                "shell_path": "paper/tables/baseline_characteristics.shell.json",
            },
        ],
    }


def test_run_publication_shell_sync_writes_cohort_flow_and_table1_inputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    paper_root = tmp_path / "paper"

    write_json(paper_root / "display_registry.json", _registry_payload())
    write_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "source_contract_path": "paper/medical_reporting_contract.json",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "steps": [],
            "exclusions": [],
            "endpoint_inventory": [],
            "design_panels": [],
        },
    )
    write_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "source_contract_path": "paper/medical_reporting_contract.json",
            "display_id": "baseline_characteristics",
            "catalog_id": "T1",
            "group_columns": [],
            "variables": [],
        },
    )
    write_json(
        study_root / "paper" / "derived" / "cohort_flow.json",
        {
            "study_id": "003-endocrine-burden-followup",
            "dataset_version": "v2026-03-31",
            "source_total_cases": 409,
            "first_surgery_cases": 357,
            "excluded_non_first_surgery": 52,
            "complete_3_month_landmark_cases": 357,
            "complete_later_endpoint_cases": 357,
            "analysis_cases": 357,
            "analysis_event_n": 98,
            "validation_contract": {
                "outer_splits": 5,
                "repeats": 5,
                "inner_splits": 4,
                "tuning_metric": "neg_brier_score",
            },
            "score_definition": {
                "simple_score": "hypopituitarism + e_axis_burden + non_gtr",
                "group_rule": "low=0; intermediate=1-2; high=3-5",
            },
        },
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table1.csv",
        [
            "Characteristic",
            "Overall (N=357)",
            "No later persistent global hypopituitarism (n=259)",
            "Later persistent global hypopituitarism (n=98)",
        ],
        [
            {
                "Characteristic": "Age, years",
                "Overall (N=357)": "51 [40-59]",
                "No later persistent global hypopituitarism (n=259)": "50 [38-58]",
                "Later persistent global hypopituitarism (n=98)": "56 [44-62]",
            },
            {
                "Characteristic": "Female sex, n (%)",
                "Overall (N=357)": "178 (49.9%)",
                "No later persistent global hypopituitarism (n=259)": "130 (50.2%)",
                "Later persistent global hypopituitarism (n=98)": "48 (49.0%)",
            },
        ],
    )

    report = module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)

    cohort_flow = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    table1 = json.loads((paper_root / "baseline_characteristics_schema.json").read_text(encoding="utf-8"))

    assert report["status"] == "synced"
    assert len(report["written_files"]) == 3

    assert cohort_flow["display_id"] == "cohort_flow"
    assert cohort_flow["catalog_id"] == "F1"
    assert cohort_flow["title"] == "Cohort derivation, endpoint inventory, and score-construction design"
    assert [item["step_id"] for item in cohort_flow["steps"]] == [
        "source_total_cases",
        "first_surgery_cases",
        "complete_3_month_landmark_cases",
        "complete_later_endpoint_cases",
        "analysis_cases",
    ]
    assert cohort_flow["steps"][-1]["detail"] == "Later persistent global hypopituitarism events: 98"
    assert cohort_flow["exclusions"] == [
        {
            "exclusion_id": "excluded_non_first_surgery",
            "from_step_id": "source_total_cases",
            "label": "Repeat / non-first-surgery cases",
            "n": 52,
            "detail": "Excluded before the first-surgery landmark cohort",
        }
    ]
    assert cohort_flow["endpoint_inventory"] == [
        {
            "endpoint_id": "later_persistent_global_hypopituitarism",
            "label": "Later persistent global hypopituitarism",
            "event_n": 98,
            "detail": "Primary manuscript endpoint",
        }
    ]
    assert [item["panel_id"] for item in cohort_flow["design_panels"]] == [
        "score_definition",
        "validation_contract",
    ]
    assert cohort_flow["design_panels"][0]["lines"][0]["label"] == "Simple score"
    assert cohort_flow["design_panels"][1]["lines"][0]["label"] == "Repeated nested validation"

    assert table1["display_id"] == "baseline_characteristics"
    assert table1["catalog_id"] == "T1"
    assert table1["title"] == "Baseline characteristics at the 3-month postoperative landmark"
    assert [item["label"] for item in table1["groups"]] == [
        "Overall (N=357)",
        "No later persistent global hypopituitarism (n=259)",
        "Later persistent global hypopituitarism (n=98)",
    ]
    assert [item["label"] for item in table1["variables"]] == ["Age, years", "Female sex, n (%)"]


def test_run_publication_shell_sync_rejects_missing_required_binding(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    paper_root = tmp_path / "paper"
    registry = _registry_payload()
    registry["displays"] = [item for item in registry["displays"] if item["requirement_key"] != "cohort_flow_figure"]
    write_json(paper_root / "display_registry.json", registry)

    with pytest.raises(ValueError, match="missing required display binding"):
        module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)


def test_run_publication_shell_sync_writes_phase_c_and_phase_d_inputs_when_bound(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    paper_root = tmp_path / "paper"

    score_risk_path = study_root / "artifacts" / "run1_followup_stratifier" / "score_risk_table.csv"
    grouped_risk_path = study_root / "artifacts" / "run1_followup_stratifier" / "grouped_risk_table.csv"
    calibration_path = study_root / "artifacts" / "run1_followup_stratifier" / "calibration_curve.csv"
    decision_path = study_root / "artifacts" / "run1_followup_stratifier" / "decision_curve.csv"
    metrics_summary_path = study_root / "artifacts" / "run1_followup_stratifier" / "metrics_summary.json"
    coefficient_path = study_root / "artifacts" / "run1_followup_stratifier" / "coefficient_summary.csv"
    feature_importance_path = study_root / "artifacts" / "run1_followup_stratifier" / "feature_importance_summary.csv"
    table2_path = paper_root / "tables" / "Table2.csv"
    table3_path = paper_root / "tables" / "Table3.csv"

    write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                *_registry_payload()["displays"],
                {
                    "display_id": "risk_layering",
                    "display_kind": "figure",
                    "requirement_key": "risk_layering_monotonic_bars",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/risk_layering.shell.json",
                },
                {
                    "display_id": "calibration_decision",
                    "display_kind": "figure",
                    "requirement_key": "binary_calibration_decision_curve_panel",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/calibration_decision.shell.json",
                },
                {
                    "display_id": "model_audit",
                    "display_kind": "figure",
                    "requirement_key": "model_complexity_audit_panel",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/model_audit.shell.json",
                },
                {
                    "display_id": "performance_summary",
                    "display_kind": "table",
                    "requirement_key": "performance_summary_table_generic",
                    "catalog_id": "T2",
                    "shell_path": "paper/tables/performance_summary.shell.json",
                },
                {
                    "display_id": "risk_event_summary",
                    "display_kind": "table",
                    "requirement_key": "grouped_risk_event_summary_table",
                    "catalog_id": "T3",
                    "shell_path": "paper/tables/risk_event_summary.shell.json",
                },
            ],
        },
    )
    write_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "Figure2",
                    "title": "Monotonic risk layering of the 3-month endocrine burden score",
                    "source_paths": [str(score_risk_path), str(grouped_risk_path)],
                },
                {
                    "figure_id": "Figure3",
                    "title": "Calibration and decision-curve comparison of the candidate packages",
                    "source_paths": [str(calibration_path), str(decision_path)],
                },
                {
                    "figure_id": "Figure4",
                    "title": "Unified model comparison and comparative model assessment",
                    "source_paths": [str(metrics_summary_path), str(coefficient_path), str(feature_importance_path)],
                },
            ],
        },
    )
    write_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "Table2",
                    "title": "Unified repeated nested validation results across candidate packages",
                    "csv_path": str(table2_path),
                },
                {
                    "table_id": "Table3",
                    "title": "Event rates across the simple-score and grouped-risk surfaces",
                    "csv_path": str(table3_path),
                },
            ],
        },
    )
    write_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "source_contract_path": "paper/medical_reporting_contract.json",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "steps": [],
            "exclusions": [],
            "endpoint_inventory": [],
            "design_panels": [],
        },
    )
    write_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "source_contract_path": "paper/medical_reporting_contract.json",
            "display_id": "baseline_characteristics",
            "catalog_id": "T1",
            "groups": [],
            "variables": [],
        },
    )
    write_json(
        study_root / "paper" / "derived" / "cohort_flow.json",
        {
            "study_id": "003-endocrine-burden-followup",
            "dataset_version": "v2026-03-31",
            "source_total_cases": 409,
            "first_surgery_cases": 357,
            "excluded_non_first_surgery": 52,
            "complete_3_month_landmark_cases": 357,
            "complete_later_endpoint_cases": 357,
            "analysis_cases": 357,
            "analysis_event_n": 98,
            "validation_contract": {
                "outer_splits": 5,
                "repeats": 5,
                "inner_splits": 4,
                "tuning_metric": "neg_brier_score",
            },
            "score_definition": {
                "simple_score": "hypopituitarism + e_axis_burden + non_gtr",
                "group_rule": "low=0; intermediate=1-2; high=3-5",
            },
        },
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table1.csv",
        ["Characteristic", "Overall", "No event", "Event"],
        [
            {"Characteristic": "Age, years", "Overall": "51 [40-59]", "No event": "50 [38-58]", "Event": "56 [44-62]"},
        ],
    )
    write_csv(
        score_risk_path,
        ["score_band", "n", "events", "risk_rate"],
        [
            {"score_band": "0", "n": "95", "events": "8", "risk_rate": "0.0842"},
            {"score_band": "1", "n": "98", "events": "18", "risk_rate": "0.1837"},
            {"score_band": "2", "n": "98", "events": "35", "risk_rate": "0.3571"},
            {"score_band": "3", "n": "54", "events": "29", "risk_rate": "0.5370"},
            {"score_band": "4+", "n": "12", "events": "8", "risk_rate": "0.6667"},
        ],
    )
    write_csv(
        grouped_risk_path,
        ["risk_group", "n", "events", "risk_rate"],
        [
            {"risk_group": "low", "n": "95", "events": "8", "risk_rate": "0.0842"},
            {"risk_group": "intermediate", "n": "196", "events": "53", "risk_rate": "0.2704"},
            {"risk_group": "high", "n": "66", "events": "37", "risk_rate": "0.5606"},
        ],
    )
    write_csv(
        calibration_path,
        ["model_id", "model_label", "calibration_bin", "n", "mean_predicted_probability", "observed_probability"],
        [
            {"model_id": "simple_score_only", "model_label": "Simple score only", "calibration_bin": "0", "n": "36", "mean_predicted_probability": "0.0943", "observed_probability": "0.1389"},
            {"model_id": "simple_score_only", "model_label": "Simple score only", "calibration_bin": "1", "n": "36", "mean_predicted_probability": "0.6004", "observed_probability": "0.5833"},
            {"model_id": "core_logistic", "model_label": "Core logistic", "calibration_bin": "0", "n": "36", "mean_predicted_probability": "0.0968", "observed_probability": "0.1111"},
            {"model_id": "core_logistic", "model_label": "Core logistic", "calibration_bin": "1", "n": "36", "mean_predicted_probability": "0.5927", "observed_probability": "0.5278"},
            {"model_id": "context_logistic", "model_label": "Context logistic", "calibration_bin": "0", "n": "36", "mean_predicted_probability": "0.0717", "observed_probability": "0.0833"},
            {"model_id": "context_logistic", "model_label": "Context logistic", "calibration_bin": "1", "n": "36", "mean_predicted_probability": "0.6481", "observed_probability": "0.6111"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "calibration_bin": "0", "n": "36", "mean_predicted_probability": "0.0811", "observed_probability": "0.1111"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "calibration_bin": "1", "n": "36", "mean_predicted_probability": "0.7012", "observed_probability": "0.5556"},
            {"model_id": "coarse_q006", "model_label": "Coarse q006", "calibration_bin": "0", "n": "36", "mean_predicted_probability": "0.0639", "observed_probability": "0.0833"},
            {"model_id": "coarse_q006", "model_label": "Coarse q006", "calibration_bin": "1", "n": "36", "mean_predicted_probability": "0.5964", "observed_probability": "0.5556"},
        ],
    )
    write_csv(
        decision_path,
        ["model_id", "model_label", "threshold", "net_benefit"],
        [
            {"model_id": "treat_all", "model_label": "Treat all", "threshold": "0.15", "net_benefit": "0.1465"},
            {"model_id": "treat_none", "model_label": "Treat none", "threshold": "0.15", "net_benefit": "0.0"},
            {"model_id": "simple_score_only", "model_label": "Simple score only", "threshold": "0.15", "net_benefit": "0.1671"},
            {"model_id": "core_logistic", "model_label": "Core logistic", "threshold": "0.15", "net_benefit": "0.1671"},
            {"model_id": "context_logistic", "model_label": "Context logistic", "threshold": "0.15", "net_benefit": "0.1615"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "threshold": "0.15", "net_benefit": "0.1442"},
            {"model_id": "coarse_q006", "model_label": "Coarse q006", "threshold": "0.15", "net_benefit": "0.1669"},
            {"model_id": "treat_all", "model_label": "Treat all", "threshold": "0.30", "net_benefit": "-0.0364"},
            {"model_id": "treat_none", "model_label": "Treat none", "threshold": "0.30", "net_benefit": "0.0"},
            {"model_id": "simple_score_only", "model_label": "Simple score only", "threshold": "0.30", "net_benefit": "0.0912"},
            {"model_id": "core_logistic", "model_label": "Core logistic", "threshold": "0.30", "net_benefit": "0.0889"},
            {"model_id": "context_logistic", "model_label": "Context logistic", "threshold": "0.30", "net_benefit": "0.0831"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "threshold": "0.30", "net_benefit": "0.0411"},
            {"model_id": "coarse_q006", "model_label": "Coarse q006", "threshold": "0.30", "net_benefit": "0.0760"},
        ],
    )
    write_json(
        metrics_summary_path,
        {
            "model_metrics": [
                {"model_id": "simple_score_only", "model_label": "Simple score only", "roc_auc": 0.7081, "brier_score": 0.1708, "calibration_slope": 1.0218},
                {"model_id": "core_logistic", "model_label": "Core logistic", "roc_auc": 0.6987, "brier_score": 0.1733, "calibration_slope": 0.9996},
                {"model_id": "context_logistic", "model_label": "Context logistic", "roc_auc": 0.7254, "brier_score": 0.1749, "calibration_slope": 0.8669},
                {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "roc_auc": 0.7235, "brier_score": 0.2036, "calibration_slope": 1.2603},
                {"model_id": "coarse_q006", "model_label": "Coarse q006", "roc_auc": 0.7189, "brier_score": 0.1759, "calibration_slope": 0.9037},
            ]
        },
    )
    write_csv(
        coefficient_path,
        ["model_id", "model_label", "feature", "coef_mean", "coef_std", "fit_count", "odds_ratio_mean"],
        [
            {"model_id": "core_logistic", "model_label": "Core logistic", "feature": "hypopituitarism", "coef_mean": "0.8423", "coef_std": "0.1816", "fit_count": "25", "odds_ratio_mean": "2.3217"},
            {"model_id": "core_logistic", "model_label": "Core logistic", "feature": "e_axis_burden", "coef_mean": "0.7302", "coef_std": "0.0702", "fit_count": "25", "odds_ratio_mean": "2.0755"},
            {"model_id": "core_logistic", "model_label": "Core logistic", "feature": "non_gtr", "coef_mean": "0.6760", "coef_std": "0.1639", "fit_count": "25", "odds_ratio_mean": "1.9660"},
        ],
    )
    write_csv(
        feature_importance_path,
        ["model_id", "model_label", "feature", "importance_mean", "importance_std", "fit_count"],
        [
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "feature": "e_axis_burden", "importance_mean": "0.2343", "importance_std": "0.0335", "fit_count": "25"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "feature": "diameter", "importance_mean": "0.2107", "importance_std": "0.0164", "fit_count": "25"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "feature": "age", "importance_mean": "0.1986", "importance_std": "0.0291", "fit_count": "25"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "feature": "hypopituitarism", "importance_mean": "0.1919", "importance_std": "0.0350", "fit_count": "25"},
            {"model_id": "benchmark_rf", "model_label": "Benchmark RF", "feature": "knosp", "importance_mean": "0.0535", "importance_std": "0.0097", "fit_count": "25"},
        ],
    )
    write_csv(
        table2_path,
        ["Model", "AUROC", "AUPRC", "Brier score", "Calibration intercept", "Calibration slope"],
        [
            {"Model": "Simple 3-month score", "AUROC": "0.7081", "AUPRC": "0.4740", "Brier score": "0.1708", "Calibration intercept": "-0.0028", "Calibration slope": "1.0218"},
            {"Model": "Context-enhanced logistic audit", "AUROC": "0.7254", "AUPRC": "0.4933", "Brier score": "0.1749", "Calibration intercept": "-0.1349", "Calibration slope": "0.8669"},
        ],
    )
    write_csv(
        table3_path,
        ["Surface", "Stratum", "Cases", "Events", "Risk of later persistent global hypopituitarism"],
        [
            {"Surface": "Score band", "Stratum": "0", "Cases": "95", "Events": "8", "Risk of later persistent global hypopituitarism": "8.4%"},
            {"Surface": "Grouped risk", "Stratum": "High", "Cases": "66", "Events": "37", "Risk of later persistent global hypopituitarism": "56.1%"},
        ],
    )

    report = module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)

    assert report["status"] == "synced"
    assert len(report["written_files"]) == 8

    risk_layering = json.loads((paper_root / "risk_layering_monotonic_inputs.json").read_text(encoding="utf-8"))
    binary_panel = json.loads((paper_root / "binary_calibration_decision_curve_panel_inputs.json").read_text(encoding="utf-8"))
    model_audit = json.loads((paper_root / "model_complexity_audit_panel_inputs.json").read_text(encoding="utf-8"))
    performance_table = json.loads((paper_root / "performance_summary_table_generic.json").read_text(encoding="utf-8"))
    grouped_table = json.loads((paper_root / "grouped_risk_event_summary_table.json").read_text(encoding="utf-8"))

    assert risk_layering["displays"][0]["catalog_id"] == "F2"
    assert risk_layering["displays"][0]["left_bars"][0] == {"label": "0", "cases": 95, "events": 8, "risk": 0.0842}
    assert risk_layering["displays"][0]["right_bars"][1]["label"] == "Intermediate"

    assert binary_panel["displays"][0]["catalog_id"] == "F3"
    assert binary_panel["displays"][0]["decision_focus_window"] == {"xmin": 0.15, "xmax": 0.4}
    assert [item["label"] for item in binary_panel["displays"][0]["decision_reference_lines"]] == ["Treat none", "Treat all"]
    assert binary_panel["displays"][0]["decision_series"][0]["label"] == "Simple 3-month score"

    assert model_audit["displays"][0]["catalog_id"] == "F4"
    assert [item["panel_label"] for item in model_audit["displays"][0]["metric_panels"]] == ["A", "B", "C"]
    assert model_audit["displays"][0]["audit_panels"][0]["rows"][0]["label"] == "Preoperative hypopituitarism"
    assert model_audit["displays"][0]["audit_panels"][1]["rows"][0]["label"] == "3-month axis burden"

    assert performance_table["catalog_id"] == "T2"
    assert performance_table["row_header_label"] == "Model"
    assert performance_table["rows"][0]["label"] == "Simple 3-month score"

    assert grouped_table["catalog_id"] == "T3"
    assert grouped_table["risk_column_label"] == "Risk of later persistent global hypopituitarism"
    assert grouped_table["rows"][1]["risk_display"] == "56.1%"
