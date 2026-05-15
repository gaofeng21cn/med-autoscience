from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _fake_available_turn_runner():
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")

    class AvailableRunner:
        def start_turn(self, **kwargs):
            return {
                "runner_kind": "fake",
                "start_mode": "fake_started",
                "available": True,
                "live": True,
            }

    turn_lifecycle.set_turn_runner_for_tests(AvailableRunner())
    turn_lifecycle.set_delayed_timers_enabled_for_tests(False)
    try:
        yield
    finally:
        turn_lifecycle.set_delayed_timers_enabled_for_tests(False)
        turn_lifecycle.reset_turn_runner_for_tests()
        turn_lifecycle.reset_clock_for_tests()


def test_paused_quest_does_not_drain_due_delayed_auto_continue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    try:
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T00:00:00+00:00"))
        running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
        module.complete_turn_and_normalize(
            runtime_root=runtime_root,
            quest_id="quest-001",
            run_id=running["active_run_id"],
            runner_status="succeeded",
            source="test-runner",
        )
        module.pause_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-pause")
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T00:00:01+00:00"))

        inspected = module.inspect_turn_lifecycle(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.reset_clock_for_tests()

    quest_root = runtime_root / "quests" / "quest-001"
    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert inspected["status"] == "none"
    assert "drained_delayed_turn" not in inspected
    assert state["status"] == "paused"
    assert state["active_run_id"] is None
    assert state["worker_running"] is False
    assert not (quest_root / "artifacts" / "runtime" / "delayed_turns.json").exists()


def test_late_worker_completion_cannot_unpause_human_paused_quest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    module.pause_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-pause")

    completion = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="failed",
        source="late-worker",
    )

    state = json.loads((runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert completion["status"] == "stale_completion_ignored"
    assert completion["next_turn"] is None
    assert state["status"] == "paused"
    assert state["active_run_id"] is None
    assert state["worker_running"] is False
    assert state["worker_pending"] is False


def test_terminal_runtime_state_blocks_direct_schedule_attempt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    module.pause_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-pause")

    scheduled = module.schedule_turn(
        runtime_root=runtime_root,
        quest_id="quest-001",
        reason="retry_backoff",
        source="late-timer",
    )

    state = json.loads((runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert scheduled["status"] == "blocked"
    assert scheduled["blocked_reason"] == "terminal_runtime_state"
    assert scheduled["started"] is False
    assert scheduled["scheduled"] is False
    assert state["status"] == "paused"
    assert state["active_run_id"] is None
    assert state["worker_running"] is False


def test_terminal_runtime_state_blocks_direct_explicit_resume_schedule_attempt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    module.pause_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-pause")

    scheduled = module.schedule_turn(
        runtime_root=runtime_root,
        quest_id="quest-001",
        reason="explicit_resume",
        source="direct-schedule",
    )

    state = json.loads((runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert scheduled["status"] == "blocked"
    assert scheduled["blocked_reason"] == "terminal_runtime_state"
    assert scheduled["started"] is False
    assert scheduled["scheduled"] is False
    assert state["status"] == "paused"
    assert state["active_run_id"] is None
    assert state["worker_running"] is False


def test_explicit_resume_restarts_paused_quest_without_opening_auto_schedule(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    first = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    module.pause_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-pause")

    resumed = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="explicit-user-wakeup")

    state = json.loads((runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert resumed["status"] == "running"
    assert resumed["scheduled"] is True
    assert resumed["started"] is True
    assert resumed["queued"] is False
    assert resumed["turn_reason"] == "explicit_resume"
    assert resumed["active_run_id"] != first["active_run_id"]
    assert state["status"] == "running"
    assert state["active_run_id"] == resumed["active_run_id"]
    assert state["worker_running"] is True
