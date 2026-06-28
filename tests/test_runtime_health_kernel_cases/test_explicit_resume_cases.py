from __future__ import annotations

from pathlib import Path

from tests.test_runtime_health_kernel import (
    _kernel,
    _write_runtime_health_fixture_event,
)


def test_runtime_health_stopped_quest_waits_for_explicit_resume_without_probe(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dm-cvd"
    _write_runtime_health_fixture_event(module,
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
    _write_runtime_health_fixture_event(module,
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
    _write_runtime_health_fixture_event(module,
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
    _write_runtime_health_fixture_event(module,
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
