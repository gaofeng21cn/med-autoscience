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
    assert apply_result["domain_truth_owner"] == "med-autoscience"
    assert apply_result["recommended_task_kind"] == "domain_route/reconcile-apply"
    assert apply_result["authority_boundary"]["mas_resumes_provider_worker"] is False
    handoff = apply_result["opl_runtime_owner_route_handoff"]
    assert handoff["queue_owner"] == "one-person-lab"
    assert handoff["reason"] == expected_reason
    assert handoff["authority_boundary"]["mas_submits_runtime_chat"] is False
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert runtime_state["continuation_policy"] == "wait_for_opl_runtime_owner"
    assert runtime_state["continuation_anchor"] == "opl_runtime_owner_route"
    assert runtime_state["continuation_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert runtime_state["last_opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    return runtime_state


def test_scan_domain_routes_redrives_publication_gate_closeout_after_specificity_targets_resolve(
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
            "anchor_kind": "missing",
            "allow_write": False,
            "bundle_tasks_downstream_only": True,
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
            "next_work_unit": {
                "unit_id": "gate_needs_specificity",
                "lane": "controller",
                "controller_work_unit_executable": False,
                "non_executable_reason": "gate_needs_specificity_without_targets",
                "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
            },
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
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
                "blocked_reason": "publication_gate still needs specificity even though publication_eval now carries concrete targets",
                "next_owner": "publication_gate",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "same_fingerprint_auto_turn_count": 4,
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert "blocked_turn_closeout" not in runtime_state
        assert "last_liveness_reconcile_reason" not in runtime_state
        assert runtime_state["pending_user_message_count"] == 0
        assert runtime_state["continuation_anchor"] == "decision"
        assert runtime_state["continuation_reason"] == "runtime_platform_repair_redrive"
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-specificity"
        assert authorization["work_unit_id"] == "gate_needs_specificity"
        assert authorization["work_unit_fingerprint"] == "publication-blockers::obesity"
        assert authorization["next_work_unit"] == {"unit_id": "gate_needs_specificity", "lane": "controller"}
        assert {item["target_kind"] for item in authorization["specificity_targets"]} == {
            "claim",
            "figure",
            "table",
            "metric",
            "source_path",
        }
        assert runtime_state["last_runtime_platform_repair"]["clear_reason"] == (
            "stale_publication_gate_closeout_targets_resolved"
        )
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
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
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
                "runtime_health_epoch": "runtime-health-epoch-obesity",
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "idle",
                "retry_budget_remaining": 3,
                "blocking_reasons": [],
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "pending_user_message_count": 0,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-stale",
                "closeout_path": str(
                    quest_root
                    / "artifacts"
                    / "runtime"
                    / "turn_closeouts"
                    / "mas-run-obesity-stale.json"
                ),
                "blocked_reason": "publication_gate still needs specificity",
                "next_owner": "publication_gate",
            },
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_wait",
                "action": "block",
                "reason_code": "blocked_turn_closeout_waiting_for_owner",
                "requires_user_input": False,
                "valid_blocking": True,
                "kind": "turn_closeout",
                "next_owner": "publication_gate",
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity",
                "source_signature": "truth-source-obesity",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "auto_runtime_parked",
            "paper_stage": "scientific_anchor_missing",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "parked"},
        },
    )

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
        expected_reason="stale_publication_gate_closeout_targets_resolved",
    )
    assert apply_result["reason"] == "stale_publication_gate_closeout_targets_resolved"
    assert apply_result["current_controller_authorization_written"] is True
    assert apply_result["stale_specificity_cleared"] is True
    assert apply_result["blocked_turn_closeout_clear"]["cleared"] is True
    assert apply_result["existing_pending_user_message_resume"] is None
    assert apply_result["gate_status"]["ready"] is False
    assert "blocked_turn_closeout" not in runtime_state
    assert "last_liveness_reconcile_reason" not in runtime_state
    assert runtime_state["pending_user_message_count"] == 0
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == "current-specificity"
    assert runtime_state["last_runtime_platform_repair"]["clear_reason"] == (
        "stale_publication_gate_closeout_targets_resolved"
    )
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_redrives_controller_authorized_paper_line_owner_closeout_after_targets_resolve(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return_to_controller::publication-blockers::dpcc",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::dpcc",
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
            "decision_id": "current-specificity-paper-line-owner",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "request_gate_specificity"}],
            "route_target": "controller",
            "work_unit_fingerprint": "publication-blockers::dpcc",
            "next_work_unit": {
                "unit_id": "gate_needs_specificity",
                "lane": "controller",
                "controller_work_unit_executable": False,
                "non_executable_reason": "gate_needs_specificity_without_targets",
                "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
            },
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "blocked_turn_closeout": {
                "run_id": "mas-run-dpcc-paper-line-owner",
                "blocked_reason": (
                    "control_plane_route_blocked_for_paper_line_repair: targets are concrete but "
                    "the turn lacks an authorized paper-line repair owner"
                ),
                "next_owner": (
                    "MAS/controller-authorized paper-line repair owner for paper/numeric_trace.json "
                    "and paper/evidence_ledger.json citation-key provenance"
                ),
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "same_fingerprint_auto_turn_count": 4,
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert "blocked_turn_closeout" not in runtime_state
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-specificity-paper-line-owner"
        assert authorization["work_unit_id"] == "gate_needs_specificity"
        assert authorization["next_work_unit"] == {"unit_id": "gate_needs_specificity", "lane": "controller"}
        assert {item["target_kind"] for item in authorization["specificity_targets"]} == {
            "claim",
            "figure",
            "table",
            "metric",
            "source_path",
        }
        assert runtime_state["last_runtime_platform_repair"]["clear_reason"] == (
            "stale_publication_gate_closeout_targets_resolved"
        )
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dpcc-paper-line-redriven",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dpcc-paper-line-redriven"},
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
            "decision": "blocked",
            "reason": "quest_waiting_for_user",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "parked",
                "active_run_id": None,
                "runtime_audit": {"status": "parked", "worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-epoch-dpcc",
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
                "pending_user_message_count": 0,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "blocked_turn_closeout": {
                "run_id": "mas-run-dpcc-paper-line-owner",
                "blocked_reason": "control_plane_route_blocked_for_paper_line_repair",
                "next_owner": (
                    "MAS/controller-authorized paper-line repair owner for paper/numeric_trace.json "
                    "and paper/evidence_ledger.json citation-key provenance"
                ),
            },
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_wait",
                "action": "block",
                "reason_code": "blocked_turn_closeout_waiting_for_owner",
                "requires_user_input": False,
                "valid_blocking": True,
                "kind": "turn_closeout",
                "next_owner": (
                    "MAS/controller-authorized paper-line repair owner for paper/numeric_trace.json "
                    "and paper/evidence_ledger.json citation-key provenance"
                ),
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dpcc",
                "source_signature": "truth-source-dpcc",
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
            "paper_stage": "write",
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

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    runtime_state = _assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason="stale_publication_gate_closeout_targets_resolved",
    )
    assert apply_result["reason"] == "stale_publication_gate_closeout_targets_resolved"
    assert apply_result["current_controller_authorization_written"] is True
    assert apply_result["blocked_turn_closeout_clear"]["cleared"] is True
    assert "blocked_turn_closeout" not in runtime_state
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == (
        "current-specificity-paper-line-owner"
    )
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_redrives_mas_controller_closeout_when_specificity_authorization_is_stale(
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
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-specificity-with-targets",
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
            "pending_user_message_count": 0,
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
                "blocked_reason": "controller authorization still marks gate_needs_specificity without targets",
                "next_owner": "MAS/controller",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "last_controller_decision_authorization": {
                "decision_id": "old-specificity-without-targets",
                "route_target": "controller",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::obesity",
                "next_work_unit": {"unit_id": "gate_needs_specificity", "lane": "controller"},
                "controller_work_unit_executable": False,
                "non_executable_reason": "gate_needs_specificity_without_targets",
                "controller_work_unit_lifecycle": {
                    "lifecycle_state": "needs_specificity",
                    "latest_event_type": "needs_specificity",
                    "delivery_blocked": True,
                    "block_reason": "needs_specificity",
                    "terminal_consumed": True,
                },
            },
            "same_fingerprint_auto_turn_count": 4,
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert "blocked_turn_closeout" not in runtime_state
        assert runtime_state["continuation_reason"] == "runtime_platform_repair_redrive"
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-specificity-with-targets"
        assert authorization["work_unit_id"] == "gate_needs_specificity"
        assert "non_executable_reason" not in authorization
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
                "active_run_id": "run-obesity-redriven",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-obesity-redriven"},
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
            "decision": "blocked",
            "reason": "quest_waiting_for_user",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "stale",
                "active_run_id": None,
                "runtime_audit": {"status": "stale", "worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-epoch-obesity",
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
                "retry_budget_remaining": 3,
                "blocking_reasons": ["quest_marked_running_but_no_live_session"],
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "pending_user_message_count": 0,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-stale",
                "blocked_reason": "controller authorization still marks gate_needs_specificity without targets",
                "next_owner": "MAS/controller",
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity",
                "source_signature": "truth-source-obesity",
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
            "paper_stage": "scientific_anchor_missing",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
        },
    )

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
        expected_reason="stale_publication_gate_closeout_targets_resolved",
    )
    assert apply_result["current_controller_authorization_written"] is True
    assert apply_result["blocked_turn_closeout_clear"]["cleared"] is True
    assert "blocked_turn_closeout" not in runtime_state
    authorization = runtime_state["last_controller_decision_authorization"]
    assert authorization["decision_id"] == "current-specificity-with-targets"
    assert authorization["work_unit_id"] == "gate_needs_specificity"
    assert "non_executable_reason" not in authorization


def test_scan_domain_routes_redrives_mas_controller_closeout_when_authorization_was_cleared(
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
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-specificity-after-closeout",
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
            "pending_user_message_count": 0,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-stale",
                "blocked_reason": "controller_authorization_consumption_missing_for_gate_specificity_targets",
                "next_owner": "MAS/controller",
            },
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert "blocked_turn_closeout" not in runtime_state
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-specificity-after-closeout"
        assert authorization["work_unit_id"] == "gate_needs_specificity"
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
                "active_run_id": "run-obesity-after-closeout",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-obesity-after-closeout"},
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
            "decision": "blocked",
            "reason": "quest_waiting_for_user",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "parked",
                "active_run_id": None,
                "runtime_audit": {"status": "parked", "worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-epoch-obesity",
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "idle",
                "retry_budget_remaining": 3,
                "blocking_reasons": [],
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "pending_user_message_count": 0,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-stale",
                "blocked_reason": "controller_authorization_consumption_missing_for_gate_specificity_targets",
                "next_owner": "MAS/controller",
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity",
                "source_signature": "truth-source-obesity",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "auto_runtime_parked",
            "paper_stage": "scientific_anchor_missing",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "parked"},
        },
    )

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
        expected_reason="stale_publication_gate_closeout_targets_resolved",
    )
    assert apply_result["reason"] == "stale_publication_gate_closeout_targets_resolved"
    assert apply_result["current_controller_authorization_written"] is True
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == "current-specificity-after-closeout"


def test_scan_domain_routes_resumes_pending_platform_redrive_after_stale_specificity_clear(
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
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-specificity-after-clear",
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
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "runtime_platform_repair_redrive",
            "last_runtime_platform_repair": {
                "clear_reason": "stale_specificity_terminal",
                "cleared_keys": ["last_controller_decision_authorization", "blocked_turn_closeout"],
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert runtime_state["continuation_reason"] == "runtime_platform_repair_redrive"
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-specificity-after-clear"
        assert authorization["work_unit_id"] == "gate_needs_specificity"
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
                "active_run_id": "run-obesity-after-clear",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-obesity-after-clear"},
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
            "runtime_liveness_audit": {"active_run_id": None, "runtime_audit": {"worker_running": False}},
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-epoch-obesity",
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "idle",
                "retry_budget_remaining": 2,
                "blocking_reasons": [],
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
                "pending_user_message_count": 0,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "interaction_arbitration": {
                "classification": "platform_repair_decision_redrive",
                "action": "resume",
                "reason_code": "runtime_platform_repair_decision_redrive",
            },
            "publication_eval": publication_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity",
                "source_signature": "truth-source-obesity",
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
            "paper_stage": "scientific_anchor_missing",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
        },
    )

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
        expected_reason="runtime_controller_redrive_required",
    )
    assert apply_result["repair_kind"] == "pending_runtime_platform_repair_redrive"
    assert apply_result["current_controller_authorization_written"] is True
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == "current-specificity-after-clear"


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
