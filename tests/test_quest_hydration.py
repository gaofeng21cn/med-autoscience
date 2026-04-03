from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def _time_to_event_reporting_contract() -> dict[str, object]:
    return {
        "reporting_guideline_family": "TRIPOD",
        "display_registry_required": True,
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
    }


def test_run_quest_hydration_writes_required_medical_runtime_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    report = module.run_hydration(
        quest_root=quest_root,
        hydration_payload={
            "medical_analysis_contract": {"study_archetype": "clinical_classifier", "endpoint_type": "time_to_event"},
            "medical_reporting_contract": _time_to_event_reporting_contract(),
            "entry_state_summary": "Study root: /tmp/studies/001-risk",
            "literature_records": [
                {
                    "record_id": "pmid:12345",
                    "title": "Prediction model paper",
                    "authors": ["A. Author"],
                    "year": 2024,
                    "journal": "BMC Medicine",
                    "doi": "10.1000/example",
                    "pmid": "12345",
                    "pmcid": None,
                    "arxiv_id": None,
                    "abstract": "Structured abstract",
                    "full_text_availability": "abstract_only",
                    "source_priority": 2,
                    "citation_payload": {"journal": "BMC Medicine"},
                    "local_asset_paths": [],
                    "relevance_role": "anchor",
                    "claim_support_scope": ["primary_claim"],
                }
            ],
        },
    )

    assert (quest_root / "paper" / "medical_analysis_contract.json").exists()
    assert (quest_root / "paper" / "medical_reporting_contract.json").exists()
    assert (quest_root / "paper" / "cohort_flow.json").exists()
    assert (quest_root / "paper" / "baseline_characteristics_schema.json").exists()
    assert (quest_root / "paper" / "time_to_event_performance_summary.json").exists()
    assert (quest_root / "paper" / "time_to_event_discrimination_calibration_inputs.json").exists()
    assert (quest_root / "paper" / "time_to_event_grouped_inputs.json").exists()
    assert (quest_root / "paper" / "time_to_event_decision_curve_inputs.json").exists()
    assert (quest_root / "paper" / "multicenter_generalizability_inputs.json").exists()
    assert (quest_root / "paper" / "references.bib").exists()
    assert (quest_root / "paper" / "reference_coverage_report.json").exists()
    assert (quest_root / "literature" / "pubmed" / "records.jsonl").exists()
    assert (quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json").exists()
    assert report["status"] == "hydrated"
    assert report["literature_report"]["record_count"] == 1

    report_payload = json.loads(
        (quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json").read_text(encoding="utf-8")
    )
    assert report_payload["literature_report"]["record_count"] == 1


def test_run_quest_hydration_writes_semantic_display_ids_and_catalog_ids(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    module.run_hydration(
        quest_root=quest_root,
        hydration_payload={
            "medical_analysis_contract": {"study_archetype": "clinical_classifier", "endpoint_type": "time_to_event"},
            "medical_reporting_contract": _time_to_event_reporting_contract(),
            "entry_state_summary": "Study root: /tmp/studies/001-risk",
            "literature_records": [],
        },
    )

    display_registry = json.loads((quest_root / "paper" / "display_registry.json").read_text(encoding="utf-8"))
    assert display_registry["displays"] == [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
            "shell_path": "paper/figures/cohort_flow.shell.json",
        },
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
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
            "shell_path": "paper/tables/baseline_characteristics.shell.json",
        },
        {
            "display_id": "time_to_event_performance_summary",
            "display_kind": "table",
            "requirement_key": "table2_time_to_event_performance_summary",
            "catalog_id": "T2",
            "shell_path": "paper/tables/time_to_event_performance_summary.shell.json",
        },
    ]
    figure_shell = json.loads((quest_root / "paper" / "figures" / "cohort_flow.shell.json").read_text(encoding="utf-8"))
    table_shell = json.loads(
        (quest_root / "paper" / "tables" / "baseline_characteristics.shell.json").read_text(encoding="utf-8")
    )
    performance_shell = json.loads(
        (quest_root / "paper" / "tables" / "time_to_event_performance_summary.shell.json").read_text(encoding="utf-8")
    )
    assert figure_shell["display_id"] == "cohort_flow"
    assert figure_shell["catalog_id"] == "F1"
    assert table_shell["display_id"] == "baseline_characteristics"
    assert table_shell["catalog_id"] == "T1"
    assert performance_shell["display_id"] == "time_to_event_performance_summary"
    assert performance_shell["catalog_id"] == "T2"

    grouped_inputs = json.loads((quest_root / "paper" / "time_to_event_grouped_inputs.json").read_text(encoding="utf-8"))
    discrimination_inputs = json.loads(
        (quest_root / "paper" / "time_to_event_discrimination_calibration_inputs.json").read_text(encoding="utf-8")
    )
    decision_inputs = json.loads((quest_root / "paper" / "time_to_event_decision_curve_inputs.json").read_text(encoding="utf-8"))
    generalizability_inputs = json.loads(
        (quest_root / "paper" / "multicenter_generalizability_inputs.json").read_text(encoding="utf-8")
    )
    performance_inputs = json.loads(
        (quest_root / "paper" / "time_to_event_performance_summary.json").read_text(encoding="utf-8")
    )
    assert grouped_inputs["displays"][0]["display_id"] == "km_risk_stratification"
    assert grouped_inputs["displays"][0]["catalog_id"] == "F3"
    assert discrimination_inputs["displays"][0]["display_id"] == "discrimination_calibration"
    assert discrimination_inputs["displays"][0]["catalog_id"] == "F2"
    assert decision_inputs["displays"][0]["display_id"] == "decision_curve"
    assert decision_inputs["displays"][0]["catalog_id"] == "F4"
    assert generalizability_inputs["displays"][0]["display_id"] == "multicenter_generalizability"
    assert generalizability_inputs["displays"][0]["catalog_id"] == "F5"
    assert performance_inputs["display_id"] == "time_to_event_performance_summary"
    assert performance_inputs["catalog_id"] == "T2"


def test_run_quest_hydration_rejects_semantic_display_plan_without_catalog_id(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="catalog_id"):
        module.run_hydration(
            quest_root=quest_root,
            hydration_payload={
                "medical_analysis_contract": {"study_archetype": "clinical_classifier"},
                "medical_reporting_contract": {
                    "reporting_guideline_family": "TRIPOD",
                    "display_shell_plan": [
                        {
                            "display_id": "cohort_flow",
                            "display_kind": "figure",
                            "requirement_key": "cohort_flow_figure",
                        }
                    ],
                },
                "entry_state_summary": "Study root: /tmp/studies/001-risk",
                "literature_records": [],
            },
        )


def test_run_quest_hydration_accepts_legacy_display_plan_without_catalog_id(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    module.run_hydration(
        quest_root=quest_root,
        hydration_payload={
            "medical_analysis_contract": {"study_archetype": "clinical_classifier"},
            "medical_reporting_contract": {
                "reporting_guideline_family": "TRIPOD",
                "display_shell_plan": [
                    {
                        "display_id": "Figure1",
                        "display_kind": "figure",
                        "requirement_key": "cohort_flow_figure",
                    },
                    {
                        "display_id": "Table1",
                        "display_kind": "table",
                        "requirement_key": "table1_baseline_characteristics",
                    },
                ],
            },
            "entry_state_summary": "Study root: /tmp/studies/001-risk",
            "literature_records": [],
        },
    )

    display_registry = json.loads((quest_root / "paper" / "display_registry.json").read_text(encoding="utf-8"))
    assert display_registry["displays"] == [
        {
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "shell_path": "paper/figures/Figure1.shell.json",
        },
        {
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "shell_path": "paper/tables/Table1.shell.json",
        },
    ]


def test_run_quest_hydration_rejects_semantic_table_display_plan_without_catalog_id(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="catalog_id"):
        module.run_hydration(
            quest_root=quest_root,
            hydration_payload={
                "medical_analysis_contract": {"study_archetype": "clinical_classifier"},
                "medical_reporting_contract": {
                    "reporting_guideline_family": "TRIPOD",
                    "display_shell_plan": [
                        {
                            "display_id": "baseline_characteristics",
                            "display_kind": "table",
                            "requirement_key": "table1_baseline_characteristics",
                        }
                    ],
                },
                "entry_state_summary": "Study root: /tmp/studies/001-risk",
                "literature_records": [],
            },
        )
