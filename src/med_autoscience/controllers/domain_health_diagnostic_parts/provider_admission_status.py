from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)


ACTION_QUEUE_SELF_IDENTITY_BLOCKING_STATES = frozenset(
    {
        "typed_blocker",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }
)


def execution_state_kind(status_payload: Mapping[str, Any]) -> str | None:
    envelope = _mapping(status_payload.get("current_execution_envelope"))
    return _non_empty_text(envelope.get("state_kind")) or _non_empty_text(envelope.get("execution_state_kind"))


def status_blocks_action_queue_self_identity(
    status_payload: Mapping[str, Any],
    *,
    current_identity: Mapping[str, Any],
    current_identity_required: bool,
) -> bool:
    if current_identity_required and not current_identity:
        return True
    if execution_state_kind(status_payload) in ACTION_QUEUE_SELF_IDENTITY_BLOCKING_STATES:
        return True
    current_work_unit = _mapping(status_payload.get("current_work_unit"))
    return _non_empty_text(current_work_unit.get("status")) in ACTION_QUEUE_SELF_IDENTITY_BLOCKING_STATES


__all__ = [
    "execution_state_kind",
    "status_blocks_action_queue_self_identity",
]
