from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan import SUPERVISION_LATEST_RELATIVE_PATH
from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
CONSUMER_LATEST_RELATIVE_PATH = Path("artifacts/supervision/consumer/latest.json")
CONSUMER_HISTORY_RELATIVE_PATH = Path("artifacts/supervision/consumer/history.jsonl")
RUNTIME_PLATFORM_REPAIR_PACKET_RELATIVE_PATH = Path(
    "artifacts/supervision/consumer/runtime_platform_repair.json"
)
SUPPORTED_ACTION_TYPE = "runtime_platform_repair"
SUPPORTED_REQUEST_ACTION_TYPES = frozenset(
    {
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    }
)
SUPPORTED_MODE = "developer_apply_safe"
BRANCH_NAME = "codex/mas-supervisor-queue-consumer"
OWNED_FILES = [
    "src/med_autoscience/cli.py",
    "src/med_autoscience/cli_parts/parser.py",
    "src/med_autoscience/cli_public_surface.py",
    "src/med_autoscience/controllers/runtime_supervisor_consumer.py",
    "tests/test_cli.py",
    "tests/test_cli_cases/runtime_supervisor_consume_command.py",
    "tests/test_runtime_supervisor_consumer.py",
]
VERIFICATION_COMMANDS = [
    "uv run pytest tests/test_runtime_supervisor_consumer.py tests/test_cli_cases/runtime_supervisor_consume_command.py -q",
    "uv run pytest tests/test_cli.py::test_runtime_supervisor_consume_command_dispatches_controller tests/test_runtime_supervisor_consumer.py -q",
    "git diff --check",
]
FORBIDDEN_SURFACES = [
    "paper/**",
    "manuscript/**",
    "current_package/**",
    "paper/current_package/**",
    "manuscript/current_package/**",
    "src/med_autoscience/platform/**",
]
ALLOWED_WRITE_SURFACES = [
    "artifacts/supervision/consumer/latest.json",
    "artifacts/supervision/consumer/history.jsonl",
    "studies/<study_id>/artifacts/supervision/consumer/runtime_platform_repair.json",
    "studies/<study_id>/artifacts/supervision/consumer/publication_gate_specificity_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/return_to_ai_reviewer_workflow.json",
]
MERGE_CLEANUP_CHECKLIST = [
    "focused pytest green",
    "git diff --check green",
    "review diff touches only owned files",
    "merge branch into main after parallel worker coordination",
    "remove worktree after absorb",
]


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


def _packet_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return _study_root(profile, study_id) / RUNTIME_PLATFORM_REPAIR_PACKET_RELATIVE_PATH


def _request_packet_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    if action_type not in SUPPORTED_REQUEST_ACTION_TYPES:
        raise ValueError(f"unsupported supervisor request action_type: {action_type}")
    return _study_root(profile, study_id) / "artifacts" / "supervision" / "consumer" / f"{action_type}.json"


def _scan_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def _consumer_history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_HISTORY_RELATIVE_PATH


def _github_block_reason(developer_mode_payload: Mapping[str, Any]) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE:
        return "developer_apply_safe_required"
    return None


def _repair_task(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    handoff_packet = _mapping(action.get("handoff_packet"))
    packet_path = _packet_path(profile, study_id)
    apply_allowed = (
        apply
        and _text(developer_mode_payload.get("mode")) == SUPPORTED_MODE
        and developer_mode_payload.get("safe_actions_enabled") is True
    )
    blocked_reason = None if apply_allowed or not apply else _github_block_reason(developer_mode_payload)
    dispatch_status = "applied" if apply_allowed else "dry_run" if not apply else "blocked"
    return {
        "surface": "runtime_platform_repair_task",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
        "action_type": SUPPORTED_ACTION_TYPE,
        "action_id": _text(action.get("action_id")),
        "reason": _text(action.get("reason")) or _text(handoff_packet.get("reason")),
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "dry_run": not apply,
        "branch_name": BRANCH_NAME,
        "owned_files": list(OWNED_FILES),
        "verification_commands": list(VERIFICATION_COMMANDS),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "merge_cleanup_checklist": list(MERGE_CLEANUP_CHECKLIST),
        "github_gate": dict(_mapping(developer_mode_payload.get("github_user_gate"))),
        "effective_mode": _text(developer_mode_payload.get("mode")),
        "requested_mode": _text(developer_mode_payload.get("requested_mode")),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "platform_code_mutation_allowed": False,
        "source_action": dict(action),
        "handoff_packet": {
            **handoff_packet,
            "surface": "runtime_platform_repair_handoff_packet",
            "action_type": SUPPORTED_ACTION_TYPE,
            "branch_name": BRANCH_NAME,
            "owned_files": list(OWNED_FILES),
            "verification_commands": list(VERIFICATION_COMMANDS),
            "forbidden_surfaces": list(FORBIDDEN_SURFACES),
            "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
            "github_gate": dict(_mapping(developer_mode_payload.get("github_user_gate"))),
            "effective_mode": _text(developer_mode_payload.get("mode")),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "platform_code_mutation_allowed": False,
        },
        "refs": {
            "scan_latest": str(_scan_latest_path(profile)),
            "repair_packet_path": str(packet_path),
        },
    }


def _request_owner_for_action_type(action_type: str) -> str:
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    return "controller"


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _request_owner_for_action_type(action_type)
    )


def _request_output_surface_for_action_type(action_type: str) -> str:
    if action_type == "publication_gate_specificity_required":
        return "artifacts/publication_eval/latest.json"
    if action_type == "return_to_ai_reviewer_workflow":
        return "artifacts/publication_eval/latest.json"
    return "artifacts/supervision/requests"


def _request_packet_ref_for_action_type(action_type: str) -> str:
    if action_type == "publication_gate_specificity_required":
        return "artifacts/supervision/requests/publication_gate_specificity/latest.json"
    if action_type == "return_to_ai_reviewer_workflow":
        return "artifacts/supervision/requests/ai_reviewer/latest.json"
    return "artifacts/supervision/requests"


def _request_task(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    action_type = _text(action.get("action_type")) or "unknown_action"
    handoff_packet = _mapping(action.get("handoff_packet"))
    packet_path = _request_packet_path(profile, study_id, action_type)
    apply_allowed = (
        apply
        and _text(developer_mode_payload.get("mode")) == SUPPORTED_MODE
        and developer_mode_payload.get("safe_actions_enabled") is True
    )
    blocked_reason = None if apply_allowed or not apply else _github_block_reason(developer_mode_payload)
    dispatch_status = "applied" if apply_allowed else "dry_run" if not apply else "blocked"
    authority = _text(action.get("authority")) or _text(handoff_packet.get("authority")) or "observability_only"
    request_owner = _owner_from_action(action, action_type)
    required_output_surface = (
        _text(action.get("required_output_surface"))
        or _text(handoff_packet.get("required_output_surface"))
        or _request_output_surface_for_action_type(action_type)
    )
    request_packet_ref = _request_packet_ref_for_action_type(action_type)
    owner_pickup = {
        "owner": request_owner,
        "state": "pending",
        "required_output_surface": required_output_surface,
        "request_packet_ref": request_packet_ref,
        "supervisor_authority_boundary": "request_only",
    }
    return {
        "surface": "supervisor_request_handoff_task",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
        "action_type": action_type,
        "action_id": _text(action.get("action_id")),
        "reason": _text(action.get("reason")) or _text(handoff_packet.get("reason")),
        "authority": authority,
        "request_owner": request_owner,
        "expected_owner": request_owner,
        "next_executable_owner": request_owner,
        "required_output_surface": required_output_surface,
        "request_packet_ref": request_packet_ref,
        "owner_pickup": owner_pickup,
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "dry_run": not apply,
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "github_gate": dict(_mapping(developer_mode_payload.get("github_user_gate"))),
        "effective_mode": _text(developer_mode_payload.get("mode")),
        "requested_mode": _text(developer_mode_payload.get("requested_mode")),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "platform_code_mutation_allowed": False,
        "source_action": dict(action),
        "handoff_packet": {
            **handoff_packet,
            "surface": "supervisor_request_handoff_packet",
            "schema_version": SCHEMA_VERSION,
            "study_id": study_id,
            "quest_id": _text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
            "request_kind": _text(handoff_packet.get("request_kind")) or action_type,
            "action_type": action_type,
            "authority": authority,
            "request_owner": request_owner,
            "expected_owner": request_owner,
            "next_executable_owner": request_owner,
            "required_output_surface": required_output_surface,
            "request_packet_ref": request_packet_ref,
            "owner_pickup": owner_pickup,
            "supervisor_authority_boundary": "request_only",
            "consumer_mutation_scope": "supervision_handoff_only",
            "consumer_does_not_mutate": [
                "paper",
                "manuscript",
                "current_package",
                "submission_minimal",
                "publication_eval",
                "medical_claims",
            ],
            "effective_mode": _text(developer_mode_payload.get("mode")),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "platform_code_mutation_allowed": False,
        },
        "refs": {
            "scan_latest": str(_scan_latest_path(profile)),
            "request_packet_path": str(packet_path),
        },
    }


def _ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "study_id": _text(action.get("study_id")),
        "action_type": _text(action.get("action_type")),
        "action_id": _text(action.get("action_id")),
        "reason": reason,
    }


def _selected_actions(
    *,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    request_selected: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    allowed_studies = set(study_ids)
    actions = scan_payload.get("action_queue")
    if not isinstance(actions, list):
        return selected, request_selected, ignored
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        study_id = _text(action.get("study_id"))
        if study_id not in allowed_studies:
            ignored.append(_ignored_action(action, "study_not_requested"))
            continue
        action_type = _text(action.get("action_type"))
        if action_type == SUPPORTED_ACTION_TYPE:
            selected.append(dict(action))
            continue
        if action_type in SUPPORTED_REQUEST_ACTION_TYPES:
            request_selected.append(dict(action))
            continue
        else:
            ignored.append(_ignored_action(action, "unsupported_action_type"))
            continue
    return selected, request_selected, ignored


def supervisor_consume(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
) -> dict[str, Any]:
    resolved_study_ids = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="external_queue_consumer",
    )
    developer_mode_payload = developer_mode.to_dict()
    scan_payload = _read_json_object(_scan_latest_path(profile)) or {}
    selected_actions, selected_request_actions, ignored_actions = _selected_actions(
        scan_payload=scan_payload,
        study_ids=resolved_study_ids,
    )
    repair_tasks = [
        _repair_task(
            profile=profile,
            action=action,
            developer_mode_payload=developer_mode_payload,
            apply=apply,
        )
        for action in selected_actions
    ]
    request_tasks = [
        _request_task(
            profile=profile,
            action=action,
            developer_mode_payload=developer_mode_payload,
            apply=apply,
        )
        for action in selected_request_actions
    ]
    written_files: list[str] = []
    if apply and developer_mode.safe_actions_enabled:
        for task in repair_tasks:
            if _text(task.get("dispatch_status")) != "applied":
                continue
            packet_path = Path(_mapping(task.get("refs")).get("repair_packet_path"))
            packet = _mapping(task.get("handoff_packet"))
            _write_json(packet_path, packet)
            written_files.append(str(packet_path))
        for task in request_tasks:
            if _text(task.get("dispatch_status")) != "applied":
                continue
            packet_path = Path(_mapping(task.get("refs")).get("request_packet_path"))
            packet = _mapping(task.get("handoff_packet"))
            _write_json(packet_path, packet)
            written_files.append(str(packet_path))

    payload = {
        "surface": "runtime_supervisor_consumer",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "source_surface": str(_scan_latest_path(profile)),
        "dry_run": not apply,
        "requested_studies": list(resolved_study_ids),
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "github_gate": dict(developer_mode.github_user_gate),
        "developer_supervisor_mode": developer_mode_payload,
        "apply_allowed": bool(apply and developer_mode.safe_actions_enabled),
        "repair_task_count": len(repair_tasks),
        "repair_tasks": repair_tasks,
        "request_task_count": len(request_tasks),
        "request_tasks": request_tasks,
        "ignored_actions": ignored_actions,
        "branch_name": BRANCH_NAME,
        "owned_files": list(OWNED_FILES),
        "verification_commands": list(VERIFICATION_COMMANDS),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "merge_cleanup_checklist": list(MERGE_CLEANUP_CHECKLIST),
        "written_files": written_files,
        "refs": {
            "latest_path": str(_consumer_latest_path(profile)),
            "history_path": str(_consumer_history_path(profile)),
        },
    }
    if apply and developer_mode.safe_actions_enabled and (repair_tasks or request_tasks):
        written_files.append(str(_consumer_latest_path(profile)))
        payload["written_files"] = written_files
        _write_json(_consumer_latest_path(profile), payload)
        _append_json_line(
            _consumer_history_path(profile),
            {
                "generated_at": generated_at,
                "study_ids": list(resolved_study_ids),
                "repair_task_count": len(repair_tasks),
                "request_task_count": len(request_tasks),
                "written_files": list(written_files),
                "effective_mode": developer_mode.mode,
            },
        )
    return payload


__all__ = [
    "BRANCH_NAME",
    "CONSUMER_LATEST_RELATIVE_PATH",
    "FORBIDDEN_SURFACES",
    "OWNED_FILES",
    "SCHEMA_VERSION",
    "SUPPORTED_REQUEST_ACTION_TYPES",
    "VERIFICATION_COMMANDS",
    "supervisor_consume",
]
