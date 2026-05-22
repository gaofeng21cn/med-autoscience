from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_runtime_transport_mas_runtime_core import (
    _cleanup_process,
    _spawn_sleep_worker,
    _write_completed_stdout,
    _write_latest_turn_receipt,
    _write_running_state,
    _write_turn_closeout,
)


def test_inspect_live_runtime_keeps_current_run_when_closeout_exists_but_lease_is_live(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"
    worker = _spawn_sleep_worker()
    try:
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T00:00:01+00:00"))
        _write_running_state(quest_root=quest_root, active_run_id="run-active")
        state_path = quest_root / ".ds" / "runtime_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(
            {
                "last_runner_completion": {
                    "state": "completed",
                    "run_id": "run-previous",
                    "reason": "turn_closeout_present",
                },
                "last_completed_run_id": "run-previous",
                "last_known_run_id": "run-previous",
            }
        )
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _write_explicit_live_worker_lease(turn_lifecycle, quest_root=quest_root, run_id="run-active", pid=worker.pid)
        _write_completed_stdout(quest_root=quest_root, run_id="run-active")
        _write_turn_closeout(quest_root=quest_root, run_id="run-active")
        _write_turn_closeout(quest_root=quest_root, run_id="run-previous")
        _write_latest_turn_receipt(
            quest_root=quest_root,
            run_id="run-active",
            status="queued",
            started=False,
            queued=True,
        )

        result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")

        repaired = json.loads(state_path.read_text(encoding="utf-8"))
        assert result["status"] == "live"
        assert result["active_run_id"] == "run-active"
        assert result["worker_running"] is True
        assert repaired["active_run_id"] == "run-active"
        assert repaired["worker_running"] is True
        assert worker.poll() is None
    finally:
        turn_lifecycle.reset_clock_for_tests()
        _cleanup_process(worker)


def _write_explicit_live_worker_lease(turn_lifecycle, *, quest_root: Path, run_id: str, pid: int) -> None:
    lease_path = turn_lifecycle.worker_lease_path(quest_root=quest_root, run_id=run_id)
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    lease_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "quest_id": quest_root.name,
                "run_id": run_id,
                "heartbeat_at": "2026-05-08T00:00:00+00:00",
                "last_output_at": "2026-05-08T00:00:00+00:00",
                "last_seen_at": "2026-05-08T00:00:00+00:00",
                "started_at": "2026-05-08T00:00:00+00:00",
                "pid": pid,
                "monitor_state": "live",
                "monitor_kind": "mas_per_run_worker_wrapper",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
