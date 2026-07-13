from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND as NEXT_ACTION_SURFACE_KIND


def has_canonical_next_action(payload: Mapping[str, Any]) -> bool:
    next_action = _mapping(payload.get("next_action"))
    return _text(next_action.get("surface_kind")) == NEXT_ACTION_SURFACE_KIND


def canonical_next_action_identity_complete(next_action: Mapping[str, Any]) -> bool:
    payload = _mapping(next_action)
    expected = _mapping(payload.get("expected_output_contract"))
    return (
        _text(payload.get("surface_kind")) == NEXT_ACTION_SURFACE_KIND
        and _text(payload.get("action_id")) is not None
        and _text(payload.get("idempotency_key")) is not None
        and _text(payload.get("action_family")) is not None
        and _text(expected.get("output_kind")) is not None
    )


def legacy_next_action_authority_retirement() -> dict[str, Any]:
    return {
        "status": "retired",
        "authority": "NextActionEnvelope",
        "reason": "legacy_next_action_authority_retired_use_next_action_envelope",
        "retired_surfaces": [
            "current_work_unit",
            "current_executable_owner_action",
            "provider_attempt",
            "current_execution_envelope",
        ],
        "default_selector_policy": "fail_closed",
        "diagnostic_only": True,
    }


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None
