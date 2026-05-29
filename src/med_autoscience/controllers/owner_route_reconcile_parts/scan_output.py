from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable


def merge_previous_unscanned_study_handoff(
    *,
    previous_payload: Mapping[str, Any] | None,
    scanned_studies: list[dict[str, Any]],
    scanned_action_queue: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
    current_execution_envelopes: Mapping[str, Any],
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
                "domain_diagnostic_command": "ops/medautoscience/bin/domain-health-diagnostic",
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
        "current_execution_envelopes": dict(current_execution_envelopes),
        "current_execution_evidence": {
            "action_queue": action_queue,
        },
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
    profile: Any,
    latest_path: Path,
    history_path: Path,
    generated_at: str,
    resolved_study_ids: tuple[str, ...],
    domain_authority_refs_index: Any,
    study_root_for_id: Callable[[str], Path],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_json_line: Callable[[Path, Mapping[str, Any]], None],
    text: Callable[[object], str | None],
    mapping: Callable[[object], dict[str, Any]],
) -> None:
    write_json(latest_path, payload)
    for study in studies:
        owner_route = mapping(study.get("owner_route"))
        if not owner_route:
            continue
        try:
            study_root = Path(text(study.get("study_root")) or study_root_for_id(text(study.get("study_id")) or ""))
            study["owner_route_authority_ref_index"] = domain_authority_refs_index.record_owner_route_receipt(
                study_root=study_root,
                receipt=owner_route,
                receipt_path=latest_path,
            )
        except (OSError, TypeError, ValueError, RuntimeError):
            continue
    write_json(latest_path, payload)
    append_json_line(
        history_path,
        {
            "generated_at": generated_at,
            "study_ids": list(resolved_study_ids),
            "action_ids": [text(action.get("action_id")) for action in action_queue],
            "latest_action_count": len(action_queue),
        },
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "build_scan_domain_routes_payload",
    "merge_previous_unscanned_study_handoff",
    "persist_scan_domain_routes_payload",
]
