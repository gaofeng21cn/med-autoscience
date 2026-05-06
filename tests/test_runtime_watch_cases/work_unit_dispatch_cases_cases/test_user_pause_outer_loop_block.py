from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_blocks_outer_loop_dispatch_for_user_paused_study(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    publication_eval_ref = _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    charter_ref = _write_charter(study_root)
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_user_paused_requires_explicit_wakeup",
            include_control_plane_snapshot=True,
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

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_outer_loop_tick",
        lambda **kwargs: calls.append(str(kwargs.get("source") or "")) or {"dispatch_status": "executed"},
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json").read_text(encoding="utf-8")
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
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    publication_eval_ref = _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    charter_ref = _write_charter(study_root)
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_waiting_for_explicit_wakeup_after_manual_hold",
            include_control_plane_snapshot=True,
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

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_outer_loop_tick",
        lambda **kwargs: calls.append(str(kwargs.get("source") or "")) or {"dispatch_status": "executed"},
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "explicit_wakeup_required"
