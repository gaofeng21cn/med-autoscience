from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_inspect_live_runtime_projects_worker_wrapper_watchdog_fields(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})

    class WrapperRunner:
        def start_turn(self, **kwargs):
            return {
                "runner_kind": "codex_exec",
                "start_mode": "worker_wrapper_subprocess",
                "available": True,
                "live": True,
                "pid": 4242,
                "monitor_kind": "mas_per_run_worker_wrapper",
                "monitor_pid": 4242,
                "stdout_path": str(tmp_path / "stdout.jsonl"),
                "stderr_path": str(tmp_path / "stderr.txt"),
            }

    try:
        turn_lifecycle.set_turn_runner_for_tests(WrapperRunner())
        running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
        monkeypatch.setattr(turn_lifecycle, "pid_live", lambda pid: pid == 4242)

        result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.reset_turn_runner_for_tests()

    lease = json.loads(
        (
            runtime_root
            / "quests"
            / "quest-001"
            / ".ds"
            / "runs"
            / running["active_run_id"]
            / "worker_lease.json"
        ).read_text(encoding="utf-8")
    )
    assert lease["monitor_kind"] == "mas_per_run_worker_wrapper"
    assert lease["monitor_pid"] == 4242
    assert lease["monitor_state"] == "live"
    assert result["worker_watchdog"]["monitor_kind"] == "mas_per_run_worker_wrapper"
    assert result["worker_watchdog"]["monitor_state"] == "live"
    assert result["worker_watchdog"]["live"] is True


def test_inspect_live_runtime_marks_wrapper_lost_as_stale(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"
    try:
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T00:00:00+00:00"))
        _write_running_state(quest_root=quest_root, active_run_id="run-active")
        lease_path = turn_lifecycle.worker_lease_path(quest_root=quest_root, run_id="run-active")
        lease_path.parent.mkdir(parents=True, exist_ok=True)
        lease_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "quest_id": "quest-001",
                    "run_id": "run-active",
                    "heartbeat_at": "2026-05-07T22:59:00+00:00",
                    "monitor_kind": "mas_per_run_worker_wrapper",
                    "monitor_pid": 5555,
                    "monitor_state": "live",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(turn_lifecycle, "pid_live", lambda pid: False)

        result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.reset_clock_for_tests()

    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert result["status"] == "stale"
    assert result["stale_active_run_id"] == "run-active"
    assert state["active_run_id"] is None
    assert state["worker_running"] is False


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
        }
    )
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
