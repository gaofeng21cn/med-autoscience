from __future__ import annotations

import json
from pathlib import Path

from tests.test_runtime_health_kernel import (
    _assert_observability_readback_boundary,
    _kernel,
)


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
    assert result["appended_event_count"] == 0
    assert result["suppressed_local_runtime_event_persistence"] is True
    assert persisted["suppressed_local_runtime_event_persistence"] is True
    assert module.read_runtime_health_events(study_root=study_root) == []
    assert persisted["projection_metadata"]["authority"] is False
    assert persisted["projection_metadata"]["lag_status"] == "current"
    assert persisted["projection_metadata"]["derived_from_event_id"] == persisted["runtime_health_epoch"]
    _assert_observability_readback_boundary(result["opl_observability_readback_boundary"])
    _assert_observability_readback_boundary(persisted["opl_observability_readback_boundary"])
    _assert_observability_readback_boundary(
        persisted["projection_metadata"]["opl_observability_readback_boundary"]
    )


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
