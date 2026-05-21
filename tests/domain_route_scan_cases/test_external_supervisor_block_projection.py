from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_owner_route_required(
    *,
    apply_result: dict,
    ensure_calls: list[dict[str, object]],
    quest_root: Path,
    expected_reason: str,
) -> dict:
    assert ensure_calls == []
    assert apply_result["dispatch_status"] == "owner_route_required"
    assert apply_result["reason"] == expected_reason
    assert apply_result["queue_owner"] == "one-person-lab"
    assert apply_result["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert apply_result["opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert runtime_state["continuation_policy"] == "wait_for_opl_runtime_owner"
    assert runtime_state["continuation_anchor"] == "opl_runtime_owner_route"
    assert runtime_state["continuation_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert runtime_state["last_opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    return runtime_state


def test_scan_domain_routes_dispatches_external_supervisor_repair_after_repeated_block(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
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


def test_scan_domain_routes_dispatches_external_supervisor_repair_from_blocked_lifecycle_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: _status_payload(study_id=study_id, study_root=study_root, quest_root=quest_root),
    )
    progress_payload = _progress_payload(study_id=study_id, study_root=study_root)
    progress_payload["ai_repair_lifecycle"]["state"] = "blocked"
    monkeypatch.setattr(module.study_progress, "read_study_progress", lambda **_: progress_payload)

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
    action = study["action_queue"][0]
    assert action["reason"] == "runtime_recovery_not_authorized"
    assert action["authority"] == "external_supervisor"
    assert study["owner_route"]["allowed_actions"] == ["runtime_platform_repair"]
    assert study["recovery_intent"]["current_action"] == "safe_reconcile_ready"


def test_scan_domain_routes_applies_external_supervisor_redrive_when_specificity_targets_supersede_terminal(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::obesity",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::obesity",
                "next_work_unit": {"unit_id": "gate_needs_specificity", "lane": "controller"},
                "specificity_targets": _specificity_targets(study_root),
            }
        ],
    }
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "blockers": ["missing_publication_anchor"],
            "current_required_action": "return_to_publishability_gate",
            "supervisor_phase": "scientific_anchor_missing",
        },
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-specificity",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_gate_specificity"}],
            "route_target": "controller",
            "work_unit_fingerprint": "publication-blockers::obesity",
            "next_work_unit": {"unit_id": "gate_needs_specificity", "lane": "controller"},
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
            "pending_user_message_ids": ["msg-data", "msg-gate"],
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-stale",
                "closeout_path": str(
                    quest_root
                    / "artifacts"
                    / "runtime"
                    / "turn_closeouts"
                    / "mas-run-obesity-stale.json"
                ),
                "blocked_reason": "AI reviewer authority missing",
                "next_owner": "ai_reviewer",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "same_fingerprint_auto_turn_count": 0,
            "last_controller_decision_authorization": {
                "decision_id": "current-specificity",
                "route_target": "controller",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::obesity",
                "controller_work_unit_lifecycle": {
                    "lifecycle_state": "needs_specificity",
                    "latest_event_type": "needs_specificity",
                    "delivery_blocked": True,
                    "block_reason": "needs_specificity",
                    "terminal_consumed": True,
                },
            },
            "control_intent_lifecycle": {
                "state": "needs_specificity",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::obesity",
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert "last_controller_decision_authorization" not in runtime_state
        assert "control_intent_lifecycle" not in runtime_state
        assert "blocked_turn_closeout" not in runtime_state
        assert "last_liveness_reconcile_reason" not in runtime_state
        assert runtime_state["pending_user_message_count"] == 2
        assert runtime_state["continuation_anchor"] == "user_message_queue"
        assert runtime_state["continuation_reason"] == "runtime_platform_repair_resume_existing_pending_user_message"
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-obesity-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-obesity-recovered"},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            **_status_payload(study_id=study_id, study_root=study_root, quest_root=quest_root),
            "quest_status": "waiting_for_user",
            "publication_eval": publication_eval,
        },
    )
    progress_payload = _progress_payload(study_id=study_id, study_root=study_root)
    progress_payload["ai_repair_lifecycle"]["state"] = "blocked"
    monkeypatch.setattr(module.study_progress, "read_study_progress", lambda **_: progress_payload)

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    runtime_state = _assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason="stale_specificity_terminal_targets_resolved",
    )
    assert apply_result["reason"] == "stale_specificity_terminal_targets_resolved"
    assert apply_result["stale_specificity_cleared"] is True
    assert apply_result["existing_pending_user_message_resume"]["marked"] is True
    assert apply_result["blocked_turn_closeout_clear"]["cleared"] is True
    assert apply_result["gate_status"]["ready"] is False
    assert "blocked_turn_closeout" not in runtime_state
    assert runtime_state["pending_user_message_count"] == 2
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_redrives_half_repaired_pending_queue_with_stale_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::obesity",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::obesity",
                "next_work_unit": {"unit_id": "gate_needs_specificity", "lane": "controller"},
                "specificity_targets": _specificity_targets(study_root),
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 2,
            "continuation_policy": "auto",
            "continuation_anchor": "user_message_queue",
            "continuation_reason": "runtime_platform_repair_resume_existing_pending_user_message",
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-stale",
                "closeout_path": str(
                    quest_root
                    / "artifacts"
                    / "runtime"
                    / "turn_closeouts"
                    / "mas-run-obesity-stale.json"
                ),
                "blocked_reason": "AI reviewer authority missing",
                "next_owner": "ai_reviewer",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert "blocked_turn_closeout" not in runtime_state
        assert "last_liveness_reconcile_reason" not in runtime_state
        assert runtime_state["pending_user_message_count"] == 2
        assert runtime_state["continuation_anchor"] == "user_message_queue"
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-obesity-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-obesity-recovered"},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            **_status_payload(study_id=study_id, study_root=study_root, quest_root=quest_root),
            "quest_status": "waiting_for_user",
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "user_message_queue",
                "continuation_reason": "runtime_platform_repair_resume_existing_pending_user_message",
                "pending_user_message_count": 2,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "interaction_arbitration": {
                "classification": "pending_user_message_redrive",
                "action": "resume",
                "reason_code": "runtime_platform_repair_pending_user_message_redrive",
                "requires_user_input": False,
                "valid_blocking": False,
                "kind": "user_message_queue",
                "decision_type": None,
                "source_artifact_path": None,
                "pending_user_message_count": 2,
                "controller_stage_note": "Runtime platform repair marked an existing pending user-message queue for autonomous redrive.",
            },
            "publication_eval": publication_eval,
        },
    )
    progress_payload = _progress_payload(study_id=study_id, study_root=study_root)
    progress_payload["ai_repair_lifecycle"] = {
        **progress_payload["ai_repair_lifecycle"],
        "state": "applied",
        "external_supervisor_required": False,
        "blocked_reason": None,
    }
    monkeypatch.setattr(module.study_progress, "read_study_progress", lambda **_: progress_payload)

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        persist_surfaces=False,
    )

    apply_result = result["studies"][0]["runtime_platform_repair_apply"]
    runtime_state = _assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason="stale_blocked_turn_closeout_pending_queue_redrive",
    )
    assert apply_result["reason"] == "stale_blocked_turn_closeout_pending_queue_redrive"
    assert apply_result["existing_pending_user_message_resume"]["marked"] is True
    assert apply_result["blocked_turn_closeout_clear"]["cleared"] is True
    assert "blocked_turn_closeout" not in runtime_state


def _write_previous_scan(workspace_root: Path, *, study_id: str) -> None:
    previous_route = {
        "surface": "domain_route_owner_route",
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
            "surface": "portable_domain_route_scan",
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
