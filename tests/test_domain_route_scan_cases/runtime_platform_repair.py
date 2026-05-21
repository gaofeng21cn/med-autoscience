from __future__ import annotations

from .shared import *

def test_scan_domain_routes_queues_external_repair_for_retry_exhausted_no_live_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
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
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
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
    assert result["queue_history"]["latest_action_count"] == 1
    assert result["two_layer_ai_repair_policy"]["internal_ai_repair"]["monitor_interval_seconds"] == 300
    assert result["two_layer_ai_repair_policy"]["developer_supervisor"]["heartbeat_interval_seconds"] == 3600
    assert result["two_layer_ai_repair_policy"]["developer_supervisor"]["developer_attention_after_hours"] == 6
    assert result["developer_supervisor_mode"]["mode"] == "developer_apply_safe"
    assert result["developer_supervisor_mode"]["developer_mode_enabled"] is True
    assert result["developer_supervisor_mode"]["safe_actions_enabled"] is True
    assert result["developer_supervisor_mode"]["github_user_gate"]["login"] == "gaofeng21cn"
    assert Path(result["refs"]["latest_path"]).is_file()
    assert Path(result["refs"]["history_path"]).is_file()


def test_scan_domain_routes_does_not_apply_runtime_platform_repair_without_explicit_flag(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
    )

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert runtime_state == original_runtime_state
    assert result["studies"][0]["runtime_platform_repair_apply"] is None
    assert result["studies"][0]["action_queue"][0]["action_type"] == "runtime_platform_repair"


def test_scan_domain_routes_explicit_runtime_platform_repair_clears_stale_specificity_and_resumes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    _assert_owner_route_required(
        apply_result=apply_result,
        runtime_state=runtime_state,
        ensure_calls=ensure_calls,
        expected_reason="stale_specificity_terminal_gate_cleared",
    )
    assert "last_controller_decision_authorization" not in runtime_state
    assert "retry_state" not in runtime_state
    assert "last_stage_fingerprint" not in runtime_state
    assert runtime_state["same_fingerprint_auto_turn_count"] == 0
    assert apply_result["stale_specificity_cleared"] is True
    assert study["ai_repair_lifecycle"]["state"] == "owner_route_required"
    assert study["ai_repair_lifecycle"]["dispatch_status"] == "owner_route_required"
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_runtime_platform_repair_allows_concrete_bundle_stage_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
    )

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    study = result["studies"][0]
    apply_result = study["runtime_platform_repair_apply"]
    _assert_owner_route_required(
        apply_result=apply_result,
        runtime_state=runtime_state,
        ensure_calls=ensure_calls,
        expected_reason="stale_specificity_terminal_gate_cleared",
    )
    assert "last_controller_decision_authorization" not in runtime_state
    assert apply_result["gate_status"]["ready"] is True
    assert apply_result["gate_status"]["blockers"] == ["stale_study_delivery_mirror"]
    assert apply_result["stale_specificity_cleared"] is True
    assert study["paper_package_mutated"] is False

def test_scan_domain_routes_suppresses_stale_runtime_recovery_lifecycle_when_worker_is_live(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm", quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    _write_json(
        lifecycle_path,
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": "002-dm",
            "quest_id": "quest-dm002",
            "state": "external_supervisor_required",
            "blocked_reason": "runtime_recovery_not_authorized",
            "external_supervisor_required": True,
            "top_action": {
                "action_type": "controller_repair",
                "repair_kind": "bounded_work_unit_redrive",
                "auto_apply_allowed": True,
            },
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_id": "quest-dm002",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-live-dm002",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-dm002",
                "worker_running": True,
                "runtime_audit": {"worker_running": True, "active_run_id": "run-live-dm002"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
                "worker_liveness_state": {
                    "state": "live",
                    "runtime_liveness_status": "live",
                    "worker_running": True,
                    "active_run_id": "run-live-dm002",
                },
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "002-dm",
            "paper_stage": "analysis-campaign",
            "supervision": {"active_run_id": "run-live-dm002", "health_status": "live"},
            "ai_repair_lifecycle": json.loads(lifecycle_path.read_text(encoding="utf-8")),
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("002-dm",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["active_run_id"] == "run-live-dm002"
    assert study["runtime_health"]["worker_liveness_state"]["worker_running"] is True
    assert study["action_queue"] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["external_supervisor_required"] is False
    assert study["next_owner"] is None
    assert study["owner_route"]["current_owner"] == "managed_runtime"
    assert study["owner_route"]["next_owner"] is None
    assert study["owner_route"]["owner_reason"] is None
    assert study["ai_repair_lifecycle"] is None
    assert not lifecycle_path.exists()
