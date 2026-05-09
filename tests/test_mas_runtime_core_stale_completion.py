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


def test_complete_turn_ignores_stale_runner_completion_while_new_run_is_active(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    old_run = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    quest_root = runtime_root / "quests" / "quest-001"
    state_path = quest_root / ".ds" / "runtime_state.json"
    before = json.loads(state_path.read_text(encoding="utf-8"))
    before.update(
        {
            "active_run_id": "run-new",
            "worker_running": True,
            "worker_pending": False,
            "last_completed_run_id": None,
            "retry_state": None,
        }
    )
    state_path.write_text(json.dumps(before, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=old_run["active_run_id"],
        runner_status="succeeded",
        source="test-runner",
    )

    after = json.loads(state_path.read_text(encoding="utf-8"))
    events = [
        json.loads(line)
        for line in (quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert result["status"] == "stale_completion_ignored"
    assert result["next_turn"] is None
    assert after["active_run_id"] == "run-new"
    assert after["worker_running"] is True
    assert after["last_completed_run_id"] is None
    assert after["retry_state"] is None
    assert events[-1]["event"] == "stale_runner_completion_ignored"
    assert events[-1]["run_id"] == old_run["active_run_id"]
    assert events[-1]["active_run_id"] == "run-new"
