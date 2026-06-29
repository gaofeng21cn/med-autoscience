from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def owner_action_from_domain_transition(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    return None


def consumed_closeout_typed_blocker_allows_domain_transition_successor(
    *,
    payload: Mapping[str, Any],
    domain_transition_action: Mapping[str, Any],
    repair_progress_action: Mapping[str, Any] | None,
) -> bool:
    return False


__all__ = [
    "consumed_closeout_typed_blocker_allows_domain_transition_successor",
    "owner_action_from_domain_transition",
]
