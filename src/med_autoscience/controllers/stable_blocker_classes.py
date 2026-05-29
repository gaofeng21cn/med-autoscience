from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


DISPATCH_SUPERSEDED_BLOCKER = "dispatch_superseded_by_current_owner_route"
PUBLICATION_GATE_SUPERSESSION_BLOCKER = "publication_gate_supersession_blocked"
RUNTIME_RECOVERY_BLOCKER = "runtime_recovery_blocked"
CURRENT_OWNER_ROUTE_BLOCKER = "current_owner_route_blocked"
STAGE_ATTEMPT_CLOSEOUT_BLOCKER = "stage_attempt_closeout_blocked"


_DISPATCH_SUPERSEDED_REASONS = {
    "stale_return_to_ai_reviewer_dispatch_superseded_by_consumed_ai_reviewer_routeback",
    "stale_return_to_ai_reviewer_dispatch_superseded_by_consumed_ai_reviewer_production_handoff",
    "stale_return_to_ai_reviewer_dispatch_superseded_by_current_ai_reviewer_stage_admission",
    "stale_return_to_ai_reviewer_dispatch_superseded_by_ai_reviewer_currentness_route",
    "stale_run_quality_repair_dispatch_superseded_by_consumed_ai_reviewer_routeback",
    "stale_run_quality_repair_dispatch_superseded_by_current_ai_reviewer_stage_admission",
    "stale_run_quality_repair_dispatch_superseded_by_ai_reviewer_currentness_route",
}

_PUBLICATION_GATE_SUPERSESSION_REASONS = {
    "stale_run_quality_repair_dispatch_superseded_by_publication_gate_route",
    "stale_return_to_ai_reviewer_dispatch_superseded_by_publication_gate_route",
    "owner_authorized_publication_gate_replay_stage_attempt_blocker",
    "delivered_package_handoff_typed_blocker_observed_for_default_executor_dispatch",
}

_RUNTIME_RECOVERY_REASONS = {
    "runtime_recovery_not_authorized",
    "runtime_recovery_retry_budget_exhausted",
    "runtime_recovery_not_authorized_stage_attempt_blocker",
    "runtime_recovery_retry_budget_terminal_blocker",
    "quest_waiting_opl_runtime_owner_route",
}

_CURRENT_OWNER_ROUTE_REASONS = {
    "current_owner_route_typed_blocker_observed_for_default_executor_dispatch",
}

_STAGE_ATTEMPT_CLOSEOUT_REASONS = {
    "stage_attempt_closeout_typed_blocker_observed_for_default_executor_dispatch",
}

_EXPLANATIONS = {
    DISPATCH_SUPERSEDED_BLOCKER: (
        "The OPL default-executor dispatch is stale because the current MAS owner route "
        "or consumed handoff already supersedes that attempt."
    ),
    PUBLICATION_GATE_SUPERSESSION_BLOCKER: (
        "The previous dispatch is superseded by the current publication-gate owner route "
        "or human-gate blocker."
    ),
    RUNTIME_RECOVERY_BLOCKER: (
        "Runtime recovery state is diagnostic only here; it requires an OPL-owned "
        "stage-attempt admission receipt or typed blocker."
    ),
    CURRENT_OWNER_ROUTE_BLOCKER: (
        "The current MAS owner route is already a typed blocker, so the old dispatch "
        "must not be replayed as executable work."
    ),
    STAGE_ATTEMPT_CLOSEOUT_BLOCKER: (
        "The observed default-executor closeout is a typed blocker and does not close "
        "domain readiness or publication readiness."
    ),
}


def stable_blocker_class(reason: str | None) -> str | None:
    reason_text = _text(reason)
    if reason_text is None:
        return None
    if reason_text in _DISPATCH_SUPERSEDED_REASONS:
        return DISPATCH_SUPERSEDED_BLOCKER
    if reason_text in _PUBLICATION_GATE_SUPERSESSION_REASONS:
        return PUBLICATION_GATE_SUPERSESSION_BLOCKER
    if reason_text in _RUNTIME_RECOVERY_REASONS:
        return RUNTIME_RECOVERY_BLOCKER
    if reason_text in _CURRENT_OWNER_ROUTE_REASONS:
        return CURRENT_OWNER_ROUTE_BLOCKER
    if reason_text in _STAGE_ATTEMPT_CLOSEOUT_REASONS:
        return STAGE_ATTEMPT_CLOSEOUT_BLOCKER
    return reason_text


def blocker_explanation(blocker_class: str | None) -> str | None:
    return _EXPLANATIONS.get(_text(blocker_class) or "")


def blocker_details(
    *,
    blocker_class: str | None,
    detail_reason: str | None,
    action_type: str | None = None,
    owner_route: Mapping[str, Any] | None = None,
    domain_transition: Mapping[str, Any] | None = None,
    blocked_reason: str | None = None,
) -> dict[str, Any]:
    route = _mapping(owner_route)
    transition = _mapping(domain_transition)
    details = {
        "blocker_class": _text(blocker_class),
        "detail_reason": _text(detail_reason),
        "action_type": _text(action_type),
        "blocked_reason": _text(blocked_reason) or _text(route.get("owner_reason")),
        "owner_route_next_owner": _text(route.get("next_owner")),
        "owner_route_owner_reason": _text(route.get("owner_reason")),
        "domain_transition": _compact_mapping(
            {
                "decision_type": transition.get("decision_type"),
                "route_target": transition.get("route_target"),
                "owner": transition.get("owner"),
                "controller_action": transition.get("controller_action"),
            }
        ),
    }
    return _compact_mapping(details)


def source_refs_from_payloads(
    *payloads: Mapping[str, Any] | None,
    extra_refs: Sequence[object] = (),
) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        data = _mapping(payload)
        refs.extend(_strings(_sequence(data.get("source_refs"))))
        refs.extend(_strings(_mapping(data.get("source_refs")).values()))
        refs.extend(
            _strings(
                [
                    data.get("source_fingerprint"),
                    data.get("idempotency_key"),
                    data.get("work_unit_fingerprint"),
                ]
            )
        )
    refs.extend(_strings(extra_refs))
    return _unique(refs)


def _compact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value is not None and value != {} and value != []
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else ()


def _strings(values: Sequence[object]) -> list[str]:
    return [text for value in values if (text := _text(value))]


def _unique(values: Sequence[str]) -> list[str]:
    refs: list[str] = []
    for value in values:
        if value not in refs:
            refs.append(value)
    return refs


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "CURRENT_OWNER_ROUTE_BLOCKER",
    "DISPATCH_SUPERSEDED_BLOCKER",
    "PUBLICATION_GATE_SUPERSESSION_BLOCKER",
    "RUNTIME_RECOVERY_BLOCKER",
    "STAGE_ATTEMPT_CLOSEOUT_BLOCKER",
    "blocker_details",
    "blocker_explanation",
    "source_refs_from_payloads",
    "stable_blocker_class",
]
