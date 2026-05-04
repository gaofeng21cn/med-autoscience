from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.submission_minimal_cases.package_core_and_authority import make_paper_workspace
from tests.test_study_delivery_sync_cases.shared import make_delivery_workspace


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _snapshot(
    *,
    paper_write_allowed: bool = True,
    bundle_build_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "surface": "control_plane_snapshot",
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

    assert result["status"] == "control_plane_route_blocked"
    assert "control_plane_snapshot_missing" in result["control_plane_route_gate"]["blocking_reasons"]
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

    assert result["status"] == "control_plane_route_blocked"
    assert "projection_only_write_blocked" in result["control_plane_route_gate"]["blocking_reasons"]
    assert not submission_root.exists()


def test_delivery_sync_without_snapshot_is_blocked_before_current_package_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_delivery_workspace(tmp_path)

    result = module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert result["status"] == "control_plane_route_blocked"
    assert "control_plane_snapshot_missing" in result["control_plane_route_gate"]["blocking_reasons"]
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (study_root / "manuscript" / "current_package.zip").exists()


def test_publication_gate_apply_false_is_read_only_without_snapshot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate_parts.supervisor_and_cli")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    quest_root.mkdir(parents=True)
    report_path = quest_root / "publication_gate_report.json"
    markdown_path = quest_root / "publication_gate_report.md"

    monkeypatch.setattr(module, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        module,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["scientific_anchor_missing"],
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": False,
            "draft_handoff_delivery_required": False,
            "draft_handoff_delivery_status": "not_required",
            "draft_handoff_delivery_manifest_path": None,
            "bundle_tasks_downstream_only": True,
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "blocked",
        },
    )
    monkeypatch.setattr(module, "write_gate_files", lambda quest_root, report: (report_path, markdown_path))

    result = module.run_controller(quest_root=quest_root, apply=False)

    assert result["status"] == "blocked"
    assert result["draft_handoff_delivery_sync"] is None
    assert result["study_delivery_stale_sync"] is None
    assert result["journal_package_sync"] is None


def test_publication_gate_apply_true_passes_same_route_context_to_downstream_writes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate_parts.supervisor_and_cli")
    route_context = {"control_plane_snapshot": _snapshot(bundle_build_allowed=True)}
    paper_root = tmp_path / "study" / "paper"
    study_root = tmp_path / "study"
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    quest_root.mkdir(parents=True)
    report_path = quest_root / "publication_gate_report.json"
    markdown_path = quest_root / "publication_gate_report.md"
    seen: dict[str, Any] = {}

    class State:
        pass

    state = State()
    state.paper_root = paper_root
    state.quest_root = quest_root
    state.runtime_state = {}

    def build_report(_state: object) -> dict[str, Any]:
        return {
            "status": "blocked",
            "allow_write": True,
            "blockers": [],
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": True,
            "draft_handoff_delivery_required": False,
            "draft_handoff_delivery_status": "not_required",
            "draft_handoff_delivery_manifest_path": None,
            "study_delivery_status": "stale_manifest_source_changed",
            "study_delivery_stale_reason": "delivery_manifest_source_changed",
            "study_delivery_missing_source_paths": [],
            "primary_journal_target": {
                "journal_slug": "journal-a",
                "publication_profile": "general_medical_journal",
            },
            "journal_requirements_status": "resolved",
            "journal_package_status": "missing",
            "journal_requirements_study_root": str(study_root),
            "bundle_tasks_downstream_only": False,
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "current_required_action": "continue_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "ready",
        }

    monkeypatch.setattr(module, "build_gate_state", lambda quest_root: state)
    monkeypatch.setattr(module, "build_gate_report", build_report)
    monkeypatch.setattr(module, "write_gate_files", lambda quest_root, report: (report_path, markdown_path))
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **kwargs: seen.setdefault("delivery_context", kwargs["control_plane_route_context"]) or {"status": "synced"},
    )
    monkeypatch.setattr(
        module.journal_package_controller,
        "materialize_journal_package",
        lambda **kwargs: seen.setdefault("journal_context", kwargs["control_plane_route_context"])
        or {"status": "materialized"},
    )
    monkeypatch.setattr(module, "_materialize_publication_eval_latest", lambda **kwargs: None)

    module.run_controller(
        quest_root=quest_root,
        apply=True,
        enqueue_intervention=False,
        control_plane_route_context=route_context,
    )

    assert seen["delivery_context"] is route_context
    assert seen["journal_context"] is route_context


def test_quality_repair_batch_derives_route_context_from_runtime_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_id = "quest-001"
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-22T08:00:00+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-22T08:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "risk stratification validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Generated delivery mirror is stale.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "delivery mirror is stale",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::quality-repair::2026-04-22T08:00:00+00:00",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Refresh generated delivery mirror through controller-owned surfaces.",
                "route_target": "review",
                "route_key_question": "Which deterministic publication-surface repair is still blocking?",
                "route_rationale": "Package freshness must be repaired before publication gate replay.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": f"evaluation-summary::{study_root.name}::2026-04-22T08:01:00+00:00",
            "quality_closure_truth": {"state": "quality_repair_required"},
            "quality_execution_lane": {"lane_id": "general_quality_repair"},
        },
    )
    route_context = {"control_plane_snapshot": _snapshot(bundle_build_allowed=True)}
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "study_id": kwargs["study_id"],
            "study_root": str(kwargs["study_root"]),
            "quest_id": quest_id,
            **route_context,
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["control_plane_route_context"]),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert seen["gate_context"] == route_context
    assert result["control_plane_route_gate"]["allowed"] is True
    assert result["control_plane_route_gate"]["snapshot_ref"]["surface"] == "control_plane_snapshot"


def test_fresh_snapshot_authorizes_submission_minimal_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    result = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        control_plane_route_context={"control_plane_snapshot": _snapshot(paper_write_allowed=True)},
    )

    assert result["control_plane_route_gate"]["allowed"] is True
    assert (paper_root / "submission_minimal" / "submission_manifest.json").exists()
