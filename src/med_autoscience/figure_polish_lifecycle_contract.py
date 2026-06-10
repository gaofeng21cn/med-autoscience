from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FIGURE_POLISH_LIFECYCLE_BASENAME = "figure_polish_lifecycle.json"

VALID_LIFECYCLE_STATES = (
    "draft_rendered",
    "deterministic_qc_clear",
    "visual_audit_findings",
    "revised",
    "audit_clear",
    "publication_manifested",
)

REQUIRED_EVENT_FIELDS = ("state", "figure_id", "artifact_ref", "actor", "evidence_ref")
REQUIRED_RELATIONSHIP_REFS = (
    "figure_visual_audit_receipt",
    "display_pack_lock_publication_figure_quality_refs",
)
FORBIDDEN_TRUE_EVENT_FLAGS = ("mutates_data", "carries_publication_verdict")


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return payload


def _require_schema_version(payload: dict[str, Any], *, contract_name: str) -> None:
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise ValueError(f"{contract_name}.schema_version must be an integer")
    if schema_version != 1:
        raise ValueError(f"{contract_name}.schema_version must equal 1")


def _require_non_empty_string(item: dict[str, Any], field_name: str, *, context: str) -> str:
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field_name} must be a non-empty string")
    return value.strip()


def _require_object_list(payload: dict[str, Any], field_name: str, *, contract_name: str) -> list[dict[str, Any]]:
    value = payload.get(field_name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{contract_name}.{field_name} must be a non-empty list")
    entries: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{contract_name}.{field_name}[{index}] must be a JSON object")
        entries.append(dict(item))
    return entries


def _actor_requires_model_or_reviewer_ref(actor: str) -> bool:
    actor_tokens = set(re.split(r"[^a-z0-9]+", actor.lower()))
    return "ai" in actor_tokens or "vlm" in actor_tokens


def _require_ai_vlm_actor_ref(event: dict[str, Any], *, actor: str, context: str) -> dict[str, str]:
    if not _actor_requires_model_or_reviewer_ref(actor):
        return {}
    model_ref = event.get("model_ref")
    reviewer_ref = event.get("reviewer_ref")
    has_model_ref = isinstance(model_ref, str) and bool(model_ref.strip())
    has_reviewer_ref = isinstance(reviewer_ref, str) and bool(reviewer_ref.strip())
    if not has_model_ref and not has_reviewer_ref:
        raise ValueError(f"{context} AI/VLM actor requires model_ref or reviewer_ref")
    normalized: dict[str, str] = {}
    if has_model_ref:
        normalized["model_ref"] = model_ref.strip()
    if has_reviewer_ref:
        normalized["reviewer_ref"] = reviewer_ref.strip()
    return normalized


def _validate_event_authority_flags(event: dict[str, Any], *, context: str) -> None:
    for field_name in FORBIDDEN_TRUE_EVENT_FLAGS:
        if field_name in event and event[field_name] is not False:
            raise ValueError(f"{context}.{field_name} must be false when provided")


def _require_state_sequence_chunk(events: list[dict[str, Any]]) -> None:
    states = [event.get("state") for event in events]
    if states[0] != VALID_LIFECYCLE_STATES[0]:
        raise ValueError("figure_polish_lifecycle.events state sequence must start with draft_rendered")
    if len(states) > len(VALID_LIFECYCLE_STATES):
        raise ValueError("figure_polish_lifecycle.events state sequence is longer than the allowed lifecycle")
    expected_prefix = VALID_LIFECYCLE_STATES[: len(states)]
    for index, (actual, expected) in enumerate(zip(states, expected_prefix, strict=True)):
        if actual != expected:
            raise ValueError(
                "figure_polish_lifecycle.events state sequence must be an ordered hard-gate prefix; "
                f"expected {expected!r} at index {index}, got {actual!r}"
            )


def _require_state_sequence(events: list[dict[str, Any]]) -> None:
    chunk: list[dict[str, Any]] = []
    for event in events:
        state = event.get("state")
        if state == VALID_LIFECYCLE_STATES[0] and chunk:
            _require_state_sequence_chunk(chunk)
            chunk = []
        chunk.append(event)
    if chunk:
        _require_state_sequence_chunk(chunk)


def _require_relationship_refs(payload: dict[str, Any]) -> dict[str, str]:
    value = payload.get("relationship_refs")
    if not isinstance(value, dict):
        raise ValueError("figure_polish_lifecycle.relationship_refs must be a JSON object")
    normalized: dict[str, str] = {}
    for field_name in REQUIRED_RELATIONSHIP_REFS:
        normalized[field_name] = _require_non_empty_string(
            value,
            field_name,
            context="figure_polish_lifecycle.relationship_refs",
        )
    return {**value, **normalized}


def load_figure_polish_lifecycle(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="figure_polish_lifecycle")
    lifecycle_id = _require_non_empty_string(payload, "lifecycle_id", context="figure_polish_lifecycle")
    relationship_refs = _require_relationship_refs(payload)
    events = _require_object_list(payload, "events", contract_name="figure_polish_lifecycle")
    _require_state_sequence(events)

    normalized_events: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        context = f"figure_polish_lifecycle.events[{index}]"
        _validate_event_authority_flags(event, context=context)
        normalized_event = dict(event)
        for field_name in REQUIRED_EVENT_FIELDS:
            normalized_event[field_name] = _require_non_empty_string(event, field_name, context=context)
        if normalized_event["state"] not in VALID_LIFECYCLE_STATES:
            raise ValueError(f"{context}.state must be one of {list(VALID_LIFECYCLE_STATES)!r}")
        normalized_event.update(_require_ai_vlm_actor_ref(event, actor=normalized_event["actor"], context=context))
        normalized_events.append(normalized_event)

    return {
        **payload,
        "lifecycle_id": lifecycle_id,
        "relationship_refs": relationship_refs,
        "events": normalized_events,
    }
