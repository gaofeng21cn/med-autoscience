from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
