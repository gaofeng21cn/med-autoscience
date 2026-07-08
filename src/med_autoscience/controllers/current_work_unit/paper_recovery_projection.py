from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit.action_projection_fields import (
    action_type as _action_type,
    work_unit_fingerprint as _work_unit_fingerprint,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit.primitives import (
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)
from med_autoscience.runtime_control.owner_route_attempt_protocol import (
    normalize_currentness_sources,
)


def owner_receipt_recorded_recovery(
    progress: Mapping[str, Any],
) -> dict[str, Any] | None:
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_receipt_recorded":
        return None
    next_action = _mapping(recovery.get("next_safe_action"))
    if _text(next_action.get("kind")) != "consume_owner_receipt":
        return None
    if _text(next_action.get("owner_receipt_ref")) or _text(recovery.get("owner_receipt_ref")):
        return recovery
    for ref in _text_items(recovery.get("evidence_refs")):
        if "receipt" in ref:
            return recovery
    return None


def paper_recovery_successor_action(
    progress: Mapping[str, Any],
) -> dict[str, Any] | None:
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return None
    next_action = _mapping(recovery.get("next_safe_action"))
    next_action_kind = _text(next_action.get("kind"))
    if next_action_kind != "run_mas_owner_callable":
        return None
    successor = _mapping(next_action.get("successor_owner_action"))
    if not successor:
        successor = _paper_recovery_callable_successor(
            progress,
            recovery=recovery,
            next_action=next_action,
        )
    action_type = _action_type(successor)
    work_unit_id = _work_unit_id(successor.get("work_unit_id")) or _work_unit_id(
        successor.get("next_work_unit")
    )
    fingerprint = _text(successor.get("work_unit_fingerprint")) or _text(
        successor.get("action_fingerprint")
    )
    owner = (
        _text(successor.get("owner"))
        or _text(successor.get("next_owner"))
        or _text(next_action.get("owner"))
    )
    if action_type is None or work_unit_id is None or fingerprint is None or owner is None:
        return None
    owner_callable = _mapping(next_action.get("owner_callable"))
    owner_callable_surface = _text(owner_callable.get("callable_surface"))
    if next_action_kind == "run_mas_owner_callable" and owner_callable_surface is None:
        return None
    source_surface = _text(successor.get("source_surface")) or _text(successor.get("source"))
    active_caller_class = "mas_owner_callable"
    paper_mission_default_role = "direct_mas_owner_callable"
    currentness_basis = normalize_currentness_sources(
        _mapping(successor.get("owner_route_currentness_basis")),
        _mapping(successor.get("currentness_basis")),
        _mapping(next_action.get("owner_route_currentness_basis")),
        _mapping(recovery.get("owner_route_currentness_basis")),
        {
            "source": source_surface,
            "source_eval_id": _text(successor.get("source_eval_id")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    )
    return {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": source_surface,
            "next_owner": owner,
            "owner": owner,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "work_unit_id": work_unit_id,
            "next_work_unit": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_ref": _text(successor.get("source_ref")),
            "domain_transition_decision_type": _text(successor.get("domain_transition_decision_type")),
            "domain_transition_controller_action": _text(successor.get("domain_transition_controller_action")),
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "target_surface": _mapping(successor.get("target_surface")),
            "owner_receipt_required": True,
            "provider_admission_pending": False,
            "transition_request_pending": False,
            "provider_attempt_or_lease_required": False,
            "provider_admission_requires_opl_runtime_result": False,
            "opl_transition_runtime_required": False,
            "default_paper_mission_entry": False,
            "ordinary_schedulable": True,
            "active_caller_class": active_caller_class,
            "paper_mission_default_role": paper_mission_default_role,
            "can_select_next_paper_stage": False,
            "can_authorize_provider_admission": False,
            "counts_as_paper_progress": False,
            "forbidden_claims": [
                "ordinary_task_admission",
                "paper_progress",
                "publication_ready",
                "runtime_ready",
                "provider_admission_authorized",
                "DM002_complete",
                "DM003_complete",
            ],
            "paper_recovery_successor": {
                "phase": _text(recovery.get("phase")),
                "source_next_safe_action_kind": next_action_kind,
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": False,
                "opl_transition_runtime_required": False,
                "source_surface": source_surface,
                "owner_callable_surface": owner_callable_surface,
                "active_caller_class": active_caller_class,
                "can_select_next_paper_stage": False,
                "counts_as_paper_progress": False,
            },
            "owner_route_currentness_basis": currentness_basis,
        }.items()
        if value not in (None, "", [], {})
    }


def paper_recovery_successor_consumes_terminal_stop_loss(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if _text(action.get("action_type")) != "run_gate_clearing_batch":
        return False
    if (
        _text(action.get("source_surface"))
        or _text(action.get("source"))
        or _text(_mapping(action.get("paper_recovery_successor")).get("source_surface"))
    ) != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return False
    blocker_work_unit = _work_unit_id(blocker.get("work_unit_id"))
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    if action_work_unit is None or action_work_unit != blocker_work_unit:
        return False
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return False
    if not repair_progress_proves_safe_successor_delta(repair):
        return False
    blocker_eval = _text(blocker.get("source_eval_id")) or _text(
        _mapping(blocker.get("currentness_basis")).get("source_eval_id")
    )
    action_eval = _text(action.get("source_eval_id")) or _text(
        _mapping(action.get("owner_route_currentness_basis")).get("source_eval_id")
    )
    return not (blocker_eval is not None and action_eval is not None and blocker_eval != action_eval)


def repair_progress_proves_safe_successor_delta(repair: Mapping[str, Any]) -> bool:
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return False
    if repair.get("paper_delta_observed") is not True:
        return False
    if not (
        repair.get("accepted_owner_receipt") is True
        or (
            repair.get("progress_delta_candidate") is True
            and repair.get("gate_replay_done") is True
        )
    ):
        return False
    if repair.get("gate_replay_done") is not True:
        return False
    return (
        _text(repair.get("repair_execution_evidence_ref")) is not None
        or _text(repair.get("owner_receipt_ref")) is not None
        or bool(_text_items(repair.get("gate_replay_refs")))
    )


def _paper_recovery_callable_successor(
    progress: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    owner_callable = _mapping(next_action.get("owner_callable"))
    current_authority = _mapping(recovery.get("current_authority"))
    obligation = _mapping(current_authority.get("obligation"))
    action_type = (
        _text(owner_callable.get("action_type"))
        or _text(obligation.get("action_type"))
    )
    work_unit_id = (
        _work_unit_id(obligation.get("work_unit_id"))
    )
    fingerprint = (
        _text(obligation.get("work_unit_fingerprint"))
        or _text(obligation.get("action_fingerprint"))
    )
    owner = (
        _text(next_action.get("owner"))
        or _text(current_authority.get("owner"))
        or _text(obligation.get("owner"))
    )
    callable_surface = _text(owner_callable.get("callable_surface"))
    if action_type is None or work_unit_id is None or fingerprint is None or owner is None:
        return {}
    if callable_surface is None:
        return {}
    return {
        "action_type": action_type,
        "owner": owner,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_surface": "paper_recovery_state.next_safe_action.owner_callable",
        "target_surface": {
            "ref_kind": "mas_owner_callable",
            "route_target": owner,
            "surface_ref": callable_surface,
            "owner_callable_surface": callable_surface,
        },
        "owner_route_currentness_basis": normalize_currentness_sources(
            _mapping(obligation.get("currentness_basis")),
            {
                "source": "paper_recovery_state.next_safe_action.owner_callable",
                "source_eval_id": _text(_mapping(progress.get("publication_eval")).get("eval_id")),
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
        ),
    }


__all__ = [
    "owner_receipt_recorded_recovery",
    "paper_recovery_successor_action",
    "paper_recovery_successor_consumes_terminal_stop_loss",
    "repair_progress_proves_safe_successor_delta",
]
