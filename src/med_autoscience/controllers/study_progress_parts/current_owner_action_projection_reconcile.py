from __future__ import annotations

from typing import Any, Mapping

from .current_executable_owner_action import owner_action_next_step
from .macro_state_projection import compact_study_macro_state_from_payload
from .shared import _mapping_copy, _non_empty_text

CURRENT_OWNER_ACTION_SOURCES = frozenset(
    {
        "stage_kernel_projection.current_owner_delta",
        "stage_artifact_index.next_owner_action",
        "study_progress.next_forced_delta.owner_action",
        "domain_transition",
        "repair_progress_projection.mas_owner_repair_execution_evidence",
    }
)
READINESS_ACTION = "complete_medical_paper_readiness_surface"


def reconcile_current_owner_action_projection(payload: dict[str, Any]) -> dict[str, Any]:
    action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_owner_action_supersedes_stale_user_park(payload, action):
        payload["study_macro_state"] = compact_study_macro_state_from_payload(payload)
        return payload
    updated = dict(payload)
    auto_parked = _mapping_copy(updated.get("auto_runtime_parked"))
    next_step = owner_action_next_step(action)
    auto_parked.update(
        {
            "parked": False,
            "parked_state": None,
            "parked_state_label": None,
            "parked_owner": None,
            "resource_release_expected": False,
            "awaiting_explicit_wakeup": False,
            "auto_execution_complete": False,
            "superseded_by_current_owner_action": True,
            "summary": "Stage Native current owner action is available; stale user-park projection is not the current execution owner.",
            "next_action_summary": next_step,
        }
    )
    updated["auto_runtime_parked"] = auto_parked
    for key in (
        "parked_state",
        "parked_owner",
        "resource_release_expected",
        "awaiting_explicit_wakeup",
        "auto_execution_complete",
    ):
        updated[key] = auto_parked.get(key)
    study_id = _non_empty_text(updated.get("study_id"))
    current_stage = _non_empty_text(updated.get("current_stage"))
    if current_stage == "auto_runtime_parked":
        updated["current_stage"] = "publication_supervision"
    if next_step is not None:
        updated["next_system_action"] = next_step
        updated["next_step"] = next_step
        status_contract = _mapping_copy(updated.get("status_narration_contract"))
        if status_contract:
            status_contract["next_step"] = next_step
            updated["status_narration_contract"] = status_contract
        operator_status = _mapping_copy(updated.get("operator_status_card"))
        if operator_status:
            operator_status["current_focus"] = next_step
            updated["operator_status_card"] = operator_status
    updated["needs_user_decision"] = False
    updated["needs_physician_decision"] = False
    updated["physician_decision_summary"] = None
    updated["user_decision_summary"] = None
    dashboard = _mapping_copy(updated.get("ai_first_operations_dashboard"))
    dashboard_user_view = _mapping_copy(dashboard.get("user_view"))
    if dashboard_user_view:
        dashboard_user_view.update(
            {
                "current_stage": updated.get("current_stage"),
                "blockers": updated.get("current_blockers"),
                "next_step": updated.get("next_system_action"),
                "human_review_required": False,
            }
        )
        dashboard["user_view"] = dashboard_user_view
        updated["ai_first_operations_dashboard"] = dashboard
    updated["study_macro_state"] = {
        "surface": "study_macro_state",
        "schema_version": 1,
        "study_id": study_id,
        "writer_state": "queued",
        "user_next": "repair",
        "reason": "quality",
        "details": {
            "decision_owner": _non_empty_text(action.get("next_owner")),
            "route_owner": _non_empty_text(action.get("next_owner")),
            "next_work_unit": _non_empty_text(action.get("work_unit_id")),
            "source_ref": _non_empty_text(action.get("source_ref")),
            "source": _non_empty_text(action.get("source")),
        },
        "conditions": [
            {
                "type": "CurrentOwnerActionSupersedesStaleUserPark",
                "status": "true",
                "reason": "Stage Native current owner action exists and no current human-gate authority ref is present.",
            }
        ],
    }
    return updated


def current_owner_action_supersedes_stale_user_park(
    payload: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("surface_kind")) != "current_executable_owner_action":
        return False
    if _non_empty_text(action.get("source")) not in CURRENT_OWNER_ACTION_SOURCES:
        return False
    auto_parked = _mapping_copy(payload.get("auto_runtime_parked"))
    if auto_parked.get("parked") is not True:
        return False
    if _non_empty_text(auto_parked.get("parked_state")) != "waiting_user_decision":
        return False
    classification = _mapping_copy(auto_parked.get("runtime_failure_classification"))
    if _has_human_gate_authority_ref(payload):
        return False
    if auto_parked.get("auto_execution_complete") is True:
        return False
    if _non_empty_text(action.get("next_owner")) == "user":
        return False
    return bool(
        _non_empty_text(action.get("next_owner"))
        or _non_empty_text(action.get("work_unit_id"))
        or _text_items(action.get("allowed_actions"))
    )


def current_execution_envelope_actions(
    *,
    handoff: Mapping[str, Any],
    current_executable_owner_action: Mapping[str, Any],
    paper_progress_delta_counted: bool = False,
) -> list[dict[str, Any]]:
    if _mapping_copy(handoff.get("typed_blocker")) and handoff.get("running_provider_attempt") is not True:
        return []
    handoff_actions = [
        dict(item)
        for item in handoff.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    current_action = _current_executable_owner_action_as_envelope_action(current_executable_owner_action)
    if handoff_actions:
        if _handoff_actions_superseded_by_current_paper_delta(
            handoff=handoff,
            handoff_actions=handoff_actions,
            current_action=current_action,
            paper_progress_delta_counted=paper_progress_delta_counted,
        ):
            return [current_action] if current_action is not None else []
        if _handoff_actions_superseded_by_reconciled_current_action(
            handoff=handoff,
            handoff_actions=handoff_actions,
            current_action=current_action,
        ):
            return [current_action] if current_action is not None else []
        return handoff_actions
    return [current_action] if current_action is not None else []


def _current_executable_owner_action_as_envelope_action(
    current_executable_owner_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _non_empty_text(current_executable_owner_action.get("surface_kind")) != "current_executable_owner_action":
        return None
    allowed_actions = _text_items(current_executable_owner_action.get("allowed_actions"))
    action_type = allowed_actions[0] if allowed_actions else _non_empty_text(
        current_executable_owner_action.get("action_type")
    )
    owner = _non_empty_text(current_executable_owner_action.get("next_owner"))
    work_unit_id = _non_empty_text(current_executable_owner_action.get("work_unit_id"))
    if action_type is None and owner is None and work_unit_id is None:
        return None
    action = {
        "action_type": action_type,
        "owner": owner,
        "recommended_owner": owner,
        "next_owner": owner,
        "next_work_unit": work_unit_id or action_type,
        "work_unit_id": work_unit_id,
        "allowed_actions": allowed_actions,
        "source_surface": _non_empty_text(current_executable_owner_action.get("source")),
        "source_ref": _non_empty_text(current_executable_owner_action.get("source_ref")),
    }
    target_surface = _mapping_copy(current_executable_owner_action.get("target_surface"))
    if target_surface:
        action["target_surface"] = target_surface
    target_surface_specificity = _non_empty_text(
        current_executable_owner_action.get("target_surface_specificity")
    )
    if target_surface_specificity is not None:
        action["target_surface_specificity"] = target_surface_specificity
    required_delta_kind = _non_empty_text(current_executable_owner_action.get("required_delta_kind"))
    if required_delta_kind is not None:
        action["required_delta_kind"] = required_delta_kind
    acceptance_refs = _text_items(current_executable_owner_action.get("acceptance_refs"))
    if acceptance_refs:
        action["acceptance_refs"] = acceptance_refs
    return action


def _handoff_actions_superseded_by_current_paper_delta(
    *,
    handoff: Mapping[str, Any],
    handoff_actions: list[dict[str, Any]],
    current_action: Mapping[str, Any] | None,
    paper_progress_delta_counted: bool,
) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return False
    if not handoff_actions:
        return False
    first_handoff_action = handoff_actions[0]
    if not _is_readiness_action(first_handoff_action):
        return False
    if current_action is not None and not _is_readiness_action(current_action):
        return True
    return paper_progress_delta_counted


def _handoff_actions_superseded_by_reconciled_current_action(
    *,
    handoff: Mapping[str, Any],
    handoff_actions: list[dict[str, Any]],
    current_action: Mapping[str, Any] | None,
) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return False
    if current_action is None or not handoff_actions:
        return False
    if _non_empty_text(current_action.get("source_surface")) not in CURRENT_OWNER_ACTION_SOURCES:
        return False
    return not _actions_have_same_identity(left=current_action, right=handoff_actions[0])


def _actions_have_same_identity(
    *,
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> bool:
    left_action_type = _non_empty_text(left.get("action_type")) or _first_text(_text_items(left.get("allowed_actions")))
    right_action_type = _non_empty_text(right.get("action_type")) or _first_text(_text_items(right.get("allowed_actions")))
    if left_action_type is not None and right_action_type is not None and left_action_type != right_action_type:
        return False
    left_work_unit = _work_unit_identity(left.get("work_unit_id")) or _work_unit_identity(left.get("next_work_unit"))
    right_work_unit = _work_unit_identity(right.get("work_unit_id")) or _work_unit_identity(right.get("next_work_unit"))
    if left_work_unit is not None and right_work_unit is not None and left_work_unit != right_work_unit:
        return False
    left_fingerprints = _action_identity_fingerprints(left)
    right_fingerprints = _action_identity_fingerprints(right)
    if left_fingerprints and right_fingerprints and not left_fingerprints.intersection(right_fingerprints):
        return False
    return True


def _action_identity_fingerprints(action: Mapping[str, Any]) -> set[str]:
    return {
        text
        for value in (
            action.get("work_unit_fingerprint"),
            action.get("action_fingerprint"),
            action.get("fingerprint"),
        )
        if (text := _non_empty_text(value)) is not None
    }


def _is_readiness_action(action: Mapping[str, Any]) -> bool:
    values = {
        _non_empty_text(action.get("action_type")),
        _non_empty_text(action.get("work_unit_id")),
        _non_empty_text(action.get("next_work_unit")),
        *_text_items(action.get("allowed_actions")),
    }
    return READINESS_ACTION in values


def _first_text(values: list[str]) -> str | None:
    return values[0] if values else None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _has_human_gate_authority_ref(payload: Mapping[str, Any]) -> bool:
    auto_parked = _mapping_copy(payload.get("auto_runtime_parked"))
    for surface in (
        payload,
        auto_parked,
        _mapping_copy(payload.get("refs")),
        _mapping_copy(auto_parked.get("refs")),
    ):
        if _surface_has_human_gate_ref(surface):
            return True
    return False


def _work_unit_identity(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _non_empty_text(value.get("unit_id")) or _non_empty_text(value.get("work_unit_id"))
    return _non_empty_text(value)


def _surface_has_human_gate_ref(surface: Mapping[str, Any]) -> bool:
    for key in (
        "human_gate_ref",
        "human_gate_resume_ref",
        "human_gate_or_resume_ref",
        "human_gate_authority_ref",
        "decision_ref",
        "receipt_ref",
        "source_artifact_path",
    ):
        if _non_empty_text(surface.get(key)) is not None:
            return True
    for key in (
        "human_gate_refs",
        "human_gate_resume_refs",
        "human_gate_or_resume_refs",
        "human_gate_authority_refs",
    ):
        if _text_items(surface.get(key)):
            return True
    for gate in surface.get("family_human_gates") or []:
        gate_payload = _mapping_copy(gate)
        if _surface_has_human_gate_ref(gate_payload):
            return True
        for evidence in gate_payload.get("evidence_refs") or []:
            if _non_empty_text(_mapping_copy(evidence).get("ref")) is not None:
                return True
    return False


__all__ = [
    "current_execution_envelope_actions",
    "current_owner_action_supersedes_stale_user_park",
    "reconcile_current_owner_action_projection",
]
