from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_route_scan_cases.owner_route_test_helpers import assert_owner_route_required
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_clears_stale_package_terminal_when_current_controller_runtime_work_unit_is_current(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::current"
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "primary_claim",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-analysis-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "current_package_freshness_required",
            "same_fingerprint_auto_turn_count": 5,
            "retry_state": {"terminal": True, "current_package_freshness_required": True},
            "last_controller_decision_authorization": {
                "decision_id": "old-finalize-refresh",
                "route_target": "finalize",
                "work_unit_id": "submission_minimal_refresh",
                "work_unit_fingerprint": work_unit_fingerprint,
                "controller_actions": ["run_gate_clearing_batch"],
                "controller_work_unit_lifecycle": {
                    "lifecycle_state": "current_package_freshness_required",
                    "latest_event_type": "current_package_freshness_required",
                    "delivery_blocked": True,
                    "block_reason": "current_package_freshness_required",
                    "terminal_consumed": True,
                },
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-analysis-redrive"
        assert authorization["work_unit_id"] == "analysis_claim_evidence_repair"
        assert authorization["work_unit_fingerprint"] == work_unit_fingerprint
        assert authorization["specificity_targets"][0]["target_kind"] == "claim"
        assert runtime_state["same_fingerprint_auto_turn_count"] == 0
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dm002-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dm002-recovered"},
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
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": publication_eval,
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "managed_runtime_escalated",
            "paper_stage": "analysis-campaign",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason="opl_runtime_owner_route_required",
    )
    authorization = runtime_state["last_controller_decision_authorization"]
    assert authorization["decision_id"] == "current-analysis-redrive"
    assert authorization["work_unit_id"] == "analysis_claim_evidence_repair"
    assert "retry_state" not in runtime_state
    assert runtime_state["same_fingerprint_auto_turn_count"] == 0
    assert apply_result["stale_controller_terminal_cleared"] is True
    assert study["blocked_reason"] == "opl_runtime_owner_route_required"
    assert study["next_owner"] == "one-person-lab"
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_writes_current_controller_authorization_before_no_live_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::current"
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::current",
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "specificity_targets": [
                    {"target_kind": "metric", "target_id": "main_metric", "source_path": str(study_root / "artifacts" / "results" / "main_result.json")}
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-dpcc-analysis-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "publication_eval_ref": {
                "eval_id": f"publication-eval::{study_id}::current",
                "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": study_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "same_fingerprint_auto_turn_count": 5,
        },
    )

    def fake_ensure_study_runtime(**_: object) -> dict[str, object]:
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-dpcc-analysis-redrive"
        assert authorization["publication_eval_id"] == f"publication-eval::{study_id}::current"
        assert authorization["publication_eval_ref"]["eval_id"] == authorization["publication_eval_id"]
        assert authorization["work_unit_id"] == "analysis_claim_evidence_repair"
        assert authorization["specificity_targets"][0]["target_kind"] == "metric"
        assert runtime_state["same_fingerprint_auto_turn_count"] == 0
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dpcc-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dpcc-recovered"},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "active",
                "decision": "resume",
                "reason": "quest_marked_running_but_no_live_session",
                "active_run_id": None,
                "runtime_liveness_audit": {"active_run_id": None, "runtime_audit": {"worker_running": False}},
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "managed_runtime_escalated",
                "paper_stage": "analysis-campaign",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": None, "health_status": "recovering"},
                "quality_review_loop": {"closure_state": "review_required"},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        quest_root=quest_root,
        expected_reason="opl_runtime_owner_route_required",
    )
    assert apply_result["current_controller_authorization_written"] is True
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == "current-dpcc-analysis-redrive"
    assert study["blocked_reason"] == "opl_runtime_owner_route_required"
    assert study["next_owner"] == "one-person-lab"
    assert study["external_supervisor_required"] is False


def test_scan_domain_routes_resumes_waiting_controller_work_unit_pending_after_authorization_written(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::current"
    publication_eval = {
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "current-dpcc-analysis-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    authorization = {
        "decision_id": "current-dpcc-analysis-redrive",
        "route_target": "write",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": ["run_quality_repair_batch"],
        "source": "domain_route_scan_platform_repair",
    }
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
            "continuation_reason": "controller_work_unit_pending",
            "last_controller_decision_authorization": authorization,
            "same_fingerprint_auto_turn_count": 0,
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert runtime_state["last_controller_decision_authorization"] == authorization
        assert runtime_state["continuation_reason"] == "controller_work_unit_pending"
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "runtime_liveness_audit": {
                "active_run_id": "run-dpcc-after-auth",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-dpcc-after-auth"},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "waiting_for_user",
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "active_run_id": None,
                "runtime_liveness_audit": {"active_run_id": None, "runtime_audit": {"worker_running": False}},
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
                "continuation_state": {
                    "quest_status": "waiting_for_user",
                    "active_run_id": None,
                    "continuation_policy": "auto",
                    "continuation_anchor": "decision",
                    "continuation_reason": "controller_work_unit_pending",
                    "pending_user_message_count": 0,
                    "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
                },
                "interaction_arbitration": {
                    "classification": "platform_repair_decision_redrive",
                    "action": "resume",
                    "reason_code": "runtime_platform_repair_decision_redrive",
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": None, "health_status": "escalated"},
                "quality_review_loop": {"closure_state": "review_required"},
            },
            study_id,
            publication_eval,
        ),
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
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        ensure_calls=ensure_calls,
        quest_root=quest_root,
        expected_reason=None,
    )
    assert apply_result["repair_kind"] == "pending_runtime_platform_repair_redrive"
    assert apply_result["current_controller_authorization_written"] is True
    assert runtime_state["last_controller_decision_authorization"] == authorization
    assert study["external_supervisor_required"] is False


def test_scan_domain_routes_applies_current_controller_redrive_for_live_activity_timeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::current"
    publication_eval = {
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "specificity_targets": [
                    {
                        "target_kind": "metric",
                        "target_id": "main_metric",
                        "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "current-dpcc-live-timeout-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": "run-live-timeout",
            "worker_running": True,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "same_fingerprint_auto_turn_count": 5,
        },
    )

    def fake_ensure_study_runtime(**_: object) -> dict[str, object]:
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-dpcc-live-timeout-redrive"
        assert authorization["work_unit_id"] == "analysis_claim_evidence_repair"
        assert authorization["specificity_targets"][0]["target_kind"] == "metric"
        assert runtime_state["active_run_id"] is None
        assert runtime_state["worker_running"] is False
        assert runtime_state["same_fingerprint_auto_turn_count"] == 0
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "resume_postcondition": {
                "effective": True,
                "failure_mode": None,
                "snapshot_status": "running",
                "active_run_id": "run-dpcc-redriven",
                "scheduled": True,
                "started": True,
                "queued": False,
            },
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
        }

    pause_calls: list[dict[str, object]] = []

    def fake_pause_study_runtime(**kwargs: object) -> dict[str, object]:
        pause_calls.append(dict(kwargs))
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert runtime_state["last_controller_decision_authorization"]["decision_id"] == "current-dpcc-live-timeout-redrive"
        assert runtime_state["active_run_id"] is None
        assert runtime_state["worker_running"] is False
        assert runtime_state["same_fingerprint_auto_turn_count"] == 0
        runtime_state["status"] = "paused"
        (quest_root / ".ds" / "runtime_state.json").write_text(
            json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "decision": "pause",
            "reason": "human_takeover_requested",
            "quest_status": "paused",
        }

    monkeypatch.setattr(module.study_runtime_router, "pause_study_runtime", fake_pause_study_runtime)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "running",
                "decision": "noop",
                "reason": "quest_already_running",
                "active_run_id": "run-live-timeout",
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-live-timeout",
                    "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-live-timeout"},
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "recover_runtime",
                    "attempt_state": "recovering",
                    "retry_budget_remaining": 3,
                    "worker_liveness_state": {
                        "state": "activity_timeout",
                        "runtime_liveness_status": "live",
                        "worker_running": True,
                        "active_run_id": "run-live-timeout",
                    },
                    "blocking_reasons": [
                        "live_worker_meaningful_artifact_delta_timeout",
                        "same_fingerprint_loop",
                    ],
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": "run-live-timeout", "health_status": "recovering"},
                "quality_review_loop": {"closure_state": "review_required"},
            },
            study_id,
            publication_eval,
        ),
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
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        pause_calls=pause_calls,
        quest_root=quest_root,
        expected_reason=None,
    )
    assert apply_result["reason"] == "runtime_controller_redrive_required"
    assert apply_result["repair_kind"] == "live_activity_timeout_current_controller_redrive"
    assert apply_result["force_fresh_turn"]["forced"] is False
    assert apply_result["force_fresh_turn"]["reason"] == "opl_runtime_owner_route_required"
    assert apply_result["current_controller_authorization_written"] is True
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == "current-dpcc-live-timeout-redrive"
    assert study["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["next_owner"] == "one-person-lab"
    assert study["external_supervisor_required"] is False


def test_scan_domain_routes_derives_live_activity_timeout_from_progress_when_runtime_health_is_still_live(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_fingerprint = "publication-blockers::current"
    publication_eval = {
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
                "specificity_targets": [
                    {
                        "target_kind": "metric",
                        "target_id": "main_metric",
                        "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "decision_id": "current-dpcc-progress-timeout-redrive",
            "study_id": study_id,
            "quest_id": study_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": study_id,
            "active_run_id": "run-live-heartbeat-only",
            "worker_running": True,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "same_fingerprint_auto_turn_count": 5,
        },
    )

    def fake_ensure_study_runtime(**_: object) -> dict[str, object]:
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-dpcc-progress-timeout-redrive"
        assert authorization["work_unit_id"] == "analysis_claim_evidence_repair"
        assert runtime_state["active_run_id"] is None
        assert runtime_state["worker_running"] is False
        assert runtime_state["same_fingerprint_auto_turn_count"] == 0
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_status": "running",
            "decision": "resume",
            "resume_postcondition": {
                "effective": True,
                "active_run_id": "run-dpcc-progress-redriven",
                "scheduled": True,
                "started": True,
                "queued": False,
            },
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "running",
                "decision": "noop",
                "reason": "quest_already_running",
                "active_run_id": "run-live-heartbeat-only",
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-live-heartbeat-only",
                    "runtime_audit": {
                        "status": "live",
                        "worker_running": True,
                        "active_run_id": "run-live-heartbeat-only",
                    },
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "continue_supervising_runtime",
                    "attempt_state": "live",
                    "retry_budget_remaining": 3,
                    "worker_liveness_state": {
                        "state": "live",
                        "runtime_liveness_status": "live",
                        "worker_running": True,
                        "active_run_id": "run-live-heartbeat-only",
                    },
                    "blocking_reasons": [],
                },
                "publication_eval": publication_eval,
            },
            {
                "study_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "write",
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
                "supervision": {"active_run_id": "run-live-heartbeat-only", "health_status": "recovering"},
                "quality_review_loop": {"closure_state": "review_required"},
                "progress_freshness": {
                    "activity_timeout": {
                        "state": "timed_out",
                        "active_run_id": "run-live-heartbeat-only",
                        "breach_types": ["same_fingerprint_loop"],
                    }
                },
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    apply_result = result["studies"][0]["runtime_platform_repair_apply"]
    runtime_state = assert_owner_route_required(
        apply_result=apply_result,
        quest_root=quest_root,
        expected_reason=None,
    )
    assert apply_result["repair_kind"] == "live_activity_timeout_current_controller_redrive"
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == (
        "current-dpcc-progress-timeout-redrive"
    )
