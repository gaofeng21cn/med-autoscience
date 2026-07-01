from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer_parts import current_action_queue
from med_autoscience.controllers.study_progress_parts import canonical_next_action_gate
from med_autoscience.controllers.owner_callable_action_policy import (
    SUPPORTED_ACTION_TYPES as OWNER_CALLABLE_ACTION_TYPES,
)


LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON = (
    canonical_next_action_gate.legacy_next_action_authority_retirement()["reason"]
)
NEXT_ACTION_ENVELOPE_IDENTITY_MISMATCH_REASON = "next_action_envelope_identity_mismatch"
LEGACY_NEXT_ACTION_AUTHORITY_VALUES = {
    "current_executable_owner_action",
    "legacy_next_action_authority",
    "stage_native_workspace_next_action",
    "study_progress.current_executable_owner_action",
}
CANONICAL_NEXT_ACTION_AUTHORITY_VALUES = {
    "mas_next_action_envelope",
    "NextActionEnvelope",
}
STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES = {
    "current_executable_owner_action",
    "legacy_next_action_authority",
    "study_progress.current_executable_owner_action",
}
DEFAULT_EXECUTABLE_NEXT_ACTION_TYPES = {
    "complete_medical_paper_readiness_surface",
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
}


def retire_incomplete_authority_actions(
    actions: Iterable[Mapping[str, Any]],
    ignored: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    retired: list[dict[str, Any]] = []
    for action in actions:
        payload = dict(action)
        if next_action_identity_mismatches(payload):
            retired.append(
                current_action_queue.ignored_action(
                    payload,
                    NEXT_ACTION_ENVELOPE_IDENTITY_MISMATCH_REASON,
                )
            )
            continue
        if requires_next_action_envelope(payload):
            retired.append(
                current_action_queue.ignored_action(
                    payload,
                    LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
                )
            )
            continue
        selected.append(payload)
    return selected, _unique_ignored_actions([*ignored, *retired])


def requires_next_action_envelope(action: Mapping[str, Any]) -> bool:
    authority = _text(action.get("authority")) or _text(_mapping(action.get("handoff_packet")).get("authority"))
    source = (
        _text(action.get("source"))
        or _text(action.get("source_surface"))
        or _text(action.get("current_action_source"))
    )
    legacy_authority = (
        authority in LEGACY_NEXT_ACTION_AUTHORITY_VALUES
        or source in LEGACY_NEXT_ACTION_AUTHORITY_VALUES
    )
    strict_legacy_authority = (
        authority in STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES
        or source in STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES
    )
    next_action = _next_action_payload(action)
    canonical_envelope_action = _text(action.get("surface_kind")) == "mas_next_action_envelope" or (
        authority in CANONICAL_NEXT_ACTION_AUTHORITY_VALUES
        and source in {None, *CANONICAL_NEXT_ACTION_AUTHORITY_VALUES}
    )
    if strict_legacy_authority or legacy_authority:
        return True
    if canonical_envelope_action and canonical_next_action_gate.canonical_next_action_identity_complete(next_action):
        return False
    return _text(action.get("action_type")) in OWNER_CALLABLE_ACTION_TYPES


def next_action_identity_mismatches(action: Mapping[str, Any]) -> bool:
    next_action = _next_action_payload(action)
    if not canonical_next_action_gate.canonical_next_action_identity_complete(next_action):
        return False
    next_action_type = _text(next_action.get("action_type"))
    action_type = _text(action.get("action_type"))
    if next_action_type is not None and action_type is not None and next_action_type != action_type:
        return True
    next_work_unit = _text(next_action.get("work_unit_id"))
    action_work_unit = _text(action.get("work_unit_id")) or _text(action.get("next_work_unit"))
    if next_work_unit is not None and action_work_unit is not None and next_work_unit != action_work_unit:
        return True
    next_action_family = _text(next_action.get("action_family"))
    action_family = _text(action.get("action_family"))
    if next_action_family is not None and action_family is not None and next_action_family != action_family:
        return True
    next_output_kind = _text(_mapping(next_action.get("expected_output_contract")).get("output_kind"))
    action_output_kind = _text(
        _mapping(action.get("expected_output_contract")).get("output_kind")
    )
    if next_output_kind is not None and action_output_kind is not None and next_output_kind != action_output_kind:
        return True
    return False


def _next_action_payload(action: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping(action.get("handoff_packet"))
    prompt_contract = _mapping(action.get("prompt_contract"))
    source_action = _mapping(action.get("source_action"))
    return (
        _mapping(action.get("next_action"))
        or _mapping(handoff.get("next_action"))
        or _mapping(prompt_contract.get("next_action"))
        or _mapping(source_action.get("next_action"))
        or (
            dict(action)
            if _text(action.get("surface_kind")) == "mas_next_action_envelope"
            else {}
        )
    )


def _unique_ignored_actions(actions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for action in actions:
        payload = dict(action)
        identity = (
            _text(payload.get("study_id")),
            _text(payload.get("action_type")),
            _text(payload.get("action_id")),
            _text(payload.get("reason")),
        )
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(payload)
    return unique


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON",
    "CANONICAL_NEXT_ACTION_AUTHORITY_VALUES",
    "LEGACY_NEXT_ACTION_AUTHORITY_VALUES",
    "DEFAULT_EXECUTABLE_NEXT_ACTION_TYPES",
    "NEXT_ACTION_ENVELOPE_IDENTITY_MISMATCH_REASON",
    "STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES",
    "next_action_identity_mismatches",
    "requires_next_action_envelope",
    "retire_incomplete_authority_actions",
]
