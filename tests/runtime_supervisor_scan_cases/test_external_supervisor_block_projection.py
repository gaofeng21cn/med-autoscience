from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_supervisor_scan_dispatches_external_supervisor_repair_after_repeated_block(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    _write_previous_scan(profile.workspace_root, study_id=study_id)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: _status_payload(study_id=study_id, study_root=study_root, quest_root=quest_root),
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: _progress_payload(study_id=study_id, study_root=study_root),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=True,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
    action = study["action_queue"][0]
    assert action["authority"] == "external_supervisor"
    assert action["reason"] == "runtime_recovery_not_authorized"
    assert action["handoff_packet"]["recommended_owner"] == "external_engineering_agent"
    assert [item["action_type"] for item in result["action_queue"]] == ["runtime_platform_repair"]
    assert study["external_supervisor_required"] is True
    assert study["next_owner"] == "external_supervisor"
    assert study["blocked_reason"] == "runtime_recovery_not_authorized"
    assert study["why_not_applied"] == "runtime_recovery_not_authorized"
    assert study["repeat_suppression"]["repeat_suppressed"] is False
    assert study["repeat_suppression"]["why_not_applied"] is None
    assert study["recovery_intent"]["current_action"] == "safe_reconcile_ready"
    assert study["recovery_intent"]["reason"] == "runtime_recovery_not_authorized"
    assert study["recovery_intent"]["last_result"] is None
    assert study["recovery_intent"]["evidence_refs"]["action_ids"] == [action["action_id"]]


def _write_previous_scan(workspace_root: Path, *, study_id: str) -> None:
    previous_route = {
        "surface": "runtime_supervisor_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "truth_epoch": "truth-epoch-dm002",
        "runtime_health_epoch": "runtime-health-epoch-dm002",
        "work_unit_fingerprint": "truth-snapshot::blocked",
        "failure_signature": "runtime_recovery_not_authorized",
        "trace_id": "owner-route-trace::previous",
        "route_epoch": "truth-epoch-dm002",
        "source_fingerprint": "truth-source-dm002",
        "current_owner": "controller_stop",
        "next_owner": "external_supervisor",
        "owner_reason": "runtime_recovery_not_authorized",
        "active_run_id": None,
        "allowed_actions": [],
        "blocked_actions": ["runtime_platform_repair", "return_to_ai_reviewer_workflow"],
        "idempotency_key": "owner-route::previous",
    }
    _write_json(
        workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": previous_route,
                    "meaningful_artifact_delta": False,
                }
            ],
            "action_queue": [],
        },
    )


def _status_payload(*, study_id: str, study_root: Path, quest_root: Path) -> dict:
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": "quest-dm002",
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "runtime_liveness_audit": {
            "status": "parked",
            "active_run_id": None,
            "runtime_audit": {"status": "parked", "worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-dm002",
            "canonical_runtime_action": "continue_supervising_runtime",
            "attempt_state": "idle",
            "retry_budget_remaining": 3,
            "blocking_reasons": [],
        },
        "publication_eval": {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::specific",
                    "action_type": "return_to_controller",
                    "work_unit_fingerprint": "publication-blockers::specific",
                    "next_work_unit": {"unit_id": "gate_needs_specificity"},
                    "specificity_targets": _specificity_targets(study_root),
                }
            ],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002",
            "source_signature": "truth-source-dm002",
        },
    }


def _progress_payload(*, study_id: str, study_root: Path) -> dict:
    return {
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "current_stage": "runtime_blocked",
        "paper_stage": "scientific_anchor_missing",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "ai_repair_lifecycle": {
            "state": "external_supervisor_required",
            "blocked_reason": "runtime_recovery_not_authorized",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "projection_only": True,
            "top_action": {
                "action_type": "controller_repair",
                "repair_kind": "bounded_work_unit_redrive",
                "owner": "mas_controller",
                "auto_apply_allowed": True,
            },
        },
    }


def _specificity_targets(study_root: Path) -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "primary_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "table",
            "target_id": "submission_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "publication_gate_blocked",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "publication_gate_blocked",
        },
    ]
