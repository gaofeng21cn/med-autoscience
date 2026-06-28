from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import paper_progress_stall


def build_and_attach(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    projection = paper_progress_stall.build_paper_progress_stall_read_model(
        status_payload=status,
        progress_payload=progress,
        owner_route=owner_route,
        action_queue=actions,
    )
    return projection, [
        _attach_projection(action=action, projection=projection)
        for action in actions
    ]


def _attach_projection(*, action: Mapping[str, Any], projection: Mapping[str, Any]) -> dict[str, Any]:
    action_fingerprint = _current_action_fingerprint(action)
    stall_fingerprint = _text(projection.get("action_fingerprint"))
    handoff_packet = _mapping(action.get("handoff_packet"))
    return {
        **action,
        "paper_progress_stall": dict(projection),
        "paper_progress_stall_action_fingerprint": stall_fingerprint,
        "action_fingerprint": action_fingerprint,
        "handoff_packet": {
            **handoff_packet,
            "paper_progress_stall": dict(projection),
            "paper_progress_stall_action_fingerprint": stall_fingerprint,
            "action_fingerprint": _current_action_fingerprint(handoff_packet) or action_fingerprint,
        },
    }


def _current_action_fingerprint(action: Mapping[str, Any]) -> str | None:
    return (
        _text(action.get("action_fingerprint"))
        or _text(action.get("work_unit_fingerprint"))
        or _text(_mapping(action.get("owner_route")).get("work_unit_fingerprint"))
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["build_and_attach"]
