from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.profiles import WorkspaceProfile


def materialize_fresh_ai_reviewer_transition_controller_decision_if_required(
    *,
    study_root: Path,
    profile: WorkspaceProfile | None = None,
    status_payload: Mapping[str, Any] | None = None,
    source: str = "med_autoscience",
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_profile = profile or gate_clearing_batch.resolve_profile_for_study_root(resolved_study_root)
    if resolved_profile is None:
        return None
    outer_loop = import_module("med_autoscience.controllers.study_outer_loop")
    status = _status_payload(
        profile=resolved_profile,
        study_root=resolved_study_root,
        status_payload=status_payload,
    )
    domain_transition = _mapping(status.get("domain_transition"))
    transition_unit = _mapping(domain_transition.get("next_work_unit"))
    transition_unit_id = _text(transition_unit.get("unit_id"))
    transition_action = _text(domain_transition.get("controller_action"))
    transition_type = _text(domain_transition.get("decision_type"))
    if (
        transition_type != "ai_reviewer_re_eval"
        or transition_action != "return_to_ai_reviewer_workflow"
        or transition_unit_id is None
    ):
        return None
    tick_request = outer_loop.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=resolved_study_root,
        status_payload=dict(status),
    )
    if not isinstance(tick_request, dict):
        return None
    if not tick_request_matches_ai_reviewer_domain_transition(
        tick_request=tick_request,
        transition_action=transition_action,
        transition_type=transition_type,
        transition_unit_id=transition_unit_id,
    ):
        return None
    if latest_controller_decision_matches_tick_request(
        study_root=resolved_study_root,
        tick_request=tick_request,
    ):
        return {
            "status": "already_current",
            "work_unit_id": transition_unit_id,
            "work_unit_fingerprint": _text(tick_request.get("work_unit_fingerprint")),
        }
    materialized = outer_loop.materialize_non_dispatching_outer_loop_decision(
        profile=resolved_profile,
        study_id=_text(status.get("study_id")) or resolved_study_root.name,
        study_root=resolved_study_root,
        status_payload=dict(status),
        charter_ref=tick_request["charter_ref"],
        publication_eval_ref=tick_request["publication_eval_ref"],
        decision_type=str(tick_request["decision_type"]),
        route_target=_text(tick_request.get("route_target")),
        route_key_question=_text(tick_request.get("route_key_question")),
        route_rationale=_text(tick_request.get("route_rationale")),
        source_route_key_question=_text(tick_request.get("source_route_key_question")),
        work_unit_fingerprint=_text(tick_request.get("work_unit_fingerprint")),
        next_work_unit=_mapping_or_none(tick_request.get("next_work_unit")),
        blocking_work_units=[
            dict(item) for item in tick_request.get("blocking_work_units") or [] if isinstance(item, Mapping)
        ],
        requires_human_confirmation=bool(tick_request.get("requires_human_confirmation")),
        controller_actions=[
            dict(item) for item in tick_request.get("controller_actions") or [] if isinstance(item, Mapping)
        ],
        reason=_text(tick_request.get("reason"))
        or "fresh domain transition requires current controller authorization before runtime turn",
        source=source,
    )
    return {
        "status": "materialized",
        "work_unit_id": transition_unit_id,
        "work_unit_fingerprint": _text(tick_request.get("work_unit_fingerprint")),
        "materialization": dict(materialized) if isinstance(materialized, Mapping) else {},
    }


def tick_request_matches_ai_reviewer_domain_transition(
    *,
    tick_request: Mapping[str, Any],
    transition_action: str,
    transition_type: str,
    transition_unit_id: str,
) -> bool:
    tick_unit_id = work_unit_id_from_tick_request(tick_request)
    if tick_unit_id != transition_unit_id:
        return False
    if transition_action not in controller_action_types_from_tick_request(tick_request):
        return False
    fingerprint = _text(tick_request.get("work_unit_fingerprint"))
    return fingerprint == f"domain-transition::{transition_type}::{transition_unit_id}"


def latest_controller_decision_matches_tick_request(
    *,
    study_root: Path,
    tick_request: Mapping[str, Any],
) -> bool:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    try:
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return False
    if not isinstance(decision, Mapping):
        return False
    decision_actions = controller_action_types_from_tick_request({"controller_actions": decision.get("controller_actions")})
    tick_actions = controller_action_types_from_tick_request(tick_request)
    decision_unit = _mapping(decision.get("next_work_unit"))
    decision_unit_id = _text(decision_unit.get("unit_id"))
    return (
        _text(decision.get("work_unit_fingerprint")) == _text(tick_request.get("work_unit_fingerprint"))
        and decision_unit_id == work_unit_id_from_tick_request(tick_request)
        and decision_actions == tick_actions
    )


def work_unit_id_from_tick_request(tick_request: Mapping[str, Any]) -> str | None:
    next_work_unit = _mapping(tick_request.get("next_work_unit"))
    return _text(next_work_unit.get("unit_id"))


def controller_action_types_from_tick_request(tick_request: Mapping[str, Any]) -> list[str]:
    action_types: list[str] = []
    for item in tick_request.get("controller_actions") or []:
        if not isinstance(item, Mapping):
            continue
        action_type = _text(item.get("action_type"))
        if action_type:
            action_types.append(action_type)
    return sorted(set(action_types))


def _status_payload(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if isinstance(status_payload, Mapping) and status_payload:
        return dict(status_payload)
    router = import_module("med_autoscience.controllers.study_runtime_router")
    payload = router.progress_projection(
        profile=profile,
        study_root=study_root,
        sync_runtime_summary=False,
        include_progress_projection=False,
    )
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_or_none(value: object) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, Mapping) else None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "controller_action_types_from_tick_request",
    "latest_controller_decision_matches_tick_request",
    "materialize_fresh_ai_reviewer_transition_controller_decision_if_required",
    "tick_request_matches_ai_reviewer_domain_transition",
    "work_unit_id_from_tick_request",
]
