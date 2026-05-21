from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
import argparse
import fcntl
import json
import os
import pty
import select
import subprocess
import time
import termios
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport.mas_runtime_core_worker_codex_isolation import (
    apply_managed_runtime_home,
    preserve_host_codex_canonical_bin,
    remove_active_python_virtualenv,
)
from med_autoscience.runtime_transport.mas_runtime_core_worker_env import (
    load_workspace_mas_config_env,
    prepend_configured_tool_dirs_to_path,
    workspace_root_from_quest_root,
)


HEARTBEAT_INTERVAL_SECONDS = 5


def quest_python_runtime_env(*, quest_root: Path, run_id: str | None = None) -> dict[str, str]:
    cache_root = quest_root / ".ds" / "python_pycache"
    cache_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    load_workspace_mas_config_env(quest_root=quest_root, env=env)
    env["PYTHONPYCACHEPREFIX"] = str(cache_root)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    remove_active_python_virtualenv(env)
    prepend_configured_tool_dirs_to_path(env)
    if run_id:
        preserve_host_codex_canonical_bin(env)
        apply_managed_runtime_home(env=env, quest_root=quest_root, run_id=run_id)
    return env


def workspace_python_path(*, quest_root: Path) -> Path | None:
    workspace_root = workspace_root_from_quest_root(quest_root)
    if workspace_root is None:
        return None
    return workspace_root / ".venv" / "bin" / "python3"


def workspace_python_available(*, quest_root: Path) -> bool:
    python_path = workspace_python_path(quest_root=quest_root)
    return python_path is not None and python_path.is_file() and os.access(python_path, os.X_OK)


def _codex_exec_command(*, codex_binary: str, prompt: str) -> list[str]:
    return [
        codex_binary,
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--ephemeral",
        prompt,
    ]


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
    terminal_attach_capable: bool = False,
) -> list[str]:
    if not workspace_python_available(quest_root=quest_root):
        raise RuntimeError("workspace_python_missing_or_not_executable")
    workspace_python = workspace_python_path(quest_root=quest_root)
    if workspace_python is None:
        raise RuntimeError("workspace_python_missing_or_not_executable")
    command = [
        str(workspace_python),
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
    if terminal_attach_capable:
        command.append("--terminal-attach-capable")
    return command


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
    parser.add_argument("--terminal-attach-capable", action="store_true")
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
        terminal_attach_capable=args.terminal_attach_capable,
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
    terminal_attach_capable: bool = False,
) -> int:
    run_root = quest_root / ".ds" / "runs" / run_id
    lease_path = run_root / "worker_lease.json"
    runner_exit_path = run_root / "runner_exit.json"
    terminal_bridge_path = run_root / "terminal_bridge.json"
    terminal_transcript_path = run_root / "terminal.log"
    terminal_command_queue_path = run_root / "terminal_commands.jsonl"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = prompt_path.read_text(encoding="utf-8")
    if terminal_attach_capable:
        _write_json(
            terminal_bridge_path,
            _terminal_bridge_payload(
                quest_id=quest_id,
                run_id=run_id,
                terminal_transcript_path=terminal_transcript_path,
                status="starting",
                terminal_command_queue_path=terminal_command_queue_path,
            ),
        )
        return _run_terminal_capable_wrapper(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
            prompt=prompt,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            codex_binary=codex_binary,
            lease_path=lease_path,
            runner_exit_path=runner_exit_path,
            terminal_bridge_path=terminal_bridge_path,
            terminal_transcript_path=terminal_transcript_path,
            terminal_command_queue_path=terminal_command_queue_path,
        )
    stdout_handle = stdout_path.open("a", encoding="utf-8")
    stderr_handle = stderr_path.open("a", encoding="utf-8")
    try:
        child = subprocess.Popen(
            _codex_exec_command(codex_binary=codex_binary, prompt=prompt),
            cwd=str(quest_root),
            env=quest_python_runtime_env(quest_root=quest_root, run_id=run_id),
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


def _run_terminal_capable_wrapper(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    run_id: str,
    prompt: str,
    stdout_path: Path,
    stderr_path: Path,
    codex_binary: str,
    lease_path: Path,
    runner_exit_path: Path,
    terminal_bridge_path: Path,
    terminal_transcript_path: Path,
    terminal_command_queue_path: Path,
) -> int:
    master_fd, slave_fd = pty.openpty()
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    terminal_transcript_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_handle = stdout_path.open("ab")
    stderr_handle = stderr_path.open("a", encoding="utf-8")
    terminal_handle = terminal_transcript_path.open("ab")
    child: subprocess.Popen[bytes] | None = None
    try:
        child = subprocess.Popen(
            _codex_exec_command(codex_binary=codex_binary, prompt=prompt),
            cwd=str(quest_root),
            env=quest_python_runtime_env(quest_root=quest_root, run_id=run_id),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            start_new_session=True,
        )
        os.close(slave_fd)
        _write_json(
            terminal_bridge_path,
            _terminal_bridge_payload(
                quest_id=quest_id,
                run_id=run_id,
                terminal_transcript_path=terminal_transcript_path,
                status="live",
                child_pid=child.pid,
                terminal_command_queue_path=terminal_command_queue_path,
            ),
        )
        last_heartbeat = 0.0
        command_cursor = 0
        while child.poll() is None:
            now = time.monotonic()
            if now - last_heartbeat >= HEARTBEAT_INTERVAL_SECONDS:
                _update_lease(
                    lease_path=lease_path,
                    quest_id=quest_id,
                    run_id=run_id,
                    child_pid=child.pid,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    monitor_state="live",
                    terminal_attach_capable=True,
                    terminal_transcript_path=terminal_transcript_path,
                )
                last_heartbeat = now
            command_cursor = _process_terminal_commands(
                master_fd=master_fd,
                command_queue_path=terminal_command_queue_path,
                cursor=command_cursor,
                bridge_path=terminal_bridge_path,
                terminal_transcript_path=terminal_transcript_path,
                quest_id=quest_id,
                run_id=run_id,
                child_pid=child.pid,
            )
            _drain_pty_once(master_fd=master_fd, stdout_handle=stdout_handle, terminal_handle=terminal_handle)
        returncode = child.wait()
        _drain_pty_until_empty(master_fd=master_fd, stdout_handle=stdout_handle, terminal_handle=terminal_handle)
    except OSError as exc:
        if child is None:
            try:
                os.close(slave_fd)
            except OSError:
                pass
        stderr_handle.write(f"{type(exc).__name__}: {exc}\n")
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
                "monitor_kind": "mas_per_run_terminal_bridge_wrapper",
                "terminal_attach_capable": True,
            },
        )
        _write_json(
            terminal_bridge_path,
            _terminal_bridge_payload(
                quest_id=quest_id,
                run_id=run_id,
                terminal_transcript_path=terminal_transcript_path,
                status="error",
                error=f"{type(exc).__name__}: {exc}",
                terminal_command_queue_path=terminal_command_queue_path,
            ),
        )
        _complete_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
            runner_status="error",
        )
        return 1
    finally:
        stdout_handle.close()
        stderr_handle.close()
        terminal_handle.close()
        try:
            os.close(master_fd)
        except OSError:
            pass
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
        terminal_attach_capable=True,
        terminal_transcript_path=terminal_transcript_path,
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
            "monitor_kind": "mas_per_run_terminal_bridge_wrapper",
            "monitor_pid": None,
            "child_pid": child.pid,
            "terminal_attach_capable": True,
            "terminal_transcript_path": str(terminal_transcript_path),
        },
    )
    _write_json(
        terminal_bridge_path,
        _terminal_bridge_payload(
            quest_id=quest_id,
            run_id=run_id,
            terminal_transcript_path=terminal_transcript_path,
            status="exited",
            child_pid=child.pid,
            child_returncode=returncode,
            terminal_command_queue_path=terminal_command_queue_path,
            latest_command=_read_json(terminal_bridge_path).get("latest_command"),
        ),
    )
    _complete_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id=run_id,
        runner_status=runner_status,
    )
    return int(returncode or 0)


def _drain_pty_once(*, master_fd: int, stdout_handle: Any, terminal_handle: Any) -> None:
    readable, _, _ = select.select([master_fd], [], [], 0.1)
    if readable:
        _copy_pty_chunk(master_fd=master_fd, stdout_handle=stdout_handle, terminal_handle=terminal_handle)


def _drain_pty_until_empty(*, master_fd: int, stdout_handle: Any, terminal_handle: Any) -> None:
    while True:
        readable, _, _ = select.select([master_fd], [], [], 0)
        if not readable:
            return
        if not _copy_pty_chunk(master_fd=master_fd, stdout_handle=stdout_handle, terminal_handle=terminal_handle):
            return


def _copy_pty_chunk(*, master_fd: int, stdout_handle: Any, terminal_handle: Any) -> bool:
    try:
        chunk = os.read(master_fd, 65536)
    except OSError:
        return False
    if not chunk:
        return False
    stdout_handle.write(chunk)
    stdout_handle.flush()
    terminal_handle.write(chunk)
    terminal_handle.flush()
    return True


def _process_terminal_commands(
    *,
    master_fd: int,
    command_queue_path: Path,
    cursor: int,
    bridge_path: Path,
    terminal_transcript_path: Path,
    quest_id: str,
    run_id: str,
    child_pid: int,
) -> int:
    try:
        with command_queue_path.open("r", encoding="utf-8") as handle:
            handle.seek(cursor)
            lines = handle.readlines()
            next_cursor = handle.tell()
    except FileNotFoundError:
        return cursor
    except OSError:
        return cursor
    for line in lines:
        try:
            command = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(command, dict):
            _apply_terminal_command(
                master_fd=master_fd,
                command=command,
                bridge_path=bridge_path,
                terminal_transcript_path=terminal_transcript_path,
                quest_id=quest_id,
                run_id=run_id,
                child_pid=child_pid,
                command_queue_path=command_queue_path,
            )
    return next_cursor


def _apply_terminal_command(
    *,
    master_fd: int,
    command: dict[str, Any],
    bridge_path: Path,
    terminal_transcript_path: Path,
    quest_id: str,
    run_id: str,
    child_pid: int,
    command_queue_path: Path,
) -> None:
    operation = str(command.get("operation") or "").strip()
    payload = command.get("payload") if isinstance(command.get("payload"), dict) else {}
    status = "applied"
    error: str | None = None
    try:
        if operation == "terminal_input":
            os.write(master_fd, str(payload.get("text") or "").encode("utf-8"))
        elif operation == "resize_terminal":
            _resize_pty(master_fd=master_fd, rows=int(payload.get("rows") or 0), cols=int(payload.get("cols") or 0))
        elif operation == "detach_terminal":
            status = "detached"
        else:
            status = "ignored"
            error = "unknown_terminal_command"
    except OSError as exc:
        status = "error"
        error = f"{type(exc).__name__}: {exc}"
    _write_json(
        bridge_path,
        _terminal_bridge_payload(
            quest_id=quest_id,
            run_id=run_id,
            terminal_transcript_path=terminal_transcript_path,
            status="live",
            child_pid=child_pid,
            terminal_command_queue_path=command_queue_path,
            latest_command={
                "command_id": command.get("command_id"),
                "operation": operation,
                "status": status,
                "error": error,
                "applied_at": _utc_now(),
            },
        ),
    )


def _resize_pty(*, master_fd: int, rows: int, cols: int) -> None:
    if rows <= 0 or cols <= 0:
        raise OSError("rows and cols must be positive")
    winsize = rows.to_bytes(2, "little") + cols.to_bytes(2, "little") + b"\x00\x00\x00\x00"
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)


def _terminal_bridge_payload(
    *,
    quest_id: str,
    run_id: str,
    terminal_transcript_path: Path,
    status: str,
    child_pid: int | None = None,
    child_returncode: int | None = None,
    error: str | None = None,
    terminal_command_queue_path: Path | None = None,
    latest_command: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "quest_id": quest_id,
        "run_id": run_id,
        "status": status,
        "bridge_kind": "mas_controlled_pty",
        "terminal_attach_capable": True,
        "terminal_transcript_path": str(terminal_transcript_path),
        "terminal_command_queue_path": str(terminal_command_queue_path) if terminal_command_queue_path is not None else None,
        "terminal_input_owner": "mas_terminal_attach_contract",
        "terminal_input_mode": "lease_guarded_command_queue",
        "chat_quest_input_allowed": False,
        "recorded_at": _utc_now(),
    }
    if child_pid is not None:
        payload["child_pid"] = child_pid
    if child_returncode is not None:
        payload["child_returncode"] = child_returncode
    if error:
        payload["error"] = error
    if latest_command is not None:
        payload["latest_command"] = latest_command
    return payload


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
    terminal_attach_capable: bool = False,
    terminal_transcript_path: Path | None = None,
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
            "terminal_attach_capable": terminal_attach_capable,
            "terminal_bridge_status": "enabled" if terminal_attach_capable else "disabled_by_run_capability",
            "terminal_bridge_kind": "mas_controlled_pty" if terminal_attach_capable else None,
            "terminal_input_owner": "mas_terminal_attach_contract" if terminal_attach_capable else None,
            "terminal_command_queue_path": str(lease_path.parent / "terminal_commands.jsonl") if terminal_attach_capable else None,
            "chat_quest_input_allowed": False,
        }
    )
    if terminal_transcript_path is not None:
        payload["terminal_transcript_path"] = str(terminal_transcript_path)
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
