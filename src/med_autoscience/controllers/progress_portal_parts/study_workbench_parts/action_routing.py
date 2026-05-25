from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

from ..rendering import list_html, status_chip
from ..status_display import display_text


def action_owner_routing_policy(
    *,
    route_decision_trail: Mapping[str, Any],
    route_map: Mapping[str, Any],
) -> dict[str, Any]:
    route_available = _non_empty_text(route_decision_trail.get("status")) == "available"
    handoff_policy = _mapping(route_map.get("owner_route_handoff_policy")) or _default_owner_route_handoff_policy()
    next_owner = _non_empty_text(route_decision_trail.get("next_owner"))
    missing: list[str] = []
    available: list[str] = []
    if route_available:
        available.append("route_decision_trail")
    else:
        missing.append("route_decision_trail")
    if handoff_policy:
        available.append("owner_route_handoff_policy")
    else:
        missing.append("owner_route_handoff")
    status = "available" if route_available and next_owner else "missing"
    if status != "available" and "owner_route_handoff" not in missing:
        missing.append("owner_route_handoff")
    if next_owner is None:
        missing.append("next_owner")
    return {
        "status": status,
        "next_owner": next_owner,
        "routing_role": "display_and_owner_route_projection",
        "owner_route_handoff_policy": handoff_policy,
        "conditions": {
            "available": available,
            "missing": missing,
            "stale": [],
            "conflict": [],
        },
        "authority": {
            "writes_authority_surface": False,
            "can_execute_controller_actions": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_artifact_mutation": False,
        },
    }


def workbench_summary(
    *,
    overview: Mapping[str, Any],
    route_map: Mapping[str, Any],
    route_decision_trail: Mapping[str, Any],
    action_owner_routing_policy: Mapping[str, Any],
    refs: list[str],
) -> dict[str, list[str]]:
    available: list[str] = []
    missing: list[str] = []
    if any(value not in (None, "", [], {}) for key, value in overview.items() if key != "study_id"):
        available.append("overview")
    else:
        missing.append("overview")
    for key, payload in (
        ("route_map", route_map),
        ("route_decision_trail", route_decision_trail),
    ):
        if _non_empty_text(payload.get("status")) == "available":
            available.append(key)
        else:
            missing.append(key)
    if action_owner_routing_policy:
        available.append("action_owner_routing_policy")
    else:
        missing.append("action_owner_routing_policy")
    if refs:
        available.append("source_refs")
    else:
        missing.append("source_refs")
    return {"available": available, "missing": missing}


def render_action_owner_routing_section(policy: Mapping[str, Any]) -> str:
    handoff_policy = _mapping(policy.get("owner_route_handoff_policy"))
    values = {
        "status": display_text(policy.get("status"), empty_text="missing", preserve_known_token=True),
        "next_owner": display_text(policy.get("next_owner"), empty_text="缺失", preserve_known_token=True),
        "required_receipt": display_text(
            handoff_policy.get("required_receipt_surface"),
            empty_text="缺失",
            preserve_known_token=True,
        ),
    }
    return (
        '<section class="panel wide"><h2>Action Owner Routing '
        + status_chip(policy.get("status") or "missing")
        + "</h2>"
        + _key_value_table(values)
        + list_html(_condition_items(_mapping(policy.get("conditions"))), empty_text="当前没有 action owner routing 条件。")
        + "</section>"
    )


def _default_owner_route_handoff_policy() -> dict[str, Any]:
    return {
        "policy": "route_only_to_owner_no_direct_execution",
        "required_receipt_surface": "mas_runtime_owner_route_handoff",
        "allowed_receipt_owners": [
            "MedAutoScience",
            "OPL provider transport",
        ],
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_mutation": False,
        "missing_behavior": "display_missing_do_not_infer",
    }


def _condition_items(conditions: Mapping[str, Any]) -> list[str]:
    items: list[str] = []
    for key in ("missing", "stale", "conflict"):
        for item in _string_list(conditions.get(key)):
            items.append(f"{key}: {item}")
    return items


def _key_value_table(values: Mapping[str, object]) -> str:
    return "".join(
        f"<div><dt>{escape(str(key))}</dt><dd>{escape(str(value))}</dd></div>"
        for key, value in values.items()
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
