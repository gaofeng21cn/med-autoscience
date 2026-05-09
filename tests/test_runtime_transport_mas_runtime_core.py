from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import time

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


def test_mas_runtime_core_creates_and_resumes_quest_without_external_daemon(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    create_result = module.create_quest(
        runtime_root=runtime_root,
        payload={"quest_id": "quest-001", "study_id": "study-001", "auto_start": False},
    )
    resume_result = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    quest_root = runtime_root / "quests" / "quest-001"
    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert create_result["source"] == "mas_runtime_core"
    assert create_result["snapshot"]["status"] == "created"
    assert resume_result["source"] == "mas_runtime_core"
    assert resume_result["snapshot"]["status"] == "running"
    assert resume_result["snapshot"]["active_run_id"].startswith("mas-run-")
    assert state["runtime_backend_id"] == "mas_runtime_core"
    assert state["external_mds_required"] is False


def test_chat_quest_persists_user_message_queue_and_schedules_idle_turn(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})

    result = module.chat_quest(runtime_root=runtime_root, quest_id="quest-001", text="继续分析", source="test-user")

    quest_root = runtime_root / "quests" / "quest-001"
    queue = json.loads((quest_root / "artifacts" / "runtime" / "user_message_queue.json").read_text(encoding="utf-8"))
    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert result["status"] == "scheduled"
    assert result["scheduled"] is True
    assert result["started"] is True
    assert result["turn_reason"] == "user_message"
    assert queue["pending"] == []
    assert queue["completed"][0]["content"] == "继续分析"
    assert queue["completed"][0]["source"] == "test-user"
    assert queue["completed"][0]["claimed_by_run_id"] == state["active_run_id"]
    assert state["pending_user_message_count"] == 0
    assert state["worker_running"] is True
    assert state["active_run_id"].startswith("mas-run-")


def test_schedule_turn_serializes_active_worker_without_second_run(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    first = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    second = module.schedule_turn(runtime_root=runtime_root, quest_id="quest-001", reason="auto_continue", source="test")

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert second["status"] == "queued"
    assert second["scheduled"] is True
    assert second["started"] is False
    assert second["queued"] is True
    assert second["active_run_id"] == first["active_run_id"]
    assert state["active_run_id"] == first["active_run_id"]
    assert state["worker_pending"] is True
    assert state["pending_turn_reason"] == "auto_continue"


def test_complete_turn_normalizes_and_prioritizes_queued_user_messages(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    module.chat_quest(runtime_root=runtime_root, quest_id="quest-001", text="新用户消息", source="test-user")

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="succeeded",
        source="test-runner",
    )

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert result["next_turn"]["reason"] == "queued_user_messages"
    assert result["next_turn"]["started"] is True
    assert result["next_turn"]["queued"] is False
    assert state["status"] == "running"
    assert state["worker_running"] is True
    assert state["active_run_id"] != running["active_run_id"]
    assert state["pending_user_message_count"] == 0


def test_complete_turn_auto_policy_schedules_delayed_auto_continue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="succeeded",
        source="test-runner",
    )

    assert result["status"] == "active"
    assert result["next_turn"]["reason"] == "auto_continue"
    assert result["next_turn"]["scheduled"] is True
    assert result["next_turn"]["started"] is False
    assert result["next_turn"]["delay_seconds"] == 0.2


def test_due_delayed_auto_continue_is_drained_by_lifecycle_reconcile(tmp_path: Path) -> None:
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
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T00:00:01+00:00"))

        drained = module.inspect_turn_lifecycle(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.reset_clock_for_tests()

    assert drained["status"] == "live"
    assert drained["drained_delayed_turn"]["reason"] == "auto_continue"
    assert drained["active_run_id"].startswith("mas-run-")


def test_pending_worker_reason_is_drained_before_default_auto_continue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    module.schedule_turn(runtime_root=runtime_root, quest_id="quest-001", reason="recovery", source="watch")

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="succeeded",
        source="test-runner",
    )

    assert result["next_turn"]["reason"] == "recovery"
    assert result["next_turn"]["started"] is True
    assert result["next_turn"]["queued"] is False


def test_complete_turn_retryable_failure_schedules_backoff_without_second_worker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="error",
        source="test-runner",
    )

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "active"
    assert result["next_turn"]["reason"] == "retry_backoff"
    assert result["next_turn"]["started"] is False
    assert result["next_turn"]["delay_seconds"] == 1.0
    assert state["active_run_id"] is None
    assert state["worker_running"] is False
    assert state["retry_state"] == {
        "attempt": 1,
        "max_attempts": 3,
        "next_delay_seconds": 1.0,
        "last_runner_status": "error",
    }


def test_same_fingerprint_guard_stops_auto_spin_until_artifact_delta(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    quest_root = runtime_root / "quests" / "quest-001"
    state_path = quest_root / ".ds" / "runtime_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["same_fingerprint_auto_turn_count"] = 2
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="succeeded",
        source="test-runner",
        same_fingerprint=True,
    )

    updated = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["next_turn"] is None
    assert updated["same_fingerprint_auto_turn_count"] == 3
    assert updated["worker_running"] is False
    assert updated["worker_pending"] is False
    assert updated["control_intent_lifecycle"] == {
        "state": "await_artifact_delta_or_gate_replay",
        "block_reason": "same_fingerprint_no_artifact_delta",
        "same_fingerprint_auto_turn_count": 3,
    }


def test_complete_turn_writes_turn_receipt_to_lifecycle_sqlite_and_storage_hook(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    quest_root = runtime_root / "quests" / "quest-001"

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="succeeded",
        source="test-runner",
    )

    hook = json.loads(
        (quest_root / "artifacts" / "runtime" / "post_turn_storage_maintenance" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    db_path = quest_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT run_id, reason, status, idempotency_key FROM turn_receipts WHERE quest_root = ? ORDER BY recorded_at",
            (str(quest_root.resolve()),),
        ).fetchall()

    assert result["ok"] is True
    assert hook["surface"] == "post_turn_storage_maintenance_hook"
    assert hook["status"] == "recorded"
    assert hook["run_id"] == running["active_run_id"]
    assert ("explicit_resume", "started") in {(row[1], row[2]) for row in rows}
    assert ("explicit_resume", "finished") in {(row[1], row[2]) for row in rows}
    assert all(row[3].startswith("turn-") for row in rows)


def test_complete_turn_waiting_for_user_blocking_decision_stops_without_auto_continue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="waiting_for_user",
        source="test-runner",
        blocking_decision_request={"interaction_id": "decision-001", "question": "continue?"},
    )

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "waiting_for_user"
    assert result["next_turn"] is None
    assert state["active_run_id"] is None
    assert state["worker_running"] is False
    assert state["waiting_interaction_id"] == "decision-001"


def test_normalization_failure_cleans_live_state_and_records_failure_receipt(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    quest_root = runtime_root / "quests" / "quest-001"

    def fail_next_turn(**kwargs):
        raise RuntimeError("next turn scheduler failed")

    monkeypatch.setattr(turn_lifecycle, "_next_turn_after_normalization", fail_next_turn)

    result = module.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id="quest-001",
        run_id=running["active_run_id"],
        runner_status="succeeded",
        source="test-runner",
    )

    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    latest_receipt = json.loads((quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json").read_text())
    assert result["ok"] is False
    assert result["status"] == "normalization_failed"
    assert state["active_run_id"] is None
    assert state["worker_running"] is False
    assert state["normalization_error"] == "RuntimeError: next turn scheduler failed"
    assert latest_receipt["status"] == "normalization_failed"


def test_inspect_live_runtime_reconciles_stale_state_without_worker_lease(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"
    state_path = quest_root / ".ds" / "runtime_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update({"status": "running", "active_run_id": "run-stale", "worker_running": True})
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")
    repaired = json.loads(state_path.read_text(encoding="utf-8"))

    assert result["status"] == "stale"
    assert result["worker_running"] is False
    assert result["active_run_id"] is None
    assert result["stale_active_run_id"] == "run-stale"
    assert repaired["active_run_id"] is None
    assert repaired["worker_running"] is False
    assert repaired["continuation_policy"] == "auto"


def test_inspect_live_runtime_keeps_stale_heartbeat_when_worker_pid_is_live(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})

    class PidRunner:
        def start_turn(self, **kwargs):
            return {
                "runner_kind": "fake",
                "start_mode": "fake_started",
                "available": True,
                "live": True,
                "pid": 4242,
            }

    try:
        turn_lifecycle.set_turn_runner_for_tests(PidRunner())
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T00:00:00+00:00"))
        running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
        monkeypatch.setattr(turn_lifecycle, "pid_live", lambda pid: pid == 4242)
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T01:00:01+00:00"))

        result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.reset_turn_runner_for_tests()
        turn_lifecycle.reset_clock_for_tests()

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "live"
    assert result["active_run_id"] == running["active_run_id"]
    assert result["worker_running"] is True
    assert state["active_run_id"] == running["active_run_id"]
    assert state["worker_running"] is True


def test_inspect_live_runtime_treats_stale_worker_heartbeat_as_not_live(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    try:
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T00:00:00+00:00"))
        running = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
        turn_lifecycle.set_clock_for_tests(lambda: turn_lifecycle.datetime.fromisoformat("2026-05-08T01:00:01+00:00"))

        result = module.inspect_quest_live_runtime(runtime_root=runtime_root, quest_id="quest-001")
    finally:
        turn_lifecycle.reset_clock_for_tests()

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "stale"
    assert result["stale_active_run_id"] == running["active_run_id"]
    assert state["active_run_id"] is None
    assert state["worker_running"] is False


@pytest.mark.parametrize(("operation_name", "expected_status"), [("pause_quest", "paused"), ("stop_quest", "stopped")])
def test_terminal_runtime_operation_terminates_active_and_orphan_leased_workers(
    tmp_path: Path, operation_name: str, expected_status: str
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    quest_root = runtime_root / "quests" / "quest-001"
    active_worker = _spawn_sleep_worker()
    orphan_worker = _spawn_sleep_worker()
    try:
        _write_running_state(quest_root=quest_root, active_run_id="run-active")
        _write_worker_lease(turn_lifecycle, quest_root=quest_root, run_id="run-active", pid=active_worker.pid)
        _write_worker_lease(turn_lifecycle, quest_root=quest_root, run_id="run-orphan", pid=orphan_worker.pid)

        result = getattr(module, operation_name)(runtime_root=runtime_root, quest_id="quest-001", source="test")

        state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        assert result["status"] == expected_status
        assert state["active_run_id"] is None
        assert state["worker_running"] is False
        assert _wait_for_process_exit(active_worker), f"active worker pid {active_worker.pid} was not terminated"
        assert _wait_for_process_exit(orphan_worker), f"orphan worker pid {orphan_worker.pid} was not terminated"
    finally:
        _cleanup_process(active_worker)
        _cleanup_process(orphan_worker)


def test_runner_unavailable_fails_closed_without_live_worker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    turn_lifecycle = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turns")
    runtime_root = tmp_path / "workspace" / "runtime"
    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})

    class UnavailableRunner:
        def start_turn(self, **kwargs):
            return {"runner_kind": "fake", "available": False, "fail_closed": True}

    try:
        turn_lifecycle.set_turn_runner_for_tests(UnavailableRunner())
        result = module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")
    finally:
        turn_lifecycle.reset_turn_runner_for_tests()

    state = json.loads(
        (runtime_root / "quests" / "quest-001" / ".ds" / "runtime_state.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is False
    assert result["status"] == "runner_unavailable"
    assert result["started"] is False
    assert state["active_run_id"] is None
    assert state["worker_running"] is False


def test_codex_exec_runner_allows_mas_owned_non_git_quest_runtime(monkeypatch, tmp_path: Path) -> None:
    runner_module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_runner")
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    runtime_root = tmp_path / "workspace" / "runtime"
    seen = {}

    class StartedProcess:
        pid = 12345

    def fake_popen(args, **kwargs):
        seen["args"] = list(args)
        seen["cwd"] = kwargs.get("cwd")
        seen["stdin"] = kwargs.get("stdin")
        return StartedProcess()

    monkeypatch.setattr(runner_module, "command_available", lambda binary: binary == "codex")
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = runner_module.CodexExecTurnRunner().start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id="quest-001",
        run_id="run-001",
        reason="explicit_resume",
        claimed_user_messages=(),
    )

    assert result["live"] is True
    assert result["command"] == ["codex", "exec", "--json", "--skip-git-repo-check"]
    assert seen["args"][:4] == ["codex", "exec", "--json", "--skip-git-repo-check"]
    assert seen["cwd"] == str(quest_root)
    assert seen["stdin"] is subprocess.DEVNULL


def test_mas_runtime_core_live_execution_reads_local_runtime_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    module.resume_quest(runtime_root=runtime_root, quest_id="quest-001", source="test")

    result = module.inspect_quest_live_execution(runtime_root=runtime_root, quest_id="quest-001")

    assert result["ok"] is True
    assert result["status"] == "live"
    assert result["source"] == "mas_runtime_core_turn_lifecycle"
    assert result["runner_live"] is True
    assert result["bash_live"] is False
    assert result["runtime_audit"]["worker_running"] is True


def test_mas_runtime_core_monitoring_url_points_to_progress_portal(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    workspace_root = tmp_path / "workspace"
    runtime_root = workspace_root / "runtime"
    portal_path = workspace_root / "ops" / "mas" / "progress" / "index.html"
    portal_path.parent.mkdir(parents=True)
    portal_path.write_text("<!doctype html><title>MAS Progress Portal</title>", encoding="utf-8")

    result = module.resolve_daemon_url(runtime_root=runtime_root)

    assert result == portal_path.resolve().as_uri()
    assert result != runtime_root.resolve().as_uri()


def test_mas_runtime_core_monitoring_url_requires_materialized_progress_portal(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    try:
        module.resolve_daemon_url(runtime_root=runtime_root)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("resolve_daemon_url should require a materialized MAS Progress Portal")

    assert "MAS Progress Portal is not materialized" in message
    assert "workspace progress-portal" in message
    assert str(runtime_root.parent / "ops" / "mas" / "progress" / "index.html") in message


def test_mas_runtime_core_update_startup_context_echoes_typed_receipt_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
    runtime_root = tmp_path / "workspace" / "runtime"

    module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})
    result = module.update_quest_startup_context(
        runtime_root=runtime_root,
        quest_id="quest-001",
        startup_contract={"scope": "full_research"},
        requested_baseline_ref={"baseline_id": "demo"},
    )

    startup_context = json.loads(
        (runtime_root / "quests" / "quest-001" / "artifacts" / "runtime" / "startup_context.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["ok"] is True
    assert result["quest_id"] == "quest-001"
    assert result["snapshot"]["quest_id"] == "quest-001"
    assert result["snapshot"]["startup_contract"] == {"scope": "full_research"}
    assert result["snapshot"]["requested_baseline_ref"] == {"baseline_id": "demo"}
    assert startup_context["quest_id"] == "quest-001"


def test_runtime_transport_package_defaults_to_mas_runtime_core(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport")
    runtime_root = tmp_path / "workspace" / "runtime"

    result = module.create_quest(runtime_root=runtime_root, payload={"quest_id": "quest-001"})

    assert result["source"] == "mas_runtime_core"
    assert result["snapshot"]["runtime_backend_id"] == "mas_runtime_core"


def test_mas_runtime_core_repair_paper_live_paths_rewrites_without_external_launcher(
    tmp_path: Path,
) -> None:
    helpers = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_parts.execution_helpers")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    legacy_root = tmp_path / "legacy-workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "legacy" / "mds-runtime",
        med_deepscientist_repo_root=None,
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    paper_workspace = profile.managed_runtime_quests_root / "quest-001" / ".ds" / "worktrees" / "paper-run-001"
    paper_root = paper_workspace / "paper"
    source_csv = workspace_root / "studies" / "001-risk" / "artifacts" / "score.csv"
    source_csv.parent.mkdir(parents=True, exist_ok=True)
    source_csv.write_text("score\n1\n", encoding="utf-8")
    legacy_score_path = str(legacy_root / source_csv.relative_to(workspace_root))
    catalog_path = paper_root / "figures" / "figure_catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "figures": [
                    {
                        "figure_id": "F1",
                        "export_paths": [
                            str(paper_root / "paper" / "figures" / "generated" / "F1.png"),
                        ],
                        "source_paths": [legacy_score_path],
                        "qc_result": {
                            "layout_sidecar_path": str(
                                paper_root / "paper" / "figures" / "generated" / "F1.layout.json"
                            )
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = helpers.repair_paper_live_paths(
        profile=profile,
        quest_id="quest-001",
        workspace_root=paper_workspace,
        current_workspace_root=workspace_root,
    )

    repaired_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["source"] == "mas_runtime_core"
    assert result["external_mds_required"] is False
    assert str(catalog_path) in result["repaired_files"]
    assert repaired_catalog["figures"][0]["source_paths"] == [
        os.path.relpath(source_csv, paper_workspace).replace(os.sep, "/")
    ]
    assert repaired_catalog["figures"][0]["export_paths"] == ["paper/figures/generated/F1.png"]
    assert repaired_catalog["figures"][0]["qc_result"]["layout_sidecar_path"] == (
        "paper/figures/generated/F1.layout.json"
    )


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


def _write_worker_lease(turn_lifecycle, *, quest_root: Path, run_id: str, pid: int) -> None:
    lease_path = turn_lifecycle.worker_lease_path(quest_root=quest_root, run_id=run_id)
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    lease_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "quest_id": quest_root.name,
                "run_id": run_id,
                "heartbeat_at": "2026-05-08T00:00:00+00:00",
                "started_at": "2026-05-08T00:00:00+00:00",
                "pid": pid,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _spawn_sleep_worker() -> subprocess.Popen:
    return subprocess.Popen(
        ["sleep", "30"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _wait_for_process_exit(process: subprocess.Popen, timeout_seconds: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return True
        time.sleep(0.02)
    return process.poll() is not None


def _cleanup_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except OSError:
        try:
            process.terminate()
        except OSError:
            return
    _wait_for_process_exit(process, timeout_seconds=1.0)
    if process.poll() is None:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except OSError:
            try:
                process.kill()
            except OSError:
                return
