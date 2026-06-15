from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_blocks_outer_loop_dispatch_for_user_paused_study(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    publication_eval_ref = _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    charter_ref = _write_charter(study_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_user_paused_requires_explicit_wakeup",
            include_authority_snapshot=True,
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "active_run_id": None,
        "runtime_liveness_status": "none",
        "continuation_state": {
            "quest_id": "quest-001",
            "quest_status": "paused",
            "active_run_id": None,
            "stop_reason": "user_pause",
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "user_pause",
            "continuation_reason": "user_pause",
        },
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "explicit_resume_pending",
            "awaiting_explicit_wakeup": True,
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "blocking_reasons": ["quest_user_paused_requires_explicit_wakeup"],
        },
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "What bounded gate-clearing batch is required?",
        "route_rationale": "Run deterministic gate-clearing batch first.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run deterministic gate-clearing batch first.",
    }
    calls: list[str] = []

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(
        module.domain_status_projection,
        "study_outer_loop_tick",
        lambda **kwargs: calls.append(str(kwargs.get("source") or "")) or {"dispatch_status": "executed"},
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "explicit_wakeup_required"
    assert latest["outcome"] == "explicit_wakeup_required"
    assert latest["reason"] == "user pause or manual hold requires explicit wakeup before autonomous dispatch"


def test_watch_runtime_blocks_outer_loop_dispatch_for_manual_hold(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    publication_eval_ref = _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    charter_ref = _write_charter(study_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_waiting_for_explicit_wakeup_after_manual_hold",
            include_authority_snapshot=True,
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "active_run_id": None,
        "runtime_liveness_status": "none",
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "manual_hold",
            "awaiting_explicit_wakeup": True,
        },
        "publication_supervisor_state": {
            "supervisor_phase": "manual_hold",
            "phase_owner": "user",
            "current_required_action": "explicit_wakeup_required",
        },
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "What bounded gate-clearing batch is required?",
        "route_rationale": "Run deterministic gate-clearing batch first.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run deterministic gate-clearing batch first.",
    }
    calls: list[str] = []

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(
        module.domain_status_projection,
        "study_outer_loop_tick",
        lambda **kwargs: calls.append(str(kwargs.get("source") or "")) or {"dispatch_status": "executed"},
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "explicit_wakeup_required"


def test_fresh_current_owner_action_clears_explicit_wakeup_residue(
    tmp_path: Path,
    monkeypatch,
) -> None:
    support = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan_support"
    )
    wakeup = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = helpers.write_study(profile.workspace_root, study_id)
    stale_status = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="blocked",
            reason="quest_waiting_for_explicit_wakeup_after_manual_hold",
            include_authority_snapshot=True,
        ),
        "study_root": str(study_root),
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "explicit_resume_pending",
            "awaiting_explicit_wakeup": True,
        },
        "awaiting_explicit_wakeup": True,
        "parked_state": "explicit_resume_pending",
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
        },
    }
    fresh_progress = {
        "study_id": study_id,
        "quest_id": study_id,
        "study_root": str(study_root),
        "decision": "blocked",
        "reason": "blocked_turn_closeout_waiting_for_owner",
        "auto_runtime_parked": {
            "parked": False,
            "parked_state": None,
            "awaiting_explicit_wakeup": False,
            "superseded_by_current_owner_action": True,
        },
        "awaiting_explicit_wakeup": False,
        "parked_state": None,
        "current_executable_owner_action": {
            "status": "ready",
            "source": "domain_transition",
            "next_owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            "work_unit_fingerprint": (
                "domain-transition::ai_reviewer_re_eval::"
                "ai_reviewer_medical_prose_quality_review"
            ),
        },
        "current_work_unit": {
            "status": "executable_owner_action",
            "owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "ai_reviewer",
            "next_work_unit": "ai_reviewer_medical_prose_quality_review",
        },
    }

    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: fresh_progress,
    )

    refreshed = support._with_fresh_progress_currentness(
        profile=profile,
        study_root=study_root,
        status_payload=stale_status,
    )

    assert refreshed["reason"] == "blocked_turn_closeout_waiting_for_owner"
    assert refreshed["awaiting_explicit_wakeup"] is False
    assert refreshed["auto_runtime_parked"]["superseded_by_current_owner_action"] is True
    assert wakeup._outer_loop_dispatch_blocked_by_explicit_wakeup_contract(refreshed) is None
