from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_owner_for_action_type,
)
from med_autoscience.profiles import WorkspaceProfile


WORKSPACE_NEXT_ACTION_AUTHORITY = "stage_native_workspace_next_action"
WORKSPACE_NEXT_ACTION_DIAGNOSTIC_AUTHORITY = "stage_native_workspace_next_action_diagnostic_only"
NEXT_ACTION_ADMISSION_POLICY = "requires_canonical_current_work_unit_or_opl_stage_transition_authority_binding"
NEXT_ACTION_AUTHORITY_BINDING_REQUIRED = "stage_native_workspace_next_action_requires_authority_binding"


def stage_native_next_actions(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    if profile is None:
        return []
    actions: list[dict[str, Any]] = []
    for study_id in study_ids:
        action = _stage_native_next_action(profile=profile, study_id=study_id)
        if action is not None:
            actions.append(action)
    return actions


def default_dispatch_allowed(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("authority")) == WORKSPACE_NEXT_ACTION_AUTHORITY
        and action.get("default_dispatch_allowed") is True
    )


def is_diagnostic_action(action: Mapping[str, Any]) -> bool:
    return _text(action.get("authority")) == WORKSPACE_NEXT_ACTION_DIAGNOSTIC_AUTHORITY


def diagnostic_blocked_reason(action: Mapping[str, Any]) -> str:
    return _text(action.get("default_dispatch_blocked_reason")) or NEXT_ACTION_AUTHORITY_BINDING_REQUIRED


def _stage_native_next_action(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    study_root = profile.studies_root / study_id
    next_action = _read_json_mapping(study_root / "control" / "next_action.json")
    if next_action is None:
        return None
    action_type = _text(next_action.get("action_id")) or _text(next_action.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    if _text(next_action.get("status")) != "ready_for_owner_action":
        return None
    owner = _text(next_action.get("owner")) or request_owner_for_action_type(action_type)
    quest_id = _read_quest_id(study_root=study_root, fallback=study_id)
    admission = _stage_native_next_action_admission(next_action)
    current_work_unit_binding = _mapping(next_action.get("current_work_unit_binding"))
    owner_route = _stage_native_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        action_type=action_type,
        owner=owner,
        next_action=next_action,
    )
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"stage-native-next-action::{study_id}::{action_type}",
        "reason": action_type,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": (
            WORKSPACE_NEXT_ACTION_AUTHORITY
            if admission["default_dispatch_allowed"]
            else WORKSPACE_NEXT_ACTION_DIAGNOSTIC_AUTHORITY
        ),
        "default_dispatch_allowed": admission["default_dispatch_allowed"],
        "default_dispatch_blocked_reason": admission["blocked_reason"],
        "stage_native_next_action_admission": admission,
        "required_output_surface": _text(next_action.get("target_surface"))
        or _text(next_action.get("required_output_surface"))
        or "artifacts/reports/medical_publication_surface/latest.json",
        "source_surface": _text(next_action.get("source_surface")),
        "stage_index_ref": _text(next_action.get("stage_index_ref")),
        "current_stage_id": _text(next_action.get("current_stage_id")),
        "current_package_status": _text(next_action.get("current_package_status")),
        "current_work_unit_binding": current_work_unit_binding or None,
        "owner_route": owner_route,
        "handoff_packet": {
            "owner": owner,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "owner_route": owner_route,
            "source_surface": _text(next_action.get("source_surface")),
            "current_work_unit_binding": current_work_unit_binding or None,
            "stage_native_next_action_admission": admission,
        },
    }


def _stage_native_next_action_admission(next_action: Mapping[str, Any]) -> dict[str, Any]:
    authority_boundary = _mapping(next_action.get("stage_transition_authority_boundary"))
    current_work_unit_binding = _mapping(next_action.get("current_work_unit_binding"))
    has_stage_authority_binding = (
        _text(authority_boundary.get("stage_transition_authority"))
        in {"one-person-lab", "OPL Stage Transition Authority"}
        and authority_boundary.get("intent_can_write_stage_current_pointer") is False
        and authority_boundary.get("intent_can_write_stage_run_terminal_state") is False
        and authority_boundary.get("intent_can_publish_current_owner_delta") is False
    )
    has_current_work_unit_binding = (
        _text(current_work_unit_binding.get("source")) == "canonical_current_work_unit"
        and _text(current_work_unit_binding.get("work_unit_id")) is not None
        and _text(current_work_unit_binding.get("work_unit_fingerprint")) is not None
    )
    allowed = has_stage_authority_binding and has_current_work_unit_binding
    return {
        "policy": NEXT_ACTION_ADMISSION_POLICY,
        "default_dispatch_allowed": allowed,
        "blocked_reason": None if allowed else NEXT_ACTION_AUTHORITY_BINDING_REQUIRED,
        "has_stage_transition_authority_boundary": has_stage_authority_binding,
        "has_current_work_unit_binding": has_current_work_unit_binding,
        "stage_run_current_authority": _text(next_action.get("stage_run_current_authority")),
        "source_surface": _text(next_action.get("source_surface")) or "control/next_action.json",
    }


def _stage_native_owner_route(
    *,
    study_id: str,
    quest_id: str,
    action_type: str,
    owner: str,
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    current_stage_id = _text(next_action.get("current_stage_id")) or "unknown_stage"
    source_surface = _text(next_action.get("source_surface")) or "control/next_action.json"
    current_work_unit_binding = _mapping(next_action.get("current_work_unit_binding"))
    has_canonical_work_unit_binding = _text(current_work_unit_binding.get("source")) == "canonical_current_work_unit"
    work_unit_id = (
        _text(current_work_unit_binding.get("work_unit_id")) if has_canonical_work_unit_binding else None
    ) or action_type
    fingerprint = (
        _text(current_work_unit_binding.get("work_unit_fingerprint"))
        if has_canonical_work_unit_binding
        else None
    ) or f"stage-native-next-action::{current_stage_id}::{action_type}::{source_surface}"
    epoch = f"stage-native-next-action::{study_id}::{current_stage_id}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": epoch,
        "runtime_health_epoch": epoch,
        "work_unit_fingerprint": fingerprint,
        "failure_signature": action_type,
        "trace_id": f"owner-route-trace::{study_id}::{action_type}",
        "route_epoch": epoch,
        "source_fingerprint": fingerprint,
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": action_type,
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_surface": source_surface,
            "stage_index_ref": _text(next_action.get("stage_index_ref")),
            "current_stage_id": current_stage_id,
            "current_work_unit_binding": current_work_unit_binding or None,
            "owner_route_currentness_basis": {
                "truth_epoch": epoch,
                "runtime_health_epoch": epoch,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "idempotency_key": f"owner-route::{study_id}::{epoch}::{owner}::{action_type}",
    }


def _read_quest_id(*, study_root: Path, fallback: str) -> str:
    study_yaml = study_root / "study.yaml"
    try:
        for line in study_yaml.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("quest_id:"):
                return line.split(":", 1)[1].strip().strip("'\"") or fallback
    except OSError:
        return fallback
    return fallback


def _read_json_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
