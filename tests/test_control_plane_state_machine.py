from __future__ import annotations

import importlib


def _surface(payload: dict[str, object]) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.controllers.control_plane_state")
    return module.build_control_plane_state_surface(payload)


def test_control_plane_state_matrix_exposes_canonical_fields() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_state")

    catalog = module.control_plane_state_catalog()

    assert {
        "live",
        "running",
        "no_live",
        "recovering",
        "blocked_human",
        "blocked_external",
        "blocked_platform",
    } <= set(catalog)
    for state, spec in catalog.items():
        assert spec["state"] == state
        assert isinstance(spec["owner"], str)
        assert isinstance(spec["auto_recovery_allowed"], bool)
        assert isinstance(spec["resource_release_expected"], bool)
        assert isinstance(spec["long_write_turn_allowed"], bool)


def test_control_plane_state_uses_facts_for_strict_live_projection() -> None:
    surface = _surface(
        {
            "study_id": "001-live",
            "quest_id": "quest-001",
            "quest_status": "running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-live-001",
        }
    )

    assert surface["current_state"] == "live"
    assert surface["owner"] == "mas_controller"
    assert surface["long_write_turn_allowed"] is True
    assert surface["control_plane_facts"]["strict_live"] is True
    assert surface["control_plane_facts"]["active_run_id"] == "run-live-001"


def test_control_plane_state_uses_facts_for_no_live_projection() -> None:
    surface = _surface(
        {
            "quest_status": "running",
            "runtime_liveness_status": "none",
            "reason": "quest_marked_running_but_no_live_session",
        }
    )

    assert surface["current_state"] == "no_live"
    assert surface["owner"] == "mas_controller"
    assert surface["auto_recovery_allowed"] is True
    assert surface["resource_release_expected"] is False
    assert surface["control_plane_facts"]["missing_live_session"] is True


def test_control_plane_state_maps_user_parked_to_blocked_human() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "quest_status": "active",
        }
    )

    assert surface["current_state"] == "blocked_human"
    assert surface["owner"] == "human_operator"
    assert surface["auto_recovery_allowed"] is False
    assert surface["resource_release_expected"] is True
    assert surface["auto_runtime_parked"]["parked_state"] == "package_ready_handoff"


def test_control_plane_state_maps_external_upstream_to_external_owner() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "quest_status": "retrying",
            "mds_failure_diagnosis": {
                "diagnosis_code": "codex_upstream_quota_error",
                "retriable": False,
                "problem": "account balance is negative",
            },
        }
    )

    assert surface["current_state"] == "blocked_external"
    assert surface["owner"] == "external_runtime_or_operator"
    assert surface["auto_recovery_allowed"] is False
    assert surface["resource_release_expected"] is True
    assert surface["runtime_failure_classification"]["external_blocker"] is True


def test_control_plane_state_maps_platform_repair_to_platform_owner() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "quest_status": "failed",
            "mds_failure_diagnosis": {
                "diagnosis_code": "provider_invalid_params",
                "retriable": False,
            },
        }
    )

    assert surface["current_state"] == "blocked_platform"
    assert surface["owner"] == "mas_platform_sre"
    assert surface["auto_recovery_allowed"] is False
    assert surface["resource_release_expected"] is True


def test_control_plane_state_does_not_project_gate_blocker_as_user_parked() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "reason": "quest_completion_requested_before_publication_gate_clear",
            "quest_status": "stopped",
            "current_state_summary": {
                "runtime_health_status": "inactive",
                "runtime_decision": "blocked",
                "runtime_reason": "quest_completion_requested_before_publication_gate_clear",
            },
        }
    )

    assert surface["current_state"] == "queued"
    assert surface["owner"] == "mas_controller"
    assert surface["auto_runtime_parked"]["parked"] is False
