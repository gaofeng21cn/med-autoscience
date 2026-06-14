from __future__ import annotations

from collections.abc import Mapping
from typing import Any


WEAK_CURRENT_OWNER_TICKET_REASON = (
    "fresh_progress_current_owner_ticket_requires_strong_currentness_identity"
)

_SYNTHETIC_PREFIX = "study-progress-current-owner-ticket::"


def owner_route_has_strong_currentness(owner_route: Mapping[str, Any]) -> bool:
    route = _mapping(owner_route)
    if not route:
        return False
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return _payload_has_strong_currentness(route) or _payload_has_strong_currentness(
        source_refs
    ) or _payload_has_strong_currentness(basis)


def owner_route_values(
    *,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
    ticket: Mapping[str, Any],
    action_type: str,
    work_unit_id: str,
) -> dict[str, str]:
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_work_unit_basis = _mapping(current_work_unit.get("currentness_basis"))
    ticket_work_unit = _mapping(ticket.get("work_unit"))
    current_action_target = _mapping(current_action.get("target_surface"))
    owner_route = _mapping(progress.get("owner_route"))
    route_refs = _mapping(owner_route.get("source_refs"))
    route_basis = _mapping(route_refs.get("owner_route_currentness_basis"))
    truth = _mapping(progress.get("study_truth_snapshot"))
    runtime_health = _mapping(progress.get("runtime_health_snapshot"))
    source_eval_id = _first_strong_text(
        current_action.get("source_eval_id"),
        current_action.get("publication_eval_id"),
        current_action_target.get("publication_eval_id"),
        current_work_unit.get("source_eval_id"),
        current_work_unit.get("publication_eval_id"),
        current_work_unit_basis.get("source_eval_id"),
        current_work_unit_basis.get("publication_eval_id"),
        ticket.get("source_eval_id"),
        ticket_work_unit.get("source_eval_id"),
        route_basis.get("source_eval_id"),
        route_refs.get("source_eval_id"),
        owner_route.get("source_eval_id"),
    )
    source_fingerprint = _first_strong_text(
        current_action.get("source_fingerprint"),
        current_work_unit.get("source_fingerprint"),
        current_work_unit_basis.get("source_fingerprint"),
        ticket.get("source_fingerprint"),
        ticket_work_unit.get("source_fingerprint"),
        route_basis.get("source_fingerprint"),
        route_refs.get("source_fingerprint"),
        owner_route.get("source_fingerprint"),
        source_eval_id,
    )
    work_unit_fingerprint = _first_strong_text(
        current_action.get("work_unit_fingerprint"),
        current_action.get("action_fingerprint"),
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
        current_work_unit_basis.get("work_unit_fingerprint"),
        current_work_unit_basis.get("action_fingerprint"),
        ticket.get("work_unit_fingerprint"),
        ticket.get("action_fingerprint"),
        ticket_work_unit.get("work_unit_fingerprint"),
        ticket_work_unit.get("action_fingerprint"),
        route_basis.get("work_unit_fingerprint"),
        route_refs.get("work_unit_fingerprint"),
        owner_route.get("work_unit_fingerprint"),
    )
    if source_fingerprint is None or work_unit_fingerprint is None:
        return {}
    truth_epoch = _first_strong_text(
        progress.get("truth_epoch"),
        truth.get("truth_epoch"),
        current_work_unit_basis.get("truth_epoch"),
        route_basis.get("truth_epoch"),
        route_refs.get("study_truth_epoch"),
        owner_route.get("truth_epoch"),
        source_fingerprint,
    )
    runtime_health_epoch = _first_strong_text(
        progress.get("runtime_health_epoch"),
        runtime_health.get("runtime_health_epoch"),
        current_work_unit_basis.get("runtime_health_epoch"),
        route_basis.get("runtime_health_epoch"),
        route_refs.get("runtime_health_epoch"),
        owner_route.get("runtime_health_epoch"),
        truth_epoch,
    )
    source_ref = _text(current_action.get("source_ref")) or _text(ticket.get("source_ref"))
    values = {
        "truth_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "source_fingerprint": source_fingerprint,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_eval_id": source_eval_id,
        "source_ref": source_ref,
        "work_unit_id": work_unit_id,
        "action_type": action_type,
    }
    return {key: value for key, value in values.items() if value is not None}


def weak_current_owner_ticket_action(
    *,
    study_id: str,
    quest_id: str | None,
    action_type: str,
    owner: str,
    work_unit_id: str,
    source_surface: str,
    current_action: Mapping[str, Any],
    ticket: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"study-progress-current-owner-ticket::{study_id}::{action_type}",
        "reason": WEAK_CURRENT_OWNER_TICKET_REASON,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "study_progress.current_owner_ticket_weak_identity",
        "source_surface": source_surface,
        "current_action_source": _text(current_action.get("source"))
        or _text(current_action.get("source_surface")),
        "source_ref": _text(current_action.get("source_ref")) or _text(ticket.get("source_ref")),
        "work_unit_id": work_unit_id,
        "default_dispatch_allowed": False,
        "default_dispatch_blocked_reason": WEAK_CURRENT_OWNER_TICKET_REASON,
        "weak_currentness_identity": {
            "missing_any_of": [
                "owner_route_currentness_basis",
                "source_fingerprint",
                "work_unit_fingerprint",
                "source_eval_id",
            ],
            "synthetic_fingerprint_forbidden": _SYNTHETIC_PREFIX,
        },
    }


def _payload_has_strong_currentness(payload: Mapping[str, Any]) -> bool:
    return any(
        _strong_text(payload.get(key)) is not None
        for key in (
            "source_fingerprint",
            "work_unit_fingerprint",
            "action_fingerprint",
            "source_eval_id",
        )
    )


def _first_strong_text(*values: object) -> str | None:
    for value in values:
        text = _strong_text(value)
        if text is not None:
            return text
    return None


def _strong_text(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    if text.startswith(_SYNTHETIC_PREFIX):
        return None
    if text == "unknown":
        return None
    return text


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "WEAK_CURRENT_OWNER_TICKET_REASON",
    "owner_route_has_strong_currentness",
    "owner_route_values",
    "weak_current_owner_ticket_action",
]
