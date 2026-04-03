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

    report = module.run_validation(quest_root=quest_root)

    assert report["status"] == "clear"
    assert report["blockers"] == []
