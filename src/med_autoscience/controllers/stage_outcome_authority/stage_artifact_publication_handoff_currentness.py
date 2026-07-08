from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part


ACTION_TYPE = "publication_handoff_owner_gate"
OWNER = "publication_gate_owner"


def is_current(current_study: Mapping[str, Any]) -> bool:
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    allowed_actions = {_text(item) for item in route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    if _text(route.get("next_owner")) == OWNER and allowed_actions == {ACTION_TYPE}:
        return True
    action = _mapping(current_study.get("current_executable_owner_action"))
    return (
        _text(action.get("source")) == "stage_artifact_index.next_owner_action"
        and _text(action.get("next_owner")) == OWNER
        and ACTION_TYPE in {_text(item) for item in action.get("allowed_actions") or []}
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["ACTION_TYPE", "OWNER", "is_current"]
