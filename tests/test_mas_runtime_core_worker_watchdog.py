from __future__ import annotations

import importlib
import json
from pathlib import Path
import stat
import sys


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


def test_schedule_turn_terminal_capability_projects_controlled_bridge_to_lease(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"

    class TerminalCapableRunner:
        def start_turn(self, **kwargs):
            assert kwargs["terminal_attach_capable"] is True
            return {
                "runner_kind": "codex_exec",
                "start_mode": "terminal_bridge_worker_wrapper_subprocess",
                "available": True,
                "live": True,
                "pid": 4242,
                "monitor_kind": "mas_per_run_terminal_bridge_wrapper",
                "monitor_pid": 4242,
                "stdout_path": str(tmp_path / "stdout.jsonl"),
                "stderr_path": str(tmp_path / "stderr.txt"),
                "terminal_attach_capable": True,
                "terminal_bridge_status": "enabled",
                "terminal_bridge_kind": "mas_controlled_pty",
                "terminal_input_owner": "mas_terminal_attach_contract",
                "chat_quest_input_allowed": False,
                "terminal_bridge_path": str(tmp_path / "terminal_bridge.json"),
                "terminal_transcript_path": str(tmp_path / "terminal.log"),
            }

    try:
        turn_lifecycle.set_turn_runner_for_tests(TerminalCapableRunner())
        running = turn_lifecycle.schedule_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_root.name,
            reason="explicit_terminal_attach_test",
            source="test",
            terminal_attach_capable=True,
        )
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
    assert running["terminal_attach_capable"] is True
    assert running["terminal_bridge_status"] == "enabled"
    assert lease["monitor_kind"] == "mas_per_run_terminal_bridge_wrapper"
    assert lease["terminal_attach_capable"] is True
    assert lease["terminal_bridge_status"] == "enabled"
    assert lease["terminal_bridge_kind"] == "mas_controlled_pty"
    assert lease["terminal_input_owner"] == "mas_terminal_attach_contract"
    assert lease["chat_quest_input_allowed"] is False
    assert lease["terminal_bridge_path"] == str(tmp_path / "terminal_bridge.json")
    assert lease["terminal_transcript_path"] == str(tmp_path / "terminal.log")


def test_worker_wrapper_terminal_capable_mode_runs_controlled_pty_bridge(tmp_path: Path) -> None:
    wrapper = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    runtime_root = tmp_path / "workspace" / "runtime"
    quest_root = runtime_root / "quests" / "quest-001"
    run_id = "run-001"
    prompt_path = quest_root / ".ds" / "runs" / run_id / "prompt.md"
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    stderr_path = quest_root / ".ds" / "runs" / run_id / "stderr.txt"
    fake_codex = tmp_path / "fake-codex"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("controlled prompt", encoding="utf-8")
    fake_codex.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "print('fake terminal runner attached')\n"
        "print('stdin is tty:', sys.stdin.isatty())\n",
        encoding="utf-8",
    )
    fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

    returncode = wrapper.run_wrapper(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id=run_id,
        prompt_path=prompt_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        codex_binary=str(fake_codex),
        terminal_attach_capable=True,
    )

    run_root = quest_root / ".ds" / "runs" / run_id
    bridge = json.loads((run_root / "terminal_bridge.json").read_text(encoding="utf-8"))
    lease = json.loads((run_root / "worker_lease.json").read_text(encoding="utf-8"))
    runner_exit = json.loads((run_root / "runner_exit.json").read_text(encoding="utf-8"))
    transcript = (run_root / "terminal.log").read_text(encoding="utf-8")

    assert returncode == 0
    assert bridge["status"] == "exited"
    assert bridge["bridge_kind"] == "mas_controlled_pty"
    assert bridge["terminal_attach_capable"] is True
    assert bridge["terminal_input_owner"] == "mas_terminal_attach_contract"
    assert bridge["chat_quest_input_allowed"] is False
    assert lease["terminal_attach_capable"] is True
    assert lease["terminal_bridge_status"] == "enabled"
    assert lease["terminal_bridge_kind"] == "mas_controlled_pty"
    assert lease["chat_quest_input_allowed"] is False
    assert runner_exit["runner_status"] == "succeeded"
    assert runner_exit["monitor_kind"] == "mas_per_run_terminal_bridge_wrapper"
    assert "fake terminal runner attached" in transcript
    assert "stdin is tty: True" in transcript


def test_worker_wrapper_terminal_capable_mode_consumes_mas_terminal_input_queue(tmp_path: Path) -> None:
    wrapper = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper")
    runtime_root = tmp_path / "workspace" / "runtime"
    quest_root = runtime_root / "quests" / "quest-001"
    run_id = "run-001"
    prompt_path = quest_root / ".ds" / "runs" / run_id / "prompt.md"
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    stderr_path = quest_root / ".ds" / "runs" / run_id / "stderr.txt"
    command_queue_path = quest_root / ".ds" / "runs" / run_id / "terminal_commands.jsonl"
    fake_codex = tmp_path / "fake-codex"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("controlled prompt", encoding="utf-8")
    command_queue_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "command_id": "cmd-input-1",
                "operation": "terminal_input",
                "payload": {"text": "hello from mas attach\\n"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    fake_codex.write_text(
        f"#!{sys.executable}\n"
        "import os, select, sys\n"
        "ready, _, _ = select.select([sys.stdin], [], [], 2)\n"
        "line = sys.stdin.readline() if ready else ''\n"
        "print('received:', line.strip())\n",
        encoding="utf-8",
    )
    fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

    returncode = wrapper.run_wrapper(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id=run_id,
        prompt_path=prompt_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        codex_binary=str(fake_codex),
        terminal_attach_capable=True,
    )

    run_root = quest_root / ".ds" / "runs" / run_id
    bridge = json.loads((run_root / "terminal_bridge.json").read_text(encoding="utf-8"))
    transcript = (run_root / "terminal.log").read_text(encoding="utf-8")

    assert returncode == 0
    assert "hello from mas attach" in transcript
    assert "received:" in transcript
    assert bridge["latest_command"]["command_id"] == "cmd-input-1"
    assert bridge["latest_command"]["operation"] == "terminal_input"
    assert bridge["latest_command"]["status"] == "applied"


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
