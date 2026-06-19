from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SURFACE_KIND = "mas_runtime_live_tail_work_orders"
VERSION = "mas-runtime-live-tail-work-orders.v1"


def live_tail_work_orders_from_audit(audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    live_completion = audit.get("live_runtime_readiness_completion")
    if not isinstance(live_completion, Mapping):
        return []
    tails = live_completion.get("open_surface_tails")
    if not isinstance(tails, list):
        return []
    return [_work_order_from_tail(tail) for tail in tails if isinstance(tail, Mapping)]


def validate_live_tail_work_order_contract(
    contract: Mapping[str, Any],
    audit: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if contract.get("surface_kind") != SURFACE_KIND:
        violations.append(_violation("<contract>", "surface_kind_mismatch"))
    if contract.get("version") != VERSION:
        violations.append(_violation("<contract>", "version_mismatch"))
    if contract.get("repo_source_retirement_blocked") is not False:
        violations.append(_violation("<contract>", "repo_source_retirement_blocked"))
    if contract.get("live_runtime_readiness_claim_allowed") is not False:
        violations.append(_violation("<contract>", "live_runtime_claim_allowed"))

    expected = {
        order["surface_id"]: order
        for order in live_tail_work_orders_from_audit(audit)
        if _text(order.get("surface_id")) is not None
    }
    raw_orders = contract.get("work_orders")
    orders = raw_orders if isinstance(raw_orders, list) else []
    observed = {
        str(order.get("surface_id")): order
        for order in orders
        if isinstance(order, Mapping) and _text(order.get("surface_id")) is not None
    }
    if set(observed) != set(expected):
        violations.append(_violation("<contract>", "work_order_surface_set_mismatch"))

    for surface_id, expected_order in expected.items():
        observed_order = observed.get(surface_id)
        if not isinstance(observed_order, Mapping):
            continue
        for key in (
            "status",
            "next_owner",
            "repo_source_retirement_blocked",
            "live_runtime_readiness_claim_allowed",
            "missing_evidence_status",
            "typed_blocker_when_missing",
        ):
            if observed_order.get(key) != expected_order.get(key):
                violations.append(_violation(surface_id, f"field_mismatch:{key}"))
        for key in (
            "acceptable_evidence_ref_families",
            "forbidden_evidence_substitutes",
        ):
            if sorted(str(item) for item in observed_order.get(key, [])) != sorted(
                str(item) for item in expected_order.get(key, [])
            ):
                violations.append(_violation(surface_id, f"list_mismatch:{key}"))
    return violations


def _work_order_from_tail(tail: Mapping[str, Any]) -> dict[str, Any]:
    gate = tail.get("evidence_gate")
    gate_mapping = gate if isinstance(gate, Mapping) else {}
    surface_id = str(tail.get("surface_id"))
    return {
        "surface_id": surface_id,
        "status": "evidence_required",
        "next_owner": str(gate_mapping.get("next_owner", "surface owner")),
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": False,
        "missing_evidence_status": str(
            gate_mapping.get("missing_evidence_status", "evidence_required")
        ),
        "typed_blocker_when_missing": f"{surface_id}_live_runtime_readiness_evidence_required",
        "acceptable_evidence_ref_families": sorted(
            str(item)
            for item in gate_mapping.get("acceptable_evidence_ref_families", [])
        ),
        "forbidden_evidence_substitutes": sorted(
            str(item)
            for item in gate_mapping.get("forbidden_evidence_substitutes", [])
        ),
    }


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "SURFACE_KIND",
    "VERSION",
    "live_tail_work_orders_from_audit",
    "validate_live_tail_work_order_contract",
]
