from __future__ import annotations

import importlib
import json
from pathlib import Path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_runtime_reentry_gate_defaults_to_ready_when_not_configured(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_reentry_gate")
    study_root = tmp_path / "study"
    study_root.mkdir(parents=True, exist_ok=True)

    result = module.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload={"study_id": "001-risk"},
        execution={},
    )

    assert result["status"] == "not_configured"
    assert result["allow_runtime_entry"] is True
    assert result["required_paths"] == []


def test_runtime_reentry_gate_blocks_when_required_paths_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_reentry_gate")
    study_root = tmp_path / "study"
    study_root.mkdir(parents=True, exist_ok=True)

    result = module.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload={"study_id": "001-risk"},
        execution={
            "runtime_reentry_gate": {
                "enabled": True,
                "execution_root": "analysis/clean_room_execution",
                "first_runtime_unit": "00_entry_validation",
                "required_paths": [
                    "analysis/paper_facing_evidence_contract.md",
                    "analysis/clean_room_runbook.md",
                ],
            }
        },
    )

    assert result["status"] == "blocked"
    assert result["allow_runtime_entry"] is False
    assert "missing_required_path:analysis/paper_facing_evidence_contract.md" in result["blockers"]
    assert "missing_required_path:analysis/clean_room_runbook.md" in result["blockers"]


def test_runtime_reentry_gate_is_ready_when_contract_and_unit_exist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_reentry_gate")
    study_root = tmp_path / "study"
    write_text(study_root / "analysis" / "paper_facing_evidence_contract.md", "# contract\n")
    write_text(study_root / "analysis" / "clean_room_runbook.md", "# runbook\n")
    (study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint").mkdir(parents=True, exist_ok=True)

    result = module.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload={"study_id": "001-risk"},
        execution={
            "runtime_reentry_gate": {
                "enabled": True,
                "execution_root": "analysis/clean_room_execution",
                "first_runtime_unit": "10_china_primary_endpoint",
                "required_paths": [
                    "analysis/paper_facing_evidence_contract.md",
                    "analysis/clean_room_runbook.md",
                ],
            }
        },
    )

    assert result["status"] == "ready"
    assert result["allow_runtime_entry"] is True
    assert result["blockers"] == []
    assert result["first_runtime_unit"] == "10_china_primary_endpoint"


def test_runtime_reentry_gate_reports_startup_hydration_state_when_required(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_reentry_gate")
    study_root = tmp_path / "study"
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    write_text(study_root / "analysis" / "paper_facing_evidence_contract.md", "# contract\n")
    write_text(study_root / "analysis" / "clean_room_runbook.md", "# runbook\n")
    (study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint").mkdir(parents=True, exist_ok=True)
    write_json(quest_root / "paper" / "medical_analysis_contract.json", {"status": "unsupported"})
    write_json(quest_root / "paper" / "medical_reporting_contract.json", {"status": "resolved"})

    result = module.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload={"study_id": "001-risk"},
        execution={
            "runtime_reentry_gate": {
                "enabled": True,
                "execution_root": "analysis/clean_room_execution",
                "first_runtime_unit": "10_china_primary_endpoint",
                "required_paths": [
                    "analysis/paper_facing_evidence_contract.md",
                    "analysis/clean_room_runbook.md",
                ],
                "require_startup_hydration": True,
                "require_managed_skill_audit": True,
            }
        },
        quest_root=quest_root,
    )

    assert result["status"] == "ready"
    assert result["allow_runtime_entry"] is True
    assert result["require_startup_hydration"] is True
    assert result["require_managed_skill_audit"] is True
    assert result["startup_hydration_validation"]["status"] == "blocked"


def test_runtime_reentry_gate_blocks_when_startup_hydration_is_enforced(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_reentry_gate")
    study_root = tmp_path / "study"
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    write_text(study_root / "analysis" / "paper_facing_evidence_contract.md", "# contract\n")
    write_text(study_root / "analysis" / "clean_room_runbook.md", "# runbook\n")
    (study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint").mkdir(parents=True, exist_ok=True)
    write_json(quest_root / "paper" / "medical_analysis_contract.json", {"status": "unsupported"})
    write_json(quest_root / "paper" / "medical_reporting_contract.json", {"status": "resolved"})

    result = module.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload={"study_id": "001-risk"},
        execution={
            "runtime_reentry_gate": {
                "enabled": True,
                "execution_root": "analysis/clean_room_execution",
                "first_runtime_unit": "10_china_primary_endpoint",
                "required_paths": [
                    "analysis/paper_facing_evidence_contract.md",
                    "analysis/clean_room_runbook.md",
                ],
                "require_startup_hydration": True,
            }
        },
        quest_root=quest_root,
        enforce_startup_hydration=True,
    )

    assert result["status"] == "blocked"
    assert result["allow_runtime_entry"] is False
    assert "unsupported_medical_analysis_contract" in result["blockers"]
