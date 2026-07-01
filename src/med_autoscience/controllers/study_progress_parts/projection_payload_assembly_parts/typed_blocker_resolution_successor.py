from __future__ import annotations

from typing import Any, Mapping

from ..canonical_owner_action_projection import owner_action_next_step
from .current_execution_surfaces import (
    typed_blocker_reason as _typed_blocker_reason,
)
from ..shared import _mapping_copy, _non_empty_text


def promote_typed_blocker_resolution_owner_action(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return dict(payload)
    owner = _non_empty_text(current_action.get("next_owner")) or "mas_authority_kernel"
    action_type = _non_empty_text(current_action.get("action_type"))
    work_unit_id = _non_empty_text(current_action.get("work_unit_id"))
    next_step = owner_action_next_step(current_action) or (
        f"等待 {owner} owner 处理当前 typed-blocker resolution owner action。"
    )
    blocker = _typed_blocker_resolution_blocker(payload)
    current_blockers = _typed_blocker_resolution_current_blockers(
        payload.get("current_blockers"),
        blocker=blocker,
    )
    summary = _typed_blocker_resolution_summary(
        owner=owner,
        action_type=action_type,
        work_unit_id=work_unit_id,
        blocker=blocker,
    )
    updated = dict(payload)
    updated["current_stage"] = "owner_action_ready"
    updated["current_stage_summary"] = summary
    updated["paper_stage"] = (
        _non_empty_text(updated.get("paper_stage")) or "publishability_gate_blocked"
    )
    updated["paper_stage_summary"] = summary
    updated["runtime_decision"] = "owner_action_required"
    updated["runtime_reason"] = "typed_blocker_resolution_owner_action_ready"
    updated["current_blockers"] = current_blockers
    updated["next_system_action"] = next_step
    updated["needs_user_decision"] = True
    updated["needs_physician_decision"] = True
    updated["physician_decision_summary"] = summary
    updated["user_decision_summary"] = summary
    updated["paper_facing_action"] = _owner_action_paper_facing_action(current_action)
    updated["study_macro_state"] = _typed_blocker_resolution_macro_state(
        payload.get("study_macro_state"),
        owner=owner,
        action_type=action_type,
        work_unit_id=work_unit_id,
        blocker=blocker,
    )
    updated["user_visible_projection"] = _typed_blocker_resolution_user_visible(
        updated.get("user_visible_projection"),
        current_action=current_action,
        current_blockers=current_blockers,
        next_step=next_step,
        summary=summary,
        owner=owner,
    )
    updated["status_narration_contract"] = (
        _typed_blocker_resolution_status_narration_contract(
            updated.get("status_narration_contract"),
            current_blockers=current_blockers,
            next_step=next_step,
            summary=summary,
        )
    )
    return updated


def _typed_blocker_resolution_blocker(payload: Mapping[str, Any]) -> str:
    readback = _mapping_copy(payload.get("typed_blocker_resolution_readback"))
    typed_blocker = _mapping_copy(readback.get("typed_blocker"))
    successor = _mapping_copy(readback.get("successor_work_unit"))
    action = _mapping_copy(payload.get("current_executable_owner_action"))
    paper_delta = _mapping_copy(action.get("paper_facing_delta"))
    return (
        _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(successor.get("successor_reason"))
        or _non_empty_text(paper_delta.get("expected_delta"))
        or "paper_mission_stage_route_domain_gate_pending"
    )


def _typed_blocker_resolution_current_blockers(
    value: object,
    *,
    blocker: str,
) -> list[str]:
    stale_fragments = (
        "quest user paused requires explicit wakeup",
        "explicit wakeup",
        "OPL current_control_state handoff",
        "provider admission",
        "runtime owner",
    )
    blockers = [blocker]
    for item in value or []:
        text = _non_empty_text(item)
        if text is None:
            continue
        if any(fragment in text for fragment in stale_fragments):
            continue
        if text not in blockers:
            blockers.append(text)
    return blockers[:8]


def _typed_blocker_resolution_summary(
    *,
    owner: str,
    action_type: str | None,
    work_unit_id: str | None,
    blocker: str,
) -> str:
    action = action_type or "typed-blocker resolution owner action"
    work_unit = f"，work unit={work_unit_id}" if work_unit_id else ""
    return (
        f"OPL terminal receipt 已被 MAS 消费为 typed blocker；当前需 {owner} "
        f"处理 {action}{work_unit}。当前阻塞：{blocker}。"
    )


def _typed_blocker_resolution_macro_state(
    value: object,
    *,
    owner: str,
    action_type: str | None,
    work_unit_id: str | None,
    blocker: str,
) -> dict[str, Any]:
    macro = _mapping_copy(value)
    details = _mapping_copy(macro.get("details"))
    details.update(
        {
            "paper_stage": "publishability_gate_blocked",
            "reason_separation": {
                "control_reason_policy": "typed_blocker_resolution_owner_action",
                "diagnostic_reason_policy": "legacy_runtime_pause_demoted",
            },
            "next_work_unit": work_unit_id,
            "route_owner": owner,
            "action_type": action_type,
            "typed_blocker": blocker,
        }
    )
    macro.update(
        {
            "surface": "study_macro_state",
            "schema_version": 1,
            "writer_state": "owner_action_ready",
            "user_next": "decide",
            "reason": "typed_blocker_resolution_owner_action_ready",
            "details": {
                key: item
                for key, item in details.items()
                if item not in (None, "", [], {})
            },
            "suppression_reason": "typed_blocker_resolution_successor_promoted",
        }
    )
    return macro


def _typed_blocker_resolution_user_visible(
    value: object,
    *,
    current_action: Mapping[str, Any],
    current_blockers: list[str],
    next_step: str,
    summary: str,
    owner: str,
) -> dict[str, Any]:
    user_visible = _mapping_copy(value)
    user_visible.update(
        {
            "state": "owner_action_ready/decide/typed_blocker_resolution",
            "writer_state": "owner_action_ready",
            "user_next": "decide",
            "reason": "typed_blocker_resolution_owner_action_ready",
            "package_delivered": False,
            "actual_write_active": False,
            "meaningful_artifact_delta": False,
            "next_owner": owner,
            "why_not_progressing": current_blockers[0] if current_blockers else None,
            "user_action_required": True,
            "state_label": "MAS owner action ready",
            "state_summary": summary,
            "current_stage": "owner_action_ready",
            "current_stage_label": "MAS owner action ready",
            "current_stage_summary": summary,
            "status_summary": summary,
            "paper_stage": "publishability_gate_blocked",
            "paper_stage_summary": summary,
            "current_blockers": current_blockers,
            "next_system_action": next_step,
            "next_step": next_step,
            "needs_user_decision": True,
            "needs_physician_decision": True,
            "current_executable_owner_action": dict(current_action),
        }
    )
    return {key: item for key, item in user_visible.items() if item is not None}


def _owner_action_paper_facing_action(action: Mapping[str, Any]) -> dict[str, Any]:
    authority = _mapping_copy(action.get("authority_boundary"))
    return {
        "surface_kind": "paper_mission_paper_facing_action",
        "schema_version": 1,
        "status": "owner_action_ready",
        "source_surface": "paper_mission.next_action",
        "study_id": action.get("study_id"),
        "next_owner": action.get("next_owner") or action.get("owner"),
        "action_type": action.get("action_type"),
        "allowed_actions": action.get("allowed_actions"),
        "work_unit_id": action.get("work_unit_id"),
        "work_unit_fingerprint": action.get("work_unit_fingerprint"),
        "required_delta_kind": action.get("required_delta_kind"),
        "target_surface": action.get("target_surface"),
        "target_surface_specificity": action.get("target_surface_specificity"),
        "paper_facing_delta": action.get("paper_facing_delta"),
        "accepted_answer_shape": action.get("accepted_answer_shape"),
        "route_back": action.get("route_back"),
        "verification": action.get("verification"),
        "next_step": owner_action_next_step(action),
        "authority_boundary": {
            "projection_only": authority.get("projection_only", True),
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_write_current_package": False,
            "can_start_provider_attempt": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
            "can_claim_paper_progress": False,
        },
    }


def _typed_blocker_resolution_status_narration_contract(
    value: object,
    *,
    current_blockers: list[str],
    next_step: str,
    summary: str,
) -> dict[str, Any]:
    contract = _mapping_copy(value)
    stage = _mapping_copy(contract.get("stage"))
    stage["current_stage"] = "owner_action_ready"
    contract["stage"] = stage
    readiness = _mapping_copy(contract.get("readiness"))
    readiness["needs_physician_decision"] = True
    contract["readiness"] = readiness
    contract["current_blockers"] = current_blockers
    contract["latest_update"] = summary
    contract["next_step"] = next_step
    return contract
