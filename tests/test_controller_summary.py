from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.controller_summary"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_study_charter(study_root: Path, *, charter_id: str = "charter::001-risk::v1") -> Path:
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    _write_json(
        charter_path,
        {
            "schema_version": 1,
            "charter_id": charter_id,
            "study_id": "001-risk",
            "publication_objective": "Build a submission-ready survival-risk study.",
        },
    )
    return charter_path


def test_resolve_controller_summary_ref_defaults_to_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_controller_summary_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "controller" / "controller_summary.json").resolve()


def test_read_controller_summary_reads_stable_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    charter_path = _write_study_charter(study_root)
    summary_path = study_root / "artifacts" / "controller" / "controller_summary.json"
    _write_json(
        summary_path,
        {
            "summary_id": "controller-summary::001-risk::v1",
            "study_id": "001-risk",
            "study_charter_ref": {
                "charter_id": "charter::001-risk::v1",
                "artifact_path": str(charter_path),
            },
            "controller_policy": {"scope": "full_research"},
            "route_trigger_authority": {"decision_policy": "autonomous"},
        },
    )

    payload = module.read_controller_summary(study_root=study_root)

    assert payload["summary_id"] == "controller-summary::001-risk::v1"
    assert payload["study_charter_ref"] == {
        "charter_id": "charter::001-risk::v1",
        "artifact_path": str(charter_path.resolve()),
    }
    assert payload["controller_policy"] == {"scope": "full_research"}
    assert payload["route_trigger_authority"] == {"decision_policy": "autonomous"}


def test_resolve_controller_summary_ref_rejects_runtime_backflow_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_ref = study_root / "runtime" / "quests" / "001-risk" / "controller_summary.json"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_controller_summary_ref(study_root=study_root, ref=runtime_ref)


def test_read_controller_summary_rejects_non_mapping_study_charter_ref(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(
        study_root / "artifacts" / "controller" / "controller_summary.json",
        {
            "summary_id": "controller-summary::001-risk::v1",
            "study_id": "001-risk",
            "study_charter_ref": "charter::001-risk::v1",
            "controller_policy": {"scope": "full_research"},
            "route_trigger_authority": {"decision_policy": "autonomous"},
        },
    )

    with pytest.raises(ValueError, match="study_charter_ref must be a JSON object"):
        module.read_controller_summary(study_root=study_root)


def test_read_controller_summary_rejects_study_charter_id_mismatch(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    charter_path = _write_study_charter(study_root, charter_id="charter::001-risk::v1")
    _write_json(
        study_root / "artifacts" / "controller" / "controller_summary.json",
        {
            "summary_id": "controller-summary::001-risk::v1",
            "study_id": "001-risk",
            "study_charter_ref": {
                "charter_id": "charter::001-risk::v2",
                "artifact_path": str(charter_path),
            },
            "controller_policy": {"scope": "full_research"},
            "route_trigger_authority": {"decision_policy": "autonomous"},
        },
    )

    with pytest.raises(ValueError, match="charter_id mismatch"):
        module.read_controller_summary(study_root=study_root)


def test_materialize_controller_summary_writes_stable_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    charter_path = _write_study_charter(study_root)

    written_ref = module.materialize_controller_summary(
        study_root=study_root,
        study_id="001-risk",
        study_charter_ref={
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str(charter_path),
        },
        controller_policy={
            "scope": "full_research",
            "startup_boundary_gate": {
                "allow_compute_stage": True,
                "required_first_anchor": "scout",
            },
            "journal_shortlist": {"status": "resolved", "journals": ["BMC Medicine"]},
            "controller_first_policy_summary": "controller-first summary",
            "automation_ready_summary": "automation-ready summary",
        },
        route_trigger_authority={
            "decision_policy": "autonomous",
            "launch_profile": "continue_existing_state",
            "startup_contract_profile": "paper_required_autonomous",
        },
    )

    summary_path = study_root / "artifacts" / "controller" / "controller_summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))

    assert written_ref == {
        "summary_id": "controller-summary::001-risk::v1",
        "artifact_path": str(summary_path.resolve()),
    }
    assert payload == {
        "schema_version": 1,
        "summary_id": "controller-summary::001-risk::v1",
        "study_id": "001-risk",
        "study_charter_ref": {
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str(charter_path.resolve()),
        },
        "controller_policy": {
            "scope": "full_research",
            "startup_boundary_gate": {
                "allow_compute_stage": True,
                "required_first_anchor": "scout",
            },
            "journal_shortlist": {"status": "resolved", "journals": ["BMC Medicine"]},
            "controller_first_policy_summary": "controller-first summary",
            "automation_ready_summary": "automation-ready summary",
        },
        "route_trigger_authority": {
            "decision_policy": "autonomous",
            "launch_profile": "continue_existing_state",
            "startup_contract_profile": "paper_required_autonomous",
        },
    }
