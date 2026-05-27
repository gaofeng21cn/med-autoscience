from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionType
from med_autoscience.profiles import WorkspaceProfile


def materialize_fresh_domain_transition_controller_decision_if_required(
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
    if not domain_transition_is_materializable(
        transition_action=transition_action,
        transition_type=transition_type,
        transition_unit_id=transition_unit_id,
    ):
        return None
    tick_request = outer_loop.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=resolved_study_root,
        status_payload=dict(status),
    )
    if not isinstance(tick_request, dict):
        tick_request = status_domain_transition_tick_request(
            study_root=resolved_study_root,
            status_payload=status,
        )
        if not isinstance(tick_request, dict):
            return None
    if not tick_request_matches_domain_transition(
        tick_request=tick_request,
        transition_action=transition_action,
        transition_type=transition_type,
        transition_unit_id=transition_unit_id,
    ):
        tick_request = status_domain_transition_tick_request(
            study_root=resolved_study_root,
            status_payload=status,
        )
        if not isinstance(tick_request, dict) or not tick_request_matches_domain_transition(
            tick_request=tick_request,
            transition_action=transition_action,
            transition_type=transition_type,
            transition_unit_id=transition_unit_id,
        ):
            return None
    currentness_basis = _text(tick_request.get("currentness_basis")) or "outer_loop_tick_request"
    if latest_controller_decision_matches_tick_request(
        study_root=resolved_study_root,
        tick_request=tick_request,
    ):
        return {
            "status": "already_current",
            "work_unit_id": transition_unit_id,
            "work_unit_fingerprint": _text(tick_request.get("work_unit_fingerprint")),
            "currentness_basis": currentness_basis,
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
        "currentness_basis": currentness_basis,
        "materialization": dict(materialized) if isinstance(materialized, Mapping) else {},
    }


def materialize_fresh_ai_reviewer_transition_controller_decision_if_required(
    *,
    study_root: Path,
    profile: WorkspaceProfile | None = None,
    status_payload: Mapping[str, Any] | None = None,
    source: str = "med_autoscience",
) -> dict[str, Any] | None:
    return materialize_fresh_domain_transition_controller_decision_if_required(
        study_root=study_root,
        profile=profile,
        status_payload=status_payload,
        source=source,
    )


def domain_transition_is_materializable(
    *,
    transition_action: str | None,
    transition_type: str | None,
    transition_unit_id: str | None,
) -> bool:
    if transition_unit_id is None:
        return False
    return bool(_tick_request_spec_for_transition(transition_type=transition_type, transition_action=transition_action))


def status_domain_transition_tick_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    ai_reviewer_request = status_domain_transition_ai_reviewer_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )
    if ai_reviewer_request is not None:
        return ai_reviewer_request
    publication_gate_request = status_domain_transition_publication_gate_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )
    if publication_gate_request is not None:
        return publication_gate_request
    return status_domain_transition_route_back_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )


def status_domain_transition_ai_reviewer_tick_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _status_payload_requests_human_gate(status_payload):
        return None
    domain_transition = _mapping(status_payload.get("domain_transition"))
    transition_unit = _mapping(domain_transition.get("next_work_unit"))
    transition_unit_id = _text(transition_unit.get("unit_id"))
    transition_action = _text(domain_transition.get("controller_action"))
    transition_type = _text(domain_transition.get("decision_type"))
    if (
        transition_type != "ai_reviewer_re_eval"
        or transition_action != StudyDecisionActionType.RETURN_TO_AI_REVIEWER_WORKFLOW.value
        or transition_unit_id is None
    ):
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    charter_ref = _stable_charter_ref(resolved_study_root)
    publication_eval_ref = _stable_publication_eval_ref(resolved_study_root)
    if charter_ref is None or publication_eval_ref is None:
        return None
    reason = _text(transition_unit.get("summary")) or "Re-run AI reviewer manuscript-quality review after upstream manuscript repair."
    return {
        "study_root": resolved_study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "route_target": _text(domain_transition.get("route_target")) or "review",
        "route_key_question": "当前稿件是否已经通过 AI reviewer-owned publication evaluation？",
        "route_rationale": "Mechanical or stale publication projection cannot authorize quality closure; AI reviewer must own the next evaluation.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": StudyDecisionActionType.RETURN_TO_AI_REVIEWER_WORKFLOW.value,
                "payload_ref": str((resolved_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": reason,
        "work_unit_fingerprint": f"domain-transition::{transition_type}::{transition_unit_id}",
        "next_work_unit": dict(transition_unit),
        "blocking_work_units": [dict(transition_unit)],
        "currentness_basis": "status_domain_transition",
    }


def status_domain_transition_route_back_tick_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _status_payload_requests_human_gate(status_payload):
        return None
    domain_transition = _mapping(status_payload.get("domain_transition"))
    transition_unit = _mapping(domain_transition.get("next_work_unit"))
    transition_unit_id = _text(transition_unit.get("unit_id"))
    transition_action = _text(domain_transition.get("controller_action"))
    transition_type = _text(domain_transition.get("decision_type"))
    if (
        transition_type != StudyDecisionType.ROUTE_BACK_SAME_LINE.value
        or transition_action != StudyDecisionActionType.REQUEST_OPL_STAGE_ATTEMPT.value
        or transition_unit_id is None
    ):
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    charter_ref = _stable_charter_ref(resolved_study_root)
    publication_eval_ref = _stable_publication_eval_ref(resolved_study_root)
    if charter_ref is None or publication_eval_ref is None:
        return None
    reason = _text(transition_unit.get("summary")) or "Run current same-line quality repair for the AI reviewer route-back."
    route_target = _text(domain_transition.get("route_target")) or "write"
    return {
        "study_root": resolved_study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
        "route_target": route_target,
        "route_key_question": "当前 AI reviewer-backed route-back 应由哪一个同线 owner work unit 继续？",
        "route_rationale": "The current AI reviewer route-back must be materialized as a quality repair controller work unit before runtime continuation.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
                "payload_ref": str((resolved_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": reason,
        "work_unit_fingerprint": f"domain-transition::{transition_type}::{transition_unit_id}",
        "next_work_unit": dict(transition_unit),
        "blocking_work_units": [dict(transition_unit)],
        "currentness_basis": "status_domain_transition",
    }


def status_domain_transition_publication_gate_tick_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _status_payload_requests_human_gate(status_payload):
        return None
    domain_transition = _mapping(status_payload.get("domain_transition"))
    transition_unit = _mapping(domain_transition.get("next_work_unit"))
    transition_unit_id = _text(transition_unit.get("unit_id"))
    transition_action = _text(domain_transition.get("controller_action"))
    transition_type = _text(domain_transition.get("decision_type"))
    if (
        transition_type != "publication_gate_blocker"
        or transition_action != StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value
        or transition_unit_id is None
    ):
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    charter_ref = _stable_charter_ref(resolved_study_root)
    publication_eval_ref = _stable_publication_eval_ref(resolved_study_root)
    if charter_ref is None or publication_eval_ref is None:
        return None
    reason = _text(transition_unit.get("summary")) or "Replay the MAS publication gate after owner-authorized repair."
    return {
        "study_root": resolved_study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "publication_gate_blocker",
        "route_target": _text(domain_transition.get("route_target")) or "review",
        "route_key_question": "当前 AI reviewer-backed publication eval 是否已经通过 MAS publication gate？",
        "route_rationale": "The current AI reviewer evaluation must be replayed through the publication gate before package or submission work can proceed.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value,
                "payload_ref": str((resolved_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": reason,
        "work_unit_fingerprint": f"domain-transition::{transition_type}::{transition_unit_id}",
        "next_work_unit": dict(transition_unit),
        "blocking_work_units": [dict(transition_unit)],
        "currentness_basis": "status_domain_transition",
    }


def tick_request_matches_domain_transition(
    *,
    tick_request: Mapping[str, Any],
    transition_action: str,
    transition_type: str,
    transition_unit_id: str,
) -> bool:
    expected_action = _tick_request_spec_for_transition(
        transition_type=transition_type,
        transition_action=transition_action,
    )
    if expected_action is None:
        return False
    tick_unit_id = work_unit_id_from_tick_request(tick_request)
    if tick_unit_id != transition_unit_id:
        return False
    if expected_action not in controller_action_types_from_tick_request(tick_request):
        return False
    fingerprint = _text(tick_request.get("work_unit_fingerprint"))
    return fingerprint == f"domain-transition::{transition_type}::{transition_unit_id}"


def tick_request_matches_ai_reviewer_domain_transition(
    *,
    tick_request: Mapping[str, Any],
    transition_action: str,
    transition_type: str,
    transition_unit_id: str,
) -> bool:
    return tick_request_matches_domain_transition(
        tick_request=tick_request,
        transition_action=transition_action,
        transition_type=transition_type,
        transition_unit_id=transition_unit_id,
    )


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


def _tick_request_spec_for_transition(
    *,
    transition_type: str | None,
    transition_action: str | None,
) -> str | None:
    if (
        transition_type == "ai_reviewer_re_eval"
        and transition_action == StudyDecisionActionType.RETURN_TO_AI_REVIEWER_WORKFLOW.value
    ):
        return StudyDecisionActionType.RETURN_TO_AI_REVIEWER_WORKFLOW.value
    if (
        transition_type == StudyDecisionType.ROUTE_BACK_SAME_LINE.value
        and transition_action
        in {
            StudyDecisionActionType.REQUEST_OPL_STAGE_ATTEMPT.value,
            StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        }
    ):
        return StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value
    if (
        transition_type == "publication_gate_blocker"
        and transition_action == StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value
    ):
        return StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value
    return None


def _stable_charter_ref(study_root: Path) -> dict[str, str] | None:
    path = study_root / "artifacts" / "controller" / "study_charter.json"
    payload = _read_json_mapping(path)
    charter_id = _text(payload.get("charter_id"))
    if charter_id is None:
        return None
    return {"charter_id": charter_id, "artifact_path": str(path)}


def _stable_publication_eval_ref(study_root: Path) -> dict[str, str] | None:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _read_json_mapping(path)
    eval_id = _text(payload.get("eval_id"))
    if eval_id is None:
        return None
    return {"eval_id": eval_id, "artifact_path": str(path)}


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _status_payload_requests_human_gate(status_payload: Mapping[str, Any]) -> bool:
    publication_supervisor_state = _mapping(status_payload.get("publication_supervisor_state"))
    current_required_action = _text(publication_supervisor_state.get("current_required_action"))
    if current_required_action == "human_confirmation_required":
        return True
    return _text(status_payload.get("controller_confirmation_status")) == "pending"


def _status_payload(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if isinstance(status_payload, Mapping) and status_payload:
        return dict(status_payload)
    router = import_module("med_autoscience.controllers.domain_status_projection")
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
    "domain_transition_is_materializable",
    "latest_controller_decision_matches_tick_request",
    "materialize_fresh_domain_transition_controller_decision_if_required",
    "materialize_fresh_ai_reviewer_transition_controller_decision_if_required",
    "status_domain_transition_route_back_tick_request",
    "status_domain_transition_tick_request",
    "status_domain_transition_ai_reviewer_tick_request",
    "status_domain_transition_publication_gate_tick_request",
    "tick_request_matches_domain_transition",
    "tick_request_matches_ai_reviewer_domain_transition",
    "work_unit_id_from_tick_request",
]
