from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_hard_auto_recovery_ignores_stale_continuation_run_id() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup")

    assert module._should_hard_auto_recover_managed_study(
        {
            **make_progress_projection_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_marked_running_but_no_live_session",
            ),
            "quest_status": "running",
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-stale",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:previous",
            },
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
        }
    )


def test_flapping_recovery_probe_clears_hold_when_current_status_is_live(
    tmp_path: Path,
) -> None:
    policy = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_recovery_policy")
    study_root = tmp_path / "studies" / "001-risk"
    dump_json(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        {
            "surface_kind": "mas_opl_runtime_owner_handoff",
            "schema_version": 1,
            "recorded_at": "2026-04-26T00:01:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "status": "handoff_required",
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_runtime_read_model_retired": True,
            "mas_materializes_runtime_supervision": False,
            "health_status": "recovering",
            "runtime_stability_status": "flapping",
            "flapping_episode_count": 2,
            "flapping_circuit_breaker": True,
            "typed_blocker": {
                "blocker_type": "opl_runtime_owner_handoff_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
            },
        },
    )

    hold = policy.hold_for_flapping_circuit_breaker(
        study_root=study_root,
        status_payload={
            **make_progress_projection_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_marked_running_but_no_live_session",
            ),
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-recovered",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-recovered",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    )

    assert hold is not None
    assert hold["recovery_probe"] == {
        "probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::2",
        "status": "clear_hold",
        "recommended_action": "ready_to_resume",
        "reason": "runtime_liveness_confirmed_live",
        "next_probe_id": None,
        "liveness": {
            "status": "live",
            "active_run_id": "run-recovered",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
        },
        "current_status": {
            "quest_status": "running",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_stability_status": "live",
            "flapping_circuit_breaker": False,
            "flapping_episode_count": 2,
        },
    }
