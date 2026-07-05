from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def top_level_stage_closure_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    repair_budget = _stage_closure_repair_budget(payload)
    next_transition = (
        _non_empty_text(_mapping(outcome.get("next_transition")).get("transition_kind"))
        or _non_empty_text(outcome.get("transition_kind"))
        or _non_empty_text(outcome.get("next_action"))
    )
    stage_next_legal_action = _non_empty_text(outcome.get("next_action")) or next_transition
    next_legal_action = (
        _canonical_next_legal_action(payload)
        or stage_next_legal_action
    )
    return {
        "repair_budget": repair_budget or None,
        "next_legal_action": next_legal_action,
        "stage_closure": _compact(
            {
                "projection_status": _non_empty_text(decision.get("projection_status")),
                "decision_ref": _non_empty_text(decision.get("decision_ref")),
                "outcome": outcome or None,
                "outcome_kind": _non_empty_text(decision.get("outcome_kind"))
                or _non_empty_text(outcome.get("kind")),
                "next_transition": next_transition,
                "next_legal_action": stage_next_legal_action,
                "package_kind": _non_empty_text(decision.get("package_kind"))
                or _non_empty_text(outcome.get("package_kind")),
                "known_blockers": _text_list(decision.get("known_blockers")),
                "repair_budget": repair_budget or None,
            }
        )
        or None,
    }


def _canonical_next_legal_action(payload: Mapping[str, Any]) -> str | None:
    owner_gate_readback = _mapping(payload.get("submission_authority_owner_gate_readback"))
    owner_gate_action = _non_empty_text(owner_gate_readback.get("next_legal_action"))
    if owner_gate_action:
        return owner_gate_action
    next_action = _mapping(payload.get("next_action"))
    next_action_surface = _non_empty_text(next_action.get("surface_kind"))
    next_action_family = _non_empty_text(next_action.get("action_family"))
    next_action_type = _non_empty_text(next_action.get("action_type"))
    receipt_consumption = _mapping(payload.get("mas_receipt_consumption"))
    receipt_action = _non_empty_text(receipt_consumption.get("next_legal_action"))
    receipt_status = _non_empty_text(receipt_consumption.get("status"))
    if (
        receipt_status == "owner_consumed_route_checkpoint"
        and next_action_surface == "mas_next_action_envelope"
        and next_action_family != "paper.stage_closure.owner_consumption"
    ):
        receipt_action = None
    if (
        receipt_action
        and receipt_action != "request_opl_runtime_readback"
        and receipt_status != "owner_consumed_typed_blocker"
    ):
        return receipt_action
    if receipt_status == "owner_consumed_typed_blocker":
        return None
    if next_action_surface != "mas_next_action_envelope":
        return None
    action_family = next_action_family
    if action_family == "runtime.opl_route":
        return "request_opl_runtime_readback"
    if action_family == "paper.gate.publishability_replay":
        return "run_publication_gate_replay"
    if action_family == "blocked.typed":
        return "materialize_typed_blocker_or_route_redesign"
    if action_family == "human.approval":
        stage_closure = _mapping(payload.get("stage_closure_decision"))
        stage_outcome = _mapping(stage_closure.get("outcome"))
        if _non_empty_text(stage_outcome.get("next_action")):
            return None
        stage_decision = _mapping(payload.get("stage_terminal_decision"))
        route_command = _mapping(payload.get("opl_route_command"))
        if (
            _non_empty_text(stage_decision.get("decision_kind")) == "human_gate"
            or _non_empty_text(route_command.get("command_kind")) == "wait_for_human"
        ):
            return "request_human_decision"
    if next_action_type:
        return next_action_type
    return None


def _stage_closure_repair_budget(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("stage_closure_decision"))
    candidates = (
        _mapping(decision.get("repair_budget")),
        _mapping(
            _mapping(payload.get("quality_repair_batch_followthrough")).get(
                "repair_budget"
            )
        ),
        _mapping(
            _mapping(payload.get("gate_clearing_batch_followthrough")).get(
                "repair_budget"
            )
        ),
        _mapping(payload.get("route_back_budget")),
    )
    for candidate in candidates:
        budget = _normalize_repair_budget(candidate)
        if budget:
            return budget
    return {}


def _normalize_repair_budget(value: Mapping[str, Any]) -> dict[str, Any]:
    budget = _select_repair_budget_mapping(_mapping(value))
    max_count = _int_value(
        budget.get("repair_budget_max")
        or budget.get("max_attempts")
        or budget.get("max_opl_redrives")
    )
    attempt_count = _int_value(
        budget.get("repair_attempt_count")
        or budget.get("attempt_count")
        or budget.get("next_observed_count")
    )
    status = _non_empty_text(budget.get("repair_budget_status"))
    if status is None:
        if budget.get("budget_exhausted") is True:
            status = "exhausted"
        elif max_count is not None and attempt_count is not None:
            status = "exhausted" if attempt_count >= max_count else "remaining"
    return _compact(
        {
            "repair_budget_max": max_count,
            "repair_attempt_count": attempt_count,
            "repair_budget_status": status,
            "on_exhausted": _non_empty_text(budget.get("on_exhausted"))
            or ("degraded_handoff" if status == "exhausted" else None),
        }
    )


def _select_repair_budget_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(value)
    if _budget_has_attempt_fields(direct):
        return direct
    nested_candidates = [
        _mapping(direct.get("quality_repair_batch")),
        _mapping(direct.get("gate_clearing_batch")),
    ]
    for candidate in nested_candidates:
        if _non_empty_text(candidate.get("repair_budget_status")) == "exhausted":
            return candidate
    for candidate in nested_candidates:
        if _budget_has_attempt_fields(candidate):
            return candidate
    return direct


def _budget_has_attempt_fields(value: Mapping[str, Any]) -> bool:
    return any(
        key in value
        for key in (
            "repair_budget_max",
            "max_attempts",
            "max_opl_redrives",
            "repair_attempt_count",
            "attempt_count",
            "next_observed_count",
            "repair_budget_status",
            "budget_exhausted",
        )
    )


def _int_value(value: object) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _non_empty_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        text
        for text in (_non_empty_text(item) for item in value)
        if text is not None
    ]


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, [], {})}


__all__ = ["top_level_stage_closure_projection"]
