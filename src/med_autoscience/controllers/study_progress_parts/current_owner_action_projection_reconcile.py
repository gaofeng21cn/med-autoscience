from __future__ import annotations

from typing import Any, Mapping

from .current_executable_owner_action import owner_action_next_step
from .macro_state_projection import compact_study_macro_state_from_payload
from .shared import _mapping_copy, _non_empty_text
from ..stage_route_currentness_identity import currentness_identities_match

CURRENT_OWNER_ACTION_SOURCES = frozenset(
    {
        "stage_kernel_projection.current_owner_delta",
        "stage_artifact_index.next_owner_action",
        "study_progress.next_forced_delta.owner_action",
        "domain_transition",
        "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "repair_progress_projection.mas_owner_repair_execution_evidence",
        "publication_eval.recommended_actions.readiness_blocker_repair",
    }
)
CURRENT_CONTROL_TYPED_BLOCKER_SUCCESSOR_SOURCES = frozenset(
    {
        "domain_transition",
        "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "repair_progress_projection.mas_owner_repair_execution_evidence",
        "publication_eval.recommended_actions.readiness_blocker_repair",
    }
)
READINESS_ACTION = "complete_medical_paper_readiness_surface"
OWNER_ACTION_SUPERSEDABLE_PARKED_STATES = frozenset(
    {
        "waiting_user_decision",
        "explicit_resume_pending",
    }
)
OWNER_ACTION_SUPERSEDABLE_EXPLICIT_RESUME_REASONS = frozenset(
    {
        "blocked_turn_closeout_waiting_for_owner",
        "completed_parked_auto_continue_no_new_message",
        "parked_after_checkpoint_no_new_message",
    }
)


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
        intervention_lane = _mapping_copy(updated.get("intervention_lane"))
        if _non_empty_text(intervention_lane.get("lane_id")) == "auto_runtime_parked":
            intervention_lane.update(
                {
                    "lane_id": "current_owner_action_ready",
                    "title": "当前 owner action 已就绪",
                    "severity": "handoff",
                    "summary": next_step,
                    "recommended_action_id": "inspect_current_owner_action",
                    "parked_state": None,
                    "parked_owner": None,
                    "awaiting_explicit_wakeup": False,
                    "resource_release_expected": False,
                    "superseded_by_current_owner_action": True,
                }
            )
            updated["intervention_lane"] = {
                key: value for key, value in intervention_lane.items() if value not in (None, "", [], {})
            }
        operator_verdict = _mapping_copy(updated.get("operator_verdict"))
        if _non_empty_text(operator_verdict.get("decision_mode")) == "auto_runtime_parked":
            operator_verdict.update(
                {
                    "lane_id": "current_owner_action_ready",
                    "decision_mode": "monitor_only",
                    "needs_intervention": False,
                    "summary": next_step,
                    "reason_summary": next_step,
                }
            )
            updated["operator_verdict"] = {
                key: value for key, value in operator_verdict.items() if value not in (None, "", [], {})
            }
        for key in ("recovery_contract", "autonomy_contract"):
            surface = _mapping_copy(updated.get(key))
            if not surface:
                continue
            if _non_empty_text(surface.get("action_mode")) == "auto_runtime_parked":
                surface["action_mode"] = "inspect_current_owner_action"
            if _non_empty_text(surface.get("autonomy_state")) == "auto_runtime_parked":
                surface["autonomy_state"] = "autonomous_progress"
            surface["summary"] = next_step
            updated[key] = {
                item_key: item_value
                for item_key, item_value in surface.items()
                if item_key
                not in {
                    "auto_runtime_parked",
                    "parked_state",
                    "resource_release_expected",
                    "awaiting_explicit_wakeup",
                    "auto_execution_complete",
                }
            }
        operator_status = _mapping_copy(updated.get("operator_status_card"))
        if operator_status:
            if _non_empty_text(operator_status.get("handling_state")) in {
                "auto_runtime_parked",
                "explicit_resume_pending",
            }:
                operator_status["handling_state"] = "scientific_or_quality_repair_in_progress"
                operator_status["handling_state_label"] = "论文硬阻塞处理中"
            operator_status["current_focus"] = next_step
            updated["operator_status_card"] = {
                key: value
                for key, value in operator_status.items()
                if key
                not in {
                    "auto_runtime_parked",
                    "parked_state",
                    "resource_release_expected",
                    "awaiting_explicit_wakeup",
                    "auto_execution_complete",
                    "reopen_policy",
                }
            }
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


def current_control_typed_blocker_successor_action(action: Mapping[str, Any] | None) -> bool:
    if not isinstance(action, Mapping):
        return False
    source = _non_empty_text(action.get("source"))
    if source not in CURRENT_CONTROL_TYPED_BLOCKER_SUCCESSOR_SOURCES:
        return False
    if source in {
        "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "publication_eval.recommended_actions.readiness_blocker_repair",
    }:
        return False
    if source == "repair_progress_projection.mas_owner_repair_execution_evidence":
        precedence = _mapping_copy(action.get("repair_progress_precedence"))
        if not (
            precedence.get("paper_delta_observed") is True
            or precedence.get("accepted_owner_receipt") is True
        ):
            return False
    return _non_empty_text(action.get("action_type")) is not None and _non_empty_text(
        action.get("work_unit_id")
    ) is not None


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
    parked_state = _non_empty_text(auto_parked.get("parked_state"))
    if parked_state not in OWNER_ACTION_SUPERSEDABLE_PARKED_STATES:
        return False
    if parked_state == "explicit_resume_pending" and _non_empty_text(
        auto_parked.get("source_reason")
    ) not in OWNER_ACTION_SUPERSEDABLE_EXPLICIT_RESUME_REASONS:
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


def current_execution_evidence_actions(
    *,
    handoff: Mapping[str, Any],
    current_executable_owner_action: Mapping[str, Any],
    paper_progress_delta_counted: bool = False,
) -> list[dict[str, Any]]:
    if handoff.get("terminal_closeout_consumed") is True:
        return []
    if current_execution_handoff_consumes_current_action(handoff) or _handoff_has_consumed_action_queue(handoff):
        current_action = _current_executable_owner_action_as_envelope_action(current_executable_owner_action)
        if _non_empty_text(_mapping_copy(current_action).get("source_surface")) != (
            "study_progress.next_forced_delta.owner_action"
        ):
            return []
        if _current_action_consumed_by_handoff(current_action, handoff):
            return []
        return [current_action] if current_action is not None else []
    return current_execution_envelope_actions(
        handoff=handoff,
        current_executable_owner_action=current_executable_owner_action,
        paper_progress_delta_counted=paper_progress_delta_counted,
    )


def current_execution_handoff_consumes_current_action(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return False
    blocker = _mapping_copy(handoff.get("typed_blocker"))
    if blocker:
        return True
    latest_closeout = _mapping_copy(handoff.get("latest_typed_default_executor_closeout"))
    if _non_empty_text(latest_closeout.get("status")) == "typed_blocker":
        return True
    return (
        _non_empty_text(latest_closeout.get("terminal_closeout_outcome")) == "typed_blocker"
        or _non_empty_text(latest_closeout.get("progress_delta_classification")) == "typed_blocker"
        or _non_empty_text(latest_closeout.get("terminal_closeout_status")) == "blocked"
    )


def _current_action_consumed_by_handoff(
    current_action: Mapping[str, Any] | None,
    handoff: Mapping[str, Any],
) -> bool:
    if current_action is None:
        return False
    return any(
        isinstance(item, Mapping) and currentness_identities_match(current_action, item)
        for item in handoff.get("consumed_action_queue") or []
    )


def _handoff_has_consumed_action_queue(handoff: Mapping[str, Any]) -> bool:
    return any(isinstance(item, Mapping) for item in handoff.get("consumed_action_queue") or [])


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
    for key in (
        "work_unit_fingerprint",
        "action_fingerprint",
        "fingerprint",
        "source_fingerprint",
        "source_eval_id",
        "truth_epoch",
        "runtime_health_epoch",
        "idempotency_key",
    ):
        if (value := _non_empty_text(current_executable_owner_action.get(key))) is not None:
            action[key] = value
    for key in ("owner_route_currentness_basis", "currentness_basis", "source_refs"):
        value = _mapping_copy(current_executable_owner_action.get(key))
        if value:
            action[key] = value
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
    return not currentness_identities_match(current_action, handoff_actions[0])


def _is_readiness_action(action: Mapping[str, Any]) -> bool:
    values = {
        _non_empty_text(action.get("action_type")),
        _non_empty_text(action.get("work_unit_id")),
        _non_empty_text(action.get("next_work_unit")),
        *_text_items(action.get("allowed_actions")),
    }
    return READINESS_ACTION in values


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
    "current_execution_evidence_actions",
    "current_execution_envelope_actions",
    "current_execution_handoff_consumes_current_action",
    "current_owner_action_supersedes_stale_user_park",
    "reconcile_current_owner_action_projection",
]
