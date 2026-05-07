from __future__ import annotations

from typing import Any

from med_autoscience.controllers.product_entry_parts.workspace_attention import (
    _attention_queue,
    _workspace_operator_brief,
)


def attention_queue(
    *,
    workspace_status: str,
    workspace_supervision: dict[str, Any],
    studies: list[dict[str, Any]],
    commands: dict[str, str],
) -> list[dict[str, Any]]:
    return _attention_queue(
        workspace_status=workspace_status,
        workspace_supervision=workspace_supervision,
        studies=studies,
        commands=commands,
    )


def operator_brief(
    *,
    workspace_status: str,
    workspace_alerts: list[str],
    attention_queue: list[dict[str, Any]],
    studies: list[dict[str, Any]],
    user_loop: dict[str, str],
    commands: dict[str, str],
) -> dict[str, Any]:
    return _workspace_operator_brief(
        workspace_status=workspace_status,
        workspace_alerts=workspace_alerts,
        attention_queue=attention_queue,
        studies=studies,
        user_loop=user_loop,
        commands=commands,
    )
