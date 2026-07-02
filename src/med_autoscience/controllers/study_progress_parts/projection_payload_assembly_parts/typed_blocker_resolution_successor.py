from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import study_domain_transition_guard
from med_autoscience.controllers.next_action_envelope import (
    compile_next_action_envelope,
)
from med_autoscience.controllers.paper_mission_typed_blocker_resolution import (
    latest_typed_blocker_resolution_readback,
)
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    task_intake_is_reviewer_revision,
)

from ..canonical_owner_action_projection import (
    build_canonical_owner_action_projection,
    owner_action_next_step,
)
from ..shared import _mapping_copy, _non_empty_text


def attach_typed_blocker_resolution_successor_projection(
    *,
    payload: Mapping[str, Any],
    profile: Any | None,
    study_id: str,
) -> dict[str, Any]:
    workspace_root = getattr(profile, "workspace_root", None)
    if workspace_root is None:
        return dict(payload)
    readback = latest_typed_blocker_resolution_readback(
        workspace_root=Path(workspace_root),
        study_id=study_id,
    )
    if _reviewer_revision_supersedes_resolution(
        workspace_root=Path(workspace_root),
        study_id=study_id,
        typed_blocker_resolution_readback=readback,
    ):
        return dict(payload)
    if _domain_transition_redrive_supersedes_resolution(payload):
        return dict(payload)
    if _current_consumption_route_supersedes_resolution(
        payload=payload,
        typed_blocker_resolution_readback=readback,
    ):
        return dict(payload)
    envelope = _typed_blocker_resolution_successor_envelope(
        payload=payload,
        readback=readback,
        study_id=study_id,
    )
    if envelope is None:
        return dict(payload)
    updated = dict(payload)
    updated["typed_blocker_resolution_readback"] = readback
    updated["next_action"] = envelope
    updated["canonical_next_action_source"] = "paper_mission_typed_blocker_resolution"
    updated["current_executable_owner_action"] = _mapping_copy(
        _mapping_copy(readback).get("next_owner_action")
    ) or build_canonical_owner_action_projection(updated)
    return _promote_typed_blocker_resolution_owner_action(updated)


def _domain_transition_redrive_supersedes_resolution(payload: Mapping[str, Any]) -> bool:
    stage_closure = _mapping_copy(payload.get("stage_closure"))
    stage_outcome = _mapping_copy(stage_closure.get("outcome"))
    if _non_empty_text(stage_outcome.get("kind")) == "typed_blocker":
        return False
    transition = _mapping_copy(payload.get("domain_transition"))
    if study_domain_transition_guard.runtime_redrive_decision_type(
        {"domain_transition": transition}
    ) is None:
        return False
    next_action = _mapping_copy(transition.get("next_action")) or _mapping_copy(
        transition.get("next_action_envelope")
    )
    if _non_empty_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return False
    return _non_empty_text(next_action.get("owner")) is not None


def _current_consumption_route_supersedes_resolution(
    *,
    payload: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
) -> bool:
    resolution = _mapping_copy(typed_blocker_resolution_readback)
    if _mapping_copy(resolution.get("next_owner_action")):
        return False
    next_action = _mapping_copy(payload.get("next_action"))
    if _non_empty_text(next_action.get("action_family")) != "runtime.opl_route":
        return False
    summary = _mapping_copy(payload.get("artifact_first_mission_summary"))
    read_model_source = _mapping_copy(summary.get("read_model_source"))
    if (
        _non_empty_text(read_model_source.get("source_kind"))
        != "paper_mission_consumption_ledger"
    ):
        return False
    consumption_ref = _non_empty_text(read_model_source.get("consumption_ledger_ref"))
    resolution_ref = _non_empty_text(resolution.get("source_ref")) or _non_empty_text(
        resolution.get("decision_ref")
    )
    consumption_mtime = _path_mtime(consumption_ref)
    resolution_mtime = _path_mtime(resolution_ref)
    return (
        consumption_mtime is not None
        and resolution_mtime is not None
        and consumption_mtime > resolution_mtime
    )


def _path_mtime(path_text: str | None) -> float | None:
    if path_text is None:
        return None
    try:
        return Path(path_text).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _reviewer_revision_supersedes_resolution(
    *,
    workspace_root: Path,
    study_id: str,
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
) -> bool:
    resolution = _mapping_copy(typed_blocker_resolution_readback)
    if not resolution:
        return False
    task_intake = read_latest_task_intake(
        study_root=workspace_root.expanduser().resolve() / "studies" / study_id
    )
    if not task_intake_is_reviewer_revision(task_intake):
        return False
    task_time = _payload_time(task_intake)
    resolution_time = _payload_time(resolution) or _source_ref_time(resolution)
    return (
        task_time is not None
        and resolution_time is not None
        and task_time > resolution_time
    )


def _payload_time(payload: Mapping[str, Any]) -> datetime | None:
    for key in ("emitted_at", "generated_at", "recorded_at", "created_at"):
        parsed = _timestamp(_non_empty_text(payload.get(key)))
        if parsed is not None:
            return parsed
    return None


def _source_ref_time(payload: Mapping[str, Any]) -> datetime | None:
    source_ref = _non_empty_text(payload.get("source_ref")) or _non_empty_text(
        payload.get("decision_ref")
    )
    if source_ref is None:
        return None
    mtime = _path_mtime(source_ref)
    if mtime is None:
        return None
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def _timestamp(text: str | None) -> datetime | None:
    if text is None:
        return None
    value = f"{text[:-1]}+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _promote_typed_blocker_resolution_owner_action(
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
                key: item for key, item in details.items() if item not in (None, "", [], {})
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


def _typed_blocker_resolution_successor_envelope(
    *,
    payload: Mapping[str, Any],
    readback: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any] | None:
    resolution = _mapping_copy(readback)
    action = _mapping_copy(resolution.get("next_owner_action"))
    if not action:
        return None
    source_ref = _non_empty_text(resolution.get("source_ref")) or _non_empty_text(
        resolution.get("decision_ref")
    )
    action_type = _non_empty_text(action.get("action_type")) or _first_text(
        action.get("allowed_actions")
    )
    stage_closure = _mapping_copy(payload.get("stage_closure_decision"))
    return compile_next_action_envelope(
        stage_outcome={
            "kind": "next_stage_transition",
            "study_id": _non_empty_text(action.get("study_id")) or study_id,
            "stage_id": _non_empty_text(stage_closure.get("stage_id"))
            or "submission_milestone_candidate",
            "work_unit_id": action.get("work_unit_id"),
            "work_unit_fingerprint": action.get("work_unit_fingerprint"),
            "action_family": "paper.package.submission_minimal",
            "next_action": action_type,
            "decision_signature": action.get("work_unit_fingerprint"),
            "required_input_refs": action.get("acceptance_refs"),
            "paper_facing_delta": action.get("paper_facing_delta"),
            "accepted_answer_shape": action.get("accepted_answer_shape"),
            "route_back": action.get("route_back"),
            "verification": action.get("verification"),
            "executable_owner_route": action.get("executable_owner_route"),
        },
        study_id=_non_empty_text(action.get("study_id")) or study_id,
        stage_id=_non_empty_text(stage_closure.get("stage_id"))
        or "submission_milestone_candidate",
        outcome_ref=source_ref,
        owner_route={
            "next_owner": action.get("next_owner") or "mas_authority_kernel",
            "allowed_actions": action.get("allowed_actions"),
            "action_type": action_type,
            "action_family": "paper.package.submission_minimal",
            "idempotency_key": action.get("work_unit_fingerprint"),
            "paper_facing_delta": action.get("paper_facing_delta"),
            "accepted_answer_shape": action.get("accepted_answer_shape"),
            "route_back": action.get("route_back"),
            "verification": action.get("verification"),
            "executable_owner_route": action.get("executable_owner_route"),
        },
        authority_boundary={
            "projection_only": True,
            "can_claim_stage_complete": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
        },
        diagnostic_refs=[
            {"role": "typed_blocker_resolution", "ref": source_ref}
        ]
        if source_ref is not None
        else [],
    )
