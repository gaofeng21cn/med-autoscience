from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable


def merge_previous_unscanned_study_handoff(
    *,
    previous_payload: Mapping[str, Any] | None,
    scanned_studies: list[dict[str, Any]],
    scanned_action_queue: list[dict[str, Any]],
    retain_unscanned_studies: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not retain_unscanned_studies:
        return scanned_studies, scanned_action_queue
    scanned_ids = {
        study_id
        for study in scanned_studies
        if (study_id := _text(study.get("study_id"))) is not None
    }
    if not scanned_ids:
        return scanned_studies, scanned_action_queue
    previous = _mapping(previous_payload)
    retained_studies = [
        {
            **dict(item),
            "handoff_generated_at": _text(item.get("handoff_generated_at"))
            or _text(previous.get("generated_at"))
            or _text(previous.get("recorded_at")),
            "handoff_scan_status": _text(item.get("handoff_scan_status")) or "retained_from_previous_scan",
        }
        for item in previous.get("studies") or []
        if isinstance(item, Mapping)
        and (study_id := _text(item.get("study_id"))) is not None
        and study_id not in scanned_ids
    ]
    retained_action_queue = [
        dict(item)
        for item in previous.get("action_queue") or []
        if isinstance(item, Mapping)
        and (study_id := _text(item.get("study_id"))) is not None
        and study_id not in scanned_ids
    ]
    return (
        [*retained_studies, *scanned_studies],
        [*retained_action_queue, *scanned_action_queue],
    )


def previous_action_ids(previous_payload: Mapping[str, Any] | None) -> set[str]:
    return {
        action_id
        for action in _mapping(previous_payload).get("action_queue") or []
        if isinstance(action, Mapping)
        and (action_id := _text(action.get("action_id"))) is not None
    }


def scanned_action_queue(studies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"study_id": study["study_id"], **action}
        for study in studies
        for action in study.get("action_queue", [])
        if isinstance(action, Mapping)
    ]


def attach_scan_delta(*, studies: list[dict[str, Any]], previous_action_ids: set[str]) -> None:
    for study in studies:
        study_actions = [
            action
            for action in study.get("action_queue", [])
            if isinstance(action, Mapping) and _text(action.get("action_id")) is not None
        ]
        queue_slo = _mapping(study.get("queue_slo"))
        study["scan_delta"] = {
            "previous_scan_seen": any(_text(action.get("action_id")) in previous_action_ids for action in study_actions),
            "new_action_count": sum(_text(action.get("action_id")) not in previous_action_ids for action in study_actions),
            "owner_pickup_overdue_count": int(queue_slo.get("owner_pickup_overdue_count") or 0),
            "developer_supervisor_attention_required_count": int(
                queue_slo.get("developer_supervisor_attention_required_count") or 0
            ),
        }


def build_scan_domain_routes_payload(
    *,
    schema_version: int,
    generated_at: str,
    workspace_root: Path,
    developer_mode_payload: Mapping[str, Any],
    safe_actions_enabled: bool,
    two_layer_ai_repair_policy: Mapping[str, Any],
    studies: list[dict[str, Any]],
    action_queue: list[dict[str, Any]],
    queue_history: Mapping[str, Any],
    workspace_daemon_lifecycle: Mapping[str, Any],
    provider_readiness: Mapping[str, Any] | None,
    latest_path: Path,
    history_path: Path,
) -> dict[str, Any]:
    readiness = dict(provider_readiness or {})
    return {
        "surface": "opl_current_control_state_handoff",
        "schema_version": schema_version,
        "generated_at": generated_at,
        "workspace_root": str(workspace_root),
        "scheduler_contract": {
            "codex_app_heartbeat_required": False,
            "scheduler_owner": "opl_provider_runtime_manager",
            "default_adapter": "opl_family_runtime_provider",
            "optional_adapters": [],
            "retired_tombstone_adapters": ["hermes_gateway_cron_retired_tombstone"],
            "tick_contract": {
                "command": "opl family-runtime provider-slo tick --provider temporal",
                "cadence_owner": "opl_provider_runtime_manager",
                "resident_daemon": False,
            },
            "retired_workspace_local_schedulers": ["systemd_user", "cron", "launchd"],
            "external_scheduler_role": "opl_provider_runtime_manager_calls_mas_domain_handler_or_domain_tick",
            "developer_supervisor_mode": dict(developer_mode_payload),
        },
        "developer_supervisor_mode": dict(developer_mode_payload),
        "apply_safe_actions": safe_actions_enabled,
        "runtime_apply_boundary": {
            "mas_runtime_handoff_apply_supported": False,
            "runtime_control_owner": "one-person-lab",
            "provider_completion_is_domain_completion": False,
        },
        "two_layer_ai_repair_policy": dict(two_layer_ai_repair_policy),
        "studies": studies,
        "action_queue": action_queue,
        "queue_history": dict(queue_history),
        "workspace_daemon_lifecycle": dict(workspace_daemon_lifecycle),
        "provider_readiness": readiness or None,
        "refs": {"latest_path": str(latest_path), "history_path": str(history_path)},
    }


def persist_scan_domain_routes_payload(
    *,
    payload: dict[str, Any],
    studies: list[dict[str, Any]],
    action_queue: list[dict[str, Any]],
    latest_path: Path,
    history_path: Path,
    generated_at: str,
    resolved_study_ids: tuple[str, ...],
    opl_state_index_source_adapter: Any,
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_json_line: Callable[[Path, Mapping[str, Any]], None],
    text: Callable[[object], str | None],
    mapping: Callable[[object], dict[str, Any]],
) -> None:
    previous_payload = _read_existing_payload(latest_path)
    persistent_payload = merge_persistent_current_control_payload(
        payload=payload,
        previous_payload=previous_payload,
        scanned_study_ids=resolved_study_ids,
    )
    write_json(latest_path, persistent_payload)
    for study in studies:
        owner_route = mapping(study.get("owner_route"))
        if not owner_route:
            continue
        try:
            study["owner_route_authority_ref_index"] = (
                opl_state_index_source_adapter.emit_owner_route_receipt_source(
                    receipt=owner_route,
                    receipt_path=latest_path,
                )
            )
        except (OSError, TypeError, ValueError, RuntimeError):
            continue
    persistent_payload = merge_persistent_current_control_payload(
        payload=payload,
        previous_payload=previous_payload,
        scanned_study_ids=resolved_study_ids,
    )
    write_json(latest_path, persistent_payload)
    append_json_line(
        history_path,
        {
            "generated_at": generated_at,
            "study_ids": list(resolved_study_ids),
            "action_ids": [text(action.get("action_id")) for action in action_queue],
            "latest_action_count": len(action_queue),
        },
    )


def merge_persistent_current_control_payload(
    *,
    payload: Mapping[str, Any],
    previous_payload: Mapping[str, Any] | None,
    scanned_study_ids: tuple[str, ...],
) -> dict[str, Any]:
    merged = dict(payload)
    scanned_ids = {study_id for item in scanned_study_ids if (study_id := _text(item)) is not None}
    if not scanned_ids:
        return merged
    previous = _mapping(previous_payload)
    retained_studies = [
        {
            **dict(item),
            "handoff_generated_at": _text(item.get("handoff_generated_at"))
            or _text(previous.get("generated_at"))
            or _text(previous.get("recorded_at")),
            "handoff_scan_status": _text(item.get("handoff_scan_status")) or "retained_from_previous_scan",
        }
        for item in previous.get("studies") or []
        if isinstance(item, Mapping)
        and (study_id := _text(item.get("study_id"))) is not None
        and study_id not in scanned_ids
    ]
    scanned_studies = [
        dict(item)
        for item in payload.get("studies") or []
        if isinstance(item, Mapping) and _text(item.get("study_id")) in scanned_ids
    ]
    if retained_studies:
        merged["studies"] = [*retained_studies, *scanned_studies]
    retained_actions = [
        dict(item)
        for item in previous.get("action_queue") or []
        if isinstance(item, Mapping)
        and (study_id := _text(item.get("study_id"))) is not None
        and study_id not in scanned_ids
    ]
    scanned_actions = [
        dict(item)
        for item in payload.get("action_queue") or []
        if isinstance(item, Mapping) and _text(item.get("study_id")) in scanned_ids
    ]
    if retained_actions:
        merged["action_queue"] = [*retained_actions, *scanned_actions]
    return merged


def _read_existing_payload(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(value) if isinstance(value, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "build_scan_domain_routes_payload",
    "attach_scan_delta",
    "merge_persistent_current_control_payload",
    "merge_previous_unscanned_study_handoff",
    "persist_scan_domain_routes_payload",
    "previous_action_ids",
    "scanned_action_queue",
]
