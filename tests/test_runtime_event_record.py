from __future__ import annotations

import importlib


def test_runtime_event_record_drops_legacy_worker_cleanup_snapshots() -> None:
    module = importlib.import_module("med_autoscience.runtime_event_record")
    cleanup_payload = {
        "event": "worker_lease_termination",
        "lease_count": 1200,
        "termination_count": 1200,
        "terminations": [{"lease_path": f"/tmp/run-{index}/worker_lease.json"} for index in range(1200)],
    }
    base_snapshot = {
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "blocked_turn_closeout_waiting_for_owner",
        "active_run_id": None,
        "runtime_liveness_status": "idle",
        "worker_running": False,
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
        "supervisor_tick_status": "fresh",
        "controller_owned_finalize_parking": False,
        "runtime_escalation_ref": None,
        "last_orphan_worker_cleanup": cleanup_payload,
        "last_worker_cleanup": cleanup_payload,
    }
    outer_loop_input = {
        **base_snapshot,
        "interaction_action": "none",
        "interaction_requires_user_input": False,
    }

    record = module.RuntimeEventRecord(
        schema_version=1,
        event_id="runtime-event::003-jsonl::quest-003::turn_finished::2026-05-22T10:25:49+00:00",
        study_id="003-jsonl",
        quest_id="quest-003",
        emitted_at="2026-05-22T10:25:49+00:00",
        event_source="mas_runtime_core.worker_wrapper",
        event_kind="turn_finished",
        summary_ref="quest:quest-003:turn_finished",
        status_snapshot=base_snapshot,
        outer_loop_input=outer_loop_input,
    )

    assert "last_orphan_worker_cleanup" not in record.status_snapshot
    assert "last_worker_cleanup" not in record.status_snapshot
    assert "last_orphan_worker_cleanup" not in record.outer_loop_input
    assert "last_worker_cleanup" not in record.outer_loop_input
    assert record.status_snapshot["quest_status"] == "waiting_for_user"
    assert record.outer_loop_input["interaction_requires_user_input"] is False


def test_native_runtime_event_record_drops_legacy_worker_cleanup_snapshots() -> None:
    module = importlib.import_module("med_autoscience.native_runtime_event")
    cleanup_payload = {
        "event": "worker_lease_termination",
        "lease_count": 1200,
        "termination_count": 1200,
        "terminations": [{"lease_path": f"/tmp/run-{index}/worker_lease.json"} for index in range(1200)],
    }
    snapshot = {
        "quest_status": "waiting_for_user",
        "display_status": "running",
        "active_run_id": None,
        "runtime_liveness_status": "idle",
        "worker_running": False,
        "stop_reason": None,
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_anchor": "turn_closeout",
        "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
        "pending_user_message_count": 0,
        "interaction_action": None,
        "interaction_requires_user_input": False,
        "active_interaction_id": "milestone-001",
        "last_transition_at": "2026-05-22T10:25:49+00:00",
        "last_orphan_worker_cleanup": cleanup_payload,
        "last_worker_cleanup": cleanup_payload,
    }

    record = module.NativeRuntimeEventRecord(
        schema_version=1,
        event_id="runtime-event::quest-003::turn_finished::2026-05-22T10:25:49+00:00",
        quest_id="quest-003",
        emitted_at="2026-05-22T10:25:49+00:00",
        event_source="mas_runtime_core.worker_wrapper",
        event_kind="turn_finished",
        summary_ref="quest:quest-003:turn_finished",
        status_snapshot=snapshot,
        outer_loop_input=snapshot,
    )

    assert "last_orphan_worker_cleanup" not in record.status_snapshot
    assert "last_worker_cleanup" not in record.status_snapshot
    assert "last_orphan_worker_cleanup" not in record.outer_loop_input
    assert "last_worker_cleanup" not in record.outer_loop_input
    assert record.status_snapshot["continuation_anchor"] == "turn_closeout"


def test_native_runtime_event_record_requires_continuation_anchor() -> None:
    module = importlib.import_module("med_autoscience.native_runtime_event")
    payload = {
        "schema_version": 1,
        "event_id": "runtime-event::quest-001::running::2026-04-11T00:00:00+00:00",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-11T00:00:00+00:00",
        "event_source": "daemon_app",
        "event_kind": "runtime_control_applied",
        "summary_ref": "quest:quest-001:running",
        "status_snapshot": {
            "quest_status": "running",
            "display_status": "running",
            "active_run_id": "run-001",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "stop_reason": None,
            "continuation_policy": "auto",
            "continuation_reason": "decision:decision-001",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "outer_loop_input": {
            "quest_status": "running",
            "display_status": "running",
            "active_run_id": "run-001",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "stop_reason": None,
            "continuation_policy": "auto",
            "continuation_reason": "decision:decision-001",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
    }

    try:
        module.NativeRuntimeEventRecord.from_payload(payload)
    except ValueError as exc:
        assert "continuation_anchor" in str(exc)
    else:
        raise AssertionError("NativeRuntimeEventRecord should require continuation_anchor in snapshots")
