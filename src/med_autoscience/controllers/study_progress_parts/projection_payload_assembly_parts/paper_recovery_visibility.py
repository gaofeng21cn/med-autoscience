from __future__ import annotations

from typing import Any, Mapping

from ..paper_autonomy_supervisor_decision import supervisor_decision_blocks_provider_admission
from ..current_owner_handoff_projection import (
    apply_current_owner_handoff_user_visible_status,
    current_owner_handoff_next_action,
)
from ..shared import _mapping_copy, _non_empty_text


PAPER_RECOVERY_BLOCKING_PHASES = frozenset(
    {
        "admission_blocked",
        "projection_inconsistent",
        "manual_foreground_unadopted",
    }
)
PAPER_RECOVERY_AUTHORITY_VISIBLE_PHASES = frozenset(
    {
        "admission_blocked",
        "projection_inconsistent",
        "manual_foreground_unadopted",
        "terminal_closeout_ready",
        "owner_receipt_recorded",
        "domain_blocked",
        "human_gate",
    }
)
PAPER_RECOVERY_STALE_PARK_CLEANUP_REASONS = frozenset(
    {
        "quest_already_running",
        "managed_runtime_live",
    }
)
PAPER_RECOVERY_PRESERVED_PARKED_REASONS = frozenset(
    {
        "blocked_turn_closeout_waiting_for_owner",
        "completed_parked_auto_continue_no_new_message",
        "parked_after_checkpoint_no_new_message",
        "quest_stopped_requires_explicit_rerun",
        "quest_stopped_requires_explicit_resume",
        "quest_stopped_requires_explicit_relaunch",
    }
)


def apply_paper_recovery_state_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    if not recovery:
        return payload
    phase = _non_empty_text(recovery.get("phase"))
    if phase is None:
        return payload
    next_safe_action = _mapping_copy(recovery.get("next_safe_action"))
    supervisor_decision = _mapping_copy(recovery.get("supervisor_decision"))
    summary = paper_recovery_summary(phase=phase, next_safe_action=next_safe_action)
    if summary is None:
        return payload
    observability_mode = _paper_recovery_observability_mode(
        recovery,
        next_safe_action=next_safe_action,
        payload=payload,
    )
    if observability_mode is not None:
        if observability_mode == "defer":
            return payload
        updated = dict(payload)
        if _non_empty_text(updated.get("current_stage")) == "auto_runtime_parked":
            updated["current_stage"] = "publication_supervision"
        _clear_stale_parked_top_level_fields(updated, phase=phase, summary=summary)
        updated["needs_user_decision"] = False
        updated["user_decision_summary"] = None
        updated["needs_physician_decision"] = False
        updated["physician_decision_summary"] = None
        next_action = current_owner_handoff_next_action(updated, user_visible={})
        if next_action is not None:
            updated["next_system_action"] = next_action
            user_visible = _mapping_copy(updated.get("user_visible_projection"))
            if user_visible:
                user_visible["next_system_action"] = next_action
                user_visible["next_step"] = next_action
                user_visible["needs_user_decision"] = False
                user_visible["needs_physician_decision"] = False
                updated["user_visible_projection"] = user_visible
            status_contract = _mapping_copy(updated.get("status_narration_contract"))
            if status_contract:
                status_contract["next_step"] = next_action
                readiness = _mapping_copy(status_contract.get("readiness"))
                if readiness:
                    readiness["needs_physician_decision"] = False
                    status_contract["readiness"] = readiness
                updated["status_narration_contract"] = status_contract
            operator_status = _mapping_copy(updated.get("operator_status_card"))
            if operator_status:
                operator_status["current_focus"] = next_action
                updated["operator_status_card"] = operator_status
            dashboard = _mapping_copy(updated.get("ai_first_operations_dashboard"))
            dashboard_user_view = _mapping_copy(dashboard.get("user_view"))
            if dashboard_user_view:
                dashboard_user_view.update(
                    {
                        "current_stage": updated.get("current_stage"),
                        "blockers": updated.get("current_blockers"),
                        "next_step": next_action,
                        "human_review_required": False,
                    }
                )
                dashboard["user_view"] = dashboard_user_view
                updated["ai_first_operations_dashboard"] = dashboard
        supervision = _mapping_copy(updated.get("supervision"))
        stale_active_run_id = _non_empty_text(supervision.get("stale_active_run_id"))
        if (
            _non_empty_text(supervision.get("active_run_id")) is None
            and stale_active_run_id is not None
            and not stale_active_run_id.startswith("opl-stage-attempt://")
        ):
            supervision["active_run_id"] = stale_active_run_id
            supervision.pop("stale_active_run_id", None)
            supervision.pop("liveness_suppressed_by", None)
            updated["supervision"] = supervision
        return apply_current_owner_handoff_user_visible_status(updated)
    updated = dict(payload)
    if _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action):
        blockers = list(updated.get("current_blockers") or [])
        if phase not in blockers:
            blockers.append(phase)
        updated["current_blockers"] = blockers
        updated["next_system_action"] = summary
    elif phase == "owner_receipt_recorded":
        updated["current_blockers"] = _blockers_without_stale_recovery_residue(
            updated.get("current_blockers")
        )
        updated["next_system_action"] = summary
    if _provider_admission_suppression_should_block_owner_action(
        next_safe_action=next_safe_action
    ) and _supervisor_decision_blocks_provider_admission(
        supervisor_decision,
        phase=phase,
        next_safe_action=next_safe_action,
    ) or (
        next_safe_action.get("provider_admission_allowed") is False
        and _provider_admission_suppression_should_block_owner_action(
            next_safe_action=next_safe_action
        )
    ):
        _suppress_active_provider_admission_projection(updated, blocked_by=_blocked_by(supervisor_decision))
    defer_visible_projection = (
        phase in PAPER_RECOVERY_AUTHORITY_VISIBLE_PHASES
        and phase != "owner_receipt_recorded"
        and _specific_intervention_lane_has_priority(updated)
    )
    if phase in PAPER_RECOVERY_AUTHORITY_VISIBLE_PHASES and not defer_visible_projection:
        updated = _apply_paper_recovery_authority_projection(
            updated,
            phase=phase,
            summary=summary,
            next_safe_action=next_safe_action,
            recovery=recovery,
        )
    if defer_visible_projection:
        return updated
    operator_status = _mapping_copy(updated.get("operator_status_card"))
    if operator_status:
        operator_status["paper_recovery_phase"] = phase
        if phase in PAPER_RECOVERY_AUTHORITY_VISIBLE_PHASES:
            operator_status = _drop_stale_parked_fields(operator_status)
            operator_status["handling_state"] = f"paper_recovery_{phase}"
            operator_status["handling_state_label"] = _paper_recovery_lane_title(phase)
        if (
            _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action)
            or phase == "owner_receipt_recorded"
        ) and not _operator_card_has_specific_current_focus(operator_status):
            operator_status["current_focus"] = summary
            operator_status["user_visible_verdict"] = summary
        updated["operator_status_card"] = operator_status
    user_visible = _mapping_copy(updated.get("user_visible_projection"))
    if user_visible:
        user_visible["paper_recovery_phase"] = phase
        user_visible["why_not_progressing"] = phase
        if phase == "owner_receipt_recorded":
            user_visible["next_step"] = summary
            user_visible["next_system_action"] = summary
            _clear_stale_route_fields(user_visible)
            paper_progress = _mapping_copy(user_visible.get("paper_progress_state"))
            if paper_progress:
                _clear_stale_route_fields(paper_progress)
                user_visible["paper_progress_state"] = paper_progress
        if _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action):
            user_visible["current_blockers"] = [phase]
            user_visible["next_step"] = summary
            user_visible["next_system_action"] = summary
            requires_user_decision = _paper_recovery_requires_user_decision(
                phase=phase,
                next_safe_action=next_safe_action,
            )
            user_visible["needs_user_decision"] = requires_user_decision
            user_visible["needs_physician_decision"] = requires_user_decision
        elif phase == "owner_receipt_recorded":
            user_visible["current_blockers"] = _blockers_without_stale_recovery_residue(
                user_visible.get("current_blockers")
            )
            user_visible["next_system_action"] = summary
        updated["user_visible_projection"] = user_visible
    return updated


def _paper_recovery_observability_mode(
    recovery: Mapping[str, Any],
    *,
    next_safe_action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str | None:
    kind = _non_empty_text(next_safe_action.get("kind"))
    if kind != "record_human_or_owner_gate":
        return None
    conditions = {
        text
        for item in recovery.get("conditions") or []
        if isinstance(item, Mapping)
        if (text := _non_empty_text(item.get("condition"))) is not None
    }
    if "no_current_machine_executable_recovery_obligation" not in conditions:
        return None
    owner = (_non_empty_text(next_safe_action.get("owner")) or "").lower()
    if owner in {"user", "physician", "human"}:
        return None
    operator_status = _mapping_copy(payload.get("operator_status_card"))
    if _operator_card_has_specific_current_focus(operator_status):
        return "defer"
    transition = _mapping_copy(payload.get("domain_transition"))
    if _paper_recovery_has_live_supervision(payload) or _specific_intervention_lane_has_priority(payload):
        return "defer"
    if _non_empty_text(payload.get("current_stage")) != "auto_runtime_parked":
        return "defer"
    if _non_empty_text(transition.get("decision_type")) in {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "current_owner_handoff",
        "publication_gate_blocker",
        "route_back_same_line",
    } and _paper_recovery_can_cleanup_stale_park(payload):
        return "cleanup"
    return "defer"


def _paper_recovery_has_live_supervision(payload: Mapping[str, Any]) -> bool:
    supervision = _mapping_copy(payload.get("supervision"))
    active_run_id = _non_empty_text(supervision.get("active_run_id")) or _non_empty_text(payload.get("active_run_id"))
    if active_run_id is None:
        return False
    if active_run_id.startswith("opl-stage-attempt://"):
        return False
    return _non_empty_text(supervision.get("health_status")) in {"live", "running", "attempt_running", "provider_admitted"}


def _paper_recovery_can_cleanup_stale_park(payload: Mapping[str, Any]) -> bool:
    auto_parked = _mapping_copy(payload.get("auto_runtime_parked"))
    if auto_parked.get("parked") is not True:
        return False
    if auto_parked.get("auto_execution_complete") is True:
        return False
    if _non_empty_text(auto_parked.get("source_reason")) in PAPER_RECOVERY_PRESERVED_PARKED_REASONS:
        return False
    classification = _mapping_copy(auto_parked.get("runtime_failure_classification"))
    if classification.get("requires_human_gate") is True:
        return False
    if _non_empty_text(auto_parked.get("source_reason")) in PAPER_RECOVERY_STALE_PARK_CLEANUP_REASONS:
        return True
    supervision = _mapping_copy(payload.get("supervision"))
    return (
        _non_empty_text(supervision.get("active_run_id")) is not None
        and _non_empty_text(auto_parked.get("parked_state")) in {None, "waiting_user_decision"}
        and _non_empty_text(auto_parked.get("source_reason")) is None
    )


def _phase_updates_current_blockers(*, phase: str, next_safe_action: Mapping[str, Any]) -> bool:
    if phase in PAPER_RECOVERY_BLOCKING_PHASES:
        return True
    if phase not in {"domain_blocked", "human_gate"}:
        return False
    if not _paper_recovery_requires_user_decision(
        phase=phase,
        next_safe_action=next_safe_action,
    ):
        return False
    return _non_empty_text(next_safe_action.get("kind")) != "resolve_typed_blocker"


def _paper_recovery_requires_user_decision(
    *,
    phase: str,
    next_safe_action: Mapping[str, Any],
) -> bool:
    if phase != "human_gate":
        return False
    kind = _non_empty_text(next_safe_action.get("kind"))
    owner = (_non_empty_text(next_safe_action.get("owner")) or "").lower()
    if kind == "record_human_or_owner_gate" and owner not in {"user", "physician", "human"}:
        return False
    return True


def _blockers_without_stale_recovery_residue(value: object) -> list[Any]:
    stale = {
        "anti_loop_budget_exhausted",
        "no_selected_dispatch_for_authorized_stage_packet",
    }
    return [
        item
        for item in value or []
        if not (isinstance(item, str) and item in stale)
    ]


def _apply_paper_recovery_authority_projection(
    payload: dict[str, Any],
    *,
    phase: str,
    summary: str,
    next_safe_action: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> dict[str, Any]:
    if phase != "owner_receipt_recorded" and _specific_intervention_lane_has_priority(payload):
        return dict(payload)
    updated = dict(payload)
    action_kind = _non_empty_text(next_safe_action.get("kind")) or "inspect_paper_recovery_state"
    lane_id = f"paper_recovery_{phase}"
    supervisor_decision = _mapping_copy(recovery.get("supervisor_decision"))
    if _provider_admission_suppression_should_block_owner_action(
        next_safe_action=next_safe_action
    ) and _supervisor_decision_blocks_provider_admission(
        supervisor_decision,
        phase=phase,
        next_safe_action=next_safe_action,
    ) or (
        next_safe_action.get("provider_admission_allowed") is False
        and _provider_admission_suppression_should_block_owner_action(
            next_safe_action=next_safe_action
        )
    ):
        _suppress_active_provider_admission_projection(updated, blocked_by=_blocked_by(supervisor_decision))
    if _non_empty_text(updated.get("current_stage")) == "auto_runtime_parked":
        updated["current_stage"] = "publication_supervision"
    if _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action):
        updated["next_step"] = summary
    if phase == "owner_receipt_recorded":
        updated["next_step"] = summary
        updated["next_system_action"] = summary
    requires_user_decision = _paper_recovery_requires_user_decision(
        phase=phase,
        next_safe_action=next_safe_action,
    )
    if _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action):
        updated["current_blockers"] = [phase]
        updated["next_system_action"] = summary
    elif phase == "owner_receipt_recorded":
        updated["current_blockers"] = _blockers_without_stale_recovery_residue(
            updated.get("current_blockers")
        )
        updated["next_system_action"] = summary
    updated["needs_user_decision"] = requires_user_decision
    updated["user_decision_summary"] = summary if requires_user_decision else None
    updated["needs_physician_decision"] = requires_user_decision
    updated["physician_decision_summary"] = summary if requires_user_decision else None
    _clear_stale_parked_top_level_fields(updated, phase=phase, summary=summary)
    updated["intervention_lane"] = _paper_recovery_intervention_lane(
        _mapping_copy(updated.get("intervention_lane")),
        phase=phase,
        lane_id=lane_id,
        summary=summary,
        action_kind=action_kind,
        recovery=recovery,
    )
    operator_verdict = _mapping_copy(updated.get("operator_verdict"))
    operator_verdict.update(
        {
            "lane_id": lane_id,
            "decision_mode": "paper_recovery_state",
            "needs_intervention": phase in PAPER_RECOVERY_BLOCKING_PHASES
            or phase in {"domain_blocked", "human_gate"},
            "summary": summary,
            "reason_summary": summary,
            "paper_recovery_phase": phase,
        }
    )
    if phase == "owner_receipt_recorded":
        _clear_stale_route_fields(operator_verdict)
    updated["operator_verdict"] = _drop_stale_parked_fields(operator_verdict)
    for key in ("recovery_contract", "autonomy_contract"):
        surface = _mapping_copy(updated.get(key))
        if not surface:
            continue
        if key == "recovery_contract":
            surface["action_mode"] = action_kind
        else:
            surface["autonomy_state"] = lane_id
            surface["next_signal"] = summary
        surface["summary"] = summary
        surface["paper_recovery_phase"] = phase
        surface["paper_recovery_next_safe_action"] = dict(next_safe_action)
        if phase == "owner_receipt_recorded":
            _clear_stale_route_fields(surface)
        updated[key] = _drop_stale_parked_fields(surface)
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        status_contract["next_step"] = summary
        status_contract["latest_update"] = summary
        if phase == "owner_receipt_recorded":
            _clear_stale_route_fields(status_contract)
        updated["status_narration_contract"] = status_contract
    return updated


def _suppress_active_provider_admission_projection(
    payload: dict[str, Any],
    *,
    blocked_by: str = "paper_recovery_state",
) -> None:
    if _has_opl_transition_live_readback_provider_admission(payload):
        return
    if _has_identity_bound_handoff_provider_admission(payload):
        return
    candidates = [
        dict(item)
        for item in payload.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ]
    pending_count = int(payload.get("provider_admission_pending_count") or 0)
    if candidates:
        payload["blocked_provider_admission_candidates"] = candidates
    if pending_count > 0:
        payload["paper_recovery_provider_admission_blocked_count"] = pending_count
    payload["provider_admission_candidates"] = []
    payload["provider_admission_pending_count"] = 0
    _suppress_current_work_unit_provider_admission_pending(payload)
    admission = _mapping_copy(payload.get("owner_action_admission"))
    if admission:
        admission["admission_pending"] = False
        admission["provider_attempt_start_requested"] = False
        admission["blocked_by"] = blocked_by
        payload["owner_action_admission"] = admission
    monitoring = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    monitoring_admission = _mapping_copy(monitoring.get("owner_action_admission"))
    if monitoring_admission:
        monitoring_admission["admission_pending"] = False
        monitoring_admission["provider_attempt_start_requested"] = False
        monitoring_admission["blocked_by"] = blocked_by
        monitoring["owner_action_admission"] = monitoring_admission
        payload["progress_first_monitoring_summary"] = monitoring


def _provider_admission_suppression_should_block_owner_action(
    *,
    next_safe_action: Mapping[str, Any],
) -> bool:
    return _non_empty_text(next_safe_action.get("kind")) != "run_mas_owner_callable"


def _has_identity_bound_handoff_provider_admission(payload: Mapping[str, Any]) -> bool:
    if int(payload.get("provider_admission_pending_count") or 0) <= 0:
        return False
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    if int(handoff.get("provider_admission_pending_count") or 0) <= 0:
        return False
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return False
    return any(
        _same_action_identity(candidate, current_action) or _same_action_identity(candidate, current_work_unit)
        for candidate in payload.get("provider_admission_candidates") or []
        if isinstance(candidate, Mapping)
    )


def _has_opl_transition_live_readback_provider_admission(payload: Mapping[str, Any]) -> bool:
    if int(payload.get("provider_admission_pending_count") or 0) <= 0:
        return False
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return False
    return any(
        _non_empty_text(candidate.get("opl_transition_readback_source"))
        == "opl_domain_progress_transition_runtime_live_readback"
        and candidate.get("provider_admission_pending") is True
        and (_same_action_identity(candidate, current_action) or _same_action_identity(candidate, current_work_unit))
        for candidate in payload.get("provider_admission_candidates") or []
        if isinstance(candidate, Mapping)
    )


def _same_action_identity(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_action = _non_empty_text(left.get("action_type"))
    right_action = _non_empty_text(right.get("action_type"))
    if left_action is not None and right_action is not None and left_action != right_action:
        return False
    left_work_unit = _non_empty_text(left.get("work_unit_id")) or _non_empty_text(left.get("next_work_unit"))
    right_work_unit = _non_empty_text(right.get("work_unit_id")) or _non_empty_text(right.get("next_work_unit"))
    if left_work_unit is not None and right_work_unit is not None and left_work_unit != right_work_unit:
        return False
    left_fingerprint = _non_empty_text(left.get("work_unit_fingerprint")) or _non_empty_text(
        left.get("action_fingerprint")
    )
    right_fingerprint = _non_empty_text(right.get("work_unit_fingerprint")) or _non_empty_text(
        right.get("action_fingerprint")
    )
    if left_fingerprint is not None and right_fingerprint is not None and left_fingerprint != right_fingerprint:
        return False
    return (
        left_action is not None
        and right_action is not None
        and left_work_unit is not None
        and right_work_unit is not None
        and left_fingerprint is not None
        and right_fingerprint is not None
    )


def _supervisor_decision_blocks_provider_admission(
    supervisor_decision: Mapping[str, Any],
    *,
    phase: str | None = None,
    next_safe_action: Mapping[str, Any] | None = None,
) -> bool:
    if _paper_recovery_allows_provider_admission(
        phase=phase,
        next_safe_action=_mapping_copy(next_safe_action),
        supervisor_decision=supervisor_decision,
    ):
        return False
    return supervisor_decision_blocks_provider_admission(supervisor_decision)


def _paper_recovery_allows_provider_admission(
    *,
    phase: str | None,
    next_safe_action: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
) -> bool:
    if not _supervisor_decision_allows_provider_admission(
        supervisor_decision,
        recovery_action_kind=_non_empty_text(next_safe_action.get("kind")),
    ):
        return False
    if phase in {"admission_pending", "attempt_running"}:
        return True
    if phase == "owner_action_ready":
        return next_safe_action.get("provider_admission_allowed") is True
    return False


def _supervisor_decision_allows_provider_admission(
    supervisor_decision: Mapping[str, Any],
    *,
    recovery_action_kind: str | None,
) -> bool:
    if not supervisor_decision:
        return True
    decision = _non_empty_text(supervisor_decision.get("decision"))
    if decision == "execute_current_owner_delta":
        return True
    if decision != "materialize_recovery_action":
        return False
    decision_action = _mapping_copy(supervisor_decision.get("next_safe_action"))
    decision_action_kind = _non_empty_text(decision_action.get("kind"))
    allowed_action_kinds = {
        "materialize_mas_transition_request_or_owner_callable",
        "materialize_successor_owner_action",
        "admit_provider_attempt",
        "admit_identity_bound_stage_packet",
        "consume_opl_provider_admission_readback",
    }
    if decision_action_kind is None:
        return recovery_action_kind in allowed_action_kinds
    if decision_action_kind in allowed_action_kinds:
        return True
    if decision_action_kind != "materialize_recovery_work_unit_or_receipt":
        return False
    source_action = _mapping_copy(decision_action.get("source_next_safe_action"))
    source_action_kind = _non_empty_text(source_action.get("kind"))
    return source_action_kind in allowed_action_kinds


def _blocked_by(supervisor_decision: Mapping[str, Any]) -> str:
    if _supervisor_decision_blocks_provider_admission(supervisor_decision):
        return "paper_autonomy_supervisor_decision"
    return "paper_recovery_state"


def _suppress_current_work_unit_provider_admission_pending(payload: dict[str, Any]) -> None:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    state = _mapping_copy(current_work_unit.get("state"))
    if not state or state.get("provider_admission_pending") is not True:
        return
    state["provider_admission_pending"] = False
    state["paper_recovery_provider_admission_blocked"] = True
    state.pop("pending_provider_admission_evidence", None)
    current_work_unit["state"] = state
    payload["current_work_unit"] = current_work_unit


def _clear_stale_parked_top_level_fields(
    payload: dict[str, Any],
    *,
    phase: str,
    summary: str,
) -> None:
    auto_parked = _mapping_copy(payload.get("auto_runtime_parked"))
    if auto_parked:
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
                "superseded_by_paper_recovery_state": True,
                "paper_recovery_phase": phase,
                "summary": summary,
                "next_action_summary": summary,
            }
        )
        payload["auto_runtime_parked"] = auto_parked
    for key, value in {
        "parked_state": None,
        "parked_owner": None,
        "resource_release_expected": False,
        "awaiting_explicit_wakeup": False,
        "auto_execution_complete": False,
    }.items():
        payload[key] = value


def _paper_recovery_intervention_lane(
    intervention_lane: Mapping[str, Any],
    *,
    phase: str,
    lane_id: str,
    summary: str,
    action_kind: str,
    recovery: Mapping[str, Any],
) -> dict[str, Any]:
    current_authority = _mapping_copy(recovery.get("current_authority"))
    lane = _drop_stale_parked_fields(_mapping_copy(intervention_lane))
    if phase == "owner_receipt_recorded":
        _clear_stale_route_fields(lane)
    lane.update(
        {
            "lane_id": lane_id,
            "title": _paper_recovery_lane_title(phase),
            "severity": _paper_recovery_lane_severity(phase),
            "summary": summary,
            "recommended_action_id": action_kind,
            "paper_recovery_phase": phase,
            "recovery_obligation_id": _non_empty_text(recovery.get("recovery_obligation_id")),
            "authority_owner": _non_empty_text(current_authority.get("owner")),
            "awaiting_explicit_wakeup": False,
            "resource_release_expected": False,
        }
    )
    if phase == "owner_receipt_recorded":
        for key in (
            "route_key_question",
            "handoff_source",
            "route_back_checklist",
            "route_rationale",
            "route_summary",
            "route_target",
            "route_target_label",
        ):
            lane.pop(key, None)
    return {key: value for key, value in lane.items() if value not in (None, "", [], {})}


def _specific_intervention_lane_has_priority(payload: Mapping[str, Any]) -> bool:
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    lane_id = _non_empty_text(intervention_lane.get("lane_id"))
    if lane_id in {
        "runtime_recovery_required",
        "workspace_supervision_gap",
        "quality_floor_blocker",
        "completion_evidence_required",
        "progress_continuation_required",
        "current_owner_action_ready",
        "publication_gate_specificity_required",
    }:
        return True
    autonomy_contract = _mapping_copy(payload.get("autonomy_contract"))
    restore_point = _mapping_copy(autonomy_contract.get("restore_point"))
    if (
        _non_empty_text(autonomy_contract.get("autonomy_state")) == "autonomous_progress"
        and _non_empty_text(restore_point.get("resume_mode")) is not None
    ):
        return True
    runtime_health = _mapping_copy(payload.get("runtime_health_snapshot"))
    if _non_empty_text(runtime_health.get("attempt_state")) != "escalated":
        return False
    try:
        retry_budget_remaining = int(runtime_health.get("retry_budget_remaining"))
    except (TypeError, ValueError):
        return False
    blocking_reasons = {
        text
        for item in runtime_health.get("blocking_reasons") or []
        if (text := _non_empty_text(item)) is not None
    }
    return retry_budget_remaining <= 0 and "runtime_recovery_retry_budget_exhausted" in blocking_reasons


def _operator_card_has_specific_current_focus(operator_status: Mapping[str, Any]) -> bool:
    if _mapping_copy(operator_status.get("no_op_suppression")):
        return True
    return _non_empty_text(operator_status.get("handling_state")) in {
        "publication_gate_specificity_required",
    }


def _clear_stale_route_fields(surface: dict[str, Any]) -> None:
    for stale_key in (
        "route_target",
        "route_target_label",
        "route_key_question",
        "route_summary",
        "route_rationale",
        "handoff_source",
        "route_back_checklist",
        "current_blockers",
    ):
        surface.pop(stale_key, None)


def _paper_recovery_lane_title(phase: str) -> str:
    return {
        "admission_blocked": "PaperRecovery admission blocked",
        "projection_inconsistent": "PaperRecovery projection inconsistent",
        "manual_foreground_unadopted": "PaperRecovery manual delta requires adoption",
        "terminal_closeout_ready": "PaperRecovery terminal closeout ready",
        "owner_receipt_recorded": "PaperRecovery owner receipt recorded",
        "domain_blocked": "PaperRecovery owner blocker",
        "human_gate": "PaperRecovery human gate",
    }.get(phase, "PaperRecovery recovery diagnostic")


def _paper_recovery_lane_severity(phase: str) -> str:
    if phase in {"projection_inconsistent", "admission_blocked"}:
        return "critical"
    if phase in {"domain_blocked", "human_gate", "manual_foreground_unadopted"}:
        return "handoff"
    return "monitor"


def _drop_stale_parked_fields(surface: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in dict(surface).items()
        if key
        not in {
            "auto_runtime_parked",
            "parked_state",
            "parked_owner",
            "resource_release_expected",
            "awaiting_explicit_wakeup",
            "auto_execution_complete",
            "reopen_policy",
        }
    }


def paper_recovery_summary(*, phase: str, next_safe_action: Mapping[str, Any]) -> str | None:
    kind = _non_empty_text(next_safe_action.get("kind"))
    if kind == "run_mas_owner_callable":
        owner = _non_empty_text(next_safe_action.get("owner")) or "MAS"
        return (
            f"Route the PaperRecovery diagnostic to the MAS owner callable for {owner}; "
            "OPL transport retry exhaustion does not create next-action authority."
        )
    if kind == "authorize_opl_transport_recovery_or_stable_typed_blocker":
        return "Authorize OPL transport recovery for the identity-bound provider attempt or record a stable typed blocker."
    if phase == "admission_blocked":
        return "Provider admission is blocked by the current PaperRecovery recovery diagnostic action."
    if phase == "projection_inconsistent":
        return "Paper recovery projection is inconsistent; repair the MAS recovery state before admission."
    if phase == "manual_foreground_unadopted":
        return "Foreground paper edits require MAS owner receipt adoption before they count as recovery progress."
    if phase == "terminal_closeout_ready":
        return "Consume the matching terminal closeout through MAS owner authority."
    if phase == "owner_receipt_recorded":
        return "Consume the current owner receipt through MAS owner authority."
    if phase in {"domain_blocked", "human_gate"}:
        if kind is not None and kind != "resolve_typed_blocker":
            return f"Paper recovery is waiting on {kind}."
        return "Resolve the current typed blocker through its owner before starting another provider attempt."
    if phase == "attempt_running":
        return "Watch the running provider attempt bound to the current paper recovery obligation."
    if kind is not None:
        return kind
    return None


__all__ = [
    "PAPER_RECOVERY_AUTHORITY_VISIBLE_PHASES",
    "PAPER_RECOVERY_BLOCKING_PHASES",
    "apply_paper_recovery_state_user_visible_status",
    "paper_recovery_summary",
]
