from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Protocol

from med_autoscience.controllers import publication_work_unit_lifecycle
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
        runtime_state = _sanitize_runtime_state_before_turn(
            runtime_state=runtime_state,
            quest_root=quest_root,
            quest_id=quest_id,
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
_GATE_CLEARING_BATCH_WORK_UNIT_IDS = frozenset(
    {
        "publication_gate_replay",
        "submission_authority_sync_closure",
        "submission_delivery_sync_closure",
        "submission_minimal_refresh",
    }
)
_RUNTIME_REDRIVE_ACTION_NAMES = frozenset(
    {
        "ensure_study_runtime",
        "ensure_study_runtime_relaunch_stopped",
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
    quest_root: Path | None = None,
) -> str:
    authorization = _controller_authorization(
        runtime_state,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    claimed_user_messages = _claimed_messages_for_prompt(
        claimed_user_messages=claimed_user_messages,
        authorization=authorization,
    )
    messages = json.dumps(list(claimed_user_messages), ensure_ascii=False, indent=2, sort_keys=True)
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


def _claimed_messages_for_prompt(
    *,
    claimed_user_messages: tuple[dict[str, Any], ...],
    authorization: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    if not authorization:
        return claimed_user_messages
    return tuple(message for message in claimed_user_messages if not _controller_authorization_message(message))


def _controller_authorization_message(message: Mapping[str, Any]) -> bool:
    content = str(message.get("content") or "")
    return (
        "MAS controller authorization." in content
        and "artifacts/controller_decisions/latest.json" in content
        and "active MAS authorization for this runtime turn" in content
    )


def _read_runtime_state(*, quest_root: Path) -> dict[str, Any]:
    path = quest_root / ".ds" / "runtime_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_runtime_state(*, quest_root: Path, runtime_state: Mapping[str, Any]) -> None:
    path = quest_root / ".ds" / "runtime_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(runtime_state), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sanitize_runtime_state_before_turn(
    *,
    runtime_state: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping):
        return {}
    sanitized = dict(runtime_state)
    cleared_keys: list[str] = []
    for key in ("last_controller_decision_authorization", "current_controller_authorization"):
        value = sanitized.get(key)
        if not isinstance(value, Mapping):
            continue
        closed = _closed_publication_work_unit_for_authorization(
            authorization=dict(value),
            quest_root=quest_root,
            quest_id=quest_id,
        )
        if closed is None:
            continue
        sanitized.pop(key, None)
        cleared_keys.append(key)
    if not cleared_keys:
        return sanitized
    sanitized["quest_id"] = _text(sanitized.get("quest_id")) or quest_id
    sanitized["continuation_policy"] = "auto"
    sanitized["continuation_anchor"] = "decision"
    sanitized["continuation_reason"] = "closed_controller_work_unit_authorization_cleared"
    sanitized["continuation_updated_at"] = _utc_now()
    sanitized["same_fingerprint_auto_turn_count"] = 0
    sanitized["last_runtime_turn_state_sanitization"] = {
        "reason": "publication_work_unit_lifecycle_done",
        "cleared_keys": cleared_keys,
        "applied_at": _utc_now(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }
    _write_runtime_state(quest_root=quest_root, runtime_state=sanitized)
    return sanitized


def _controller_authorization(
    runtime_state: Mapping[str, Any] | None,
    *,
    quest_root: Path | None = None,
    quest_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(runtime_state, Mapping):
        return {}
    for key in ("last_controller_decision_authorization", "current_controller_authorization"):
        value = runtime_state.get(key)
        if isinstance(value, Mapping):
            authorization = dict(value)
            if _closed_publication_work_unit_for_authorization(
                authorization=authorization,
                quest_root=quest_root,
                quest_id=quest_id,
            ) is not None:
                return {}
            return authorization
    return {}


def _closed_publication_work_unit_for_authorization(
    *,
    authorization: Mapping[str, Any],
    quest_root: Path | None,
    quest_id: str | None,
) -> dict[str, Any] | None:
    if quest_root is None:
        return None
    study_root = _resolve_study_root_from_quest_root_light(quest_root=Path(quest_root), quest_id=quest_id)
    if study_root is None:
        return None
    lifecycle_path = publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
        study_root=study_root,
    )
    try:
        payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    if not publication_work_unit_lifecycle.lifecycle_payload_is_closed(dict(payload)):
        return None
    source_eval_id = _text(payload.get("source_eval_id"))
    authorization_eval_id = _authorization_publication_eval_id(
        authorization=authorization,
        study_root=study_root,
    )
    if source_eval_id is None or authorization_eval_id is None or source_eval_id != authorization_eval_id:
        return None
    lifecycle_work_unit = _mapping(payload.get("work_unit"))
    lifecycle_work_unit_id = _text(lifecycle_work_unit.get("unit_id"))
    authorization_work_unit_ids = set(_controller_work_unit_ids(authorization))
    if lifecycle_work_unit_id is None or lifecycle_work_unit_id not in authorization_work_unit_ids:
        return None
    return {
        "reason": "publication_work_unit_lifecycle_done",
        "source_eval_id": source_eval_id,
        "work_unit_id": lifecycle_work_unit_id,
        "lifecycle_path": str(lifecycle_path),
    }


def _authorization_publication_eval_id(
    *,
    authorization: Mapping[str, Any],
    study_root: Path,
) -> str | None:
    direct_eval_id = _text(
        authorization.get("publication_eval_id")
        or authorization.get("source_eval_id")
        or _mapping(authorization.get("publication_eval_ref")).get("eval_id")
    )
    if direct_eval_id is not None:
        return direct_eval_id
    decision = _read_json_mapping(study_root / "artifacts" / "controller_decisions" / "latest.json")
    if not _authorization_matches_controller_decision(authorization=authorization, decision=decision):
        return None
    return _text(
        decision.get("publication_eval_id")
        or decision.get("source_eval_id")
        or _mapping(decision.get("publication_eval_ref")).get("eval_id")
    )


def _authorization_matches_controller_decision(
    *,
    authorization: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> bool:
    if not decision:
        return False
    authorization_decision_id = _text(authorization.get("decision_id"))
    decision_id = _text(decision.get("decision_id"))
    if authorization_decision_id is not None and decision_id is not None:
        return authorization_decision_id == decision_id
    authorization_work_units = set(_controller_work_unit_ids(authorization))
    decision_work_units = set(_controller_work_unit_ids(decision))
    if not authorization_work_units or not authorization_work_units.intersection(decision_work_units):
        return False
    authorization_fingerprint = _text(authorization.get("work_unit_fingerprint"))
    decision_fingerprint = _text(decision.get("work_unit_fingerprint"))
    return (
        authorization_fingerprint is None
        or decision_fingerprint is None
        or authorization_fingerprint == decision_fingerprint
    )


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _resolve_study_root_from_quest_root_light(*, quest_root: Path, quest_id: str | None) -> Path | None:
    resolved = Path(quest_root).expanduser().resolve()
    if resolved.parent.name != "quests" or resolved.parent.parent.name != "runtime":
        return None
    if len(resolved.parents) >= 3 and resolved.parents[2].name != "ops":
        workspace_root = resolved.parents[2]
    elif len(resolved.parents) >= 5 and resolved.parents[3].name == "ops":
        workspace_root = resolved.parents[4]
    else:
        return None
    quest_name = _text(quest_id) or resolved.name
    candidate_ids = [quest_name]
    declared_study_id = _declared_study_id_from_quest_yaml(resolved / "quest.yaml")
    if declared_study_id is not None and declared_study_id not in candidate_ids:
        candidate_ids.insert(0, declared_study_id)
    studies_root = workspace_root / "studies"
    for study_id in candidate_ids:
        candidate = (studies_root / study_id).resolve()
        if (candidate / "study.yaml").exists():
            return candidate
    if not studies_root.exists():
        return None
    for binding_path in sorted(studies_root.glob("*/runtime_binding.yaml")):
        binding_text = _yaml_string_field(binding_path, "quest_id")
        if binding_text != quest_name:
            continue
        candidate = binding_path.parent.resolve()
        if (candidate / "study.yaml").exists():
            return candidate
    return None


def _declared_study_id_from_quest_yaml(path: Path) -> str | None:
    return _yaml_string_field(path, "study_id")


def _yaml_string_field(path: Path, field_name: str) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    prefix = f"{field_name}:"
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        value = stripped[len(prefix) :].strip().strip("\"'")
        return value or None
    return None


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
        "- MAS-managed analysis-campaign/write controller work units may revise canonical `paper/` surfaces needed by "
        "the listed `work_unit_id`, `next_work_unit`, and `specificity_targets`. "
        "Foreground/manual takeover remains barred by `execution_owner_guard.supervisor_only=true`; this allowance applies "
        "only to this managed runtime worker through the active MAS controller work unit.\n"
        "- publication gate `allow_write=false` blocks generated package/submission writes such as `current_package`, "
        "`submission_minimal`, bundle builds, and submission proofing. It does not by itself block controller-authorized "
        "canonical `paper/` revisions for upstream analysis-campaign/write work units.\n"
        "- Produce a MAS-authorized durable artifact that addresses `work_unit_id`, `next_work_unit`, and any listed "
        "`specificity_targets`, or write a blocked closeout naming the missing controller/owner surface.\n"
        "- A runtime/watch/health/control-plane receipt alone is not a meaningful artifact delta for this work unit.\n\n"
        f"{controller_action_contract}"
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


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
    elif (
        not _controller_callable_action_present(names)
        and _runtime_redrive_action_present(names)
        and _gate_clearing_work_unit_present(authorization)
    ):
        names.append("run_gate_clearing_batch")
    elif "run_quality_repair_batch" not in names and _quality_repair_work_unit_present(authorization):
        names.append("run_quality_repair_batch")
    elif not _controller_callable_action_present(names) and _gate_clearing_work_unit_present(authorization):
        names.append("run_gate_clearing_batch")
    return names


def _controller_callable_action_present(action_names: list[str]) -> bool:
    return any(name in {"run_quality_repair_batch", "run_gate_clearing_batch"} for name in action_names)


def _runtime_redrive_action_present(action_names: list[str]) -> bool:
    return any(name in _RUNTIME_REDRIVE_ACTION_NAMES for name in action_names)


def _quality_repair_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    for unit_id in _controller_work_unit_ids(authorization):
        if unit_id in _QUALITY_REPAIR_BATCH_WORK_UNIT_IDS:
            return True
    return False


def _gate_clearing_work_unit_present(authorization: Mapping[str, Any]) -> bool:
    for unit_id in _primary_controller_work_unit_ids(authorization):
        if unit_id in _GATE_CLEARING_BATCH_WORK_UNIT_IDS:
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


def _primary_controller_work_unit_ids(authorization: Mapping[str, Any]) -> list[str]:
    candidates: list[object] = [
        authorization.get("work_unit_id"),
        authorization.get("next_work_unit"),
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
        append_unit_id(candidate)
    return unit_ids


def _controller_action_command(*, action_name: str, quest_id: str) -> str | None:
    command_by_action = {
        "run_quality_repair_batch": "quality-repair-batch",
        "run_gate_clearing_batch": "gate-clearing-batch",
    }
    command_name = command_by_action.get(action_name)
    if command_name is None:
        return None
    return (
        '"${MED_AUTOSCIENCE_UV_BIN:-uv}" run --directory "${MED_AUTOSCIENCE_REPO}" '
        f"python -m med_autoscience.cli {command_name} "
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
