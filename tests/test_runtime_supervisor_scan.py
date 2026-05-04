from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_supervisor_scan_queues_external_repair_for_retry_exhausted_no_live_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-dpcc-primary-care-phenotype-treatment-gap", quest_id="quest-dpcc")
    quest_root = profile.runtime_root / "quest-dpcc"
    repair_actions = study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"
    _write_json(
        repair_actions,
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "quest-dpcc",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "runtime_recovery_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_root": str(study_root),
            "quest_id": "quest-dpcc",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_status": "not_live",
            "runtime_liveness_audit": {
                "status": "not_live",
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            },
            "control_plane_snapshot": {
                "control_state": "blocked_runtime_escalation",
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("003-dpcc-primary-care-phenotype-treatment-gap",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["external_supervisor_required"] is True
    assert study["action_queue"][0]["action_type"] == "runtime_platform_repair"
    assert study["action_queue"][0]["action_id"] == (
        "supervisor-action::003-dpcc-primary-care-phenotype-treatment-gap::runtime_platform_repair::runtime_recovery_retry_budget_exhausted"
    )
    assert study["action_queue"][0]["authority"] == "external_supervisor"
    assert study["action_queue"][0]["handoff_packet"]["packet_type"] == "external_supervisor_handoff"
    assert study["action_queue"][0]["handoff_packet"]["recommended_owner"] == "external_engineering_agent"
    assert study["why_not_applied"] == "runtime_recovery_retry_budget_exhausted"
    assert study["escalation_reason"] == "runtime_recovery_retry_budget_exhausted"
    assert study["why_not_applied_timeline"][-1]["reason"] == "runtime_recovery_retry_budget_exhausted"
    assert study["scan_delta"]["previous_scan_seen"] is False
    assert study["gate_specificity"]["required"] is False
    assert study["ai_reviewer_assessment"]["missing"] is True
    assert [item["action_type"] for item in study["action_queue"]] == [
        "runtime_platform_repair",
        "return_to_ai_reviewer_workflow",
    ]
    assert study["ai_repair_lifecycle"]["blocked_reason"] == "runtime_recovery_retry_budget_exhausted"
    assert study["ai_repair_lifecycle"]["next_owner"] == "external_supervisor"
    assert study["ai_repair_lifecycle"]["authority"] == "external_supervisor"
    assert study["ai_repair_lifecycle"]["allowed_write_surfaces"] == [
        "artifacts/supervision/**",
        "artifacts/autonomy/repair_lifecycle/latest.json",
        "artifacts/autonomy/repair_actions/latest.json",
    ]
    assert study["ai_repair_lifecycle"]["forbidden_actions"] == [
        "paper_package_mutation",
        "manual_study_patch",
        "quality_gate_relaxation",
        "medical_claim_authoring",
    ]
    assert result["queue_history"]["latest_action_count"] == 2
    assert result["developer_supervisor_mode"]["mode"] == "developer_apply_safe"
    assert result["developer_supervisor_mode"]["developer_mode_enabled"] is True
    assert result["developer_supervisor_mode"]["safe_actions_enabled"] is True
    assert result["developer_supervisor_mode"]["github_user_gate"]["login"] == "gaofeng21cn"
    assert Path(result["refs"]["latest_path"]).is_file()
    assert Path(result["refs"]["history_path"]).is_file()


def test_supervisor_scan_does_not_apply_runtime_platform_repair_without_explicit_flag(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    quest_root = profile.runtime_root / "quest-nf"
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": "quest-nf",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "needs_specificity",
            "last_controller_decision_authorization": {
                "decision_id": "old-specificity",
                "route_target": "controller",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::old",
                "controller_work_unit_lifecycle": {
                    "lifecycle_state": "needs_specificity",
                    "latest_event_type": "needs_specificity",
                    "delivery_blocked": True,
                    "block_reason": "needs_specificity",
                    "terminal_consumed": True,
                },
            },
        },
    )
    original_runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("runtime platform repair must require an explicit apply flag")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fail_if_called)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {"status": "none", "worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "paper_stage": "write",
            "supervision": {"active_run_id": None, "health_status": "recovering"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
    )

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert runtime_state == original_runtime_state
    assert result["studies"][0]["runtime_platform_repair_apply"] is None
    assert result["studies"][0]["action_queue"][0]["action_type"] == "runtime_platform_repair"


def test_supervisor_scan_explicit_runtime_platform_repair_clears_stale_specificity_and_resumes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    quest_root = profile.runtime_root / "quest-nf"
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {"schema_version": 1, "status": "clear", "blockers": []},
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "recommended_actions": [
                {
                    "action_type": "continue_same_line",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "bundle-stage work is unlocked and can proceed on the critical path",
                    "work_unit_fingerprint": "publication-blockers::new",
                    "next_work_unit": {
                        "unit_id": "submission_minimal_refresh",
                        "lane": "finalize",
                        "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                    },
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-finalize",
            "study_id": "003-endocrine-burden-followup",
            "quest_id": "quest-nf",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "finalize",
            "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
            "route_rationale": "bundle-stage work is unlocked and can proceed on the critical path",
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": "quest-nf",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "pending_user_message_ids": [],
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "needs_specificity",
            "same_fingerprint_auto_turn_count": 7,
            "last_stage_fingerprint": "old-fingerprint",
            "last_stage_fingerprint_at": "2026-05-04T03:00:00+00:00",
            "retry_state": {"terminal": True, "gate_needs_specificity": True},
            "last_controller_decision_authorization": {
                "decision_id": "old-specificity",
                "route_target": "controller",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::old",
                "controller_work_unit_lifecycle": {
                    "lifecycle_state": "needs_specificity",
                    "latest_event_type": "needs_specificity",
                    "delivery_blocked": True,
                    "block_reason": "needs_specificity",
                    "terminal_consumed": True,
                },
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        return {
            "study_id": "003-endocrine-burden-followup",
            "quest_id": "quest-nf",
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "active_run_id": "run-nf-recovered",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-nf-recovered"},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "reason": "runtime_recovery_retry_budget_exhausted",
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
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "paper_stage": "write",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    study = result["studies"][0]
    assert len(ensure_calls) == 1
    assert ensure_calls[0]["source"] == "runtime_supervisor_scan_platform_repair"
    assert "last_controller_decision_authorization" not in runtime_state
    assert "retry_state" not in runtime_state
    assert "last_stage_fingerprint" not in runtime_state
    assert runtime_state["same_fingerprint_auto_turn_count"] == 0
    assert runtime_state["continuation_reason"] == "runtime_platform_repair_redrive"
    assert study["runtime_platform_repair_apply"]["dispatch_status"] == "applied"
    assert study["runtime_platform_repair_apply"]["stale_specificity_cleared"] is True
    assert study["runtime_platform_repair_apply"]["resume_result"]["decision"] == "resume"
    assert study["ai_repair_lifecycle"]["state"] == "applied"
    assert study["ai_repair_lifecycle"]["dispatch_status"] == "applied"
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_runtime_platform_repair_allows_concrete_bundle_stage_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    quest_root = profile.runtime_root / "quest-nf"
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "blockers": ["stale_study_delivery_mirror"],
            "current_required_action": "complete_bundle_stage",
            "supervisor_phase": "bundle_stage_blocked",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "recommended_actions": [
                {
                    "action_type": "continue_same_line",
                    "route_target": "finalize",
                    "route_rationale": "bundle-stage work is unlocked and can proceed on the critical path",
                    "work_unit_fingerprint": "publication-blockers::new",
                    "blocking_work_units": [
                        {
                            "unit_id": "submission_minimal_refresh",
                            "lane": "finalize",
                            "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                        }
                    ],
                    "next_work_unit": {
                        "unit_id": "submission_minimal_refresh",
                        "lane": "finalize",
                        "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                    },
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-gate-replay",
            "study_id": "003-endocrine-burden-followup",
            "quest_id": "quest-nf",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
            "route_target": "finalize",
            "route_rationale": "bundle-stage blockers are now on the critical path for this paper line",
            "next_work_unit": {
                "unit_id": "publication_gate_replay",
                "lane": "controller",
                "summary": "Replay the publication gate against current authority signatures before dispatching new work.",
                "control_surface": "publication_gate",
            },
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": "quest-nf",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "pending_user_message_ids": [],
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "needs_specificity",
            "same_fingerprint_auto_turn_count": 7,
            "last_stage_fingerprint": "old-fingerprint",
            "retry_state": {"terminal": True, "gate_needs_specificity": True},
            "last_controller_decision_authorization": {
                "decision_id": "old-specificity",
                "route_target": "controller",
                "work_unit_id": "gate_needs_specificity",
                "work_unit_fingerprint": "publication-blockers::old",
                "controller_work_unit_lifecycle": {
                    "lifecycle_state": "needs_specificity",
                    "latest_event_type": "needs_specificity",
                    "delivery_blocked": True,
                    "block_reason": "needs_specificity",
                    "terminal_consumed": True,
                },
            },
        },
    )
    ensure_calls: list[dict[str, object]] = []

    def fake_ensure_study_runtime(**kwargs: object) -> dict[str, object]:
        ensure_calls.append(dict(kwargs))
        return {
            "study_id": "003-endocrine-burden-followup",
            "quest_id": "quest-nf",
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "reason": "runtime_recovery_retry_budget_exhausted",
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
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "paper_stage": "write",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    study = result["studies"][0]
    assert len(ensure_calls) == 1
    assert "last_controller_decision_authorization" not in runtime_state
    assert runtime_state["continuation_reason"] == "runtime_platform_repair_redrive"
    assert study["runtime_platform_repair_apply"]["dispatch_status"] == "applied"
    assert study["runtime_platform_repair_apply"]["gate_status"]["ready"] is True
    assert study["runtime_platform_repair_apply"]["gate_status"]["blockers"] == ["stale_study_delivery_mirror"]
    assert study["runtime_platform_repair_apply"]["stale_specificity_cleared"] is True
    assert study["paper_package_mutated"] is False


def test_supervisor_scan_queues_specificity_and_ai_reviewer_actions_without_quality_authority(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "publication_gate_specificity_required",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "none",
                "attempt_state": "idle",
                "retry_budget_remaining": 0,
            },
            "execution_owner_guard": {"supervisor_only": True},
            "publication_eval": {
                "current_required_action": "generic_blocker_repair",
                "assessment_provenance": {"owner": "mechanical_gate"},
                "blockers": ["generic blocker"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "current_blockers": ["generic blocker"],
            "quality_review_loop": {"closure_state": "open"},
            "control_plane_snapshot": {"blocking_reasons": ["publication_eval.ai_reviewer_required"]},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    action_types = [item["action_type"] for item in result["studies"][0]["action_queue"]]
    assert action_types == ["publication_gate_specificity_required", "return_to_ai_reviewer_workflow"]
    assert {item["authority"] for item in result["studies"][0]["action_queue"]} == {"observability_only"}
    assert [item["owner"] for item in result["studies"][0]["action_queue"]] == ["publication_gate", "ai_reviewer"]
    assert [item["recommended_owner"] for item in result["studies"][0]["action_queue"]] == [
        "publication_gate",
        "ai_reviewer",
    ]
    assert [item["owner_pickup"]["owner"] for item in result["studies"][0]["action_queue"]] == [
        "publication_gate",
        "ai_reviewer",
    ]
    assert result["studies"][0]["current_stage"] == "publication_supervision"
    assert result["studies"][0]["gate_specificity"]["required"] is True
    assert result["studies"][0]["gate_specificity"]["missing_target_kinds"] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert result["studies"][0]["gate_specificity"]["gate_owner"] == "publication_gate"
    assert result["studies"][0]["gate_specificity"]["next_controller_write"] == {
        "surface": "publication_eval/latest.json",
        "writer": "publication_gate_controller",
        "materialization_mode": "controller_request_only",
        "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
    }
    assert result["studies"][0]["ai_reviewer_assessment"] == {
        "present": False,
        "owner": "mechanical_gate",
        "required": True,
        "missing": True,
    }
    assert result["studies"][0]["why_not_applied"] == "publication_gate_specificity_required"
    assert result["studies"][0]["blocked_reason"] == "publication_gate_specificity_required"
    assert result["studies"][0]["next_owner"] == "publication_gate"
    assert result["studies"][0]["supervisor_only"] is True
    assert result["studies"][0]["paper_package_mutated"] is False
    for action in result["studies"][0]["action_queue"]:
        assert action["authority"] == "observability_only"
        assert action["quality_gate_relaxation_allowed"] is False
        assert action["paper_package_mutation_allowed"] is False
        assert action["manual_study_patch_allowed"] is False
        assert action["medical_claim_authoring_allowed"] is False
        assert action["handoff_packet"]["authority"] == "observability_only"
        assert action["handoff_packet"]["request_owner"] == action["owner"]
        assert action["handoff_packet"]["recommended_owner"] == action["owner"]
        assert action["handoff_packet"]["next_executable_owner"] == action["owner"]
        assert action["handoff_packet"]["supervisor_authority_boundary"] == "request_only"
        assert action["handoff_packet"]["quality_gate_relaxation_allowed"] is False
        assert action["handoff_packet"]["paper_package_mutation_allowed"] is False
        assert action["handoff_packet"]["manual_study_patch_allowed"] is False
        assert action["handoff_packet"]["medical_claim_authoring_allowed"] is False
        assert action["handoff_packet"]["allowed_write_surfaces"] == ["artifacts/supervision/**"]


def test_supervisor_scan_apply_safe_actions_materializes_stopped_dm002_lifecycle_and_request_packets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    repair_actions = study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"
    _write_json(
        repair_actions,
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-dm",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "bounded_work_unit_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_status": "stopped",
            "reason": "publication_gate_specificity_required",
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::specificity",
                        "action_type": "return_to_controller",
                        "next_work_unit": {"unit_id": "gate_needs_specificity", "summary": "Name concrete targets."},
                        "work_unit_fingerprint": "publication-blockers::same",
                        "reason": "Publication gate needs specificity.",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_blocked",
            "quality_review_loop": {"closure_state": "review_required"},
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    specificity_request_path = study_root / "artifacts" / "supervision" / "requests" / "publication_gate_specificity" / "latest.json"
    ai_reviewer_request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    specificity_request = json.loads(specificity_request_path.read_text(encoding="utf-8"))
    ai_reviewer_request = json.loads(ai_reviewer_request_path.read_text(encoding="utf-8"))

    assert result["studies"][0]["ai_repair_lifecycle"]["blocked_reason"] == "publication_gate_specificity_required"
    assert result["studies"][0]["next_owner"] == "publication_gate"
    assert lifecycle["state"] == "blocked"
    assert lifecycle["blocked_reason"] == "publication_gate_specificity_required"
    assert lifecycle["next_owner"] == "publication_gate"
    assert specificity_request["authority"] == "observability_only"
    assert specificity_request["required_target_kinds"] == ["claim", "figure", "table", "metric", "source_path"]
    assert specificity_request["missing_target_kinds"] == ["claim", "figure", "table", "metric", "source_path"]
    assert specificity_request["gate_owner"] == "publication_gate"
    assert specificity_request["request_visibility"] == "owner_visible_checklist"
    assert [item["target_kind"] for item in specificity_request["owner_visible_checklist"]] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert specificity_request["next_controller_write"]["surface"] == "publication_eval/latest.json"
    assert specificity_request["next_controller_write"]["writer"] == "publication_gate_controller"
    assert specificity_request["next_controller_write"]["must_include_target_kinds"] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert ai_reviewer_request["authority"] == "observability_only"
    assert ai_reviewer_request["target_assessment_owner"] == "ai_reviewer"
    assert ai_reviewer_request["may_authorize_quality_gate"] is False


def test_supervisor_scan_downgrades_developer_mode_when_github_user_is_not_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "someone-else")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-dpcc-primary-care-phenotype-treatment-gap", quest_id="quest-dpcc")
    repair_actions = study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"
    _write_json(
        repair_actions,
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "quest-dpcc",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "runtime_recovery_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_root": str(study_root),
            "quest_id": "quest-dpcc",
            "quest_status": "running",
            "reason": "runtime_recovery_retry_budget_exhausted",
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
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_stage": "publication_supervision",
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("003-dpcc-primary-care-phenotype-treatment-gap",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert result["developer_supervisor_mode"]["mode"] == "external_observe"
    assert result["developer_supervisor_mode"]["developer_mode_enabled"] is False
    assert result["developer_supervisor_mode"]["safe_actions_enabled"] is False
    assert result["developer_supervisor_mode"]["github_user_gate"] == {
        "expected_login": "gaofeng21cn",
        "login": "someone-else",
        "allowed": False,
        "source": "env",
        "reason": "github_user_not_authorized_for_developer_supervisor_mode",
    }
    assert study["action_queue"] == []
    assert study["why_not_applied"] == "runtime_recovery_retry_budget_exhausted"
    assert not (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").exists()


def test_supervisor_scan_apply_safe_actions_sanitizes_unsafe_repair_authority(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-risk")
    repair_actions = study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"
    _write_json(
        repair_actions,
        {
            "surface": "autonomy_repair_orchestration",
            "schema_version": 1,
            "state": "ready_for_repair",
            "study_id": "002-risk",
            "quest_id": "quest-risk",
            "actions": [
                {
                    "action_type": "controller_repair",
                    "repair_kind": "bounded_work_unit_redrive",
                    "owner": "mas_controller",
                    "risk": "medium",
                    "auto_apply_allowed": True,
                    "paper_package_mutation_allowed": True,
                    "manual_study_patch_allowed": True,
                    "quality_gate_relaxation_allowed": True,
                    "medical_claim_authoring_allowed": True,
                    "requested_write_surfaces": [
                        "paper/submission_minimal/**",
                        "artifacts/supervision/requests/ai_reviewer/latest.json",
                    ],
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "002-risk",
            "study_root": str(study_root),
            "quest_id": "quest-risk",
            "quest_status": "stopped",
            "reason": "publication_gate_specificity_required",
            "execution_owner_guard": {"supervisor_only": True},
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::specificity",
                        "next_work_unit": {"unit_id": "gate_needs_specificity"},
                        "work_unit_fingerprint": "publication-blockers::specificity",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "002-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "control_plane_snapshot": {"blocking_reasons": ["publication_eval.ai_reviewer_required"]},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("002-risk",),
        apply_safe_actions=True,
    )

    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    top_action = lifecycle["top_action"]
    assert result["studies"][0]["supervisor_only"] is True
    assert lifecycle["authority"] == "observability_only"
    assert lifecycle["allowed_write_surfaces"] == [
        "artifacts/supervision/**",
        "artifacts/autonomy/repair_lifecycle/latest.json",
        "artifacts/autonomy/repair_actions/latest.json",
    ]
    assert lifecycle["forbidden_actions"] == [
        "paper_package_mutation",
        "manual_study_patch",
        "quality_gate_relaxation",
        "medical_claim_authoring",
    ]
    assert top_action["paper_package_mutation_allowed"] is False
    assert top_action["manual_study_patch_allowed"] is False
    assert top_action["quality_gate_relaxation_allowed"] is False
    assert top_action["medical_claim_authoring_allowed"] is False
    assert top_action["requested_write_surfaces"] == ["artifacts/supervision/**"]
