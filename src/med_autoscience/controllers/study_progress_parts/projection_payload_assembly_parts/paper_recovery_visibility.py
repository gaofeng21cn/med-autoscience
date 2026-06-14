from __future__ import annotations

from typing import Any, Mapping

from ..paper_autonomy_supervisor_decision import supervisor_decision_blocks_provider_admission
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
        "domain_blocked",
        "human_gate",
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
    updated = dict(payload)
    if _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action):
        blockers = list(updated.get("current_blockers") or [])
        if phase not in blockers:
            blockers.append(phase)
        updated["current_blockers"] = blockers
        updated["next_system_action"] = summary
    if _supervisor_decision_blocks_provider_admission(
        supervisor_decision,
        phase=phase,
        next_safe_action=next_safe_action,
    ) or (
        next_safe_action.get("provider_admission_allowed") is False
    ):
        _suppress_active_provider_admission_projection(updated, blocked_by=_blocked_by(supervisor_decision))
    if phase in PAPER_RECOVERY_AUTHORITY_VISIBLE_PHASES:
        updated = _apply_paper_recovery_authority_projection(
            updated,
            phase=phase,
            summary=summary,
            next_safe_action=next_safe_action,
            recovery=recovery,
        )
    operator_status = _mapping_copy(updated.get("operator_status_card"))
    if operator_status:
        operator_status["paper_recovery_phase"] = phase
        if phase in PAPER_RECOVERY_AUTHORITY_VISIBLE_PHASES:
            operator_status = _drop_stale_parked_fields(operator_status)
            operator_status["handling_state"] = f"paper_recovery_{phase}"
            operator_status["handling_state_label"] = _paper_recovery_lane_title(phase)
        operator_status["current_focus"] = summary
        operator_status["user_visible_verdict"] = summary
        updated["operator_status_card"] = operator_status
    user_visible = _mapping_copy(updated.get("user_visible_projection"))
    if user_visible:
        user_visible["paper_recovery_phase"] = phase
        user_visible["next_step"] = summary
        user_visible["why_not_progressing"] = phase
        if _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action):
            user_visible["current_blockers"] = [phase]
            user_visible["next_system_action"] = summary
            user_visible["needs_user_decision"] = phase == "human_gate"
            user_visible["needs_physician_decision"] = phase == "human_gate"
        updated["user_visible_projection"] = user_visible
    return updated


def _phase_updates_current_blockers(*, phase: str, next_safe_action: Mapping[str, Any]) -> bool:
    if phase in PAPER_RECOVERY_BLOCKING_PHASES:
        return True
    if phase not in {"domain_blocked", "human_gate"}:
        return False
    return _non_empty_text(next_safe_action.get("kind")) != "resolve_typed_blocker"


def _apply_paper_recovery_authority_projection(
    payload: dict[str, Any],
    *,
    phase: str,
    summary: str,
    next_safe_action: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    action_kind = _non_empty_text(next_safe_action.get("kind")) or "inspect_paper_recovery_state"
    lane_id = f"paper_recovery_{phase}"
    supervisor_decision = _mapping_copy(recovery.get("supervisor_decision"))
    if _supervisor_decision_blocks_provider_admission(
        supervisor_decision,
        phase=phase,
        next_safe_action=next_safe_action,
    ) or (
        next_safe_action.get("provider_admission_allowed") is False
    ):
        _suppress_active_provider_admission_projection(updated, blocked_by=_blocked_by(supervisor_decision))
    if _non_empty_text(updated.get("current_stage")) == "auto_runtime_parked":
        updated["current_stage"] = "publication_supervision"
    updated["next_step"] = summary
    requires_user_decision = phase == "human_gate"
    if _phase_updates_current_blockers(phase=phase, next_safe_action=next_safe_action):
        updated["current_blockers"] = [phase]
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
    updated["operator_verdict"] = _drop_stale_parked_fields(operator_verdict)
    for key in ("recovery_contract", "autonomy_contract"):
        surface = _mapping_copy(updated.get(key))
        if not surface:
            continue
        if key == "recovery_contract":
            surface["action_mode"] = action_kind
        else:
            surface["autonomy_state"] = lane_id
        surface["summary"] = summary
        surface["paper_recovery_phase"] = phase
        surface["paper_recovery_next_safe_action"] = dict(next_safe_action)
        updated[key] = _drop_stale_parked_fields(surface)
    return updated


def _suppress_active_provider_admission_projection(
    payload: dict[str, Any],
    *,
    blocked_by: str = "paper_recovery_state",
) -> None:
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
    if phase == "owner_action_ready" and next_safe_action.get("provider_admission_allowed") is True:
        return _non_empty_text(next_safe_action.get("kind")) in {
            "materialize_provider_admission_or_owner_callable",
            "materialize_successor_owner_action",
            "admit_identity_bound_stage_packet",
        }
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
        "materialize_provider_admission_or_owner_callable",
        "materialize_successor_owner_action",
        "admit_provider_attempt",
        "admit_identity_bound_stage_packet",
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
    return {key: value for key, value in lane.items() if value not in (None, "", [], {})}


def _paper_recovery_lane_title(phase: str) -> str:
    return {
        "admission_blocked": "PaperRecovery admission blocked",
        "projection_inconsistent": "PaperRecovery projection inconsistent",
        "manual_foreground_unadopted": "PaperRecovery manual delta requires adoption",
        "terminal_closeout_ready": "PaperRecovery terminal closeout ready",
        "domain_blocked": "PaperRecovery owner blocker",
        "human_gate": "PaperRecovery human gate",
    }.get(phase, "PaperRecovery authority")


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
        return f"Run the current MAS owner callable for {owner}; OPL transport retry exhaustion does not own this action."
    if kind == "authorize_opl_transport_recovery_or_stable_typed_blocker":
        return "Authorize OPL transport recovery for the identity-bound provider attempt or record a stable typed blocker."
    if phase == "admission_blocked":
        return "Provider admission is blocked by the current PaperRecovery authority action."
    if phase == "projection_inconsistent":
        return "Paper recovery projection is inconsistent; repair the MAS recovery state before admission."
    if phase == "manual_foreground_unadopted":
        return "Foreground paper edits require MAS owner receipt adoption before they count as recovery progress."
    if phase == "terminal_closeout_ready":
        return "Consume the matching terminal closeout through MAS owner authority."
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
