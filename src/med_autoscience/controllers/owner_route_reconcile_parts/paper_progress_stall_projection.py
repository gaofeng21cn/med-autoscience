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
        {
            **action,
            "paper_progress_stall": projection,
            "action_fingerprint": projection["action_fingerprint"],
            "handoff_packet": {
                **_mapping(action.get("handoff_packet")),
                "paper_progress_stall": projection,
                "action_fingerprint": projection["action_fingerprint"],
            },
        }
        for action in actions
    ]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["build_and_attach"]
