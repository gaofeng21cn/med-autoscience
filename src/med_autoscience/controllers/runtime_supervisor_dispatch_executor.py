from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile

from . import publication_gate, study_runtime_router
from .runtime_supervisor_consumer import (
    DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT,
    FORBIDDEN_SURFACES,
    SUPPORTED_MODE,
)


SCHEMA_VERSION = 1
EXECUTION_RELATIVE_ROOT = Path("artifacts/supervision/consumer/default_executor_execution")
EXECUTION_LATEST_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "latest.json"
EXECUTION_HISTORY_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "history.jsonl"
SUPPORTED_ACTION_TYPES = frozenset(
    {
        "runtime_platform_repair",
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _dispatch_dir(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT


def _execution_latest_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / EXECUTION_LATEST_RELATIVE_PATH


def _execution_history_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / EXECUTION_HISTORY_RELATIVE_PATH


def _dispatch_files(profile: WorkspaceProfile, study_id: str, action_types: tuple[str, ...]) -> list[Path]:
    root = _dispatch_dir(profile, study_id)
    if not root.is_dir():
        return []
    if action_types:
        return [root / f"{action_type}.json" for action_type in action_types if (root / f"{action_type}.json").is_file()]
    return sorted(root.glob("*.json"), key=lambda item: item.name)


def _resolve_study_ids(profile: WorkspaceProfile, study_ids: Iterable[str]) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    if explicit:
        return explicit
    if not profile.studies_root.is_dir():
        return ()
    resolved: list[str] = []
    for dispatch_dir in sorted(
        profile.studies_root.glob(f"*/{DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT.as_posix()}"),
        key=lambda item: item.as_posix(),
    ):
        try:
            study_id = dispatch_dir.relative_to(profile.studies_root).parts[0]
        except (ValueError, IndexError):
            continue
        if any(dispatch_dir.glob("*.json")):
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


def _github_block_reason(developer_mode_payload: Mapping[str, Any]) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE:
        return "developer_apply_safe_required"
    return None


def _contract_guard(dispatch: Mapping[str, Any]) -> tuple[bool, str | None]:
    if _text(dispatch.get("surface")) != "default_executor_dispatch_request":
        return False, "unsupported_dispatch_surface"
    if _text(dispatch.get("dispatch_status")) != "ready":
        return False, "dispatch_not_ready"
    if _text(dispatch.get("executor_kind")) != "codex_cli_default":
        return False, "unsupported_executor_kind"
    if dispatch.get("chat_completion_only_executor_forbidden") is not True:
        return False, "chat_completion_only_guard_missing"
    action_type = _text(dispatch.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return False, "unsupported_action_type"
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if not prompt_contract:
        return False, "prompt_contract_missing"
    for key in (
        "paper_package_mutation_allowed",
        "quality_gate_relaxation_allowed",
        "manual_study_patch_allowed",
        "medical_claim_authoring_allowed",
    ):
        if prompt_contract.get(key) is not False:
            return False, f"{key}_guard_missing"
    forbidden = {
        text
        for item in prompt_contract.get("forbidden_surfaces") or []
        if (text := _text(item)) is not None
    }
    if not set(FORBIDDEN_SURFACES).issubset(forbidden):
        return False, "forbidden_surfaces_incomplete"
    return True, None


def _quest_root_from_status(profile: WorkspaceProfile, study_id: str) -> Path | None:
    try:
        status = study_runtime_router.study_runtime_status(profile=profile, study_id=study_id, study_root=None, entry_mode=None)
    except Exception:
        return None
    status_payload = dict(status) if isinstance(status, Mapping) else status.to_dict()
    quest_root = _text(status_payload.get("quest_root"))
    return Path(quest_root).expanduser().resolve() if quest_root is not None else None


def _execute_publication_gate_specificity(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    quest_root = _quest_root_from_status(profile, study_id)
    if quest_root is None:
        return {"execution_status": "blocked", "blocked_reason": "quest_root_missing", "owner_callable_surface": None}
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "publication_gate.run_controller",
            "quest_root": str(quest_root),
        }
    state = publication_gate.build_gate_state(quest_root)
    report = publication_gate.build_gate_report(state)
    json_path, _ = publication_gate.write_gate_files(quest_root, report)
    materialized = publication_gate._materialize_publication_eval_latest(
        state=state,
        report={
            **report,
            "latest_gate_path": str(json_path),
        },
    )
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "publication_gate.write_gate_files+_materialize_publication_eval_latest",
        "quest_root": str(quest_root),
        "owner_result": {
            "report_json": str(json_path),
            "status": report.get("status"),
            "blockers": list(report.get("blockers") or []),
            "publication_eval": materialized,
        },
    }


def _execute_runtime_platform_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "runtime supervisor-scan --apply-runtime-platform-repair",
        }
    from . import runtime_supervisor_scan

    result = runtime_supervisor_scan.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode=SUPPORTED_MODE,
    )
    study_payload = next(
        (study for study in result.get("studies", []) if isinstance(study, Mapping) and _text(study.get("study_id")) == study_id),
        {},
    )
    apply_result = _mapping(study_payload.get("runtime_platform_repair_apply"))
    executed = _text(apply_result.get("dispatch_status")) == "applied"
    return {
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else _text(apply_result.get("reason")) or "runtime_platform_repair_not_applied",
        "owner_callable_surface": "runtime_supervisor_scan.supervisor_scan(apply_runtime_platform_repair=True)",
        "owner_result": apply_result or result,
    }


def _execute_ai_reviewer_workflow(*, apply: bool) -> dict[str, Any]:
    return {
        "execution_status": "blocked" if apply else "dry_run",
        "blocked_reason": "owner_callable_surface_missing",
        "owner_callable_surface": None,
        "next_owner": "repo_platform",
        "required_repo_surface": "structured_ai_reviewer_default_executor_workflow",
        "authority_note": "Default executor cannot synthesize AI reviewer-owned publication_eval without a structured reviewer record.",
    }


def _execute_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch_path: Path,
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    dispatch = _read_json_object(dispatch_path)
    if dispatch is None:
        return {
            "generated_at": generated_at,
            "study_id": study_id,
            "dispatch_path": str(dispatch_path),
            "execution_status": "blocked",
            "blocked_reason": "dispatch_payload_missing_or_invalid",
        }
    action_type = _text(dispatch.get("action_type")) or "unknown_action"
    guard_ok, guard_reason = _contract_guard(dispatch)
    if not guard_ok:
        execution = {
            "execution_status": "blocked",
            "blocked_reason": guard_reason,
            "owner_callable_surface": None,
        }
    elif apply and (
        _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE
        or developer_mode_payload.get("safe_actions_enabled") is not True
    ):
        execution = {
            "execution_status": "blocked",
            "blocked_reason": _github_block_reason(developer_mode_payload) or "developer_apply_safe_required",
            "owner_callable_surface": None,
        }
    elif action_type == "publication_gate_specificity_required":
        execution = _execute_publication_gate_specificity(profile=profile, study_id=study_id, apply=apply)
    elif action_type == "runtime_platform_repair":
        execution = _execute_runtime_platform_repair(profile=profile, study_id=study_id, apply=apply)
    elif action_type == "return_to_ai_reviewer_workflow":
        execution = _execute_ai_reviewer_workflow(apply=apply)
    else:
        execution = {
            "execution_status": "blocked",
            "blocked_reason": "unsupported_action_type",
            "owner_callable_surface": None,
        }
    return {
        "surface": "default_executor_dispatch_execution",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")),
        "action_type": action_type,
        "action_id": _text(dispatch.get("action_id")),
        "next_executable_owner": _text(dispatch.get("next_executable_owner")),
        "required_output_surface": _text(dispatch.get("required_output_surface")),
        "dispatch_path": str(dispatch_path),
        "dispatch_contract_valid": guard_ok,
        "dispatch_contract_blocked_reason": guard_reason,
        "dry_run": not apply,
        "developer_supervisor_mode": dict(developer_mode_payload),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        **execution,
    }


def execute_default_executor_dispatches(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    action_types: Iterable[str] = (),
) -> dict[str, Any]:
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="default_executor_dispatch_executor",
    )
    developer_mode_payload = developer_mode.to_dict()
    resolved_study_ids = _resolve_study_ids(profile, study_ids)
    resolved_action_types = tuple(action_type for item in action_types if (action_type := _text(item)) is not None)
    executions: list[dict[str, Any]] = []
    written_files: list[str] = []
    for study_id in resolved_study_ids:
        for dispatch_path in _dispatch_files(profile, study_id, resolved_action_types):
            execution = _execute_dispatch(
                profile=profile,
                study_id=study_id,
                dispatch_path=dispatch_path,
                developer_mode_payload=developer_mode_payload,
                apply=apply,
            )
            executions.append(execution)
        study_executions = [execution for execution in executions if execution["study_id"] == study_id]
        if apply and study_executions:
            latest_path = _execution_latest_path(profile, study_id)
            history_path = _execution_history_path(profile, study_id)
            study_payload = {
                "surface": "default_executor_dispatch_execution_study_latest",
                "schema_version": SCHEMA_VERSION,
                "generated_at": generated_at,
                "study_id": study_id,
                "executions": study_executions,
                "executed_count": sum(item.get("execution_status") == "executed" for item in study_executions),
                "blocked_count": sum(item.get("execution_status") == "blocked" for item in study_executions),
                "dry_run": False,
            }
            _write_json(latest_path, study_payload)
            _append_json_line(
                history_path,
                {
                    "generated_at": generated_at,
                    "study_id": study_id,
                    "execution_statuses": [item.get("execution_status") for item in study_executions],
                    "blocked_reasons": [item.get("blocked_reason") for item in study_executions if item.get("blocked_reason")],
                },
            )
            written_files.append(str(latest_path))
            written_files.append(str(history_path))
    payload = {
        "surface": "default_executor_dispatch_executor",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "requested_studies": list(resolved_study_ids),
        "requested_action_types": list(resolved_action_types),
        "execution_count": len(executions),
        "executed_count": sum(item.get("execution_status") == "executed" for item in executions),
        "blocked_count": sum(item.get("execution_status") == "blocked" for item in executions),
        "dry_run_count": sum(item.get("execution_status") == "dry_run" for item in executions),
        "executions": executions,
        "written_files": written_files,
    }
    return payload


__all__ = [
    "EXECUTION_LATEST_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "SUPPORTED_ACTION_TYPES",
    "execute_default_executor_dispatches",
]
