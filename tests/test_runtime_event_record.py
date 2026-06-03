from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_runtime_event_record_round_trips_and_writes_latest_alias(tmp_path: Path) -> None:
    record_module = importlib.import_module("med_autoscience.runtime_event_record")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    launch_report_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"

    record = record_module.RuntimeEventRecord(
        schema_version=1,
        event_id="runtime-event::001-risk::quest-001::status_observed::2026-04-11T09:00:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-11T09:00:00+00:00",
        event_source="progress_projection",
        event_kind="status_observed",
        summary_ref=str(launch_report_path),
        status_snapshot={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "active_run_id": None,
            "runtime_liveness_status": "none",
            "worker_running": False,
            "continuation_policy": None,
            "continuation_reason": None,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": None,
        },
        outer_loop_input={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "active_run_id": None,
            "runtime_liveness_status": "none",
            "worker_running": False,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": None,
        },
    )

    written = protocol.write_runtime_event_record(quest_root=quest_root, record=record)
    latest_ref = protocol.read_runtime_event_record_ref(quest_root=quest_root)

    assert latest_ref == written.ref()
    event_path = Path(written.artifact_path)
    latest_path = event_path.parent / "latest.json"
    assert latest_path.exists()
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_payload["event_id"] == record.event_id
    assert latest_payload["outer_loop_input"]["quest_status"] == "stopped"


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
