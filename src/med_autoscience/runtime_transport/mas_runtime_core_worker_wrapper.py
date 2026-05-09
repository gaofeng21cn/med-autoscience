from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HEARTBEAT_INTERVAL_SECONDS = 5


def wrapper_command(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    run_id: str,
    prompt_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    codex_binary: str,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper",
        "--runtime-root",
        str(runtime_root),
        "--quest-root",
        str(quest_root),
        "--quest-id",
        quest_id,
        "--run-id",
        run_id,
        "--prompt-path",
        str(prompt_path),
        "--stdout-path",
        str(stdout_path),
        "--stderr-path",
        str(stderr_path),
        "--codex-binary",
        codex_binary,
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MAS per-run Codex worker watchdog wrapper")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--quest-root", required=True)
    parser.add_argument("--quest-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--prompt-path", required=True)
    parser.add_argument("--stdout-path", required=True)
    parser.add_argument("--stderr-path", required=True)
    parser.add_argument("--codex-binary", default="codex")
    args = parser.parse_args(argv)
    return run_wrapper(
        runtime_root=Path(args.runtime_root),
        quest_root=Path(args.quest_root),
        quest_id=args.quest_id,
        run_id=args.run_id,
        prompt_path=Path(args.prompt_path),
        stdout_path=Path(args.stdout_path),
        stderr_path=Path(args.stderr_path),
        codex_binary=args.codex_binary,
    )


def run_wrapper(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    run_id: str,
    prompt_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    codex_binary: str,
) -> int:
    run_root = quest_root / ".ds" / "runs" / run_id
    lease_path = run_root / "worker_lease.json"
    runner_exit_path = run_root / "runner_exit.json"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = prompt_path.read_text(encoding="utf-8")
    stdout_handle = stdout_path.open("a", encoding="utf-8")
    stderr_handle = stderr_path.open("a", encoding="utf-8")
    try:
        child = subprocess.Popen(
            [codex_binary, "exec", "--json", "--skip-git-repo-check", prompt],
            cwd=str(quest_root),
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            start_new_session=True,
        )
    except OSError as exc:
        stdout_handle.close()
        stderr_handle.close()
        _write_json(
            runner_exit_path,
            {
                "schema_version": 1,
                "quest_id": quest_id,
                "run_id": run_id,
                "returncode": None,
                "runner_status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "recorded_at": _utc_now(),
                "monitor_kind": "mas_per_run_worker_wrapper",
            },
        )
        _complete_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
            runner_status="error",
        )
        return 1
    try:
        while child.poll() is None:
            _update_lease(
                lease_path=lease_path,
                quest_id=quest_id,
                run_id=run_id,
                child_pid=child.pid,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                monitor_state="live",
            )
            time.sleep(HEARTBEAT_INTERVAL_SECONDS)
        returncode = child.wait()
    finally:
        stdout_handle.close()
        stderr_handle.close()
    runner_status = "succeeded" if returncode == 0 else "error"
    now = _utc_now()
    _update_lease(
        lease_path=lease_path,
        quest_id=quest_id,
        run_id=run_id,
        child_pid=child.pid,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        monitor_state="exited",
        child_returncode=returncode,
        runner_status=runner_status,
        heartbeat_at=now,
    )
    _write_json(
        runner_exit_path,
        {
            "schema_version": 1,
            "quest_id": quest_id,
            "run_id": run_id,
            "returncode": returncode,
            "runner_status": runner_status,
            "recorded_at": now,
            "monitor_kind": "mas_per_run_worker_wrapper",
            "monitor_pid": None,
            "child_pid": child.pid,
        },
    )
    _complete_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id=run_id,
        runner_status=runner_status,
    )
    return int(returncode or 0)


def _complete_turn(*, runtime_root: Path, quest_root: Path, quest_id: str, run_id: str, runner_status: str) -> None:
    try:
        from med_autoscience.runtime_transport import mas_runtime_core_turns

        mas_runtime_core_turns.complete_turn_and_normalize(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
            runner_status=runner_status,
            source="mas_runtime_core.worker_wrapper",
        )
    except Exception as exc:  # Keep wrapper exit deterministic; stale recovery can pick up the lease.
        _write_json(
            quest_root / ".ds" / "runs" / run_id / "normalization_error.json",
            {
                "schema_version": 1,
                "quest_id": quest_id,
                "run_id": run_id,
                "runner_status": runner_status,
                "error": f"{type(exc).__name__}: {exc}",
                "recorded_at": _utc_now(),
            },
        )


def _update_lease(
    *,
    lease_path: Path,
    quest_id: str,
    run_id: str,
    child_pid: int,
    stdout_path: Path,
    stderr_path: Path,
    monitor_state: str,
    child_returncode: int | None = None,
    runner_status: str | None = None,
    heartbeat_at: str | None = None,
) -> None:
    payload = _read_json(lease_path)
    now = heartbeat_at or _utc_now()
    payload.update(
        {
            "schema_version": 1,
            "quest_id": quest_id,
            "run_id": run_id,
            "heartbeat_at": now,
            "last_seen_at": now,
            "last_output_at": _last_output_at(stdout_path=stdout_path, stderr_path=stderr_path),
            "stdout_cursor": _file_size(stdout_path),
            "stderr_cursor": _file_size(stderr_path),
            "last_stdout_ref": str(stdout_path),
            "last_stderr_ref": str(stderr_path),
            "monitor_kind": "mas_per_run_worker_wrapper",
            "monitor_pid": None,
            "child_pid": child_pid,
            "monitor_state": monitor_state,
            "stale_reason": None,
        }
    )
    if child_returncode is not None:
        payload["child_returncode"] = child_returncode
    if runner_status is not None:
        payload["runner_status"] = runner_status
    _write_json(lease_path, payload)


def _last_output_at(*, stdout_path: Path, stderr_path: Path) -> str | None:
    mtimes: list[float] = []
    for path in (stdout_path, stderr_path):
        try:
            mtimes.append(path.stat().st_mtime)
        except OSError:
            continue
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes), tz=UTC).replace(microsecond=0).isoformat()


def _file_size(path: Path) -> int:
    try:
        return int(path.stat().st_size)
    except OSError:
        return 0


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
