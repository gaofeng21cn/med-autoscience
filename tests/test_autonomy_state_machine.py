from __future__ import annotations

import importlib

import pytest


REQUIRED_STATES = {
    "live",
    "queued",
    "running",
    "stalled",
    "no_live",
    "recovering",
    "blocked_human",
    "blocked_external",
    "blocked_opl_runtime",
}

REQUIRED_STATE_FIELDS = {
    "owner",
    "auto_recovery_allowed",
    "resource_release_expected",
    "long_write_turn_allowed",
    "recovery_route",
    "human_gate_required",
    "operator_summary",
}


def test_autonomy_state_machine_catalog_covers_all_controller_states() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_state_machine")

    surface = module.build_autonomy_state_machine_surface({"study_id": "003-dpcc"})

    assert surface["surface"] == "autonomy_state_machine"
    assert surface["gate_relaxation_allowed"] is False
    assert set(surface["states"]) == REQUIRED_STATES
    assert surface["autonomy_state_surface"]["surface"] == "autonomy_state_surface"
    for state_name, state_spec in surface["states"].items():
        assert REQUIRED_STATE_FIELDS <= set(state_spec), state_name
        assert state_spec["state"] == state_name


def test_autonomy_slo_consumes_state_machine_and_platform_incident_loop() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_slo")

    payload = module.build_autonomy_slo_signals(
        {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "opl_domain_activity_ref": {
                "activity_state": "recovering",
                "heartbeat_state": "missing_live_session",
            },
        }
    )

    assert payload["autonomy_state_machine"]["current_state"] == "no_live"
    assert payload["incident_learning_loop"]["incident_count"] == 1
    assert payload["incident_learning_loop"]["incidents"][0]["incident_type"] == "no_live"
    assert payload["incident_loop"]["platform_incident_types"] == ["no_live"]
    state_signal = next(
        signal
        for signal in payload["efficiency_signals"]
        if signal["signal_id"] == "autonomy_state_machine"
    )
    assert state_signal == {
        "signal_id": "autonomy_state_machine",
        "source": "autonomy_state_machine",
        "state": "breach",
        "value": "no_live",
        "target": "live",
    }
    assert payload["incident_learning_loop"]["gate_relaxation_allowed"] is False


def test_autonomy_slo_turns_no_progress_into_advancement_pressure() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_slo")

    payload = module.build_autonomy_slo_signals(
        {
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "sli_summary": {
                "duplicate_dispatch_active": True,
                "next_work_unit_id": "medical_prose_write_repair",
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "actionability_status": "actionable",
                "next_work_unit": {"unit_id": "medical_prose_write_repair"},
            },
            "autonomy_incident_candidates": [
                {
                    "incident_id": "incident-repeat-dispatch",
                    "incident_type": "repeated_controller_decision",
                    "severity": "medium",
                }
            ],
        }
    )

    pressure = payload["progress_pressure"]
    assert pressure["status"] == "advance_now"
    assert pressure["no_progress_is_terminal_failure"] is False
    assert pressure["quality_gate_relaxation_allowed"] is False
    assert pressure["next_step"]["action_type"] == "dedupe_controller_dispatch"
    assert pressure["next_step"]["apply_mode"] == "controller_only"
    assert pressure["next_step"]["purpose"] == "continue_progress"
    assert pressure["continuation_plan"]["state"] == "ready_for_controller_execution"
    assert pressure["continuation_plan"]["must_continue"] is True
    assert pressure["continuation_plan"]["stop_allowed"] is False
    assert payload["slo_execution_plan"]["state"] == "ready_for_controller_execution"
    assert payload["slo_execution_plan"]["purpose"] == "continue_progress"


@pytest.mark.parametrize(
    ("profile_payload", "expected_state"),
    [
        (
            {
                "opl_domain_activity_ref": {
                    "activity_state": "running",
                    "heartbeat_state": "live",
                }
            },
            "live",
        ),
        ({}, "queued"),
        (
            {
                "opl_domain_activity_ref": {
                    "quest_status": "running",
                    "heartbeat_state": "unknown",
                }
            },
            "running",
        ),
        (
            {"mds_failure_diagnosis": {"diagnosis_code": "daemon_stalled_live_turn"}},
            "stalled",
        ),
        (
            {
                "opl_domain_activity_ref": {
                    "activity_state": "recovering",
                    "heartbeat_state": "missing_live_session",
                }
            },
            "no_live",
        ),
        (
            {"current_state_summary": {"runtime_health_status": "recovering"}},
            "recovering",
        ),
        (
            {"mds_failure_diagnosis": {"diagnosis_code": "runtime_intentionally_parked"}},
            "blocked_human",
        ),
        (
            {"mds_failure_diagnosis": {"diagnosis_code": "codex_upstream_quota_error"}},
            "blocked_external",
        ),
        (
            {"mds_failure_diagnosis": {"diagnosis_code": "provider_invalid_params"}},
            "blocked_opl_runtime",
        ),
    ],
)
def test_autonomy_state_machine_resolves_current_state(
    profile_payload: dict[str, object],
    expected_state: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_state_machine")

    surface = module.build_autonomy_state_machine_surface(
        {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            **profile_payload,
        }
    )

    assert surface["current_state"] == expected_state
    assert surface["current_state_spec"]["state"] == expected_state
    assert surface["current_state_spec"]["operator_summary"]
    assert surface["current_state_spec"]["human_gate_required"] in {True, False}
    assert surface["owner"] == surface["autonomy_state_surface"]["owner"]
    assert surface["resource_release_expected"] == surface["autonomy_state_surface"]["resource_release_expected"]
    assert surface["long_write_turn_allowed"] == surface["autonomy_state_surface"]["long_write_turn_allowed"]
    assert surface["quality_constraint"] == {"gate_relaxation_allowed": False}
