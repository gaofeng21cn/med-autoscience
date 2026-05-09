from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import subprocess
from pathlib import Path
from typing import Any, Protocol

from med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper import wrapper_command
from med_autoscience.runtime_transport.mas_runtime_core_worker_wrapper import quest_python_runtime_env
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
        stdout_path = _run_root(quest_root=quest_root, run_id=run_id) / "stdout.jsonl"
        stderr_path = _run_root(quest_root=quest_root, run_id=run_id) / "stderr.txt"
        prompt_path = _run_root(quest_root=quest_root, run_id=run_id) / "prompt.md"
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        runtime_state = _read_runtime_state(quest_root=quest_root)
        prompt_path.write_text(
            _codex_turn_prompt(
                quest_id=quest_id,
                run_id=run_id,
                reason=reason,
                claimed_user_messages=claimed_user_messages,
                runtime_state=runtime_state,
            ),
            encoding="utf-8",
        )
        wrapper_cmd = wrapper_command(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
            prompt_path=prompt_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            codex_binary=self.codex_binary,
        )
        stdout_handle = stdout_path.open("w", encoding="utf-8")
        stderr_handle = stderr_path.open("w", encoding="utf-8")
        try:
            popen_args = wrapper_cmd if self.use_worker_wrapper else [*command, prompt_path.read_text(encoding="utf-8")]
            process = subprocess.Popen(
                popen_args,
                cwd=str(quest_root),
                env=quest_python_runtime_env(quest_root=quest_root),
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
            "start_mode": "worker_wrapper_subprocess" if self.use_worker_wrapper else "subprocess",
            "command": command,
            "wrapper_command": wrapper_cmd if self.use_worker_wrapper else None,
            "available": True,
            "live": True,
            "pid": process.pid,
            "monitor_kind": "mas_per_run_worker_wrapper" if self.use_worker_wrapper else "in_process_runner_monitor",
            "monitor_pid": process.pid if self.use_worker_wrapper else None,
            "child_pid": None,
            "prompt_path": str(prompt_path),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }


_RUNNING_PROCESSES: dict[str, subprocess.Popen[str]] = {}


def pop_running_process(*, quest_root: Path, run_id: str) -> subprocess.Popen[str] | None:
    return _RUNNING_PROCESSES.pop(_process_key(quest_root=quest_root, run_id=run_id), None)


def _codex_turn_prompt(
    *,
    quest_id: str,
    run_id: str,
    reason: str,
    claimed_user_messages: tuple[dict[str, Any], ...],
    runtime_state: Mapping[str, Any] | None = None,
) -> str:
    messages = json.dumps(list(claimed_user_messages), ensure_ascii=False, indent=2, sort_keys=True)
    authorization = _controller_authorization(runtime_state)
    authorization_section = _controller_authorization_prompt_section(authorization=authorization)
    closeout_path = f"artifacts/runtime/turn_closeouts/{run_id}.json"
    return (
        f"You are running a MAS runtime turn for quest `{quest_id}`.\n"
        f"Run id: `{run_id}`.\n"
        f"Turn reason: `{reason}`.\n\n"
        "Read the quest-local runtime files, continue the research workflow according to MAS contracts, "
        "and leave durable artifacts/receipts in the quest workspace. Do not bypass MAS quality gates.\n\n"
        f"{authorization_section}"
        "Turn closeout contract:\n"
        f"- Before ending this turn, write `{closeout_path}`.\n"
        "- The closeout must be valid JSON with this shape:\n"
        "```json\n"
        "{\n"
        '  "schema_version": 1,\n'
        f'  "quest_id": "{quest_id}",\n'
        f'  "run_id": "{run_id}",\n'
        '  "status": "completed",\n'
        '  "completed_at": "<UTC ISO-8601 timestamp>",\n'
        '  "meaningful_artifact_delta": true,\n'
        '  "artifact_refs": ["relative/path/to/new-or-updated-durable-artifact"],\n'
        '  "blocked_reason": null,\n'
        '  "next_owner": null\n'
        "}\n"
        "```\n"
        "- If no safe meaningful artifact delta is possible, write a blocked closeout instead: set "
        '`"status": "blocked"`, `"meaningful_artifact_delta": false`, include a concrete `"blocked_reason"`, '
        'and set `"next_owner"` to the MAS/controller owner that must act next.\n'
        "- Do not exit silently with only console output; MAS treats a successful Codex process without this closeout as incomplete.\n"
        "- Do not mutate paper/current_package, manuscript/current_package, submission_minimal/current_package, "
        "publication gate conclusions, or medical claims unless an explicit MAS controller contract authorizes that surface.\n"
        "- Do not relax MAS quality gates, quality thresholds, publication gates, or authority boundaries.\n\n"
        f"Claimed user messages:\n```json\n{messages}\n```\n"
    )


def _read_runtime_state(*, quest_root: Path) -> dict[str, Any]:
    path = quest_root / ".ds" / "runtime_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _controller_authorization(runtime_state: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping):
        return {}
    for key in ("last_controller_decision_authorization", "current_controller_authorization"):
        value = runtime_state.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _controller_authorization_prompt_section(*, authorization: Mapping[str, Any]) -> str:
    if not authorization:
        return ""
    payload = _compact_controller_authorization(authorization)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        "Active MAS controller work unit:\n"
        "```json\n"
        f"{rendered}\n"
        "```\n"
        "- Treat this controller work unit as the first execution target for this turn.\n"
        "- This Codex process is the MAS managed runtime worker for this run. "
        "`execution_owner_guard.supervisor_only=true` protects foreground/manual agents from taking over a live run; "
        "it does not block this managed runtime worker from executing this controller work unit inside the stated "
        "MAS quality and authority boundaries.\n"
        "- Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this controller work unit. "
        "If another control-plane gate blocks a specific write surface, produce the allowed durable repair artifact "
        "or a blocked closeout that names that non-supervisor gate precisely.\n"
        "- Produce a MAS-authorized durable artifact that addresses `work_unit_id`, `next_work_unit`, and any listed "
        "`specificity_targets`, or write a blocked closeout naming the missing controller/owner surface.\n"
        "- A runtime/watch/health/control-plane receipt alone is not a meaningful artifact delta for this work unit.\n\n"
    )


def _compact_controller_authorization(authorization: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "decision_id",
        "controller_actions",
        "route_target",
        "route_key_question",
        "route_rationale",
        "work_unit_id",
        "work_unit_fingerprint",
        "next_work_unit",
        "blocking_work_units",
        "specificity_targets",
        "work_unit_targets",
        "blocking_artifact_refs",
        "blocker_details",
        "gate_blocker_details",
        "gaps",
        "source_path",
    )
    return {key: authorization[key] for key in keys if key in authorization and authorization[key] not in (None, "", [], {})}


def _run_root(*, quest_root: Path, run_id: str) -> Path:
    return quest_root / ".ds" / "runs" / run_id


def _process_key(*, quest_root: Path, run_id: str) -> str:
    return f"{quest_root.resolve()}::{run_id}"
