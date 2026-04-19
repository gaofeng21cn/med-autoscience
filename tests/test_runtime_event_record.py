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
        event_source="study_runtime_status",
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
