from __future__ import annotations

from dataclasses import dataclass
import subprocess
from pathlib import Path
from typing import Any, Protocol

from med_autoscience.runtime_transport.mas_runtime_core_turn_authorization import (
    _codex_turn_prompt,
    _read_runtime_state,
    _sanitize_runtime_state_before_turn,
    _sync_current_controller_authorization_for_turn,
)
from med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper import wrapper_command
from med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper import quest_python_runtime_env
from med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper import workspace_python_available
from med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper import workspace_python_path
from med_autoscience.runtime_transport.mas_runtime_core_turn_utils import command_available


class MasTurnRunner(Protocol):
    def start_turn(
        self,
        *,
        runtime_root: Path,
        quest_root: Path,
        quest_id: str,
        run_id: str,
        reason: str,
        claimed_user_messages: tuple[dict[str, Any], ...],
        terminal_attach_capable: bool = False,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class CodexExecTurnRunner:
    """Minimal MAS-owned runner adapter; tests can replace it with a fake runner."""

    codex_binary: str = "codex"
    dry_run: bool = False
    use_worker_wrapper: bool = True

    def start_turn(
        self,
        *,
        runtime_root: Path,
        quest_root: Path,
        quest_id: str,
        run_id: str,
        reason: str,
        claimed_user_messages: tuple[dict[str, Any], ...],
        terminal_attach_capable: bool = False,
    ) -> dict[str, Any]:
        command = [self.codex_binary, "exec", "--json", "--skip-git-repo-check"]
        if self.dry_run:
            return {
                "runner_kind": "codex_exec",
                "start_mode": "disabled_dry_run",
                "command": command,
                "available": command_available(self.codex_binary),
                "fail_closed": True,
                "error": "codex_exec_runner_dry_run_disabled",
            }
        if not command_available(self.codex_binary):
            return {
                "runner_kind": "codex_exec",
                "start_mode": "subprocess",
                "command": command,
                "available": False,
                "fail_closed": True,
                "error": f"codex binary is not available: {self.codex_binary}",
            }
        workspace_python = workspace_python_path(quest_root=quest_root)
        if self.use_worker_wrapper and not workspace_python_available(quest_root=quest_root):
            return {
                "runner_kind": "codex_exec",
                "start_mode": "worker_wrapper_subprocess",
                "command": command,
                "wrapper_command": None,
                "available": True,
                "live": False,
                "fail_closed": True,
                "error": "workspace_python_missing_or_not_executable",
                "workspace_python": str(workspace_python) if workspace_python is not None else None,
            }
        stdout_path = _run_root(quest_root=quest_root, run_id=run_id) / "stdout.jsonl"
        stderr_path = _run_root(quest_root=quest_root, run_id=run_id) / "stderr.txt"
        prompt_path = _run_root(quest_root=quest_root, run_id=run_id) / "prompt.md"
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        runtime_state = _read_runtime_state(quest_root=quest_root)
        runtime_state = _sanitize_runtime_state_before_turn(
            runtime_state=runtime_state,
            quest_root=quest_root,
            quest_id=quest_id,
        )
        runtime_state = _sync_current_controller_authorization_for_turn(
            runtime_state=runtime_state,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
        )
        prompt_path.write_text(
            _codex_turn_prompt(
                quest_id=quest_id,
                run_id=run_id,
                reason=reason,
                claimed_user_messages=claimed_user_messages,
                runtime_state=runtime_state,
                quest_root=quest_root,
            ),
            encoding="utf-8",
        )
        wrapper_cmd = (
            wrapper_command(
                runtime_root=runtime_root,
                quest_root=quest_root,
                quest_id=quest_id,
                run_id=run_id,
                prompt_path=prompt_path,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                codex_binary=self.codex_binary,
                terminal_attach_capable=terminal_attach_capable,
            )
            if self.use_worker_wrapper
            else None
        )
        stdout_handle = stdout_path.open("w", encoding="utf-8")
        stderr_handle = stderr_path.open("w", encoding="utf-8")
        try:
            popen_args = wrapper_cmd if wrapper_cmd is not None else [*command, prompt_path.read_text(encoding="utf-8")]
            env = quest_python_runtime_env(
                quest_root=quest_root,
                run_id=run_id if self.use_worker_wrapper else None,
            )
            process = subprocess.Popen(
                popen_args,
                cwd=str(quest_root),
                env=env,
                text=True,
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                start_new_session=True,
            )
        except OSError as exc:
            stdout_handle.close()
            stderr_handle.close()
            return {
                "runner_kind": "codex_exec",
                "start_mode": "subprocess",
                "command": command,
                "available": True,
                "fail_closed": True,
                "error": f"{type(exc).__name__}: {exc}",
            }
        stdout_handle.close()
        stderr_handle.close()
        _RUNNING_PROCESSES[_process_key(quest_root=quest_root, run_id=run_id)] = process
        return {
            "runner_kind": "codex_exec",
            "start_mode": _start_mode(
                use_worker_wrapper=self.use_worker_wrapper,
                terminal_attach_capable=terminal_attach_capable,
            ),
            "command": command,
            "wrapper_command": wrapper_cmd if self.use_worker_wrapper else None,
            "available": True,
            "live": True,
            "pid": process.pid,
            "monitor_kind": _monitor_kind(
                use_worker_wrapper=self.use_worker_wrapper,
                terminal_attach_capable=terminal_attach_capable,
            ),
            "monitor_pid": process.pid if self.use_worker_wrapper else None,
            "child_pid": None,
            "terminal_attach_capable": terminal_attach_capable,
            "terminal_bridge_status": "enabled" if terminal_attach_capable else "disabled_by_run_capability",
            "terminal_bridge_kind": "mas_controlled_pty" if terminal_attach_capable else None,
            "terminal_input_owner": "mas_terminal_attach_contract" if terminal_attach_capable else None,
            "chat_quest_input_allowed": False,
            "prompt_path": str(prompt_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "terminal_bridge_path": str(_run_root(quest_root=quest_root, run_id=run_id) / "terminal_bridge.json")
            if terminal_attach_capable
            else None,
            "terminal_transcript_path": str(_run_root(quest_root=quest_root, run_id=run_id) / "terminal.log")
            if terminal_attach_capable
            else None,
        }


_RUNNING_PROCESSES: dict[str, subprocess.Popen[str]] = {}


def pop_running_process(*, quest_root: Path, run_id: str) -> subprocess.Popen[str] | None:
    return _RUNNING_PROCESSES.pop(_process_key(quest_root=quest_root, run_id=run_id), None)


def _start_mode(*, use_worker_wrapper: bool, terminal_attach_capable: bool) -> str:
    if terminal_attach_capable and use_worker_wrapper:
        return "terminal_bridge_worker_wrapper_subprocess"
    return "worker_wrapper_subprocess" if use_worker_wrapper else "subprocess"


def _monitor_kind(*, use_worker_wrapper: bool, terminal_attach_capable: bool) -> str:
    if terminal_attach_capable and use_worker_wrapper:
        return "mas_per_run_terminal_bridge_wrapper"
    return "mas_per_run_worker_wrapper" if use_worker_wrapper else "in_process_runner_monitor"


def _run_root(*, quest_root: Path, run_id: str) -> Path:
    return quest_root / ".ds" / "runs" / run_id


def _process_key(*, quest_root: Path, run_id: str) -> str:
    return f"{quest_root.resolve()}::{run_id}"
