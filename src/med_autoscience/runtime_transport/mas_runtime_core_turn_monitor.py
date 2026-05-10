from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol


class ProcessLike(Protocol):
    def wait(self) -> int: ...


def arm_runner_monitor(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    run_id: str,
    source: str,
    process: ProcessLike | None,
    load_state: Callable[..., dict[str, Any]],
    text: Callable[[object], str | None],
    append_runtime_event: Callable[..., None],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    run_root: Callable[..., Path],
    utc_now: Callable[[], str],
    complete_turn_and_normalize: Callable[..., dict[str, Any]],
    persist_state: Callable[..., dict[str, Any]],
) -> None:
    if process is None:
        return

    def _wait_and_normalize() -> None:
        try:
            returncode = process.wait()
            state = load_state(quest_root=quest_root)
            if text(state.get("active_run_id")) != run_id or state.get("worker_running") is not True:
                append_runtime_event(
                    quest_root=quest_root,
                    event={
                        "event": "runner_exit_ignored",
                        "source": f"{source}:runner_monitor",
                        "run_id": run_id,
                        "returncode": returncode,
                        "recorded_at": utc_now(),
                    },
                )
                return
            runner_status = "succeeded" if returncode == 0 else "error"
            write_json(
                run_root(quest_root=quest_root, run_id=run_id) / "runner_exit.json",
                {
                    "schema_version": 1,
                    "quest_id": quest_id,
                    "run_id": run_id,
                    "returncode": returncode,
                    "runner_status": runner_status,
                    "recorded_at": utc_now(),
                },
            )
            complete_turn_and_normalize(
                runtime_root=runtime_root,
                quest_root=quest_root,
                quest_id=quest_id,
                run_id=run_id,
                runner_status=runner_status,
                source=f"{source}:runner_monitor",
            )
        except Exception as exc:
            persist_state(
                quest_root=quest_root,
                updates={
                    "status": "active",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "normalization_error": f"{type(exc).__name__}: {exc}",
                },
                source=f"{source}:runner_monitor",
                event_name="runner_monitor_failed",
            )

    thread = threading.Thread(target=_wait_and_normalize, name=f"mas-turn-monitor-{run_id}", daemon=True)
    thread.start()


__all__ = ["arm_runner_monitor"]
