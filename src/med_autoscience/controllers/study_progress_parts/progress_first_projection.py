from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_output_surface_for_action_type,
    request_output_target_surface_for_action_type,
    request_owner_for_action_type,
)
from med_autoscience.controllers.ai_reviewer_record_work_units import (
    AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
from med_autoscience.controllers.story_surface_work_units import is_story_surface_delta_write_work_unit
from med_autoscience.stage_route_contract import PROGRESS_FIRST_SPRINT_ID


PROGRESS_FIRST_OUTCOME_CLASSES = (
    "canonical_paper_or_artifact_delta",
    "ai_reviewer_current_record",
    "gate_replay_result",
    "human_gate",
    "stop_loss",
)
CURRENT_AI_REVIEWER_RECORD_CONSUMPTION_WRITE_WORK_UNIT_IDS = AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS


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
    next_forced_delta = _next_forced_delta(
        state=state,
        current_blockers=payload.get("current_blockers"),
        owner_route=owner_route,
    )
    current_owner_ticket = _current_owner_ticket(
        owner_route=owner_route,
        state=state,
        next_forced_delta=next_forced_delta,
    )
    next_forced_delta["current_owner_ticket"] = current_owner_ticket
    return {
        "progress_first_sprint_state": state,
        "next_forced_delta": next_forced_delta,
        "current_owner_ticket": current_owner_ticket,
    }


def _next_forced_delta(
    *,
    state: Mapping[str, Any],
    current_blockers: object,
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    target_surface = _target_surface(owner_route=owner_route)
    specificity = _target_surface_specificity(owner_route=owner_route)
    acceptance_refs = _acceptance_refs(owner_route=owner_route)
    owner_action = _owner_action(owner_route=owner_route, state=state)
    if state.get("paper_progress_delta_counted") is True:
        return {
            "required_delta_kind": "review_current_paper_delta",
            "reason": "paper_progress_delta_observed",
            "work_unit_id": _text(state.get("work_unit_id")),
            "eval_id": _text(state.get("eval_id")),
            "target_surface": target_surface,
            **specificity,
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
        **specificity,
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
    transition_route = _owner_route_from_domain_transition(payload)
    handoff = _mapping(payload.get("opl_current_control_state_handoff"))
    if route := _owner_route_from_handoff_action_queue(handoff):
        return route
    if route := _mapping(handoff.get("owner_route")):
        route = _owner_route_with_policy_target_surface(route)
        if transition_route and not _route_has_explicit_target_surface(route):
            return transition_route
        return route
    evidence_handoff = _mapping(_mapping(payload.get("current_execution_evidence")).get("opl_current_control_state_handoff"))
    if route := _owner_route_from_handoff_action_queue(evidence_handoff):
        return route
    if route := _mapping(evidence_handoff.get("owner_route")):
        route = _owner_route_with_policy_target_surface(route)
        if transition_route and not _route_has_explicit_target_surface(route):
            return transition_route
        return route
    if transition_route:
        return transition_route
    envelope = _mapping(payload.get("current_execution_envelope"))
    if route := _mapping(envelope.get("owner_route")):
        route = _owner_route_with_policy_target_surface(route)
        if transition_route and not _route_has_explicit_target_surface(route):
            return transition_route
        return route
    status = _mapping(payload.get("status"))
    route = _owner_route_with_policy_target_surface(_mapping(status.get("owner_route")))
    if transition_route and not _route_has_explicit_target_surface(route):
        return transition_route
    return route


def _owner_route_from_handoff_action_queue(handoff: Mapping[str, Any]) -> dict[str, Any]:
    action = _first_current_action_queue_item(handoff.get("action_queue"))
    if action is None:
        return {}
    action_type = _text(action.get("action_type"))
    if action_type is None:
        return {}
    handoff_route = _mapping(handoff.get("owner_route"))
    next_work_unit = _mapping(action.get("next_work_unit"))
    work_unit_id = (
        _text(next_work_unit.get("unit_id"))
        or _text(action.get("controller_work_unit_id"))
        or _text(action.get("work_unit_id"))
        or action_type
    )
    next_owner = (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_route.get("next_owner"))
        or request_owner_for_action_type(action_type)
    )
    route_target = (
        _text(action.get("route_target"))
        or _text(handoff_route.get("route_target"))
        or _text(handoff_route.get("next_route"))
        or next_owner
    )
    required_output_surface = _text(action.get("required_output_surface"))
    target_surface = _action_queue_target_surface(
        action=action,
        action_type=action_type,
        route_target=route_target,
    )
    source_refs = {
        key: value
        for key, value in {
            **_mapping(handoff_route.get("source_refs")),
            "work_unit_id": work_unit_id,
            "source_eval_id": _text(action.get("source_eval_id")) or _text(handoff_route.get("source_eval_id")),
            "source_fingerprint": _text(action.get("source_fingerprint"))
            or _text(action.get("fingerprint"))
            or _text(handoff_route.get("source_fingerprint")),
        }.items()
        if value is not None
    }
    route: dict[str, Any] = {
        **handoff_route,
        "next_owner": next_owner,
        "route_target": route_target,
        "allowed_actions": [action_type],
        "source_refs": source_refs,
        "owner_action": {
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
        },
        "target_surface": target_surface,
        "target_surface_source": (
            "opl_current_control_state.action_queue.required_output_surface"
            if required_output_surface is not None
            else "default_executor_action_policy.request_output_surface_for_action_type"
        ),
    }
    if source_fingerprint := _text(source_refs.get("source_fingerprint")):
        route["source_fingerprint"] = source_fingerprint
    return route


def _first_current_action_queue_item(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if not isinstance(item, Mapping):
            continue
        payload = dict(item)
        consumption = _mapping(payload.get("consumption"))
        status = _text(payload.get("consumption_status")) or _text(consumption.get("status"))
        if status in {"consumed", "receipt_consumed", "completed"}:
            continue
        return payload
    return None


def _action_queue_target_surface(
    *,
    action: Mapping[str, Any],
    action_type: str,
    route_target: str | None,
) -> dict[str, Any]:
    explicit = _mapping(action.get("required_output_target_surface"))
    if explicit:
        return explicit
    target_surface = request_output_target_surface_for_action_type(action_type)
    if target_surface is not None:
        return target_surface
    required_output_surface = _text(action.get("required_output_surface"))
    return {
        "ref_kind": "route_obligation",
        "route_target": route_target,
        "surface_ref": required_output_surface or request_output_surface_for_action_type(action_type),
    }


def _route_has_explicit_target_surface(route: Mapping[str, Any]) -> bool:
    return bool(_mapping(route.get("target_surface")) or _mapping(route.get("next_forced_target_surface")))


def _owner_route_with_policy_target_surface(route: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(route)
    if _route_has_explicit_target_surface(payload):
        return payload
    source_refs = _mapping(payload.get("source_refs"))
    work_unit_id = _text(source_refs.get("work_unit_id")) or _text(payload.get("work_unit_id"))
    action_type = _policy_action_type_for_route(payload, work_unit_id=work_unit_id)
    if action_type is None:
        return payload
    route_target = (
        _text(payload.get("route_target"))
        or _text(payload.get("next_route"))
        or _text(payload.get("next_owner"))
        or request_owner_for_action_type(action_type)
    )
    target_surface = request_output_target_surface_for_action_type(action_type)
    if target_surface is None:
        target_surface = {
            "ref_kind": "route_obligation",
            "route_target": route_target,
            "surface_ref": request_output_surface_for_action_type(action_type),
        }
    payload["route_target"] = route_target
    payload["target_surface"] = target_surface
    payload["target_surface_source"] = "default_executor_action_policy.request_output_surface_for_action_type"
    if not _mapping(payload.get("owner_action")):
        payload["owner_action"] = {
            "next_owner": _text(payload.get("next_owner")) or request_owner_for_action_type(action_type),
            "work_unit_id": work_unit_id,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
        }
    return payload


def _policy_action_type_for_route(route: Mapping[str, Any], *, work_unit_id: str | None) -> str | None:
    explicit = _first_text(route.get("allowed_actions")) or _first_text(route.get("allowed_action_refs"))
    owner_action = _mapping(route.get("owner_action"))
    action_type = explicit or _first_text(owner_action.get("allowed_actions"))
    if action_type in {"run_quality_repair_batch", "run_gate_clearing_batch"}:
        return action_type
    if action_type is not None and request_output_target_surface_for_action_type(action_type) is not None:
        return action_type
    if _publication_gate_replay_work_unit(work_unit_id):
        return "run_gate_clearing_batch"
    if _write_quality_repair_work_unit(work_unit_id):
        return "run_quality_repair_batch"
    return None


def _owner_route_from_domain_transition(payload: Mapping[str, Any]) -> dict[str, Any]:
    transition = _mapping(payload.get("domain_transition"))
    if not transition:
        return {}
    next_owner = _text(transition.get("owner"))
    route_target = _text(transition.get("route_target"))
    work_unit = _mapping(transition.get("next_work_unit"))
    work_unit_id = _text(work_unit.get("unit_id"))
    action_type = _domain_transition_action_type(
        controller_action=_text(transition.get("controller_action")),
        work_unit_id=work_unit_id,
    )
    if next_owner is None and route_target is None and work_unit_id is None and action_type is None:
        return {}
    guard = _mapping(transition.get("guard_boundary"))
    target_surface_ref = _domain_transition_target_surface_ref(
        guard=guard,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    completion = _mapping(transition.get("completion_receipt_consumption"))
    route: dict[str, Any] = {
        "next_owner": next_owner,
        "route_target": route_target,
        "next_work_unit": work_unit,
        "required_input_refs": _ref_items(transition.get("source_refs"))
        + _ref_items(transition.get("evidence_refs")),
        "source_refs": {
            key: value
            for key, value in {
                "work_unit_id": work_unit_id,
                "source_eval_id": _text(completion.get("eval_id")),
                "source_fingerprint": _text(completion.get("action_fingerprint")),
            }.items()
            if value is not None
        },
        "owner_action": {
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": [action_type] if action_type is not None else [],
            "owner_receipt_required": True,
        },
    }
    if action_type is not None:
        route["allowed_actions"] = [action_type]
    if target_surface_ref is not None:
        route["target_surface"] = {
            "ref_kind": "route_obligation",
            "route_target": route_target,
            "surface_ref": target_surface_ref,
        }
        route["target_surface_source"] = (
            _domain_transition_target_surface_source(
                guard=guard,
                action_type=action_type,
                work_unit_id=work_unit_id,
            )
        )
    return route


def _domain_transition_action_type(*, controller_action: str | None, work_unit_id: str | None) -> str | None:
    if _publication_gate_replay_work_unit(work_unit_id):
        return "run_gate_clearing_batch"
    if _write_quality_repair_work_unit(work_unit_id):
        return "run_quality_repair_batch"
    if controller_action == "request_opl_stage_attempt":
        return None
    return controller_action


def _domain_transition_target_surface_ref(
    *,
    guard: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    if action_type is not None and (
        _publication_gate_replay_action(action_type) or _write_quality_repair_work_unit(work_unit_id)
    ):
        return request_output_surface_for_action_type(action_type)
    return _text(guard.get("required_owner_surface")) or (
        request_output_surface_for_action_type(action_type) if action_type is not None else None
    )


def _domain_transition_target_surface_source(
    *,
    guard: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
) -> str:
    if action_type is not None and (
        _publication_gate_replay_action(action_type) or _write_quality_repair_work_unit(work_unit_id)
    ):
        return "default_executor_action_policy.request_output_surface_for_action_type"
    if _text(guard.get("required_owner_surface")) is not None:
        return "domain_transition.guard_boundary.required_owner_surface"
    return "default_executor_action_policy.request_output_surface_for_action_type"


def _publication_gate_replay_work_unit(work_unit_id: str | None) -> bool:
    return work_unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS


def _write_quality_repair_work_unit(work_unit_id: str | None) -> bool:
    return (
        work_unit_id in CURRENT_AI_REVIEWER_RECORD_CONSUMPTION_WRITE_WORK_UNIT_IDS
        or is_story_surface_delta_write_work_unit(work_unit_id)
    )


def _publication_gate_replay_action(action_type: str) -> bool:
    return action_type == "run_gate_clearing_batch"


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


def _target_surface_specificity(*, owner_route: Mapping[str, Any]) -> dict[str, Any]:
    if _mapping(owner_route.get("target_surface")):
        return {
            "target_surface_specificity": "explicit_owner_route_target",
            "missing_explicit_target_surface": False,
            "target_surface_diagnostic": {
                "specificity": "precise",
                "source": _text(owner_route.get("target_surface_source")) or "owner_route.target_surface",
                "missing_explicit_target_surface": False,
            },
        }
    if _mapping(owner_route.get("next_forced_target_surface")):
        return {
            "target_surface_specificity": "explicit_owner_route_target",
            "missing_explicit_target_surface": False,
            "target_surface_diagnostic": {
                "specificity": "precise",
                "source": "owner_route.next_forced_target_surface",
                "missing_explicit_target_surface": False,
            },
        }
    fallback_reason = "owner_route_missing_explicit_target_surface"
    return {
        "target_surface_specificity": "generic_route_obligation_fallback",
        "missing_explicit_target_surface": True,
        "target_surface_fallback_reason": fallback_reason,
        "target_surface_diagnostic": {
            "specificity": "generic_fallback",
            "source": "study_progress.next_forced_delta",
            "missing_explicit_target_surface": True,
            "fallback_reason": fallback_reason,
        },
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


def _current_owner_ticket(
    *,
    owner_route: Mapping[str, Any],
    state: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> dict[str, Any]:
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    allowed_actions = _text_items(owner_action.get("allowed_actions")) or _text_items(
        owner_route.get("allowed_actions")
    )
    work_unit_id = _text(owner_action.get("work_unit_id")) or _text(state.get("work_unit_id"))
    source_refs = _mapping(owner_route.get("source_refs"))
    return {
        "surface_kind": "mas_current_owner_ticket",
        "schema_version": 1,
        "owner": _text(owner_action.get("next_owner")) or _text(owner_route.get("next_owner")),
        "allowed_action": allowed_actions[0] if allowed_actions else None,
        "work_unit": _compact(
            {
                "work_unit_id": work_unit_id,
                "summary": _work_unit_summary(owner_route),
            }
        ),
        "required_input_refs": _input_refs(owner_route=owner_route, source_refs=source_refs),
        "target_surface": _mapping(next_forced_delta.get("target_surface")),
        "acceptance_criteria": list(next_forced_delta.get("acceptance_refs") or []),
        "forbidden_writes": [
            "study_truth",
            "memory_body",
            "artifact_body",
            "publication_verdict",
            "source_readiness_verdict",
            "current_package",
        ],
        "expected_receipt_or_blocker": [
            "owner_receipt",
            "typed_blocker",
            "route_back_request",
            "human_gate_request",
            "stop_loss",
        ],
        "no_loop_budget": {
            "platform_repair_is_not_deliverable_progress": True,
            "provider_completion_is_not_closeout": True,
            "repeat_same_work_unit_requires_typed_blocker_or_new_target_surface": True,
        },
        "authority_boundary": {
            "ticket_authorizes_next_attempt_only": True,
            "ticket_authorizes_publication_quality": False,
            "ticket_authorizes_artifact_mutation": False,
            "ticket_authorizes_study_truth_write": False,
        },
    }


def _work_unit_summary(owner_route: Mapping[str, Any]) -> str | None:
    for value in (
        _mapping(owner_route.get("next_work_unit")).get("summary"),
        owner_route.get("work_unit_summary"),
        owner_route.get("summary"),
    ):
        if text := _text(value):
            return text
    return None


def _input_refs(*, owner_route: Mapping[str, Any], source_refs: Mapping[str, Any]) -> list[str]:
    explicit_refs = _ref_items(owner_route.get("required_input_refs"))
    if explicit_refs:
        return list(dict.fromkeys(explicit_refs))
    refs: list[str] = []
    for value in (
        owner_route.get("evidence_refs"),
        owner_route.get("source_refs"),
        source_refs,
    ):
        refs.extend(_ref_items(value))
    return list(dict.fromkeys(refs))


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


def _first_text(value: object) -> str | None:
    if isinstance(value, str):
        return _text(value)
    if not isinstance(value, list | tuple):
        return None
    for item in value:
        if text := _text(item):
            return text
    return None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _ref_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_ref_items(item))
        return result
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        result.extend(_ref_items(item))
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["PROGRESS_FIRST_OUTCOME_CLASSES", "build_progress_first_projection"]
