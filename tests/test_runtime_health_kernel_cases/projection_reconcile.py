from __future__ import annotations

from pathlib import Path

from tests.test_runtime_health_kernel import (
    _assert_attempt_ledger_authority_boundary,
    _assert_observability_readback_boundary,
    _kernel,
)


def test_runtime_health_reconcile_publishes_projection_without_persisting_liveness_events(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dm-cvd"
    status_payload = {
        "study_id": "003-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "003-dm-cvd",
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "runtime_audit": {
                "status": "none",
                "worker_running": False,
                "interaction_watchdog": {
                    "seconds_since_last_artifact_interact": 10,
                    "seconds_since_active_execution_start": 20,
                },
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "seconds_since_latest_recorded_at": 1,
        },
    }

    first = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    status_payload["runtime_liveness_audit"]["runtime_audit"]["interaction_watchdog"][
        "seconds_since_last_artifact_interact"
    ] = 100
    status_payload["supervisor_tick_audit"]["seconds_since_latest_recorded_at"] = 90
    second = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert first["appended_event_count"] == 0
    assert first["suppressed_local_runtime_event_persistence"] is True
    assert first["suppressed_transient_event_count"] == 2
    assert module.read_runtime_health_events(study_root=study_root) == []
    assert second["appended_event_count"] == 0
    assert second["suppressed_local_runtime_event_persistence"] is True
    assert second["snapshot"]["attempt_count"] == 0


def test_runtime_health_reconcile_suppresses_opl_proof_backed_lifecycle_event_persistence(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dm-cvd"
    status_payload = {
        "study_id": "003-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "003-dm-cvd",
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "opl_lifecycle_proof_ref": "opl-stage-attempt://runtime-health-dedupe",
        "runtime_liveness_audit": {
            "status": "none",
            "runtime_audit": {
                "status": "none",
                "worker_running": False,
                "interaction_watchdog": {
                    "seconds_since_last_artifact_interact": 10,
                    "seconds_since_active_execution_start": 20,
                },
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "seconds_since_latest_recorded_at": 1,
        },
    }

    first = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    status_payload["runtime_liveness_audit"]["runtime_audit"]["interaction_watchdog"][
        "seconds_since_last_artifact_interact"
    ] = 100
    status_payload["supervisor_tick_audit"]["seconds_since_latest_recorded_at"] = 90
    second = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert first["appended_event_count"] == 0
    assert first["suppressed_local_runtime_event_persistence"] is True
    assert first["suppressed_transient_event_count"] == 3
    assert "recover_attempt" in first["suppressed_transient_event_types"]
    assert first["suppressed_lifecycle_event_types"] == ["recover_attempt"]
    assert first["suppressed_lifecycle_event_boundaries"][0]["event_type"] == "recover_attempt"
    assert first["suppressed_lifecycle_event_boundaries"][0]["mas_runtime_health_event_role"] == (
        "diagnostic_observation"
    )
    assert first["suppressed_lifecycle_event_boundaries"][0]["diagnostic_only"] is True
    assert first["suppressed_lifecycle_event_boundaries"][0]["attempt_lifecycle_authority"] is False
    assert first["suppressed_lifecycle_event_boundaries"][0]["retry_or_dead_letter_authority"] is False
    assert first["suppressed_lifecycle_event_boundaries"][0]["worker_residency_authority"] is False
    assert first["suppressed_lifecycle_event_boundaries"][0]["attempt_ledger_authority"] is False
    assert first["suppressed_lifecycle_event_boundaries"][0]["provider_admission_authority"] is False
    assert first["suppressed_lifecycle_event_boundaries"][0]["readiness_authority"] is False
    assert first["suppressed_lifecycle_event_boundaries"][0]["runtime_currentness_authority"] is False
    _assert_observability_readback_boundary(
        first["suppressed_lifecycle_event_boundaries"][0]["opl_observability_readback_boundary"]
    )
    _assert_attempt_ledger_authority_boundary(
        first["suppressed_lifecycle_event_boundaries"][0]["attempt_ledger_authority_boundary"]
    )
    assert first["suppressed_lifecycle_events_are_attempt_ledger"] is False
    assert first["attempt_count_includes_suppressed_lifecycle_observations"] is True
    assert first["attempt_count_is_lifecycle_authority"] is False
    assert first["retry_budget_remaining_is_lifecycle_authority"] is False
    _assert_attempt_ledger_authority_boundary(first["attempt_ledger_authority_boundary"])
    _assert_observability_readback_boundary(first["opl_observability_readback_boundary"])
    _assert_observability_readback_boundary(first["snapshot"]["opl_observability_readback_boundary"])
    _assert_attempt_ledger_authority_boundary(first["snapshot"]["attempt_ledger_authority_boundary"])
    assert module.read_runtime_health_events(study_root=study_root) == []
    assert second["appended_event_count"] == 0
    assert second["suppressed_local_runtime_event_persistence"] is True
    assert second["snapshot"]["attempt_count"] == 1
    assert second["snapshot"]["attempt_count_hint"] == 1
    assert second["snapshot"]["attempt_count_is_lifecycle_authority"] is False
    assert second["snapshot"]["attempt_ledger_authority"] is False
    assert second["snapshot"]["suppressed_lifecycle_events_are_attempt_ledger"] is False
