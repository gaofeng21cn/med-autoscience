from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def apply_explicit_upstream_publication_work_unit(
    publication_work_unit_payload: Mapping[str, Any],
    *,
    publication_eval_payload: Mapping[str, Any],
    upstream_work_unit_ids: frozenset[str],
    compact_publication_work_unit,
    non_empty_text,
    bounded_analysis_action: str,
    route_back_same_line_action: str,
) -> dict[str, Any]:
    explicit = explicit_upstream_publication_work_unit(
        publication_eval_payload,
        upstream_work_unit_ids=upstream_work_unit_ids,
        compact_publication_work_unit=compact_publication_work_unit,
        non_empty_text=non_empty_text,
        bounded_analysis_action=bounded_analysis_action,
        route_back_same_line_action=route_back_same_line_action,
    )
    if explicit is None:
        return dict(publication_work_unit_payload)
    payload = dict(publication_work_unit_payload)
    if explicit.get("work_unit_fingerprint"):
        payload["fingerprint"] = explicit["work_unit_fingerprint"]
    payload["next_work_unit"] = explicit["next_work_unit"]
    payload["blocking_work_units"] = explicit["blocking_work_units"]
    return payload


def explicit_upstream_publication_work_unit(
    publication_eval_payload: Mapping[str, Any],
    *,
    upstream_work_unit_ids: frozenset[str],
    compact_publication_work_unit,
    non_empty_text,
    bounded_analysis_action: str,
    route_back_same_line_action: str,
) -> dict[str, Any] | None:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        if action.get("requires_controller_decision") is not True:
            continue
        next_work_unit = compact_publication_work_unit(action.get("next_work_unit"))
        if next_work_unit is None:
            continue
        if non_empty_text(next_work_unit.get("unit_id")) not in upstream_work_unit_ids:
            continue
        action_type = non_empty_text(action.get("action_type"))
        route_target = non_empty_text(action.get("route_target"))
        lane = non_empty_text(next_work_unit.get("lane"))
        if (
            action_type != bounded_analysis_action
            and action_type != route_back_same_line_action
            and route_target != "analysis-campaign"
            and route_target != "write"
            and lane != "analysis-campaign"
            and lane != "write"
        ):
            continue
        blocking_work_units = [
            compact
            for item in (action.get("blocking_work_units") or [])
            if (compact := compact_publication_work_unit(item)) is not None
        ] or [next_work_unit]
        return {
            "work_unit_fingerprint": non_empty_text(action.get("work_unit_fingerprint")),
            "next_work_unit": next_work_unit,
            "blocking_work_units": blocking_work_units,
        }
    return None


def controller_route_context_for_publication_work_unit_payload(
    *,
    publication_work_unit_payload: Mapping[str, Any],
    gate_report: Mapping[str, Any],
    source_eval_id: str | None,
    upstream_work_unit_ids: frozenset[str],
    controller_action_type: str,
    non_empty_text,
) -> dict[str, Any] | None:
    next_work_unit = publication_work_unit_payload.get("next_work_unit")
    if not isinstance(next_work_unit, Mapping):
        return None
    work_unit_id = non_empty_text(next_work_unit.get("unit_id"))
    if work_unit_id not in upstream_work_unit_ids:
        return None
    return {
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": controller_action_type,
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "gate_fingerprint": non_empty_text(gate_report.get("gate_fingerprint")),
            "work_unit_fingerprint": non_empty_text(publication_work_unit_payload.get("fingerprint")),
        }
    }


def route_context_work_unit_id(route_context: Mapping[str, Any] | None, *, non_empty_text) -> str | None:
    if not isinstance(route_context, Mapping):
        return None
    for key in ("controller_route_context", "explicit_controller_route_context"):
        controller_route_context = route_context.get(key)
        if isinstance(controller_route_context, Mapping):
            return non_empty_text(controller_route_context.get("work_unit_id"))
    return None


def has_explicit_controller_route_context(route_context: Mapping[str, Any] | None) -> bool:
    if not isinstance(route_context, Mapping):
        return False
    return any(isinstance(route_context.get(key), Mapping) for key in ("controller_route_context", "explicit_controller_route_context"))


def route_action_for_controller_context(
    route_context: Mapping[str, Any] | None,
    *,
    upstream_work_unit_ids: frozenset[str],
    non_empty_text,
) -> str:
    controller_route_context = (
        route_context.get("controller_route_context")
        if isinstance(route_context, Mapping)
        else None
    )
    if not isinstance(controller_route_context, Mapping):
        return "bundle_build"
    if non_empty_text(controller_route_context.get("work_unit_id")) in upstream_work_unit_ids:
        return "paper_write"
    return "bundle_build"


def merge_route_contexts(
    *contexts: Mapping[str, Any] | None,
    preferred_controller_work_unit_ids: frozenset[str],
    non_empty_text,
) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}
    for context in contexts:
        if not isinstance(context, Mapping):
            continue
        payload = dict(context)
        existing_controller_context = merged.get("controller_route_context")
        merged.update(payload)
        if (
            isinstance(existing_controller_context, Mapping)
            and route_context_work_unit_id(
                {"controller_route_context": existing_controller_context},
                non_empty_text=non_empty_text,
            )
            in preferred_controller_work_unit_ids
            and route_context_work_unit_id(payload, non_empty_text=non_empty_text)
            not in preferred_controller_work_unit_ids
        ):
            merged["controller_route_context"] = dict(existing_controller_context)
    return merged or None


__all__ = [
    "apply_explicit_upstream_publication_work_unit",
    "controller_route_context_for_publication_work_unit_payload",
    "explicit_upstream_publication_work_unit",
    "has_explicit_controller_route_context",
    "merge_route_contexts",
    "route_action_for_controller_context",
    "route_context_work_unit_id",
]
