from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer_parts import current_action_selection
from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import consumed_transition_currentness
from . import owner_request_paths
from . import stage_artifact_publication_handoff_currentness


def with_consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    study = dict(current_study)
    if stage_artifact_publication_handoff_currentness.is_current(study):
        return study
    transition_route = consumed_transition_owner_route(study)
    if transition_route:
        study["owner_route"] = transition_route
    return study


def consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    transition = _mapping(current_study.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return {}
    route = current_action_selection.domain_transition_owner_route_for_study(current_study)
    if gate_replay_route(route):
        return route
    if _text(transition.get("controller_action")) is None:
        return {}
    next_work_unit = _mapping(transition.get("next_work_unit"))
    if not next_work_unit:
        return {}
    action_type = _action_type_for_consumed_transition(transition=transition, next_work_unit=next_work_unit)
    if action_type is None:
        return {}
    study_id = _text(current_study.get("study_id"))
    if study_id is None:
        return {}
    owner = _owner_for_consumed_transition(action_type=action_type, transition=transition)
    work_unit_id = _text(next_work_unit.get("unit_id")) or _text(next_work_unit.get("work_unit_id"))
    truth = _mapping(current_study.get("study_truth_snapshot"))
    route_epoch = _text(truth.get("truth_epoch")) or _text(truth.get("authority_epoch")) or study_id
    source_fingerprint = _text(truth.get("source_signature")) or (
        f"domain-transition::{_text(transition.get('decision_type')) or 'current'}::{work_unit_id or action_type}"
    )
    current_route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    current_basis = _mapping(_mapping(current_route.get("currentness_contract")).get("basis")) or _mapping(
        _mapping(current_route.get("source_refs")).get("owner_route_currentness_basis")
    )
    runtime_health_epoch = _text(_mapping(current_study.get("runtime_health_snapshot")).get("runtime_health_epoch")) or _text(
        current_basis.get("runtime_health_epoch")
    )
    owner_reason = work_unit_id or _text(transition.get("decision_type")) or action_type
    work_unit_fingerprint = (
        _text(transition.get("work_unit_fingerprint"))
        or _text(next_work_unit.get("fingerprint"))
        or f"domain-transition::{_text(transition.get('decision_type')) or 'current'}::{work_unit_id or action_type}"
    )
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": _text(current_study.get("quest_id")),
        "truth_epoch": route_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "failure_signature": owner_reason,
        "trace_id": f"owner-route-trace::{study_id}::consumed-transition::{action_type}",
        "route_epoch": route_epoch,
        "source_fingerprint": source_fingerprint,
        "current_owner": _text(current_study.get("current_owner")) or "mas_controller",
        "next_owner": owner,
        "owner_reason": owner_reason,
        "active_run_id": _text(current_study.get("active_run_id")),
        "allowed_actions": [action_type],
        "blocked_actions": [item for item in owner_request_paths.OWNER_REQUEST_RELATIVE_PATHS if item != action_type],
        "idempotency_key": f"owner-route::{study_id}::{route_epoch}::{owner}::{owner_reason}",
        "source_refs": {
            "source_eval_id": _text(completion.get("eval_id"))
            or _text(transition.get("source_eval_id"))
            or _text(transition.get("publication_eval_id"))
            or _text(_mapping(transition.get("publication_eval_ref")).get("eval_id"))
            or _text(_mapping(current_study.get("publication_eval")).get("eval_id"))
            or _text(current_basis.get("source_eval_id")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "runtime_health_epoch": runtime_health_epoch,
            "blocked_reason": owner_reason,
            "receipt_ref": _text(completion.get("receipt_ref")),
        },
    }
    return owner_route_part.ensure_owner_route_v2(route)


def gate_replay_route(route: Mapping[str, Any]) -> bool:
    if not route:
        return False
    source_refs = _mapping(route.get("source_refs"))
    return (
        _text(route.get("next_owner")) == "gate_clearing_batch"
        and "run_gate_clearing_batch" in {_text(item) for item in route.get("allowed_actions") or []}
        and _text(source_refs.get("work_unit_id")) in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
    )


def matching_consumed_transition_route(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    if stage_artifact_publication_handoff_currentness.is_current(current_study):
        return None
    route = consumed_transition_owner_route(current_study)
    if not route:
        return None
    return consumed_transition_currentness.matching_route_for_dispatch(
        dispatch=dispatch,
        transition_route=route,
        gate_replay=gate_replay_route(route),
    )


def _action_type_for_consumed_transition(
    *,
    transition: Mapping[str, Any],
    next_work_unit: Mapping[str, Any],
) -> str | None:
    decision_type = _text(transition.get("decision_type"))
    route_target = _text(transition.get("route_target"))
    controller_action = _text(transition.get("controller_action"))
    work_unit_id = _text(next_work_unit.get("unit_id")) or _text(next_work_unit.get("work_unit_id"))
    if work_unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return "run_gate_clearing_batch"
    if decision_type == "route_back_same_line" and route_target == "write":
        return "run_quality_repair_batch"
    if controller_action == "run_gate_clearing_batch":
        return "run_gate_clearing_batch"
    if controller_action == "return_to_ai_reviewer_workflow":
        return "return_to_ai_reviewer_workflow"
    if controller_action == "request_opl_stage_attempt" and work_unit_id:
        return "run_quality_repair_batch"
    return None


def _owner_for_consumed_transition(*, action_type: str, transition: Mapping[str, Any]) -> str:
    if action_type == "run_quality_repair_batch":
        return "write"
    if action_type == "run_gate_clearing_batch":
        return "gate_clearing_batch"
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    return _text(transition.get("owner")) or "med-autoscience"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "consumed_transition_owner_route",
    "gate_replay_route",
    "matching_consumed_transition_route",
    "with_consumed_transition_owner_route",
]
