from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_redrives_target_ready_mas_controller_closeout_with_control_plane_pending_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::dm002"
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::dm002",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "gate_needs_specificity", "lane": "controller"},
                "specificity_targets": _specificity_targets(study_root),
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-specificity-dm002",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_gate_specificity"}],
            "route_target": "controller",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "gate_needs_specificity",
                "lane": "controller",
                "summary": "Ask the publication gate to identify concrete targets.",
            },
        },
    )
    _write_json(
        quest_root / ".ds" / "user_message_queue.json",
        {
            "version": 1,
            "pending": [
                {
                    "message_id": "msg-publication-gate",
                    "source": "codex-publication-gate",
                    "content": "Hard control message from Codex orchestration layer: continue only bounded publication gate repair.",
                    "status": "queued",
                },
                {
                    "message_id": "msg-medical-surface",
                    "source": "codex-medical-publication-surface",
                    "content": "Hard control message from Codex orchestration layer: repair the manuscript-facing surface.",
                    "status": "queued",
                },
            ],
            "completed": [],
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 2,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "blocked_turn_closeout": {
                "run_id": "mas-run-dm002-target-ready",
                "blocked_reason": "controller_route_work_unit_unsupported",
                "next_owner": "MAS/controller",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "last_controller_decision_authorization": {
                "decision_id": "current-specificity-dm002",
                "route_target": "controller",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Ask the publication gate to identify concrete targets.",
                },
                "controller_actions": ["request_gate_specificity"],
                "specificity_targets": _specificity_targets(study_root),
                "source": "runtime_watch_outer_loop_wakeup",
                "controller_work_unit_executable": True,
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert runtime_state["pending_user_message_count"] == 2
        assert "blocked_turn_closeout" not in runtime_state
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-specificity-dm002"
        assert authorization["next_work_unit"]["unit_id"] == "gate_needs_specificity"
        assert authorization["next_work_unit"].get("controller_work_unit_executable") is None
        assert authorization.get("controller_work_unit_executable") is None
        assert {item["target_kind"] for item in authorization["specificity_targets"]} == {
            "claim",
            "figure",
            "table",
            "metric",
            "source_path",
        }
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dm002-target-ready-redrive",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dm002-target-ready-redrive"},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "quest_status": "waiting_for_user",
            "decision": "resume",
            "reason": "quest_waiting_platform_repair_redrive",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-epoch-dm002",
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "pending_user_message_count": 2,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "blocked_turn_closeout": {
                "run_id": "mas-run-dm002-target-ready",
                "blocked_reason": "controller_route_work_unit_unsupported",
                "next_owner": "MAS/controller",
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002",
                "source_signature": "truth-source-dm002",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "escalated"},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    assert len(ensure_calls) == 1
    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    assert apply_result["dispatch_status"] == "applied"
    assert apply_result["reason"] == "stale_publication_gate_closeout_targets_resolved"
    assert apply_result["current_controller_authorization_written"] is True
    assert apply_result["blocked_turn_closeout_clear"]["cleared"] is True
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


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
