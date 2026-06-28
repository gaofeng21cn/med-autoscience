from __future__ import annotations

from pathlib import Path

from tests.test_runtime_health_kernel import (
    _kernel,
    _opl_lifecycle_payload,
    _write_runtime_health_fixture_event,
)


def test_runtime_health_live_new_run_does_not_inherit_stale_recovery_budget(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    for sequence in range(1, 4):
        _write_runtime_health_fixture_event(module,
            study_root=study_root,
            study_id="001-dm-cvd",
            quest_id="001-dm-cvd",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "failed",
                    "failure_reason": "quest_marked_running_but_no_live_session",
                    "active_run_id": "run-old",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    _write_runtime_health_fixture_event(module,
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-new",
            "autonomy_slo": {
                "state": "breach",
                "breach_types": ["same_fingerprint_loop"],
            },
        },
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
    )

    assert snapshot["active_run_id"] == "run-new"
    assert snapshot["last_known_run_id"] == "run-new"
    assert snapshot["worker_liveness_state"]["state"] == "activity_timeout"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert snapshot["retry_budget_remaining"] == 3
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_does_not_recover_new_live_run_from_stale_slo_window(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    status_payload = {
        "study_id": "001-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "001-dm-cvd",
        "quest_status": "running",
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-new",
            "runtime_audit": {
                "status": "live",
                "worker_running": True,
                "active_run_id": "run-new",
            },
        },
        "autonomy_slo": {
            "generated_at": "2026-05-01T00:00:00+00:00",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
        },
        "progress_freshness": {
            "activity_timeout": {
                "state": "watching_new_run",
                "new_run_grace": {
                    "active_run_id": "run-new",
                    "observed_at": "2026-05-01T00:05:00+00:00",
                },
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "latest_recorded_at": "2026-05-01T00:05:00+00:00",
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "live"
    assert snapshot["attempt_state"] == "live"
    assert snapshot["canonical_runtime_action"] == "continue_supervising_runtime"
    assert "same_fingerprint_loop" not in snapshot["blocking_reasons"]


def test_runtime_health_uses_status_observation_time_for_new_run_grace(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    status_payload = {
        "study_id": "001-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "001-dm-cvd",
        "quest_status": "running",
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-new",
            "runtime_audit": {
                "status": "live",
                "worker_running": True,
                "active_run_id": "run-new",
            },
        },
        "autonomy_slo": {
            "generated_at": "2026-05-01T00:00:00+00:00",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "latest_recorded_at": "2026-05-01T00:05:00+00:00",
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "live"
    assert snapshot["attempt_state"] == "live"
    assert snapshot["canonical_runtime_action"] == "continue_supervising_runtime"
    assert "same_fingerprint_loop" not in snapshot["blocking_reasons"]
