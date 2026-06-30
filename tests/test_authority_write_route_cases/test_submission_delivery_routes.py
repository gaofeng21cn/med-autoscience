from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from tests.submission_minimal_cases.package_core_and_authority import make_paper_workspace
from tests.test_study_delivery_sync_cases.shared import make_delivery_workspace
from med_autoscience.controllers.study_delivery_sync_parts.delivery_descriptions import (
    _submission_source_relative_paths,
    _submission_source_signature,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_runtime_authority_snapshots(
    study_root: Path,
    *,
    blocking_reasons: list[str] | None = None,
) -> None:
    _write_json(
        study_root / "artifacts" / "truth" / "latest.json",
        {
            "surface": "study_truth_snapshot",
            "study_id": study_root.name,
            "truth_epoch": "truth-1",
            "canonical_next_action": "resume_same_study_line",
            "allowed_controller_actions": ["direct_study_execution", "direct_paper_line_write"],
            "blocking_reasons": list(blocking_reasons or []),
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "surface": "runtime_health_snapshot",
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "runtime_health_epoch": "runtime-1",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
    )


def _snapshot(
    *,
    paper_write_allowed: bool = True,
    bundle_build_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "surface": "authority_snapshot",
        "control_state": "ready",
        "canonical_next_action": "continue_bundle_stage",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "runtime-1"},
        },
        "dispatch_gate": {
            "state": "open",
            "blocking_reasons": [],
        },
        "route_authorization": {
            "authorized": paper_write_allowed and bundle_build_allowed,
            "paper_write_allowed": paper_write_allowed,
            "bundle_build_allowed": bundle_build_allowed,
            "runtime_recovery_allowed": True,
        },
    }


def test_submission_minimal_without_snapshot_is_blocked_before_writing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"
    if submission_root.exists():
        for path in sorted(submission_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        submission_root.rmdir()

    result = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert result["status"] == "authority_route_blocked"
    assert "authority_snapshot_missing" in result["authority_route_gate"]["blocking_reasons"]
    assert not submission_root.exists()


def test_projection_only_submission_minimal_does_not_materialize(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"
    if submission_root.exists():
        for path in sorted(submission_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        submission_root.rmdir()

    result = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context={"projection_only": True, "paths": [submission_root]},
    )

    assert result["status"] == "authority_route_blocked"
    assert "projection_only_write_blocked" in result["authority_route_gate"]["blocking_reasons"]
    assert not submission_root.exists()


def test_delivery_sync_without_snapshot_still_writes_non_submit_current_package(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    result = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "current_package"
    assert result["can_submit"] is False
    assert result["authority_route_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["allowed"] is False
    assert "authority_snapshot_missing" in result["submission_authority_gate"]["blocking_reasons"]
    assert (study_root / "manuscript" / "current_package").exists()
    assert (study_root / "manuscript" / "current_package.zip").exists()


def test_submission_minimal_derives_snapshot_from_study_authority_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    package_builder = importlib.import_module(
        "med_autoscience.controllers.submission_minimal_parts.package_builder"
    )
    paper_root = make_paper_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        paper_root.parent,
        blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
    )

    def write_placeholder_export(
        *,
        output_docx_path: Path | None = None,
        output_pdf_path: Path | None = None,
        **_: Any,
    ) -> None:
        output_path = output_docx_path or output_pdf_path
        assert output_path is not None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"test export placeholder")

    monkeypatch.setattr(package_builder, "export_docx", write_placeholder_export)
    monkeypatch.setattr(package_builder, "export_pdf", write_placeholder_export)

    result = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert result["authority_route_gate"]["route_authorization_flag"] == "paper_write_allowed"
    assert result["authority_route_gate"]["snapshot_ref"]["study_truth_epoch"] == "truth-1"
    assert "authority_snapshot_missing" not in result["authority_route_gate"]["blocking_reasons"]
    assert (paper_root / "submission_minimal" / "audit" / "submission_manifest.json").exists()


def test_delivery_sync_derives_snapshot_but_does_not_require_bundle_gate_for_current_package(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        study_root,
        blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
    )

    result = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "current_package"
    assert result["can_submit"] is False
    assert "authority_snapshot_missing" not in result["authority_route_gate"]["blocking_reasons"]
    assert result["authority_route_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["allowed"] is False
    assert "bundle_build_allowed_false" in result["submission_authority_gate"]["blocking_reasons"]
    assert (study_root / "manuscript" / "current_package").exists()


def test_delivery_sync_adopts_current_runtime_gate_clear_for_bundle_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        study_root,
        blocking_reasons=[
            "publication_supervisor_state.bundle_tasks_downstream_only",
            "runtime_recovery_retry_budget_exhausted",
        ],
    )
    source_root = paper_root / "submission_minimal"
    source_signature = _submission_source_signature(
        paper_root=paper_root,
        source_root=source_root,
        relative_paths=_submission_source_relative_paths(paper_root=paper_root, source_root=source_root),
    )
    quest_root = study_root.parent.parent / "runtime" / "quests" / study_root.name
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(
        f"quest_id: {study_root.name}\nruntime_reentry_gate:\n  study_id: {study_root.name}\n",
        encoding="utf-8",
    )
    gate_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(
        json.dumps(
            {
                "status": "clear",
                "blockers": [],
                "bundle_tasks_downstream_only": False,
                "authority_source_signature": source_signature,
                "paper_root": str(paper_root),
                "latest_gate_path": str(gate_path),
                "gate_fingerprint": "gate::clear",
                "work_unit_fingerprint": "work-unit::submission-minimal",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "submission_ready_package"
    assert result["can_submit"] is True
    assert result["authority_route_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["allowed"] is True
    assert result["submission_authority_gate"]["controller_route_gate"]["action_family"] == (
        "paper.package.submission_minimal"
    )
    assert result["submission_authority_gate"]["controller_route_gate"]["work_unit_id"] == (
        "submission_minimal_refresh"
    )
    assert "bundle_build_allowed_false" not in result["submission_authority_gate"]["blocking_reasons"]


def test_delivery_sync_does_not_adopt_gate_clear_with_stale_source_signature(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    _write_runtime_authority_snapshots(
        study_root,
        blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
    )
    quest_root = study_root.parent.parent / "runtime" / "quests" / study_root.name
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(
        f"quest_id: {study_root.name}\nruntime_reentry_gate:\n  study_id: {study_root.name}\n",
        encoding="utf-8",
    )
    gate_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(
        json.dumps(
            {
                "status": "clear",
                "blockers": [],
                "bundle_tasks_downstream_only": False,
                "authority_source_signature": "source::stale",
                "latest_gate_path": str(gate_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["package_kind"] == "current_package"
    assert result["can_submit"] is False
    assert result["submission_authority_gate"]["allowed"] is False
    assert "bundle_build_allowed_false" in result["submission_authority_gate"]["blocking_reasons"]


def test_fresh_snapshot_authorizes_submission_minimal_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    package_builder = importlib.import_module(
        "med_autoscience.controllers.submission_minimal_parts.package_builder"
    )
    paper_root = make_paper_workspace(tmp_path)

    def write_placeholder_export(
        *,
        output_docx_path: Path | None = None,
        output_pdf_path: Path | None = None,
        **_: Any,
    ) -> None:
        output_path = output_docx_path or output_pdf_path
        assert output_path is not None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"test export placeholder")

    monkeypatch.setattr(package_builder, "export_docx", write_placeholder_export)
    monkeypatch.setattr(package_builder, "export_pdf", write_placeholder_export)

    result = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        authority_route_context={"authority_snapshot": _snapshot(paper_write_allowed=True)},
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert (paper_root / "submission_minimal" / "audit" / "submission_manifest.json").exists()
