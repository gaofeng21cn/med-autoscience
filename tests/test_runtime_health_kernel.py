from __future__ import annotations

import importlib
import json
from pathlib import Path


def _kernel():
    return importlib.import_module("med_autoscience.controllers.runtime_health_kernel")


def test_runtime_health_strict_live_requires_worker_and_active_run_id(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": None,
            "reason": "live_runtime_missing_active_run_id",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="supervisor_tick",
        payload={"supervisor_tick_status": "fresh"},
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "unknown"
    assert snapshot["canonical_runtime_action"] == "probe_runtime_liveness"
    assert snapshot["active_run_id"] is None
    assert "live_worker_requires_active_run_id" in snapshot["blocking_reasons"]


def test_runtime_health_missing_live_session_recovers_with_stale_run_as_last_known(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        event_type="launch_attempt",
        payload={"attempt_state": "succeeded", "active_run_id": "run-599e53e9"},
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
        recorded_at="2026-05-01T00:03:00+00:00",
    )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        event_type="supervisor_tick",
        payload={"supervisor_tick_status": "fresh"},
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "missing_live_session"
    assert snapshot["active_run_id"] is None
    assert snapshot["last_known_run_id"] == "run-599e53e9"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert snapshot["retry_budget_remaining"] == 2


def test_runtime_health_recovery_budget_exhaustion_escalates(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "reason": "quest_marked_running_but_no_live_session",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="002-dm-cvd",
            quest_id="002-dm-cvd",
            event_type="recover_attempt",
            payload={"attempt_state": "failed", "failure_reason": "no_live_session"},
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
    )

    assert snapshot["attempt_state"] == "escalated"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert snapshot["retry_budget_remaining"] == 0
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]


def test_runtime_health_submission_metadata_parking_dominates_stale_recovery_budget(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="001-dm-cvd",
            quest_id="001-dm-cvd-reentry",
            event_type="recover_attempt",
            payload={
                "attempt_state": "failed",
                "failure_reason": "quest_marked_running_but_no_live_session",
            },
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd-reentry",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "paused",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "runtime_liveness_status": "unknown",
            "worker_running": False,
        },
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd-reentry",
    )

    assert snapshot["worker_liveness_state"]["state"] == "not_live"
    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_zero_retry_budget_blocks_recover_runtime_even_without_failed_attempts(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dpcc"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="003-dpcc",
            quest_id="003-dpcc",
            event_type="recover_attempt",
            payload={"attempt_state": "requested", "decision": "resume", "reason": "quest_marked_running_but_no_live_session"},
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dpcc",
        quest_id="003-dpcc",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="003-dpcc",
        quest_id="003-dpcc",
    )

    assert snapshot["retry_budget_remaining"] == 0
    assert snapshot["attempt_state"] == "escalated"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]


def test_runtime_health_zero_retry_budget_escalates_stopped_controller_guard_recovery_path(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="001-dm-cvd",
            quest_id="001-dm-cvd",
            event_type="recover_attempt",
            payload={"attempt_state": "requested", "decision": "resume", "reason": "quest_stopped_by_controller_guard"},
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "stopped",
            "runtime_liveness_status": "unknown",
            "worker_running": False,
            "decision": "resume",
            "reason": "quest_stopped_by_controller_guard",
        },
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "not_live"
    assert snapshot["retry_budget_remaining"] == 0
    assert snapshot["attempt_state"] == "escalated"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]
    assert "recover_runtime" not in snapshot["allowed_controller_actions"]


def test_runtime_health_append_deduplicates_same_source_signature(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    first = module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="recover_attempt",
        payload={"attempt_state": "failed", "failure_reason": "same_recovery_attempt"},
        recorded_at="2026-05-01T00:00:00+00:00",
        source_signature="recover-attempt::same",
    )
    second = module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="recover_attempt",
        payload={"attempt_state": "failed", "failure_reason": "same_recovery_attempt"},
        recorded_at="2026-05-01T00:05:00+00:00",
        source_signature="recover-attempt::same",
    )

    events = module.read_runtime_health_events(study_root=study_root)

    assert len(events) == 1
    assert second["event_id"] == first["event_id"]
    assert second["duplicate_replay"] is True


def test_runtime_health_stopped_quest_waits_for_explicit_resume_without_probe(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_liveness_status": "unknown",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "not_live"
    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_liveness_unknown" not in snapshot["blocking_reasons"]


def test_runtime_health_manual_hold_dominates_active_missing_live_session(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
        },
        recorded_at="2026-05-05T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
    )

    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_user_pause_dominates_active_missing_live_session(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_user_paused_requires_explicit_wakeup",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
        },
        recorded_at="2026-05-05T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
    )

    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_explicit_resume_reason_dominates_active_missing_live_session(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_liveness_status": "unknown",
            "worker_running": True,
            "active_run_id": None,
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
    )

    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"


def test_runtime_health_reconcile_materializes_snapshot_from_status_payload(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    status_payload = {
        "study_id": "002-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "002-dm-cvd",
        "quest_status": "running",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "supervisor_tick_audit": {"status": "fresh"},
        "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
    }

    shadow = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    assert shadow["canonical_runtime_action"] == "recover_runtime"
    assert not module.runtime_health_snapshot_path(study_root=study_root).exists()

    result = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot_path = module.runtime_health_snapshot_path(study_root=study_root)
    assert snapshot_path.exists()
    persisted = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert result["runtime_health_epoch"] == persisted["runtime_health_epoch"]
    assert persisted["canonical_runtime_action"] == "recover_runtime"


def test_runtime_health_treats_strict_live_activity_timeout_as_recovery(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    status_payload = {
        "study_id": "002-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "002-dm-cvd",
        "quest_status": "running",
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live-stale",
            "runtime_audit": {
                "status": "live",
                "worker_running": True,
                "active_run_id": "run-live-stale",
            },
        },
        "autonomy_slo": {
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta", "same_fingerprint_loop"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "meaningful_artifact_delta_kind": "paper_bundle",
            },
            "last_meaningful_progress": {
                "seconds_since_last_meaningful_progress": 59841,
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "latest_recorded_at": "2026-05-02T11:07:28+00:00",
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-02T11:07:29+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "activity_timeout"
    assert snapshot["worker_liveness_state"]["active_run_id"] == "run-live-stale"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert "live_worker_meaningful_artifact_delta_timeout" in snapshot["blocking_reasons"]
    assert "read_churn_without_artifact_delta" in snapshot["blocking_reasons"]


def test_runtime_health_live_new_run_does_not_inherit_stale_recovery_budget(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="001-dm-cvd",
            quest_id="001-dm-cvd",
            event_type="recover_attempt",
            payload={
                "attempt_state": "failed",
                "failure_reason": "quest_marked_running_but_no_live_session",
                "active_run_id": "run-old",
            },
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
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


def test_runtime_health_reconcile_ignores_volatile_watchdog_seconds_for_deduplication(tmp_path: Path) -> None:
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

    assert first["appended_event_count"] == 3
    assert second["appended_event_count"] == 0
    assert second["snapshot"]["attempt_count"] == 1
