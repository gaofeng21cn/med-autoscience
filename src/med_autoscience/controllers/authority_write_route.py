from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.authority_route_gate import (
    attach_authority_route_gate,
    authorize_authority_route,
)


def resolve_authority_write_route_context(
    *,
    action: str,
    context: Mapping[str, Any] | None,
    default_paths: list[Path] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    route_context = _route_context(context=context, default_paths=default_paths)
    gate = authorize_authority_route(action, route_context)
    blocking_reasons = list(gate.get("blocking_reasons") or [])
    if bool(gate.get("projection_only")):
        _append_unique(blocking_reasons, "projection_only_write_blocked")
    explicit_controller_route = _explicit_controller_route(route_context)
    if not route_context.get("authority_snapshot") and not explicit_controller_route:
        _append_unique(blocking_reasons, "authority_snapshot_missing")
    if blocking_reasons != list(gate.get("blocking_reasons") or []):
        gate = {
            **gate,
            "authorized": False,
            "allowed": False,
            "blocking_reasons": blocking_reasons,
        }
    return route_context, gate


def blocked_authority_write_payload(
    *,
    gate: Mapping[str, Any],
    **fields: Any,
) -> dict[str, Any]:
    return {
        "status": "authority_route_blocked",
        **fields,
        "authority_route_gate": dict(gate),
    }


def attach_write_route_gate(payload: Mapping[str, Any], gate: Mapping[str, Any]) -> dict[str, Any]:
    return attach_authority_route_gate(payload, gate)


def _route_context(
    *,
    context: Mapping[str, Any] | None,
    default_paths: list[Path] | None,
) -> dict[str, Any]:
    if isinstance(context, Mapping):
        return dict(context)
    return {"paths": list(default_paths or [])}


def _explicit_controller_route(route_context: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("controller_route_context", "explicit_controller_route_context"):
        value = route_context.get(key)
        if isinstance(value, Mapping):
            return value
    if all(
        _text(route_context.get(key)) is not None
        for key in ("work_unit_id", "controller_action_type", "control_surface")
    ):
        return route_context
    return {}


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "attach_write_route_gate",
    "blocked_authority_write_payload",
    "resolve_authority_write_route_context",
]
