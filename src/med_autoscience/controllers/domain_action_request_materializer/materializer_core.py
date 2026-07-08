from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_callable_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_output_surface_for_action_type,
    request_output_target_surface_for_action_type,
    request_owner_for_action_type,
    request_packet_ref_for_action_type,
    request_packet_ref_for_dispatch,
)
from med_autoscience.controllers.paper_mission_owner_surface.domain_route_contract import (
    SUPERVISION_LATEST_RELATIVE_PATH,
)
from med_autoscience.profiles import WorkspaceProfile


CONSUMER_LATEST_RELATIVE_PATH = Path("runtime/artifacts/supervision/consumer/latest.json")
CONSUMER_HISTORY_RELATIVE_PATH = Path("runtime/artifacts/supervision/consumer/history.jsonl")
OWNER_CALLABLE_ADAPTER_RELATIVE_ROOT = Path(
    "artifacts/supervision/consumer/owner_callable_adapters"
)
OWNER_CALLABLE_ADAPTER_KIND = "opl_authorized_owner_callable_adapter"
TARGET_RUNTIME_OWNER = "one-person-lab"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def text(value: object) -> str | None:
    text_value = str(value or "").strip()
    return text_value or None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def nested_mapping(value: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    payload: Mapping[str, Any] = value
    for key in keys:
        payload = mapping(payload.get(key))
    return dict(payload)


def study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def request_packet_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    if action_type not in SUPPORTED_ACTION_TYPES:
        raise ValueError(f"unsupported supervisor request action_type: {action_type}")
    return study_root(profile, study_id) / request_packet_ref_for_action_type(action_type)


def owner_callable_adapter_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    return study_root(profile, study_id) / OWNER_CALLABLE_ADAPTER_RELATIVE_ROOT / f"{action_type}.json"


def scan_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def consumer_history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_HISTORY_RELATIVE_PATH


def current_scan_study(scan_payload: Mapping[str, Any], study_id: str) -> dict[str, Any] | None:
    for study in scan_payload.get("studies") or []:
        payload = mapping(study)
        if text(payload.get("study_id")) == study_id:
            return payload
    return None


def github_block_reason(developer_mode_payload: Mapping[str, Any], *, supported_mode: str) -> str | None:
    if reason := text(developer_mode_payload.get("blocked_reason")):
        return reason
    gate = mapping(developer_mode_payload.get("github_user_gate"))
    if reason := text(gate.get("reason")):
        return reason
    if text(developer_mode_payload.get("mode")) != supported_mode:
        return "developer_apply_safe_required"
    return None


def owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = mapping(action.get("handoff_packet"))
    return (
        text(action.get("owner"))
        or text(action.get("request_owner"))
        or text(action.get("recommended_owner"))
        or text(handoff_packet.get("owner"))
        or text(handoff_packet.get("request_owner"))
        or text(handoff_packet.get("recommended_owner"))
        or request_owner_for_action_type(action_type)
    )


def request_output_surface(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = mapping(action.get("handoff_packet"))
    return (
        text(action.get("required_output_surface"))
        or text(handoff_packet.get("required_output_surface"))
        or request_output_surface_for_action_type(action_type)
    )


def request_output_target_surface(action_type: str) -> dict[str, object] | None:
    return request_output_target_surface_for_action_type(action_type)


def request_packet_ref(action_type: str) -> str:
    return request_packet_ref_for_action_type(action_type)


def request_packet_ref_for_dispatch_action(action_type: str) -> str | None:
    return request_packet_ref_for_dispatch(action_type)


def resolve_study_ids_from_scan(scan_payload: Mapping[str, Any], study_ids: Iterable[str]) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := text(item)) is not None)
    if explicit:
        return explicit
    resolved: list[str] = []
    for action in scan_payload.get("action_queue") or []:
        if isinstance(action, Mapping) and (study_id := text(action.get("study_id"))) is not None:
            resolved.append(study_id)
    for study in scan_payload.get("studies") or []:
        if isinstance(study, Mapping) and (study_id := text(study.get("study_id"))) is not None:
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


__all__ = [
    "CONSUMER_HISTORY_RELATIVE_PATH",
    "CONSUMER_LATEST_RELATIVE_PATH",
    "OWNER_CALLABLE_ADAPTER_KIND",
    "OWNER_CALLABLE_ADAPTER_RELATIVE_ROOT",
    "TARGET_RUNTIME_OWNER",
    "consumer_history_path",
    "consumer_latest_path",
    "current_scan_study",
    "github_block_reason",
    "mapping",
    "nested_mapping",
    "owner_callable_adapter_path",
    "owner_from_action",
    "request_output_surface",
    "request_output_target_surface",
    "request_packet_ref",
    "request_packet_path",
    "request_packet_ref_for_dispatch_action",
    "resolve_study_ids_from_scan",
    "scan_latest_path",
    "study_root",
    "text",
    "utc_now",
]
