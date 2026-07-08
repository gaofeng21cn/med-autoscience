from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit.action_projection_fields import (
    action_type as _action_type,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.opl_transition_readback import (
    has_opl_transition_readback as _has_opl_transition_readback,
)
from med_autoscience.controllers.current_work_unit.primitives import (
    mapping as _mapping,
    text as _text,
)
from med_autoscience.controllers.current_work_unit.paper_recovery_successor import (
    paper_recovery_successor_action_ready as _paper_recovery_successor_identity_ready,
)
AI_REVIEWER_ACTION = "return_to_ai_reviewer_workflow"
AI_REVIEWER_OWNER = "ai_reviewer"
AI_REVIEWER_WORK_UNIT = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
GATE_CLEARING_ACTION = "run_gate_clearing_batch"
GATE_CLEARING_OWNER = "gate_clearing_batch"
GATE_CLEARING_WORK_UNIT = "publication_gate_replay"
REPAIR_PROGRESS_EVIDENCE_SOURCE = "repair_progress_projection.mas_owner_repair_execution_evidence"
PAPER_RECOVERY_SUCCESSOR_SOURCE = "paper_recovery_state.next_safe_action.successor_owner_action"
GATE_FOLLOWTHROUGH_SUCCESSOR_SOURCE = "gate_clearing_batch_followthrough.actionable_current_work_unit"
QUALITY_REPAIR_ACTION = "run_quality_repair_batch"


def repair_progress_action_consuming_current_action(
    *,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any] | None,
    provider_admission: Mapping[str, Any] | None,
    surface_kind: str,
) -> dict[str, Any] | None:
    repair_action = owner_action_from_repair_progress_projection(
        progress,
        surface_kind=surface_kind,
    )
    if not _repair_progress_consumes_current_action(
        repair_action=repair_action,
        current_action=current_action,
        provider_admission=provider_admission,
        progress=progress,
    ):
        return None
    return repair_action


def owner_action_from_repair_progress_projection(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    repair_progress = _mapping(payload.get("repair_progress_projection"))
    if repair_progress.get("paper_delta_observed") is not True:
        return None
    if repair_progress.get("accepted_owner_receipt") is not True:
        return None
    source_ref = _text(repair_progress.get("repair_execution_evidence_ref")) or _text(
        repair_progress.get("owner_receipt_ref")
    )
    ai_reviewer_request_ref = _text(repair_progress.get("ai_reviewer_recheck_request_ref"))
    gate_replay_refs = _text_items(repair_progress.get("gate_replay_refs"))
    if gate_replay_refs and repair_progress.get("ai_reviewer_recheck_done") is True:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=GATE_CLEARING_OWNER,
            work_unit_id=GATE_CLEARING_WORK_UNIT,
            action_type=GATE_CLEARING_ACTION,
            required_delta_kind="publication_gate_replay_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "request_ref": gate_replay_refs[0],
            },
            acceptance_refs=gate_replay_refs,
            surface_kind=surface_kind,
        )
    if ai_reviewer_request_ref is not None:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=AI_REVIEWER_OWNER,
            work_unit_id=AI_REVIEWER_WORK_UNIT,
            action_type=AI_REVIEWER_ACTION,
            required_delta_kind="ai_reviewer_publication_eval_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "review",
                "surface_ref": "artifacts/publication_eval/latest.json",
                "request_ref": ai_reviewer_request_ref,
                "gate_replay_request_ref": gate_replay_refs[0] if gate_replay_refs else None,
            },
            acceptance_refs=[ai_reviewer_request_ref, *gate_replay_refs],
            surface_kind=surface_kind,
        )
    if gate_replay_refs:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=GATE_CLEARING_OWNER,
            work_unit_id=GATE_CLEARING_WORK_UNIT,
            action_type=GATE_CLEARING_ACTION,
            required_delta_kind="publication_gate_replay_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "request_ref": gate_replay_refs[0],
            },
            acceptance_refs=gate_replay_refs,
            surface_kind=surface_kind,
        )
    return None


def _repair_progress_consumes_current_action(
    *,
    repair_action: Mapping[str, Any] | None,
    current_action: Mapping[str, Any] | None,
    provider_admission: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    repair = _mapping(repair_action)
    current = _mapping(current_action)
    if not repair or not current:
        return False
    if _provider_handoff_matches_current_action(
        provider_admission=provider_admission,
        current_action=current,
    ):
        return False
    if (_text(repair.get("source_surface")) or _text(repair.get("source"))) != REPAIR_PROGRESS_EVIDENCE_SOURCE:
        return False
    if _action_type(current) != QUALITY_REPAIR_ACTION:
        return False
    progress_projection = _mapping(progress.get("repair_progress_projection"))
    if progress_projection.get("paper_delta_observed") is not True:
        return False
    if progress_projection.get("accepted_owner_receipt") is not True:
        return False
    if _paper_recovery_successor_action_ready(current) and not _repair_progress_matches_current_successor(
        current_action=current,
        progress=progress,
        progress_projection=progress_projection,
    ):
        return False
    if _gate_followthrough_successor_action_ready(current) and not _repair_progress_matches_current_successor(
        current_action=current,
        progress=progress,
        progress_projection=progress_projection,
    ):
        return False
    precedence = _mapping(repair.get("repair_progress_precedence"))
    source_work_unit = _work_unit_id(precedence.get("source_work_unit_id")) or _work_unit_id(
        progress_projection.get("work_unit_id")
    )
    if source_work_unit is None or source_work_unit != _work_unit_id(current.get("work_unit_id")):
        return False
    repair_eval = _text(repair.get("source_eval_id")) or _text(progress_projection.get("source_eval_id"))
    current_eval = _text(current.get("source_eval_id"))
    if repair_eval is not None and current_eval is not None and repair_eval != current_eval:
        return False
    return True


def _repair_followup_action(
    *,
    repair_progress: Mapping[str, Any],
    source_ref: str | None,
    next_owner: str,
    work_unit_id: str,
    action_type: str,
    required_delta_kind: str,
    target_surface: Mapping[str, Any],
    acceptance_refs: list[str],
    surface_kind: str,
) -> dict[str, Any]:
    owner_receipt_ref = _text(repair_progress.get("owner_receipt_ref"))
    repair_evidence_ref = _text(repair_progress.get("repair_execution_evidence_ref"))
    work_unit_fingerprint = (
        _text(repair_progress.get("work_unit_fingerprint"))
        or _text(repair_progress.get("action_fingerprint"))
        or _text(repair_progress.get("source_fingerprint"))
    )
    return _compact(
        {
            "surface_kind": surface_kind,
            "schema_version": 1,
            "status": "ready",
            "source": REPAIR_PROGRESS_EVIDENCE_SOURCE,
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "source_eval_id": _text(repair_progress.get("source_eval_id")),
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
            "required_delta_kind": required_delta_kind,
            "target_surface": _compact(target_surface),
            "target_surface_specificity": "repair_progress_followup_owner_surface",
            "source_ref": source_ref,
            "acceptance_refs": _dedupe_text(
                [
                    repair_evidence_ref,
                    owner_receipt_ref,
                    *acceptance_refs,
                ]
            ),
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "superseded_stage_native_action": QUALITY_REPAIR_ACTION,
                "superseded_readiness_action": "complete_medical_paper_readiness_surface",
                "source_work_unit_id": _text(repair_progress.get("work_unit_id")),
                "work_unit_fingerprint": _text(repair_progress.get("work_unit_fingerprint")),
                "action_fingerprint": _text(repair_progress.get("action_fingerprint")),
                "source_fingerprint": _text(repair_progress.get("source_fingerprint")),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _provider_handoff_matches_current_action(
    *,
    provider_admission: Mapping[str, Any] | None,
    current_action: Mapping[str, Any],
) -> bool:
    handoff = _mapping(provider_admission)
    if not handoff:
        return False
    if not _handoff_is_active_provider_control(handoff):
        return False
    handoff_action = _matching_handoff_action(handoff)
    if not handoff_action:
        return False
    return _action_identity_matches(handoff_action, current_action)


def _handoff_is_active_provider_control(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return True
    if handoff.get("provider_admission_pending_count") not in (None, 0):
        return _has_opl_transition_readback(handoff) or any(
            _has_opl_transition_readback(item)
            for item in handoff.get("provider_admission_candidates") or []
            if isinstance(item, Mapping)
        )
    if any(
        _has_opl_transition_readback(item)
        for item in handoff.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ):
        return True
    return any(
        _has_opl_transition_readback(item)
        for item in handoff.get("action_queue") or []
        if isinstance(item, Mapping)
    )


def _matching_handoff_action(handoff: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("current_executable_owner_action", "owner_action"):
        action = _mapping(handoff.get(key))
        if action:
            return action
    current_work_unit = _mapping(handoff.get("current_work_unit"))
    if _text(current_work_unit.get("status")) == "executable_owner_action":
        return current_work_unit
    for item in handoff.get("provider_admission_candidates") or []:
        action = _mapping(item)
        if action:
            return action
    return {}


def _action_identity_matches(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if _action_type(left) != _action_type(right):
        return False
    left_work_unit = _work_unit_id(left.get("work_unit_id")) or _work_unit_id(left.get("next_work_unit"))
    right_work_unit = _work_unit_id(right.get("work_unit_id")) or _work_unit_id(right.get("next_work_unit"))
    if left_work_unit is None or right_work_unit is None or left_work_unit != right_work_unit:
        return False
    left_fingerprint = _fingerprint(left)
    right_fingerprint = _fingerprint(right)
    return bool(left_fingerprint and right_fingerprint and left_fingerprint == right_fingerprint)


def _fingerprint(action: Mapping[str, Any]) -> str | None:
    basis = _mapping(action.get("owner_route_currentness_basis")) or _mapping(action.get("currentness_basis"))
    return (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )


def _repair_identity_fingerprint(repair: Mapping[str, Any]) -> str | None:
    basis = _mapping(repair.get("owner_route_currentness_basis")) or _mapping(repair.get("currentness_basis"))
    return (
        _text(repair.get("work_unit_fingerprint"))
        or _text(repair.get("action_fingerprint"))
        or _text(repair.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(repair.get("source_fingerprint"))
    )


def _repair_progress_matches_current_successor(
    *,
    current_action: Mapping[str, Any],
    progress: Mapping[str, Any],
    progress_projection: Mapping[str, Any],
) -> bool:
    source_work_unit = _work_unit_id(progress_projection.get("work_unit_id"))
    current_work_unit = _work_unit_id(current_action.get("work_unit_id"))
    if source_work_unit is None or current_work_unit is None or source_work_unit != current_work_unit:
        return False
    repair_eval = _text(progress_projection.get("source_eval_id"))
    current_eval = _text(current_action.get("source_eval_id"))
    if repair_eval is not None and current_eval is not None and repair_eval != current_eval:
        return False
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return False
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    followthrough_work_unit = (
        _work_unit_id(followthrough.get("work_unit_id"))
        or _work_unit_id(currentness.get("current_publication_work_unit_id"))
        or _work_unit_id(_mapping(followthrough.get("current_publication_work_unit")).get("unit_id"))
    )
    if followthrough_work_unit is None or followthrough_work_unit != current_work_unit:
        return False
    current_fingerprint = _fingerprint(current_action)
    followthrough_fingerprint = (
        _text(followthrough.get("work_unit_fingerprint"))
        or _text(currentness.get("current_work_unit_fingerprint"))
        or _text(currentness.get("explicit_work_unit_fingerprint"))
    )
    if current_fingerprint is None or followthrough_fingerprint is None:
        return False
    if current_fingerprint != followthrough_fingerprint:
        return False
    repair_fingerprint = _repair_identity_fingerprint(progress_projection)
    if repair_fingerprint is None or repair_fingerprint != current_fingerprint:
        return False
    followthrough_eval = _text(followthrough.get("source_eval_id"))
    if repair_eval is not None and followthrough_eval is not None and repair_eval != followthrough_eval:
        return False
    return True


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "canonical_next_action_authority": False,
        "projection_role": "current_work_unit_owner_consumption_guard",
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _dedupe_text(items: list[str | None]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _paper_recovery_successor_action_ready(action: Mapping[str, Any]) -> bool:
    return _paper_recovery_successor_identity_ready(action)


def _gate_followthrough_successor_action_ready(action: Mapping[str, Any]) -> bool:
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source != GATE_FOLLOWTHROUGH_SUCCESSOR_SOURCE:
        return False
    if _action_type(action) != QUALITY_REPAIR_ACTION:
        return False
    return (
        _work_unit_id(action.get("work_unit_id")) is not None
        and (_text(action.get("work_unit_fingerprint")) or _text(action.get("action_fingerprint")))
        is not None
    )


__all__ = ["repair_progress_action_consuming_current_action"]
