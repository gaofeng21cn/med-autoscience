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
            "population_accounting": [],
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
    assert cohort_flow["title"] == "Cohort derivation at the 3-month postoperative landmark"
    assert [item["step_id"] for item in cohort_flow["steps"]] == [
        "source_total_cases",
        "first_surgery_cases",
        "complete_3_month_landmark_cases",
        "complete_later_endpoint_cases",
        "analysis_cases",
    ]
    assert cohort_flow["steps"][1]["detail"] == "Excluded non-first-surgery cases: 52"
    assert cohort_flow["steps"][-1]["detail"] == "Later persistent global hypopituitarism events: 98"

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
