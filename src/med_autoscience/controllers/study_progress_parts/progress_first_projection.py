from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.stage_route_contract import PROGRESS_FIRST_SPRINT_ID


PROGRESS_FIRST_OUTCOME_CLASSES = (
    "canonical_paper_or_artifact_delta",
    "ai_reviewer_current_record",
    "gate_replay_result",
    "human_gate",
    "stop_loss",
)


def build_progress_first_projection(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    deliverable_delta = _mapping(payload.get("deliverable_progress_delta")) or _mapping(payload.get("paper_progress_delta"))
    paper_delta = _mapping(payload.get("paper_progress_delta")) or deliverable_delta
    platform_delta = _mapping(payload.get("platform_repair_delta"))
    owner_route = _current_owner_route(payload)
    source_refs = _mapping(owner_route.get("source_refs"))
    work_unit_id = _text(source_refs.get("work_unit_id")) or _text(owner_route.get("work_unit_id"))
    eval_id = _text(source_refs.get("source_eval_id")) or _text(owner_route.get("source_eval_id"))
    source_fingerprint = _text(owner_route.get("source_fingerprint")) or _text(source_refs.get("source_fingerprint"))
    paper_count = _delta_count(deliverable_delta)
    platform_count = _delta_count(platform_delta)
    classification = _classification(paper_count=paper_count, platform_count=platform_count)
    state = {
        "surface": "progress_first_sprint_state",
        "schema_version": 1,
        "sprint_id": PROGRESS_FIRST_SPRINT_ID,
        "classification": classification,
        "paper_progress_delta_counted": paper_count > 0,
        "platform_repair_delta_counted": platform_count > 0,
        "deliverable_progress_delta": deliverable_delta,
        "paper_progress_delta": paper_delta,
        "platform_repair_delta": platform_delta,
        "work_unit_id": work_unit_id,
        "eval_id": eval_id,
        "source_fingerprint": source_fingerprint,
        "next_owner": _text(owner_route.get("next_owner")),
        "allowed_nonterminal_outcomes": list(PROGRESS_FIRST_OUTCOME_CLASSES),
        "platform_only_is_paper_progress": False,
    }
    return {
        "progress_first_sprint_state": state,
        "next_forced_delta": _next_forced_delta(
            state=state,
            current_blockers=payload.get("current_blockers"),
            owner_route=owner_route,
        ),
    }


def _next_forced_delta(
    *,
    state: Mapping[str, Any],
    current_blockers: object,
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    target_surface = _target_surface(owner_route=owner_route)
    acceptance_refs = _acceptance_refs(owner_route=owner_route)
    owner_action = _owner_action(owner_route=owner_route, state=state)
    if state.get("paper_progress_delta_counted") is True:
        return {
            "required_delta_kind": "review_current_paper_delta",
            "reason": "paper_progress_delta_observed",
            "work_unit_id": _text(state.get("work_unit_id")),
            "eval_id": _text(state.get("eval_id")),
            "target_surface": target_surface,
            "acceptance_refs": acceptance_refs,
            "owner_action": owner_action,
        }
    return {
        "required_delta_kind": "paper_progress_delta_or_typed_blocker",
        "reason": _forced_delta_reason(
            classification=_text(state.get("classification")),
            current_blockers=current_blockers,
        ),
        "work_unit_id": _text(state.get("work_unit_id")),
        "eval_id": _text(state.get("eval_id")),
        "next_owner": _text(state.get("next_owner")),
        "allowed_outcomes": list(PROGRESS_FIRST_OUTCOME_CLASSES),
        "target_surface": target_surface,
        "acceptance_refs": acceptance_refs,
        "owner_action": owner_action,
    }


def _classification(*, paper_count: int, platform_count: int) -> str:
    if paper_count > 0 and platform_count > 0:
        return "mixed"
    if paper_count > 0:
        return "deliverable_progress"
    if platform_count > 0:
        return "platform_repair"
    return "typed_blocker"


def _forced_delta_reason(*, classification: str | None, current_blockers: object) -> str:
    if classification == "platform_repair":
        return "platform_repair_does_not_count_as_paper_progress"
    blockers = [item for item in current_blockers or [] if _text(item)]
    if blockers:
        return "current_blocker_requires_typed_closeout_or_next_owner"
    return "nonterminal_sprint_requires_progress_delta_or_blocker"


def _current_owner_route(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping(payload.get("opl_current_control_state_handoff"))
    if route := _mapping(handoff.get("owner_route")):
        return route
    envelope = _mapping(payload.get("current_execution_envelope"))
    if route := _mapping(envelope.get("owner_route")):
        return route
    status = _mapping(payload.get("status"))
    return _mapping(status.get("owner_route"))


def _target_surface(*, owner_route: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(owner_route.get("target_surface")) or _mapping(owner_route.get("next_forced_target_surface"))
    if explicit:
        return explicit
    route_target = _text(owner_route.get("route_target")) or _text(owner_route.get("next_route"))
    return {
        "ref_kind": "route_obligation",
        "route_target": route_target,
        "surface_ref": "study_progress.next_forced_delta",
    }


def _acceptance_refs(*, owner_route: Mapping[str, Any]) -> list[Any]:
    explicit = owner_route.get("acceptance_refs")
    if isinstance(explicit, list):
        return list(explicit)
    explicit_criteria = owner_route.get("acceptance_criteria")
    if isinstance(explicit_criteria, list):
        return list(explicit_criteria)
    return [
        "progress_first_sprint_state.deliverable_progress_delta",
        "progress_first_sprint_state.platform_repair_delta",
        "stage_contract.minimum_forward_delta",
        "stage_contract.human_gate_progress_evidence",
    ]


def _owner_action(*, owner_route: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(owner_route.get("owner_action"))
    if explicit:
        return explicit
    allowed_actions = owner_route.get("allowed_actions") or owner_route.get("allowed_action_refs")
    return {
        "next_owner": _text(owner_route.get("next_owner")) or _text(state.get("next_owner")),
        "work_unit_id": _text(state.get("work_unit_id")),
        "allowed_actions": list(allowed_actions) if isinstance(allowed_actions, list) else [],
        "owner_receipt_required": True,
    }


def _delta_count(payload: Mapping[str, Any]) -> int:
    value = payload.get("count")
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except ValueError:
            return 0
    return 0


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["PROGRESS_FIRST_OUTCOME_CLASSES", "build_progress_first_projection"]
