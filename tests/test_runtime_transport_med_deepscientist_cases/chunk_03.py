from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_inspect_quest_live_execution_combines_runtime_and_bash_audits(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "session_count": 1,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    )

    live_result = module.inspect_quest_live_execution(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert live_result == {
        "ok": True,
        "status": "live",
        "source": "combined_runner_or_bash_session",
        "active_run_id": "run-live",
        "runner_live": True,
        "bash_live": False,
        "runtime_audit": {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
        },
        "bash_session_audit": {
            "ok": True,
            "status": "none",
            "session_count": 1,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    }

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "source": "daemon_turn_worker",
            "active_run_id": "run-stale",
            "worker_running": False,
            "worker_pending": False,
            "stop_requested": False,
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "session_count": 0,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    )

    none_result = module.inspect_quest_live_execution(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert none_result == {
        "ok": True,
        "status": "none",
        "source": "combined_runner_or_bash_session",
        "active_run_id": "run-stale",
        "runner_live": False,
        "bash_live": False,
        "runtime_audit": {
            "ok": True,
            "status": "none",
            "source": "daemon_turn_worker",
            "active_run_id": "run-stale",
            "worker_running": False,
            "worker_pending": False,
            "stop_requested": False,
        },
        "bash_session_audit": {
            "ok": True,
            "status": "none",
            "session_count": 0,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    }
def test_inspect_quest_live_execution_degrades_stale_live_runtime_to_unknown(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-stale",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "interaction_watchdog": {
                "last_artifact_interact_at": "2026-04-08T10:05:03+00:00",
                "seconds_since_last_artifact_interact": 3600,
                "tool_calls_since_last_artifact_interact": 0,
                "active_execution_window": True,
                "stale_visibility_gap": True,
                "inspection_due": True,
                "user_update_due": False,
            },
            "stale_progress": True,
            "liveness_guard_reason": "stale_progress_watchdog",
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "session_count": 0,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    )

    result = module.inspect_quest_live_execution(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert result == {
        "ok": False,
        "status": "unknown",
        "source": "combined_runner_or_bash_session",
        "active_run_id": "run-live-stale",
        "runner_live": True,
        "bash_live": False,
        "stale_progress": True,
        "liveness_guard_reason": "stale_progress_watchdog",
        "runtime_audit": {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-stale",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "interaction_watchdog": {
                "last_artifact_interact_at": "2026-04-08T10:05:03+00:00",
                "seconds_since_last_artifact_interact": 3600,
                "tool_calls_since_last_artifact_interact": 0,
                "active_execution_window": True,
                "stale_visibility_gap": True,
                "inspection_due": True,
                "user_update_due": False,
            },
            "stale_progress": True,
            "liveness_guard_reason": "stale_progress_watchdog",
        },
        "bash_session_audit": {
            "ok": True,
            "status": "none",
            "session_count": 0,
            "live_session_count": 0,
            "live_session_ids": [],
        },
        "error": "Live managed runtime exceeded the artifact interaction silence threshold.",
    }
def test_inspect_quest_live_runtime_flags_missing_first_progress_after_stale_run_start(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "get_quest_session",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "active_run_id": "run-live-first-progress-missing",
                "last_transition_at": "2026-04-08T10:05:03+00:00",
                "interaction_watchdog": {
                    "last_artifact_interact_at": None,
                    "seconds_since_last_artifact_interact": None,
                    "tool_calls_since_last_artifact_interact": 0,
                    "last_tool_activity_at": None,
                    "seconds_since_last_tool_activity": None,
                    "active_execution_window": True,
                    "stale_visibility_gap": False,
                    "inspection_due": False,
                    "user_update_due": False,
                },
            },
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-first-progress-missing",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )

    result = module.inspect_quest_live_runtime(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert result == {
        "ok": True,
        "status": "live",
        "source": "daemon_turn_worker",
        "active_run_id": "run-live-first-progress-missing",
        "worker_running": True,
        "worker_pending": False,
        "stop_requested": False,
        "interaction_watchdog": {
            "last_artifact_interact_at": None,
            "seconds_since_last_artifact_interact": None,
            "tool_calls_since_last_artifact_interact": 0,
            "last_tool_activity_at": None,
            "seconds_since_last_tool_activity": None,
            "active_execution_window": True,
            "stale_visibility_gap": False,
            "inspection_due": False,
            "user_update_due": False,
        },
        "stale_progress": True,
        "liveness_guard_reason": "stale_progress_watchdog",
    }
def test_inspect_quest_live_runtime_falls_back_to_local_transition_timestamp_for_missing_first_progress(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "quests" / "001-risk" / ".ds" / "runtime_state.json",
        json.dumps({"last_transition_at": "2026-04-08T10:05:03+00:00"}) + "\n",
    )

    monkeypatch.setattr(
        module,
        "get_quest_session",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "active_run_id": "run-live-first-progress-missing",
                "last_transition_at": None,
                "interaction_watchdog": {
                    "last_artifact_interact_at": None,
                    "seconds_since_last_artifact_interact": None,
                    "tool_calls_since_last_artifact_interact": 0,
                    "last_tool_activity_at": None,
                    "seconds_since_last_tool_activity": None,
                    "active_execution_window": True,
                    "stale_visibility_gap": False,
                    "inspection_due": False,
                    "user_update_due": False,
                },
            },
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-first-progress-missing",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )

    result = module.inspect_quest_live_runtime(
        runtime_root=runtime_root,
        quest_id="001-risk",
    )

    assert result["stale_progress"] is True
    assert result["liveness_guard_reason"] == "stale_progress_watchdog"
def test_inspect_quest_live_execution_falls_back_to_local_runtime_state_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstatus: active\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "active",
                "display_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            }
        )
        + "\n",
    )

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
    )

    result = module.inspect_quest_live_execution(runtime_root=runtime_root, quest_id="001-risk")

    assert result == {
        "ok": True,
        "status": "none",
        "source": "local_runtime_state_contract",
        "active_run_id": None,
        "runner_live": False,
        "bash_live": False,
        "runtime_audit": {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
        "bash_session_audit": {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
        "local_runtime_state": {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "decision",
            "continuation_reason": "unchanged_finalize_state",
        },
        "probe_error": "daemon unavailable | daemon unavailable",
    }
def test_inspect_quest_live_execution_keeps_unknown_when_local_runtime_state_is_running(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstatus: running\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "display_status": "running",
                "active_run_id": None,
            }
        )
        + "\n",
    )

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
    )

    result = module.inspect_quest_live_execution(runtime_root=runtime_root, quest_id="001-risk")

    assert result == {
        "ok": False,
        "status": "unknown",
        "source": "combined_runner_or_bash_session",
        "active_run_id": None,
        "runner_live": False,
        "bash_live": False,
        "runtime_audit": {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
        "bash_session_audit": {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
        "error": "daemon unavailable | daemon unavailable",
    }
