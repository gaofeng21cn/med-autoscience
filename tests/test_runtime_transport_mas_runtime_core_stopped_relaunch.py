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
    try:
        yield
    finally:
        turn_lifecycle.reset_turn_runner_for_tests()


def test_resume_quest_fails_closed_for_stopped_runtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    module.stop_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-stop")

    result = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-resume")

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "terminal_runtime_state"
    assert result["runtime_status"] == "stopped"
    assert result["snapshot"]["status"] == "stopped"
    assert result["started"] is False


def test_relaunch_stopped_quest_explicitly_reopens_stopped_runtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    module.stop_quest(runtime_root=runtime_root, quest_id="quest-001", source="test-stop")

    result = module.relaunch_stopped_quest(
        runtime_root=runtime_root,
        quest_id="quest-001",
        source="controller-relaunch",
    )

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is True
    assert result["status"] == "running"
    assert result["reason"] == "explicit_relaunch_stopped"
    assert result["started"] is True
    assert result["snapshot"]["status"] == "running"
    assert result["snapshot"]["active_run_id"].startswith("mas-run-")
    assert state["status"] == "running"
    assert state["worker_running"] is True
    assert state["stop_requested"] is False
    assert state["last_relaunch_stopped"]["previous_status"] == "stopped"
    assert state["last_relaunch_stopped"]["source"] == "controller-relaunch"

