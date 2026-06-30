from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers import opl_domain_progress_transition_contract
from med_autoscience.controllers.domain_action_request_materializer_parts import current_action_queue
from med_autoscience.controllers.study_progress_parts import canonical_next_action_gate


LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON = (
    canonical_next_action_gate.legacy_next_action_authority_retirement()["reason"]
)
LEGACY_NEXT_ACTION_AUTHORITY_VALUES = {
    "current_executable_owner_action",
    "legacy_next_action_authority",
    "stage_native_workspace_next_action",
    "study_progress.current_executable_owner_action",
}
STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES = {
    "current_executable_owner_action",
    "legacy_next_action_authority",
    "study_progress.current_executable_owner_action",
}


def retire_incomplete_authority_actions(
    actions: Iterable[Mapping[str, Any]],
    ignored: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    retired: list[dict[str, Any]] = []
    for action in actions:
        payload = dict(action)
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
    if (
        authority in STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES
        or source in STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES
    ):
        return True
    next_action = _next_action_payload(action)
    if opl_domain_progress_transition_contract.next_action_identity_complete(next_action):
        return False
    return _text(next_action.get("surface_kind")) == "mas_next_action_envelope"


def _next_action_payload(action: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping(action.get("handoff_packet"))
    prompt_contract = _mapping(action.get("prompt_contract"))
    source_action = _mapping(action.get("source_action"))
    return (
        _mapping(action.get("next_action"))
        or _mapping(handoff.get("next_action"))
        or _mapping(prompt_contract.get("next_action"))
        or _mapping(source_action.get("next_action"))
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
    "LEGACY_NEXT_ACTION_AUTHORITY_VALUES",
    "STRICT_LEGACY_NEXT_ACTION_AUTHORITY_VALUES",
    "requires_next_action_envelope",
    "retire_incomplete_authority_actions",
]
