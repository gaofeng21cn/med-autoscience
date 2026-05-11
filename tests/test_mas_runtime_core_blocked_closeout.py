from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_complete_turn_blocked_closeout_parks_without_auto_continue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    try:
        turn_lifecycle.set_turn_runner_for_tests(_AvailableRunner())
        turn_lifecycle.set_delayed_timers_enabled_for_tests(False)
        running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
        quest_root = runtime_root / "quests" / "quest-001"
        _write_completed_stdout(quest_root=quest_root, run_id=running["active_run_id"])
        _write_blocked_closeout(
            quest_root=quest_root,
            run_id=running["active_run_id"],
            blocked_reason="publication gate requires AI reviewer provenance",
            next_owner="ai_reviewer",
        )

        result = module.complete_turn_and_normalize(
            runtime_root=runtime_root,
            quest_id="quest-001",
            run_id=running["active_run_id"],
            runner_status="succeeded",
            source="test-runner",
        )
    finally:
        turn_lifecycle.set_delayed_timers_enabled_for_tests(False)
        turn_lifecycle.reset_turn_runner_for_tests()

    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert result["status"] == "waiting_for_user"
    assert result["next_turn"] is None
    assert state["active_run_id"] is None
    assert state["worker_running"] is False
    assert state["worker_pending"] is False
    assert state["last_runner_status"] == "blocked_waiting_for_user"
    assert state["continuation_policy"] == "wait_for_user_or_resume"
    assert state["continuation_anchor"] == "turn_closeout"
    assert state["continuation_reason"] == "blocked_turn_closeout_waiting_for_owner"
    assert state["blocked_turn_closeout"]["blocked_reason"] == "publication gate requires AI reviewer provenance"
    assert state["blocked_turn_closeout"]["next_owner"] == "ai_reviewer"


def test_stale_liveness_blocked_closeout_reconciles_to_waiting_owner(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"
    _write_running_state(quest_root=quest_root, active_run_id="run-active")
    _write_completed_stdout(quest_root=quest_root, run_id="run-active")
    _write_blocked_closeout(
        quest_root=quest_root,
        run_id="run-active",
        blocked_reason="supervisor-only publication bundle gate",
        next_owner="publication_gate",
    )
    _write_latest_turn_receipt(quest_root=quest_root, run_id="run-active", status="queued")
    try:
        turn_lifecycle.set_delayed_timers_enabled_for_tests(False)

        result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.set_delayed_timers_enabled_for_tests(False)

    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    latest_receipt = json.loads(
        (quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "stale"
    assert result["stale_reason"] == "blocked_turn_closeout_waiting_for_owner"
    assert state["status"] == "waiting_for_user"
    assert state["continuation_policy"] == "wait_for_user_or_resume"
    assert state["continuation_reason"] == "blocked_turn_closeout_waiting_for_owner"
    assert state["blocked_turn_closeout"]["next_owner"] == "publication_gate"
    assert latest_receipt["runner_status"] == "blocked_waiting_for_user"
    assert latest_receipt["normalized_status"] == "waiting_for_user"


def test_control_plane_facts_treat_blocked_closeout_as_parked() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_facts")

    facts = module.resolve_control_plane_facts(
        {
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_status": "none",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            },
        },
        supervisor_tick_audit={"status": "fresh"},
    )

    assert facts.runtime_liveness_status == "parked"
    assert facts.reason == "blocked_turn_closeout_waiting_for_owner"
    assert facts.active_run_id is None
    assert facts.active_run_id_source == "continuation_state.parked_closeout"
    assert facts.missing_live_session is False
    assert facts.recovery_pending is False
    assert facts.to_runtime_worker_activity()["activity_state"] == "parked"


def test_active_no_live_runtime_absorbs_latest_blocked_closeout(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"
    _write_active_no_live_state(quest_root=quest_root, last_completed_run_id="run-blocked")
    _write_blocked_closeout(
        quest_root=quest_root,
        run_id="run-blocked",
        blocked_reason="AI reviewer authority missing",
        next_owner="ai_reviewer",
    )

    result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")

    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert result["status"] == "parked"
    assert result["stale_reason"] == "blocked_turn_closeout_waiting_for_owner"
    assert state["status"] == "waiting_for_user"
    assert state["active_run_id"] is None
    assert state["worker_running"] is False
    assert state["continuation_policy"] == "wait_for_user_or_resume"
    assert state["continuation_reason"] == "blocked_turn_closeout_waiting_for_owner"
    assert state["blocked_turn_closeout"]["next_owner"] == "ai_reviewer"


def test_live_run_clears_stale_blocked_closeout_from_superseded_run(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"
    _write_running_state(quest_root=quest_root, active_run_id="run-live")
    state_path = quest_root / ".ds" / "runtime_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
            "blocked_turn_closeout": {
                "run_id": "run-old",
                "blocked_reason": "old worker could not resolve uv",
                "next_owner": "mas/controller",
            },
        }
    )
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        turn_lifecycle.set_clock_for_tests(
            lambda: turn_lifecycle.datetime.fromisoformat("2026-05-09T12:00:00+00:00")
        )
        lease_path = turn_lifecycle.worker_lease_path(quest_root=quest_root, run_id="run-live")
        lease_path.parent.mkdir(parents=True, exist_ok=True)
        lease_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "quest_id": "quest-001",
                    "run_id": "run-live",
                    "heartbeat_at": "2026-05-09T12:00:00+00:00",
                    "monitor_state": "live",
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.reset_clock_for_tests()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["status"] == "live"
    assert result["active_run_id"] == "run-live"
    assert "blocked_turn_closeout" not in state
    assert "last_liveness_reconcile_reason" not in state
    assert state["status"] == "running"
    assert state["active_run_id"] == "run-live"
    assert state["worker_running"] is True
    assert state["continuation_policy"] == "auto"
    assert state["continuation_anchor"] == "live_run"
    assert state["continuation_reason"] == "stale_blocked_turn_closeout_superseded_by_live_run"
    assert state["last_stale_blocked_closeout_clear"]["active_run_id"] == "run-live"
    assert state["last_stale_blocked_closeout_clear"]["cleared_run_id"] == "run-old"


def test_quest_runtime_snapshot_adopts_reconciled_liveness_status() -> None:
    quest_state = importlib.import_module("med_autoscience.runtime_protocol.quest_state")
    snapshot = quest_state.QuestRuntimeSnapshot(quest_exists=True, quest_status="active")

    reconciled = snapshot.with_runtime_liveness_audit(
        {
            "status": "none",
            "snapshot": {
                "status": "waiting_for_user",
                "active_run_id": None,
            },
        }
    )

    assert reconciled.quest_status == "waiting_for_user"


class _AvailableRunner:
    def start_turn(self, **kwargs):
        return {
            "runner_kind": "fake",
            "start_mode": "fake_started",
            "available": True,
            "live": True,
        }


def _write_running_state(*, quest_root: Path, active_run_id: str) -> None:
    state_path = quest_root / ".ds" / "runtime_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "status": "running",
            "active_run_id": active_run_id,
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "turn_reason": "explicit_resume",
        }
    )
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_active_no_live_state(*, quest_root: Path, last_completed_run_id: str) -> None:
    state_path = quest_root / ".ds" / "runtime_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(
        {
            "status": "active",
            "active_run_id": None,
            "worker_running": False,
            "worker_pending": False,
            "continuation_policy": "auto",
            "last_completed_run_id": last_completed_run_id,
        }
    )
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_completed_stdout(*, quest_root: Path, run_id: str) -> None:
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {"type": "item.started", "item": {"id": "item-1"}},
        {"type": "item.completed", "item": {"id": "item-1"}},
        {"type": "turn.completed"},
    ]
    stdout_path.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )


def _write_blocked_closeout(
    *,
    quest_root: Path,
    run_id: str,
    blocked_reason: str,
    next_owner: str,
) -> None:
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "quest_id": quest_root.name,
                "run_id": run_id,
                "status": "blocked",
                "completed_at": "2026-05-09T11:00:00+00:00",
                "meaningful_artifact_delta": False,
                "artifact_refs": [],
                "blocked_reason": blocked_reason,
                "next_owner": next_owner,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_latest_turn_receipt(*, quest_root: Path, run_id: str, status: str) -> None:
    receipt_path = quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "quest_id": quest_root.name,
                "run_id": run_id,
                "reason": "explicit_resume",
                "source": "test",
                "status": status,
                "started": False,
                "queued": True,
                "scheduled": True,
                "idempotency_key": "turn-test",
                "recorded_at": "2026-05-09T11:00:00+00:00",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
