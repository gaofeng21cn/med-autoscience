from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_callable_adapter_projection import (
    domain_progress_transition_requests,
)


def current_consumer_dispatches(
    *,
    study_id: str,
    consumer_payload: Mapping[str, Any] | None,
    consumer_latest_path: Path,
) -> list[dict[str, Any]]:
    latest = dict(consumer_payload) if consumer_payload is not None else _read_json_object(consumer_latest_path)
    if latest is None:
        return []
    dispatches: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for dispatch in domain_progress_transition_requests(latest):
        payload = _with_owner_callable_adapter_semantics(_mapping(dispatch))
        if _text(payload.get("study_id")) != study_id:
            continue
        if _text(payload.get("dispatch_status")) != "ready":
            continue
        refs = _mapping(payload.get("refs"))
        dispatch_path = _text(refs.get("dispatch_path"))
        if dispatch_path is None:
            continue
        key = (dispatch_path, _text(payload.get("action_type")))
        if key in seen:
            continue
        seen.add(key)
        dispatches.append(payload)
    return dispatches


def explicit_transition_request_blocker_dispatches(
    *,
    study_id: str,
    requested: set[str],
    consumer_payload: Mapping[str, Any] | None,
    consumer_latest_path: Path,
) -> list[dict[str, Any]]:
    if not requested:
        return []
    latest = dict(consumer_payload) if consumer_payload is not None else _read_json_object(consumer_latest_path)
    if latest is None:
        return []
    dispatches: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for dispatch in domain_progress_transition_requests(latest):
        payload = _with_owner_callable_adapter_semantics(_mapping(dispatch))
        if _text(payload.get("study_id")) != study_id:
            continue
        if _text(payload.get("action_type")) not in requested:
            continue
        if _text(payload.get("dispatch_status")) != "transition_request_pending":
            continue
        if not _is_domain_progress_transition_request_projection(payload):
            continue
        refs = _mapping(payload.get("refs"))
        key = (_text(refs.get("dispatch_path")), _text(payload.get("action_type")))
        if key in seen:
            continue
        seen.add(key)
        dispatches.append(_as_transition_request_blocker_projection(payload))
    return dispatches


def _is_domain_progress_transition_request_projection(dispatch: Mapping[str, Any]) -> bool:
    return (
        _text(dispatch.get("surface")) == "mas_domain_progress_transition_request_projection"
        and dispatch.get("projection_only") is True
        and dispatch.get("owner_callable_carrier_projection_only") is True
    )


def _with_owner_callable_adapter_semantics(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(dispatch)
    if "prompt_contract" not in payload:
        prompt_contract_ref = _mapping(payload.get("prompt_contract_ref"))
        if prompt_contract_ref:
            payload["prompt_contract"] = prompt_contract_ref
    payload.setdefault("adapter_kind", "opl_authorized_owner_callable_adapter")
    payload.setdefault("target_runtime_owner", "one-person-lab")
    payload.setdefault("target_runtime_owner_authority_required", True)
    payload.setdefault("mas_creates_opl_outbox", False)
    payload.setdefault("mas_creates_opl_event", False)
    payload.setdefault("mas_creates_opl_stage_run", False)
    payload.setdefault("mas_dispatch_authority", False)
    payload.setdefault("dispatch_ready_for_execution_authority", False)
    return payload


def _as_transition_request_blocker_projection(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(dispatch)
    payload["dispatch_role"] = "transition_request_blocker_projection"
    payload["blocker_dispatch_only"] = True
    payload["default_next_action_authority"] = False
    payload["mas_dispatch_authority"] = False
    payload["dispatch_ready_for_execution_authority"] = False
    payload["dispatch_ready_for_execution"] = False
    payload["can_select_next_action"] = False
    payload["can_start_provider_attempt"] = False
    payload["authority_boundary"] = {
        **_mapping(payload.get("authority_boundary")),
        "dispatch_role": "transition_request_blocker_projection",
        "blocker_dispatch_only": True,
        "default_next_action_authority": False,
        "mas_dispatch_authority": False,
        "dispatch_ready_for_execution_authority": False,
        "can_select_next_action": False,
        "can_start_provider_attempt": False,
    }
    return payload


def _read_json_object(path: Path) -> dict[str, Any] | None:
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


__all__ = [
    "current_consumer_dispatches",
    "explicit_transition_request_blocker_dispatches",
]
