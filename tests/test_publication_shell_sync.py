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


def test_run_publication_shell_sync_uses_study_design_cohort_flow_fallback(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "002-early-residual-risk"
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
        paper_root / "derived" / "study_design_cohort_flow.json",
        {
            "study_id": "002-early-residual-risk",
            "dataset_version": "v2026-03-31",
            "source_total_cases": 409,
            "first_surgery_cases": 357,
            "excluded_non_first_surgery": 52,
            "complete_3_month_landmark_cases": 357,
            "complete_later_endpoint_cases": 357,
            "analysis_cases": 357,
            "analysis_event_n": 57,
            "validation_contract": {
                "outer_splits": 5,
                "repeats": 20,
                "inner_splits": 4,
                "tuning_metric": "roc_auc",
            },
            "score_definition": {
                "simple_score": "clinically informed preoperative model",
                "group_rule": "low / intermediate / high predicted-risk tertiles",
            },
        },
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table1.csv",
        ["Characteristic", "Overall (N=357)", "GTR (n=300)", "Non-GTR (n=57)"],
        [
            {
                "Characteristic": "Age, years",
                "Overall (N=357)": "51 [40-59]",
                "GTR (n=300)": "50 [39-58]",
                "Non-GTR (n=57)": "56 [44-62]",
            }
        ],
    )

    report = module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)

    cohort_flow = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    assert report["status"] == "synced"
    assert report["source_paths"]["cohort_flow_source"].endswith("paper/derived/study_design_cohort_flow.json")
    assert cohort_flow["steps"][0]["step_id"] == "source_total_cases"
    assert cohort_flow["steps"][-1]["detail"] == "Later persistent global hypopituitarism events: 57"
    assert cohort_flow["exclusions"][0]["n"] == 52


def test_run_publication_shell_sync_normalizes_publication_safe_cohort_design_labels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "002-early-residual-risk"
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
            "cohort_flow": [
                {"step_id": "source_total_cases", "label": "Source study records", "n": 409, "detail": ""},
                {"step_id": "analysis_cases", "label": "Final analysis cohort", "n": 357, "detail": ""},
            ],
            "analysis_cohort": {"non_gtr_cases": 57},
            "validation_contract": {
                "outer_splits": 5,
                "repeats": 20,
                "inner_splits": 4,
            },
            "model_hierarchy": [
                {
                    "label": "Preoperative Core Model",
                    "role": "confirmed comparator",
                    "surface": "same feature surface as the primary model",
                },
                {
                    "label": "Clinical Utility Model",
                    "role": "knowledge-guided primary model",
                    "surface": "same preoperative variables plus prespecified engineered terms",
                },
                {
                    "label": "Pathology-Augmented Model",
                    "role": "secondary postoperative comparison",
                    "surface": "primary model plus pathology variables",
                },
            ],
        },
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table1.csv",
        ["Characteristic", "Overall (N=357)"],
        [{"Characteristic": "Age, years", "Overall (N=357)": "51 [40-59]"}],
    )

    module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)

    cohort_flow = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    design_panels = {item["panel_id"]: item for item in cohort_flow["design_panels"]}

    assert design_panels["validation_contract"]["title"] == "Validation design"
    assert design_panels["model_hierarchy"]["lines"][0]["label"] == "Core preoperative model"
    assert design_panels["model_hierarchy"]["lines"][1]["label"] == "Clinically informed preoperative model"
    assert design_panels["model_hierarchy"]["lines"][2]["label"] == "Pathology-extended comparison"
    assert "surface" not in design_panels["model_hierarchy"]["lines"][0]["detail"]


def test_run_publication_shell_sync_rejects_missing_required_binding(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    paper_root = tmp_path / "paper"
    registry = _registry_payload()
    registry["displays"] = [item for item in registry["displays"] if item["requirement_key"] != "cohort_flow_figure"]
    write_json(paper_root / "display_registry.json", registry)

    with pytest.raises(ValueError, match="missing required display binding"):
        module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)


def test_run_publication_shell_sync_builds_model_complexity_metrics_from_table2_when_metrics_json_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    paper_root = tmp_path / "paper"

    write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                *_registry_payload()["displays"],
                {
                    "display_id": "model_audit",
                    "display_kind": "figure",
                    "requirement_key": "model_complexity_audit_panel",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/model_audit.shell.json",
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
                    "figure_id": "F3",
                    "title": "Clinical coherence and coefficient stability of the clinically informed preoperative model",
                    "source_artifacts": [
                        "analysis/early_residual_risk_experiment.py",
                        "tests/test_early_residual_risk_experiment.py",
                        "datasets/master/v2026-03-31/nfpitnet_analysis.csv",
                    ],
                    "derived_artifact_paths": [
                        "paper/derived/clinical_utility_model_coefficient_stability.csv",
                        "paper/derived/clinical_utility_model_domain_summary.csv",
                    ],
                },
                {
                    "figure_id": "F4",
                    "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
                    "source_artifacts": [
                        "artifacts/experiment/run-535a972f/main_lighttree/predictions_A0.csv",
                        "artifacts/experiment/run-535a972f/main_lighttree/predictions_A1.csv",
                    ],
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
            "group_columns": [],
            "variables": [],
        },
    )
    write_json(
        paper_root / "model_complexity_audit_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "model_complexity_audit_panel_inputs_v1",
            "source_contract_path": "paper/medical_reporting_contract.json",
            "status": "required_pending_materialization",
            "displays": [{"display_id": "model_audit", "template_id": "model_complexity_audit_panel", "catalog_id": "F4"}],
        },
    )
    write_json(
        study_root / "paper" / "derived" / "cohort_flow.json",
        {
            "study_id": "002-early-residual-risk",
            "dataset_version": "v2026-03-31",
            "source_total_cases": 409,
            "first_surgery_cases": 357,
            "excluded_non_first_surgery": 52,
            "complete_3_month_landmark_cases": 357,
            "complete_later_endpoint_cases": 357,
            "analysis_cases": 357,
            "analysis_event_n": 57,
            "validation_contract": {
                "outer_splits": 5,
                "repeats": 20,
                "inner_splits": 4,
                "tuning_metric": "roc_auc",
            },
            "score_definition": {
                "simple_score": "clinically informed preoperative model",
                "group_rule": "low / intermediate / high predicted-risk tertiles",
            },
        },
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table1.csv",
        ["Characteristic", "Overall (N=357)", "GTR (n=300)", "Non-GTR (n=57)"],
        [
            {
                "Characteristic": "Age, years",
                "Overall (N=357)": "51 [40-59]",
                "GTR (n=300)": "50 [39-58]",
                "Non-GTR (n=57)": "56 [44-62]",
            }
        ],
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table2.csv",
        ["Model", "AUROC", "AUPRC", "Brier score", "Calibration intercept", "Calibration slope"],
        [
            {
                "Model": "Core preoperative model",
                "AUROC": "0.8022",
                "AUPRC": "0.4479",
                "Brier score": "0.1433",
                "Calibration intercept": "-0.3108",
                "Calibration slope": "2.4065",
            },
            {
                "Model": "Clinically informed preoperative model",
                "AUROC": "0.8004",
                "AUPRC": "0.4500",
                "Brier score": "0.1099",
                "Calibration intercept": "0.0619",
                "Calibration slope": "1.0442",
            },
            {
                "Model": "Pathology-augmented model",
                "AUROC": "0.7999",
                "AUPRC": "0.4606",
                "Brier score": "0.1090",
                "Calibration intercept": "0.0586",
                "Calibration slope": "1.0395",
            },
            {
                "Model": "Elastic-net comparison model",
                "AUROC": "0.8006",
                "AUPRC": "0.4744",
                "Brier score": "0.1086",
                "Calibration intercept": "0.1581",
                "Calibration slope": "1.1096",
            },
            {
                "Model": "Random forest comparison model",
                "AUROC": "0.8359",
                "AUPRC": "0.5174",
                "Brier score": "0.1011",
                "Calibration intercept": "-0.2038",
                "Calibration slope": "0.8017",
            },
        ],
    )
    write_csv(
        paper_root / "derived" / "clinical_utility_model_coefficient_stability.csv",
        ["outer_fold", "feature_name", "domain", "coefficient", "odds_ratio", "selected_c", "intercept", "direction"],
        [
            {
                "outer_fold": "1",
                "feature_name": "age",
                "domain": "Demographics",
                "coefficient": "-0.1106",
                "odds_ratio": "0.8953",
                "selected_c": "0.1",
                "intercept": "-2.1272",
                "direction": "negative",
            },
            {
                "outer_fold": "1",
                "feature_name": "diameter",
                "domain": "Tumor burden",
                "coefficient": "0.5800",
                "odds_ratio": "1.7860",
                "selected_c": "0.1",
                "intercept": "-2.1272",
                "direction": "positive",
            },
        ],
    )
    write_csv(
        paper_root / "derived" / "clinical_utility_model_domain_summary.csv",
        ["domain", "feature_count", "mean_abs_coefficient", "median_abs_coefficient", "mean_sign_consistency"],
        [
            {
                "domain": "Tumor burden",
                "feature_count": "2",
                "mean_abs_coefficient": "0.3444",
                "median_abs_coefficient": "0.3444",
                "mean_sign_consistency": "1.0",
            },
            {
                "domain": "Invasion burden",
                "feature_count": "5",
                "mean_abs_coefficient": "0.1091",
                "median_abs_coefficient": "0.0822",
                "mean_sign_consistency": "0.8620",
            },
        ],
    )

    report = module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)

    model_audit = json.loads((paper_root / "model_complexity_audit_panel_inputs.json").read_text(encoding="utf-8"))

    assert report["status"] == "synced"
    assert report["source_paths"]["model_complexity_audit_sources"][0].endswith("artifacts/final/tables/Table2.csv")
    assert [item["label"] for item in model_audit["displays"][0]["metric_panels"][0]["rows"]] == [
        "Core preoperative model",
        "Clinically informed preoperative model",
        "Pathology-augmented model",
        "Elastic-net comparison model",
        "Random forest comparison model",
    ]
    assert model_audit["displays"][0]["audit_panels"][0]["rows"][0]["label"] == "Age"
    assert model_audit["displays"][0]["audit_panels"][1]["rows"][0]["label"] == "Tumor burden"


def test_run_publication_shell_sync_falls_back_from_noncanonical_table3_and_uses_figure2_summary(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    paper_root = tmp_path / "paper"
    bundle_root = tmp_path / "bundle"

    risk_stratification_path = bundle_root / "clinical_utility" / "risk_stratification.csv"
    summary_path = bundle_root / "clinical_utility" / "summary.json"

    write_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                *_registry_payload()["displays"],
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
                    "figure_id": "F2",
                    "title": "Clinical utility of the clinically informed preoperative model compared with the core preoperative comparator",
                    "source_paths": [str(risk_stratification_path), str(summary_path)],
                },
                {
                    "figure_id": "F4",
                    "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
                    "source_paths": [str(risk_stratification_path)],
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
            "group_columns": [],
            "variables": [],
        },
    )
    write_json(
        study_root / "paper" / "derived" / "cohort_flow.json",
        {
            "study_id": "002-early-residual-risk",
            "dataset_version": "v2026-03-31",
            "source_total_cases": 409,
            "first_surgery_cases": 357,
            "excluded_non_first_surgery": 52,
            "complete_3_month_landmark_cases": 357,
            "complete_later_endpoint_cases": 357,
            "analysis_cases": 357,
            "analysis_event_n": 57,
            "validation_contract": {
                "outer_splits": 5,
                "repeats": 20,
                "inner_splits": 4,
                "tuning_metric": "roc_auc",
            },
            "score_definition": {
                "simple_score": "clinically informed preoperative model",
                "group_rule": "low / intermediate / high predicted-risk tertiles",
            },
        },
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table1.csv",
        ["Characteristic", "Overall (N=357)", "GTR (n=300)", "Non-GTR (n=57)"],
        [
            {
                "Characteristic": "Age, years",
                "Overall (N=357)": "51 [40-59]",
                "GTR (n=300)": "50 [39-58]",
                "Non-GTR (n=57)": "56 [44-62]",
            }
        ],
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table3.csv",
        ["Domain", "Slice", "Cases", "Events", "AUROC", "Brier", "Cal. slope", "Note"],
        [
            {
                "Domain": "Tumor size",
                "Slice": "Non-large",
                "Cases": "3",
                "Events": "0",
                "AUROC": "NA",
                "Brier": "NA",
                "Cal. slope": "NA",
                "Note": "Insufficient support",
            }
        ],
    )
    write_csv(
        risk_stratification_path,
        [
            "model",
            "risk_group",
            "n",
            "non_gtr_events",
            "observed_non_gtr_rate",
            "mean_predicted_non_gtr_risk",
        ],
        [
            {
                "model": "A0",
                "risk_group": "low",
                "n": "118",
                "non_gtr_events": "5",
                "observed_non_gtr_rate": "0.0424",
                "mean_predicted_non_gtr_risk": "0.2416",
            },
            {
                "model": "A0",
                "risk_group": "high",
                "n": "118",
                "non_gtr_events": "44",
                "observed_non_gtr_rate": "0.3729",
                "mean_predicted_non_gtr_risk": "0.4667",
            },
            {
                "model": "A1",
                "risk_group": "low",
                "n": "119",
                "non_gtr_events": "4",
                "observed_non_gtr_rate": "0.0336",
                "mean_predicted_non_gtr_risk": "0.0432",
            },
            {
                "model": "A1",
                "risk_group": "high",
                "n": "119",
                "non_gtr_events": "42",
                "observed_non_gtr_rate": "0.3529",
                "mean_predicted_non_gtr_risk": "0.3318",
            },
        ],
    )
    write_json(
        summary_path,
        {
            "models": ["A0", "A1"],
            "candidate_story_model": "A1",
            "overall_metrics": {
                "A0": {"roc_auc": 0.8022},
                "A1": {"roc_auc": 0.8004},
            },
        },
    )

    report = module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)

    grouped_table = json.loads((paper_root / "grouped_risk_event_summary_table.json").read_text(encoding="utf-8"))

    assert report["status"] == "synced"
    assert report["source_paths"]["grouped_risk_event_table_source"].endswith("risk_stratification.csv")
    assert [row["surface"] for row in grouped_table["rows"]] == [
        "Core preoperative model",
        "Core preoperative model",
        "Clinically informed preoperative model",
        "Clinically informed preoperative model",
    ]
    assert grouped_table["rows"][-1] == {
        "row_id": "clinically_informed_preoperative_model_high",
        "surface": "Clinically informed preoperative model",
        "stratum": "High",
        "cases": 119,
        "events": 42,
        "risk_display": "35.3%",
    }


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


def test_run_publication_shell_sync_supports_phase_c_and_phase_d_inputs_from_legacy_bundle_artifacts(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_shell_sync")
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    bundle_root = tmp_path / "legacy-paper-bundle"
    paper_root = bundle_root / "paper"

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
            "study_id": "002-early-residual-risk",
            "dataset_version": "v2026-03-31",
            "source_total_cases": 409,
            "first_surgery_cases": 357,
            "excluded_non_first_surgery": 52,
            "complete_3_month_landmark_cases": 357,
            "complete_later_endpoint_cases": 357,
            "analysis_cases": 357,
            "analysis_event_n": 57,
            "validation_contract": {
                "outer_splits": 5,
                "repeats": 20,
                "inner_splits": 4,
                "tuning_metric": "roc_auc",
            },
            "score_definition": {
                "simple_score": "clinically informed preoperative model",
                "group_rule": "low / intermediate / high predicted-risk tertiles",
            },
        },
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table1.csv",
        ["Characteristic", "Overall (N=357)", "GTR (n=300)", "Non-GTR (n=57)"],
        [
            {
                "Characteristic": "Age, years",
                "Overall (N=357)": "51 [40-59]",
                "GTR (n=300)": "50 [39-58]",
                "Non-GTR (n=57)": "56 [44-62]",
            }
        ],
    )
    write_csv(
        study_root / "artifacts" / "final" / "tables" / "Table2.csv",
        ["Model", "AUROC", "AUPRC", "Brier score", "Calibration intercept", "Calibration slope"],
        [
            {
                "Model": "Core preoperative model",
                "AUROC": "0.8022",
                "AUPRC": "0.4479",
                "Brier score": "0.1433",
                "Calibration intercept": "-0.3108",
                "Calibration slope": "2.4065",
            },
            {
                "Model": "Clinically informed preoperative model",
                "AUROC": "0.8004",
                "AUPRC": "0.4500",
                "Brier score": "0.1099",
                "Calibration intercept": "0.0619",
                "Calibration slope": "1.0442",
            },
        ],
    )
    write_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F2",
                    "title": "Clinical utility of the clinically informed preoperative model compared with the core preoperative comparator",
                    "source_artifacts": [
                        "artifacts/analysis/run-535a972f/clinical_utility/calibration_curve.csv",
                        "artifacts/analysis/run-535a972f/clinical_utility/decision_curve.csv",
                        "artifacts/analysis/run-535a972f/clinical_utility/risk_stratification.csv",
                        "artifacts/analysis/run-535a972f/clinical_utility/summary.json",
                    ],
                },
                {
                    "figure_id": "F3",
                    "title": "Clinical coherence and coefficient stability of the clinically informed preoperative model",
                    "source_artifacts": [
                        "artifacts/experiment/run-535a972f/main_lighttree/metrics.json",
                    ],
                    "derived_artifact_paths": [
                        "paper/derived/clinical_utility_model_coefficient_stability.csv",
                        "paper/derived/clinical_utility_model_domain_summary.csv",
                    ],
                },
                {
                    "figure_id": "F4",
                    "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
                    "source_artifacts": [
                        "artifacts/analysis/run-535a972f/clinical_utility/risk_stratification.csv",
                    ],
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
                    "table_id": "T2",
                    "title": "Comparative performance of the preoperative models and contextual comparison models",
                    "csv_path": str(study_root / "artifacts" / "final" / "tables" / "Table2.csv"),
                },
                {
                    "table_id": "T3",
                    "title": "Grouped risk-event summary for the primary and comparator models",
                },
            ],
        },
    )
    write_csv(
        bundle_root / "artifacts" / "analysis" / "run-535a972f" / "clinical_utility" / "calibration_curve.csv",
        ["model", "bin_id", "mean_predicted_probability", "observed_non_gtr_rate", "n"],
        [
            {
                "model": "A0",
                "bin_id": "0",
                "mean_predicted_probability": "0.2131",
                "observed_non_gtr_rate": "0.0278",
                "n": "36",
            },
            {
                "model": "A0",
                "bin_id": "1",
                "mean_predicted_probability": "0.2861",
                "observed_non_gtr_rate": "0.1143",
                "n": "36",
            },
            {
                "model": "A1",
                "bin_id": "0",
                "mean_predicted_probability": "0.0432",
                "observed_non_gtr_rate": "0.0336",
                "n": "119",
            },
            {
                "model": "A1",
                "bin_id": "1",
                "mean_predicted_probability": "0.3318",
                "observed_non_gtr_rate": "0.3529",
                "n": "119",
            },
        ],
    )
    write_csv(
        bundle_root / "artifacts" / "analysis" / "run-535a972f" / "clinical_utility" / "decision_curve.csv",
        ["model", "threshold", "net_benefit_model", "net_benefit_treat_all", "net_benefit_treat_none"],
        [
            {
                "model": "A0",
                "threshold": "0.15",
                "net_benefit_model": "0.1671",
                "net_benefit_treat_all": "0.1465",
                "net_benefit_treat_none": "0.0",
            },
            {
                "model": "A1",
                "threshold": "0.15",
                "net_benefit_model": "0.1715",
                "net_benefit_treat_all": "0.1465",
                "net_benefit_treat_none": "0.0",
            },
            {
                "model": "A0",
                "threshold": "0.30",
                "net_benefit_model": "0.0912",
                "net_benefit_treat_all": "-0.0364",
                "net_benefit_treat_none": "0.0",
            },
            {
                "model": "A1",
                "threshold": "0.30",
                "net_benefit_model": "0.0993",
                "net_benefit_treat_all": "-0.0364",
                "net_benefit_treat_none": "0.0",
            },
        ],
    )
    write_csv(
        bundle_root / "artifacts" / "analysis" / "run-535a972f" / "clinical_utility" / "risk_stratification.csv",
        [
            "model",
            "risk_group",
            "n",
            "non_gtr_events",
            "observed_non_gtr_rate",
            "mean_predicted_non_gtr_risk",
            "min_predicted_non_gtr_risk",
            "max_predicted_non_gtr_risk",
        ],
        [
            {
                "model": "A0",
                "risk_group": "low",
                "n": "118",
                "non_gtr_events": "5",
                "observed_non_gtr_rate": "0.0424",
                "mean_predicted_non_gtr_risk": "0.2416",
                "min_predicted_non_gtr_risk": "0.1759",
                "max_predicted_non_gtr_risk": "0.2835",
            },
            {
                "model": "A0",
                "risk_group": "intermediate",
                "n": "118",
                "non_gtr_events": "8",
                "observed_non_gtr_rate": "0.0678",
                "mean_predicted_non_gtr_risk": "0.3286",
                "min_predicted_non_gtr_risk": "0.2837",
                "max_predicted_non_gtr_risk": "0.3807",
            },
            {
                "model": "A0",
                "risk_group": "high",
                "n": "118",
                "non_gtr_events": "44",
                "observed_non_gtr_rate": "0.3729",
                "mean_predicted_non_gtr_risk": "0.4667",
                "min_predicted_non_gtr_risk": "0.3814",
                "max_predicted_non_gtr_risk": "0.6750",
            },
            {
                "model": "A1",
                "risk_group": "low",
                "n": "119",
                "non_gtr_events": "4",
                "observed_non_gtr_rate": "0.0336",
                "mean_predicted_non_gtr_risk": "0.0432",
                "min_predicted_non_gtr_risk": "0.0139",
                "max_predicted_non_gtr_risk": "0.0662",
            },
            {
                "model": "A1",
                "risk_group": "intermediate",
                "n": "119",
                "non_gtr_events": "11",
                "observed_non_gtr_rate": "0.0924",
                "mean_predicted_non_gtr_risk": "0.1034",
                "min_predicted_non_gtr_risk": "0.0662",
                "max_predicted_non_gtr_risk": "0.1776",
            },
            {
                "model": "A1",
                "risk_group": "high",
                "n": "119",
                "non_gtr_events": "42",
                "observed_non_gtr_rate": "0.3529",
                "mean_predicted_non_gtr_risk": "0.3318",
                "min_predicted_non_gtr_risk": "0.1777",
                "max_predicted_non_gtr_risk": "0.6750",
            },
        ],
    )
    write_json(
        bundle_root / "artifacts" / "analysis" / "run-535a972f" / "clinical_utility" / "summary.json",
        {
            "models": ["A0", "A1", "B0", "M0_elastic", "M0_hgb"],
            "candidate_story_model": "A1",
            "overall_metrics": {
                "A0": {
                    "roc_auc": 0.8022,
                    "average_precision": 0.4479,
                    "brier_score": 0.1433,
                    "calibration_intercept": -0.3108,
                    "calibration_slope": 2.4065,
                },
                "A1": {
                    "roc_auc": 0.8004,
                    "average_precision": 0.45,
                    "brier_score": 0.1099,
                    "calibration_intercept": 0.0619,
                    "calibration_slope": 1.0442,
                },
            },
        },
    )
    write_json(
        bundle_root / "artifacts" / "experiment" / "run-535a972f" / "main_lighttree" / "metrics.json",
        {
            "A0": {
                "roc_auc": 0.8022,
                "average_precision": 0.4479,
                "brier_score": 0.1433,
                "calibration_intercept": -0.3108,
                "calibration_slope": 2.4065,
            },
            "A1": {
                "roc_auc": 0.8004,
                "average_precision": 0.45,
                "brier_score": 0.1099,
                "calibration_intercept": 0.0619,
                "calibration_slope": 1.0442,
            },
            "B0": {
                "roc_auc": 0.7999,
                "average_precision": 0.4606,
                "brier_score": 0.1090,
                "calibration_intercept": 0.0586,
                "calibration_slope": 1.0395,
            },
            "M0_elastic": {
                "roc_auc": 0.8006,
                "average_precision": 0.4744,
                "brier_score": 0.1086,
                "calibration_intercept": 0.1581,
                "calibration_slope": 1.1096,
            },
            "M0_hgb": {
                "roc_auc": 0.8359,
                "average_precision": 0.5174,
                "brier_score": 0.1011,
                "calibration_intercept": -0.2038,
                "calibration_slope": 0.8017,
            },
        },
    )
    write_csv(
        paper_root / "derived" / "clinical_utility_model_coefficient_stability.csv",
        ["outer_fold", "feature_name", "domain", "coefficient", "odds_ratio", "selected_c", "intercept", "direction"],
        [
            {
                "outer_fold": "1",
                "feature_name": "age",
                "domain": "Demographics",
                "coefficient": "-0.1106",
                "odds_ratio": "0.8953",
                "selected_c": "0.1",
                "intercept": "-2.1272",
                "direction": "negative",
            },
            {
                "outer_fold": "1",
                "feature_name": "diameter",
                "domain": "Tumor burden",
                "coefficient": "0.5800",
                "odds_ratio": "1.7860",
                "selected_c": "0.1",
                "intercept": "-2.1272",
                "direction": "positive",
            },
            {
                "outer_fold": "2",
                "feature_name": "diameter",
                "domain": "Tumor burden",
                "coefficient": "0.6000",
                "odds_ratio": "1.8221",
                "selected_c": "0.1",
                "intercept": "-2.1272",
                "direction": "positive",
            },
        ],
    )
    write_csv(
        paper_root / "derived" / "clinical_utility_model_domain_summary.csv",
        ["domain", "feature_count", "mean_abs_coefficient", "median_abs_coefficient", "mean_sign_consistency"],
        [
            {
                "domain": "Tumor burden",
                "feature_count": "2",
                "mean_abs_coefficient": "0.3444",
                "median_abs_coefficient": "0.3444",
                "mean_sign_consistency": "1.0",
            },
            {
                "domain": "Invasion burden",
                "feature_count": "5",
                "mean_abs_coefficient": "0.1091",
                "median_abs_coefficient": "0.0822",
                "mean_sign_consistency": "0.8620",
            },
        ],
    )

    report = module.run_publication_shell_sync(study_root=study_root, paper_root=paper_root)

    assert report["status"] == "synced"
    risk_layering = json.loads((paper_root / "risk_layering_monotonic_inputs.json").read_text(encoding="utf-8"))
    binary_panel = json.loads((paper_root / "binary_calibration_decision_curve_panel_inputs.json").read_text(encoding="utf-8"))
    model_audit = json.loads((paper_root / "model_complexity_audit_panel_inputs.json").read_text(encoding="utf-8"))
    performance_table = json.loads((paper_root / "performance_summary_table_generic.json").read_text(encoding="utf-8"))
    grouped_table = json.loads((paper_root / "grouped_risk_event_summary_table.json").read_text(encoding="utf-8"))

    display = risk_layering["displays"][0]
    assert display["catalog_id"] == "F2"
    assert display["left_panel_title"] == "Core preoperative comparator"
    assert display["right_panel_title"] == "Clinically informed model"
    assert display["left_bars"][0] == {"label": "Low", "cases": 118, "events": 5, "risk": 0.0424}
    assert display["right_bars"][-1] == {"label": "High", "cases": 119, "events": 42, "risk": 0.3529}

    panel_display = binary_panel["displays"][0]
    assert panel_display["catalog_id"] == "F3"
    assert [item["label"] for item in panel_display["calibration_series"]] == [
        "Core preoperative model",
        "Clinically informed preoperative model",
    ]
    assert [item["label"] for item in panel_display["decision_reference_lines"]] == ["Treat none", "Treat all"]
    assert panel_display["decision_series"][1]["label"] == "Clinically informed preoperative model"

    audit_display = model_audit["displays"][0]
    assert audit_display["catalog_id"] == "F4"
    assert [item["label"] for item in audit_display["metric_panels"][0]["rows"]] == [
        "Core preoperative model",
        "Clinically informed preoperative model",
        "Pathology-augmented model",
        "Elastic-net comparison model",
        "Random forest comparison model",
    ]
    assert audit_display["audit_panels"][0]["rows"][0]["label"] == "Age"
    assert audit_display["audit_panels"][1]["rows"][0]["label"] == "Tumor burden"

    assert performance_table["catalog_id"] == "T2"
    assert performance_table["rows"][0]["label"] == "Core preoperative model"
    assert performance_table["rows"][1]["label"] == "Clinically informed preoperative model"

    assert grouped_table["catalog_id"] == "T3"
    assert grouped_table["rows"][0]["surface"] == "Core preoperative model"
    assert grouped_table["rows"][1]["surface"] == "Core preoperative model"
    assert grouped_table["rows"][-1] == {
        "row_id": "clinically_informed_preoperative_model_high",
        "surface": "Clinically informed preoperative model",
        "stratum": "High",
        "cases": 119,
        "events": 42,
        "risk_display": "35.3%",
    }
