from __future__ import annotations

import importlib
import json
from pathlib import Path


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_startup_hydration_validation_blocks_missing_reporting_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_hydration_validation")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "medical_analysis_contract.json").write_text("{}", encoding="utf-8")

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "blocked"
    assert "missing_medical_reporting_contract" in report["blockers"]


def test_startup_hydration_validation_requires_resolved_contracts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_hydration_validation")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    write_json(
        quest_root / "paper" / "medical_analysis_contract.json",
        {"status": "resolved"},
    )
    write_json(
        quest_root / "paper" / "medical_reporting_contract.json",
        {"status": "resolved"},
    )

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "clear"
    assert report["blockers"] == []


def test_startup_hydration_validation_blocks_unsupported_contracts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_hydration_validation")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    write_json(
        quest_root / "paper" / "medical_analysis_contract.json",
        {"status": "unsupported"},
    )
    write_json(
        quest_root / "paper" / "medical_reporting_contract.json",
        {"status": "unsupported"},
    )

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "blocked"
    assert "unsupported_medical_analysis_contract" in report["blockers"]
    assert "unsupported_medical_reporting_contract" in report["blockers"]


def test_startup_hydration_validation_blocks_missing_display_registry_and_shells(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_hydration_validation")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    write_json(
        quest_root / "paper" / "medical_analysis_contract.json",
        {"status": "resolved"},
    )
    write_json(
        quest_root / "paper" / "medical_reporting_contract.json",
        {
            "status": "resolved",
            "display_registry_required": True,
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
    )

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "blocked"
    assert "missing_display_registry" in report["blockers"]
    assert "missing_figure1_shell" in report["blockers"]
    assert "missing_table1_shell" in report["blockers"]


def test_startup_hydration_validation_clears_when_display_registry_and_shells_exist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_hydration_validation")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    write_json(
        quest_root / "paper" / "medical_analysis_contract.json",
        {"status": "resolved"},
    )
    write_json(
        quest_root / "paper" / "medical_reporting_contract.json",
        {
            "status": "resolved",
            "display_registry_required": True,
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
    )
    write_json(
        quest_root / "paper" / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
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
    )
    write_json(
        quest_root / "paper" / "figures" / "Figure1.shell.json",
        {"schema_version": 1},
    )
    write_json(
        quest_root / "paper" / "tables" / "Table1.shell.json",
        {"schema_version": 1},
    )
    write_json(
        quest_root / "paper" / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
        },
    )
    write_json(
        quest_root / "paper" / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "Table1",
        },
    )

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "clear"
    assert report["blockers"] == []
    assert report["report_path"] == str(
        quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"
    )


def test_startup_hydration_validation_blocks_missing_direct_migration_stub(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_hydration_validation")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
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
    ]
    write_json(
        quest_root / "paper" / "medical_analysis_contract.json",
        {"status": "resolved"},
    )
    write_json(
        quest_root / "paper" / "medical_reporting_contract.json",
        {
            "status": "resolved",
            "display_registry_required": True,
            "display_shell_plan": display_plan,
        },
    )
    write_json(
        quest_root / "paper" / "display_registry.json",
        {
            "schema_version": 1,
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
    )
    for item in display_plan:
        shell_path = (
            quest_root / "paper" / "figures" / f"{item['display_id']}.shell.json"
            if item["display_kind"] == "figure"
            else quest_root / "paper" / "tables" / f"{item['display_id']}.shell.json"
        )
        write_json(shell_path, {"schema_version": 1})

    write_json(
        quest_root / "paper" / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
        },
    )
    write_json(
        quest_root / "paper" / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "catalog_id": "T1",
        },
    )
    write_json(
        quest_root / "paper" / "time_to_event_performance_summary.json",
        {
            "schema_version": 1,
            "table_shell_id": "table2_time_to_event_performance_summary",
            "display_id": "time_to_event_performance_summary",
            "catalog_id": "T2",
        },
    )
    write_json(
        quest_root / "paper" / "time_to_event_discrimination_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
            "displays": [{"display_id": "discrimination_calibration", "catalog_id": "F2"}],
        },
    )
    write_json(
        quest_root / "paper" / "time_to_event_grouped_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [{"display_id": "km_risk_stratification", "catalog_id": "F3"}],
        },
    )
    write_json(
        quest_root / "paper" / "time_to_event_decision_curve_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_decision_curve_inputs_v1",
            "displays": [{"display_id": "decision_curve", "catalog_id": "F4"}],
        },
    )

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "blocked"
    assert "missing_multicenter_generalizability_inputs" in report["blockers"]
