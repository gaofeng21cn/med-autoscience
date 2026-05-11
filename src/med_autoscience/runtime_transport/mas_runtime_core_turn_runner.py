from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import subprocess
from pathlib import Path
from typing import Any, Protocol

from med_autoscience.publication_eval_specificity_targets import specificity_target_status
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
_QUALITY_REPAIR_BATCH_WORK_UNIT_IDS = frozenset(
    {
        "analysis_claim_evidence_repair",
        "figure_results_trace_repair",
        "manuscript_story_repair",
        "treatment_gap_reporting_repair",
        "submission_minimal_refresh",
        "submission_delivery_sync_closure",
        "display_reporting_contract_repair",
        "controller_owned_publication_repair",
        "local_architecture_overview_repair",
    }
)
_SPECIFICITY_WORK_UNIT_IDS = frozenset({"gate_needs_specificity", "needs_specificity"})


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
    authorization_section = _controller_authorization_prompt_section(
        authorization=authorization,
        quest_id=quest_id,
    )
    closeout_path = f"artifacts/runtime/turn_closeouts/{run_id}.json"
    return (
        f"You are running a MAS runtime turn for quest `{quest_id}`.\n"
        f"Run id: `{run_id}`.\n"
        f"Turn reason: `{reason}`.\n\n"
        "Read the quest-local runtime files, continue the research workflow according to MAS contracts, "
        "and leave durable artifacts/receipts in the quest workspace. Do not bypass MAS quality gates.\n\n"
        "Runtime worker role:\n"
        "- This Codex process is the MAS managed runtime worker for this run. "
        "`execution_owner_guard.supervisor_only=true` protects foreground/manual agents from taking over a live run; "
        "it does not block this managed runtime worker from executing MAS-authorized quest-local work inside the stated "
        "quality and authority boundaries.\n"
        "- Do not treat `execution_owner_guard.supervisor_only=true` as a reason to skip this runtime turn. "
        "If another control-plane gate blocks a specific write surface, produce the allowed durable repair artifact "
        "or a blocked closeout that names that non-supervisor gate precisely.\n\n"
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


def _controller_authorization_prompt_section(*, authorization: Mapping[str, Any], quest_id: str) -> str:
    if not authorization:
        return ""
    payload = _compact_controller_authorization(authorization)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    controller_action_contract = _controller_action_execution_contract_prompt_section(
        authorization=authorization,
        quest_id=quest_id,
    )
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
        f"{controller_action_contract}"
    )


def _controller_action_execution_contract_prompt_section(
    *,
    authorization: Mapping[str, Any],
    quest_id: str,
) -> str:
    action_names = _controller_action_names(authorization)
    if not action_names:
        return ""
    command_lines = [
        command
        for action_name in action_names
        if (command := _controller_action_command(action_name=action_name, quest_id=quest_id)) is not None
    ]
    if not command_lines:
        return (
            "Controller action execution contract:\n"
            f"- Requested controller actions: {', '.join(action_names)}.\n"
            "- No callable MAS CLI command is registered in this prompt for those action names. Write the turn closeout "
            "with status=blocked, meaningful_artifact_delta=false, blocked_reason=owner_callable_surface_missing, "
            "and next_owner=MAS/controller.\n\n"
        )
    rendered_commands = "\n".join(f"  {command}" for command in command_lines)
    return (
        "Controller action execution contract:\n"
        f"- Controller action names: {', '.join(action_names)}.\n"
        "- Invoke the listed controller command before freeform artifact writing:\n"
        "```bash\n"
        f"{rendered_commands}\n"
        "```\n"
        "- Resolve `<workspace MAS profile>` from `MED_AUTOSCIENCE_PROFILE`, "
        "`ops/medautoscience/profiles/*.workspace.toml`, or `ops/medautoscience/profiles/*.local.toml`; "
        "resolve `<study_id>` from the active authorization, "
        "study runtime status, or quest/study directory identity.\n"
        "- A repair packet, gate audit, controller handoff, runtime/watch receipt, or console-only summary is not "
        "sufficient unless the controller command itself produced the durable paper-facing artifact delta or returned "
        "a concrete owner block.\n"
        "- If the command cannot be resolved or invoked safely, write the blocked closeout with "
        "blocked_reason=owner_callable_surface_missing and next_owner=MAS/controller.\n\n"
    )


def _controller_action_names(authorization: Mapping[str, Any]) -> list[str]:
    raw_actions = authorization.get("controller_actions")
    if isinstance(raw_actions, str):
        actions: list[object] = [raw_actions]
    elif isinstance(raw_actions, (list, tuple)):
        actions = list(raw_actions)
    else:
        actions = []
    names: list[str] = []
    for item in actions:
        if isinstance(item, Mapping):
            raw_name = item.get("action_type") or item.get("action") or item.get("name")
        else:
            raw_name = item
        name = str(raw_name or "").strip()
        if name and name not in names:
            names.append(name)
    if _specificity_targets_ready_for_quality_repair(authorization):
        names = [name for name in names if name != "request_gate_specificity"]
        if "run_quality_repair_batch" not in names:
            names.append("run_quality_repair_batch")
    elif "run_quality_repair_batch" not in names and _quality_repair_work_unit_present(authorization):
        names.append("run_quality_repair_batch")
    return names


def _quality_repair_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    for unit_id in _controller_work_unit_ids(authorization):
        if unit_id in _QUALITY_REPAIR_BATCH_WORK_UNIT_IDS:
            return True
    return False


def _specificity_targets_ready_for_quality_repair(authorization: Mapping[str, Any]) -> bool:
    if not any(unit_id in _SPECIFICITY_WORK_UNIT_IDS for unit_id in _controller_work_unit_ids(authorization)):
        return False
    return specificity_target_status(authorization.get("specificity_targets")).get("complete") is True


def _controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    candidates: list[object] = [
        authorization.get("work_unit_id"),
        authorization.get("next_work_unit"),
        authorization.get("blocking_work_units"),
        authorization.get("work_unit_targets"),
    ]
    unit_ids: list[str] = []

    def append_unit_id(value: object) -> None:
        if isinstance(value, Mapping):
            raw_value = value.get("unit_id") or value.get("work_unit_id") or value.get("id")
        else:
            raw_value = value
        unit_id = str(raw_value or "").strip()
        if unit_id and unit_id not in unit_ids:
            unit_ids.append(unit_id)

    for candidate in candidates:
        if isinstance(candidate, (list, tuple)):
            for item in candidate:
                append_unit_id(item)
        else:
            append_unit_id(candidate)
    return unit_ids


def _controller_action_command(*, action_name: str, quest_id: str) -> str | None:
    if action_name != "run_quality_repair_batch":
        return None
    return (
        '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}" '
        "python -m med_autoscience.cli quality-repair-batch "
        '--profile "${MED_AUTOSCIENCE_PROFILE:-<workspace MAS profile>}" --study-id <study_id> '
        f"--quest-id {quest_id}"
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
