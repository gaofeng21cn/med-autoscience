from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode


def attach_repo_write_policy(
    actions: list[dict[str, Any]],
    *,
    developer_mode: DeveloperSupervisorMode,
) -> list[dict[str, Any]]:
    policy = dict(developer_mode.to_dict()["repo_write_policy"])
    return [
        {
            **action,
            "repo_write_policy": policy,
            "handoff_packet": {
                **_mapping(action.get("handoff_packet")),
                "repo_write_policy": policy,
            },
        }
        for action in actions
    ]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
