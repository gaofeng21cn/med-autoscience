from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)


def candidate_with_stage_run_admission_identity(
    candidate: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
    dispatch_payload: Mapping[str, Any] | None = None,
    dispatch_path: Path | None = None,
    study_root: Path | None = None,
) -> dict[str, Any]:
    payload = dict(candidate)
    dispatch_payload = _mapping(dispatch_payload) or _mapping(execution)
    owner_route = _mapping(execution.get("owner_route")) or _mapping(dispatch_payload.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    refs = _mapping(dispatch_payload.get("refs"))
    dispatch_ref = _first_present_text(
        payload.get("dispatch_ref"),
        execution.get("dispatch_ref"),
        dispatch_payload.get("dispatch_ref"),
        source_refs.get("dispatch_ref"),
        source_refs.get("dispatch_path"),
        refs.get("dispatch_path"),
        str(dispatch_path) if dispatch_path is not None else None,
        payload.get("dispatch_path"),
        execution.get("dispatch_path"),
        dispatch_payload.get("dispatch_path"),
    )
    stage_packet_ref = _first_present_text(
        payload.get("stage_packet_ref"),
        execution.get("stage_packet_ref"),
        dispatch_payload.get("stage_packet_ref"),
        source_refs.get("stage_packet_ref"),
        source_refs.get("stage_packet_path"),
        refs.get("stage_packet_path"),
        refs.get("immutable_dispatch_path"),
    )
    selected_dispatch_ref = _first_present_text(
        payload.get("selected_dispatch_ref"),
        execution.get("selected_dispatch_ref"),
        dispatch_payload.get("selected_dispatch_ref"),
        source_refs.get("selected_dispatch_ref"),
        refs.get("selected_dispatch_ref"),
    )
    stage_packet_refs = _unique_texts(
        payload.get("stage_packet_refs"),
        execution.get("stage_packet_refs"),
        dispatch_payload.get("stage_packet_refs"),
        source_refs.get("stage_packet_refs"),
        [stage_packet_ref],
        payload.get("checkpoint_refs"),
        execution.get("checkpoint_refs"),
        dispatch_payload.get("checkpoint_refs"),
    )
    route_identity_key = _first_present_text(
        payload.get("route_identity_key"),
        execution.get("route_identity_key"),
        dispatch_payload.get("route_identity_key"),
        owner_route.get("route_identity_key"),
        source_refs.get("route_identity_key"),
        owner_route.get("idempotency_key"),
        dispatch_payload.get("idempotency_key"),
    )
    if route_identity_key is None:
        study_id = _non_empty_text(payload.get("study_id")) or _non_empty_text(execution.get("study_id"))
        fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
            payload.get("action_fingerprint")
        )
        if study_id is not None and fingerprint is not None:
            route_identity_key = f"provider-admission::{study_id}::{fingerprint}"
    attempt_idempotency_key = _first_present_text(
        payload.get("attempt_idempotency_key"),
        execution.get("attempt_idempotency_key"),
        dispatch_payload.get("attempt_idempotency_key"),
        owner_route.get("attempt_idempotency_key"),
        source_refs.get("attempt_idempotency_key"),
        payload.get("idempotency_key"),
        execution.get("idempotency_key"),
        dispatch_payload.get("idempotency_key"),
    )
    if attempt_idempotency_key is None:
        attempt_idempotency_key = route_identity_key
    normalized_dispatch_ref = _workspace_relative_ref(dispatch_ref, study_root=study_root)
    normalized_stage_packet_ref = _workspace_relative_ref(stage_packet_ref, study_root=study_root)
    normalized_selected_dispatch_ref = _workspace_relative_ref(selected_dispatch_ref, study_root=study_root)
    normalized_stage_packet_refs = [
        ref
        for ref in (
            _workspace_relative_ref(item, study_root=study_root)
            for item in stage_packet_refs
        )
        if ref is not None
    ]
    for key, value in {
        "dispatch_ref": normalized_dispatch_ref,
        "stage_packet_ref": normalized_stage_packet_ref,
        "selected_dispatch_ref": normalized_selected_dispatch_ref,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
    }.items():
        if value is not None:
            payload[key] = value
    if normalized_stage_packet_refs:
        payload["stage_packet_refs"] = list(dict.fromkeys(normalized_stage_packet_refs))
        payload.setdefault("checkpoint_refs", payload["stage_packet_refs"])
    if attempt_idempotency_key is not None:
        payload["idempotency_key"] = attempt_idempotency_key
    source_refs_payload = dict(_mapping(payload.get("source_refs")))
    for key, value in {
        "dispatch_ref": normalized_dispatch_ref,
        "stage_packet_ref": normalized_stage_packet_ref,
        "selected_dispatch_ref": normalized_selected_dispatch_ref,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
    }.items():
        if value is not None:
            source_refs_payload[key] = value
    if normalized_stage_packet_refs:
        source_refs_payload["stage_packet_refs"] = list(dict.fromkeys(normalized_stage_packet_refs))
    if source_refs_payload:
        payload["source_refs"] = source_refs_payload
    return payload


def _unique_texts(*values: object) -> list[str]:
    result: list[str] = []
    for value in values:
        for item in _text_items(value):
            if item not in result:
                result.append(item)
    return result


def _first_present_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
        for item in _text_items(value):
            return item
    return None


def _workspace_relative_ref(value: str | None, *, study_root: Path | None) -> str | None:
    text = _non_empty_text(value)
    if text is None or study_root is None:
        return text
    path = Path(text)
    if not path.is_absolute():
        return text
    try:
        workspace_root = Path(study_root).expanduser().resolve().parents[1]
        return path.resolve().relative_to(workspace_root).as_posix()
    except (OSError, ValueError, IndexError):
        return text


__all__ = ["candidate_with_stage_run_admission_identity"]
