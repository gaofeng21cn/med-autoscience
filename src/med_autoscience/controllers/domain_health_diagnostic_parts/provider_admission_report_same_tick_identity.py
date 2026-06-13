from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)


def same_tick_candidate_with_stage_run_identity(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    study_id = _non_empty_text(payload.get("study_id"))
    fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    route_key = _non_empty_text(payload.get("route_identity_key"))
    if route_key is None and study_id is not None and fingerprint is not None:
        route_key = f"provider-admission::{study_id}::{fingerprint}"
    attempt_key = _non_empty_text(payload.get("attempt_idempotency_key")) or route_key
    dispatch_ref = _non_empty_text(payload.get("dispatch_ref")) or _non_empty_text(payload.get("dispatch_path"))
    stage_packet_ref = _non_empty_text(payload.get("stage_packet_ref"))
    stage_packet_refs = same_tick_text_items(payload.get("stage_packet_refs"))
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.append(stage_packet_ref)
    for key, value in {
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "route_identity_key": route_key,
        "attempt_idempotency_key": attempt_key,
        "idempotency_key": attempt_key,
    }.items():
        if value is not None:
            payload[key] = value
    if stage_packet_refs:
        payload["stage_packet_refs"] = stage_packet_refs
        payload.setdefault("checkpoint_refs", list(stage_packet_refs))
    source_refs = dict(_mapping(payload.get("source_refs")))
    for key, value in {
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "route_identity_key": route_key,
        "attempt_idempotency_key": attempt_key,
    }.items():
        if value is not None:
            source_refs[key] = value
    if stage_packet_refs:
        source_refs["stage_packet_refs"] = stage_packet_refs
    if source_refs:
        payload["source_refs"] = source_refs
    return payload


def same_tick_text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = [
    "same_tick_candidate_with_stage_run_identity",
    "same_tick_text_items",
]
