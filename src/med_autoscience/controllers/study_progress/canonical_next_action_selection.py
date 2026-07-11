from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import study_domain_transition_guard


def domain_transition_canonical_next_action(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    transition = _mapping(payload.get("domain_transition"))
    if study_domain_transition_guard.runtime_redrive_decision_type(
        {"domain_transition": transition}
    ) is None:
        return {}
    next_action = _mapping(transition.get("next_action")) or _mapping(
        transition.get("next_action_envelope")
    )
    if _text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return {}
    if not _text(next_action.get("action_family")):
        return {}
    if not _text(next_action.get("owner")):
        return {}
    return next_action


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["domain_transition_canonical_next_action"]
