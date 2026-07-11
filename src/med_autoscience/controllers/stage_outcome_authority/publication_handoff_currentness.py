from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.stage_outcome_authority import owner_route_policy as owner_route_part


ACTION_TYPE = "publication_handoff_owner_gate"
OWNER = "publication_gate_owner"


def is_current(current_study: Mapping[str, Any]) -> bool:
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    allowed_actions = {_text(item) for item in route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    return _text(route.get("next_owner")) == OWNER and allowed_actions == {ACTION_TYPE}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["ACTION_TYPE", "OWNER", "is_current"]
