from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import *  # noqa: F403,F401


def test_domain_handler_export_suppresses_ordinary_tasks_when_fresh_current_work_unit_is_typed_blocker(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})
    _write_json(
        study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json",
        {
            "surface_kind": "mas_runtime_owner_route_handoff_record",
            "source": "runtime_controller_redrive_required",
            "recorded_at": "2026-06-09T12:00:00Z",
            "handoff": {
                "surface_kind": "mas_runtime_owner_route_handoff",
                "recommended_task_kind": "domain_route/reconcile-apply",
                "reason": "runtime_controller_redrive_required",
                "recorded_at": "2026-06-09T12:00:00Z",
                "runtime_state_path": "runtime/quests/002/.ds/runtime_state.json",
                "owner_route_currentness_basis": {
                    "truth_epoch": "stale-truth",
                    "runtime_health_epoch": "stale-runtime",
                    "work_unit_id": "stale_redrive",
                    "work_unit_fingerprint": "stale-redrive-fingerprint",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "decision-route-back-stale",
            "emitted_at": "2026-06-09T12:05:00Z",
            "decision_type": "route_back_same_line",
            "requires_human_confirmation": False,
            "route_target": "write",
            "route_key_question": "stale route-back should not beat current typed blocker",
            "route_rationale": "historical route-back residue",
            "work_unit_fingerprint": "stale-route-back-fingerprint",
            "next_work_unit": {
                "unit_id": "stale_writer_repair",
                "lane": "write",
                "summary": "Historical writer repair residue.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "study_id": study_id,
            "state": "breach",
            "progress_pressure": {
                "status": "advance_now",
                "continuation_required": True,
                "next_action_type": "domain_route/reconcile-apply",
                "next_work_unit_id": "stale_progress_pressure",
                "stop_allowed": False,
            },
        },
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "next_work_unit": None,
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                },
            },
            "current_executable_owner_action": None,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    stale_task_kinds = {
        task["task_kind"]
        for task in payload["pending_family_tasks"]
        if task.get("study_id") == study_id or task.get("payload", {}).get("study_id") == study_id
    }
    assert not (
        stale_task_kinds
        & {
            "paper_autonomy/repair-recheck",
            "publication_aftercare/analysis-queue-progress",
            "publication_aftercare/reviewer-refresh",
            "domain_route/reconcile-apply",
            "domain_owner/default-executor-dispatch",
        }
    )


def test_export_current_owner_action_suppresses_residual_action_under_typed_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export")

    action = module._export_current_owner_action(
        study={
            "current_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
            },
        },
        current_progress={
            "current_executable_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
            },
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
            },
            "current_execution_envelope": {"state_kind": "typed_blocker"},
        },
    )

    assert action == {}


def test_domain_handler_export_suppresses_legacy_route_tasks_under_current_owner_action(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})
    _write_json(
        study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json",
        {
            "surface_kind": "mas_runtime_owner_route_handoff_record",
            "source": "runtime_controller_redrive_required",
            "recorded_at": "2026-06-09T12:00:00Z",
            "handoff": {
                "surface_kind": "mas_runtime_owner_route_handoff",
                "recommended_task_kind": "domain_route/reconcile-apply",
                "reason": "runtime_controller_redrive_required",
                "recorded_at": "2026-06-09T12:00:00Z",
                "owner_route_currentness_basis": {
                    "truth_epoch": "stale-truth",
                    "runtime_health_epoch": "stale-runtime",
                    "work_unit_id": "stale_redrive",
                    "work_unit_fingerprint": "stale-redrive-fingerprint",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "decision-route-back-stale",
            "emitted_at": "2026-06-09T12:05:00Z",
            "decision_type": "route_back_same_line",
            "requires_human_confirmation": False,
            "route_target": "write",
            "work_unit_fingerprint": "stale-route-back-fingerprint",
            "next_work_unit": {
                "unit_id": "stale_writer_repair",
                "lane": "write",
                "summary": "Historical writer repair residue.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "study_id": study_id,
            "state": "breach",
            "progress_pressure": {
                "status": "advance_now",
                "continuation_required": True,
                "next_action_type": "domain_route/reconcile-apply",
                "next_work_unit_id": "stale_progress_pressure",
                "stop_allowed": False,
            },
        },
    )

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "work_unit_fingerprint": "current-write-repair-fingerprint",
                "action_fingerprint": "current-write-repair-fingerprint",
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "opl_current_control_state_action_queue",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "manuscript_story_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "work_unit_fingerprint": "current-write-repair-fingerprint",
                "allowed_actions": ["run_quality_repair_batch"],
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study_tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task.get("study_id") == study_id or task.get("payload", {}).get("study_id") == study_id
    ]
    assert [
        task
        for task in study_tasks
        if task["task_kind"] == "domain_route/reconcile-apply"
        or task["task_kind"].startswith("publication_aftercare/")
        or task["task_kind"] == "paper_autonomy/repair-recheck"
    ] == []
