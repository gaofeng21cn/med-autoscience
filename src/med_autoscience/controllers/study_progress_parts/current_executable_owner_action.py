from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared import _mapping_copy, _non_empty_text

SURFACE_KIND = "current_executable_owner_action"
PUBLICATION_HANDOFF_ACTION = "publication_handoff_owner_gate"
READINESS_ACTION = "complete_medical_paper_readiness_surface"
READINESS_BLOCKER = "medical_paper_readiness_not_ready"
READINESS_OWNER = "MedAutoScience"
REPAIR_PROGRESS_SOURCE = "repair_progress_projection.mas_owner_repair_execution_evidence"
AI_REVIEWER_ACTION = "return_to_ai_reviewer_workflow"
AI_REVIEWER_OWNER = "ai_reviewer"
AI_REVIEWER_WORK_UNIT = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
GATE_CLEARING_ACTION = "run_gate_clearing_batch"
GATE_CLEARING_OWNER = "gate_clearing_batch"
GATE_CLEARING_WORK_UNIT = "publication_gate_replay"


def build_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    domain_transition_action = _from_domain_transition(payload)
    repair_progress_action = _from_repair_progress_projection(payload)
    if repair_progress_action is not None:
        if not _action_consumed_by_dispatch_receipt(action=repair_progress_action, payload=payload):
            return repair_progress_action
        next_forced_delta_action = _from_next_forced_delta(payload)
        if next_forced_delta_action is not None:
            return next_forced_delta_action
    stage_native_action = _from_stage_native_current_owner_action(payload)
    if _stage_kernel_owner_answer_recorded_without_next_action(payload):
        return stage_native_action or domain_transition_action
    if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
        next_forced_delta_action = _from_next_forced_delta(payload)
        if _next_forced_delta_supersedes_stale_readiness_blocker(next_forced_delta_action):
            return next_forced_delta_action
        return (
            stage_native_action
            or domain_transition_action
            or _from_stage_kernel_readiness_followup(payload)
        )
    readiness_followup = _from_stage_kernel_readiness_followup(payload)
    if readiness_followup is not None:
        return readiness_followup
    if _stage_kernel_readiness_answer_without_followup(payload):
        return stage_native_action or domain_transition_action
    artifact_action = _from_stage_artifact_index(payload)
    if artifact_action is not None:
        return artifact_action
    return _from_next_forced_delta(payload) or domain_transition_action


def _from_stage_kernel_readiness_followup(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    readiness = _mapping_copy(payload.get("medical_paper_readiness"))
    if _non_empty_text(readiness.get("overall_status")) == "ready":
        return None
    delta = _current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return None
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return None
    source_ref = _non_empty_text(delta.get("source_ref"))
    next_action = _readiness_next_action(readiness=readiness, delta=delta)
    surface_key = _readiness_surface_key(next_action=next_action, delta=delta)
    if not _readiness_next_action_identifies_followup(
        next_action=next_action,
        surface_key=surface_key,
    ):
        return None
    target_surface = {
        "ref_kind": "mas_owner_surface",
        "surface_ref": _non_empty_text(delta.get("required_input")) or READINESS_ACTION,
        "blocked_surface": _non_empty_text(delta.get("blocked_surface"))
        or PUBLICATION_HANDOFF_ACTION,
    }
    if surface_key is not None:
        target_surface["surface_key"] = surface_key
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "stage_kernel_projection.current_owner_delta",
            "next_owner": _non_empty_text(delta.get("owner")) or READINESS_OWNER,
            "work_unit_id": READINESS_ACTION,
            "allowed_actions": [READINESS_ACTION],
            "owner_receipt_required": True,
            "required_delta_kind": "medical_paper_readiness_surface_or_typed_blocker",
            "target_surface": target_surface,
            "target_surface_specificity": "stage_kernel_typed_blocker_followup",
            "surface_key": surface_key,
            "next_action": next_action or None,
            "acceptance_refs": _text_items(delta.get("acceptance_refs")),
            "blocked_surface": _non_empty_text(delta.get("blocked_surface")) or PUBLICATION_HANDOFF_ACTION,
            "source_ref": source_ref,
            "latest_owner_answer_ref": _non_empty_text(delta.get("latest_owner_answer_ref")) or source_ref,
            "latest_owner_answer_kind": _non_empty_text(delta.get("latest_owner_answer_kind"))
            or _non_empty_text(delta.get("source_kind")),
            "artifact_first_precedence": {
                "superseded_stage_artifact_action": PUBLICATION_HANDOFF_ACTION,
                "reason": _non_empty_text(delta.get("reason")) or READINESS_BLOCKER,
                "typed_blocker_followup_takes_precedence": True,
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _from_repair_progress_projection(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    repair_progress = _mapping_copy(payload.get("repair_progress_projection"))
    if repair_progress.get("paper_delta_observed") is not True:
        return None
    if repair_progress.get("accepted_owner_receipt") is not True:
        return None
    source_ref = _non_empty_text(repair_progress.get("repair_execution_evidence_ref")) or _non_empty_text(
        repair_progress.get("owner_receipt_ref")
    )
    ai_reviewer_request_ref = _non_empty_text(repair_progress.get("ai_reviewer_recheck_request_ref"))
    gate_replay_refs = _text_items(repair_progress.get("gate_replay_refs"))
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
        )
    return None


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
) -> dict[str, Any]:
    owner_receipt_ref = _non_empty_text(repair_progress.get("owner_receipt_ref"))
    repair_evidence_ref = _non_empty_text(repair_progress.get("repair_execution_evidence_ref"))
    work_unit_fingerprint = _non_empty_text(repair_progress.get("source_fingerprint"))
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": REPAIR_PROGRESS_SOURCE,
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
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
                "superseded_stage_native_action": "run_quality_repair_batch",
                "superseded_readiness_action": READINESS_ACTION,
                "source_work_unit_id": _non_empty_text(repair_progress.get("work_unit_id")),
                "source_fingerprint": _non_empty_text(repair_progress.get("source_fingerprint")),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _from_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    next_forced_delta = _mapping_copy(payload.get("next_forced_delta"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    owner = _non_empty_text(owner_action.get("next_owner")) or _non_empty_text(
        next_forced_delta.get("next_owner")
    )
    work_unit_id = _non_empty_text(owner_action.get("work_unit_id")) or _non_empty_text(
        next_forced_delta.get("work_unit_id")
    )
    allowed_actions = _text_items(owner_action.get("allowed_actions")) or _text_items(
        next_forced_delta.get("allowed_actions")
    )
    action_type = (
        _non_empty_text(owner_action.get("action_type"))
        or _non_empty_text(next_forced_delta.get("action_type"))
        or (allowed_actions[0] if len(allowed_actions) == 1 else None)
    )
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "action_type": action_type,
            "allowed_actions": allowed_actions,
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(next_forced_delta.get("required_delta_kind")),
            "target_surface": _mapping_copy(next_forced_delta.get("target_surface")) or None,
            "target_surface_specificity": _non_empty_text(
                next_forced_delta.get("target_surface_specificity")
            ),
            "acceptance_refs": _text_items(next_forced_delta.get("acceptance_refs")),
            "authority_boundary": _authority_boundary(),
        }
    )


def _next_forced_delta_supersedes_stale_readiness_blocker(
    action: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping_copy(action)
    if _non_empty_text(payload.get("source")) != "study_progress.next_forced_delta.owner_action":
        return False
    if _non_empty_text(payload.get("required_delta_kind")) != "review_current_paper_delta":
        return False
    values = {
        _non_empty_text(payload.get("action_type")),
        _non_empty_text(payload.get("work_unit_id")),
        *_text_items(payload.get("allowed_actions")),
    }
    if READINESS_ACTION in values:
        return False
    return bool(
        values.intersection(
            {
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
                "run_quality_repair_batch",
            }
        )
    )


def _action_consumed_by_dispatch_receipt(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    consumption = _mapping_copy(_mapping_copy(payload.get("progress_first_monitoring_summary")).get("dispatch_consumption"))
    if not consumption:
        consumption = _mapping_copy(_mapping_copy(payload.get("domain_transition")).get("completion_receipt_consumption"))
    if not consumption:
        consumption = _mapping_copy(
            _mapping_copy(payload.get("domain_transition")).get("default_executor_execution_receipt_consumption")
        )
    consumption_status = _non_empty_text(consumption.get("consumption_status")) or _non_empty_text(
        consumption.get("status")
    )
    if consumption_status != "consumed":
        return False
    action_work_unit = _non_empty_text(action.get("work_unit_id"))
    consumed_work_unit = _non_empty_text(consumption.get("work_unit_id"))
    if action_work_unit is None or consumed_work_unit != action_work_unit:
        return False
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint"))
    )
    consumed_fingerprint = (
        _non_empty_text(consumption.get("work_unit_fingerprint"))
        or _non_empty_text(consumption.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(consumption.get("canonical_work_unit_identity")).get("work_unit_fingerprint"))
    )
    if action_fingerprint is not None and action_fingerprint == consumed_fingerprint:
        return True
    return _ai_reviewer_eval_receipt_consumes_repair_followup(
        action=action,
        consumption=consumption,
    )


def _ai_reviewer_eval_receipt_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    if _non_empty_text(consumption.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    receipt_ref = _non_empty_text(consumption.get("receipt_ref"))
    if receipt_ref is None or "publication_eval" not in receipt_ref:
        return False
    return _non_empty_text(consumption.get("work_unit_id")) == AI_REVIEWER_WORK_UNIT


def owner_action_next_step(action: Mapping[str, Any]) -> str | None:
    owner = _non_empty_text(action.get("next_owner"))
    actions = _text_items(action.get("allowed_actions"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    if owner is None and not actions and work_unit_id is None:
        return None
    owner_text = f"{owner} owner" if owner is not None else "当前 owner"
    action_text = f"执行 {actions[0]}" if actions else "处理当前 owner action"
    work_unit_text = f"，处理 work unit {work_unit_id}" if work_unit_id is not None else ""
    return f"等待 {owner_text} {action_text}{work_unit_text}，产出 owner receipt、typed blocker 或下一 owner handoff。"


def _from_stage_artifact_index(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    index = _mapping_copy(payload.get("stage_artifact_index"))
    if _non_empty_text(index.get("surface_kind")) != "stage_artifact_index":
        return None
    owner_action = _mapping_copy(index.get("next_owner_action"))
    owner = _non_empty_text(owner_action.get("next_owner"))
    work_unit_id = _non_empty_text(owner_action.get("work_unit_id"))
    allowed_actions = _text_items(owner_action.get("allowed_actions"))
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    stale_platform_repairs = _mapping_items(index.get("stale_platform_repairs"))
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "stage_artifact_index.next_owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": allowed_actions,
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(owner_action.get("required_delta_kind")),
            "target_surface": _mapping_copy(owner_action.get("target_surface")) or None,
            "target_surface_specificity": _non_empty_text(
                owner_action.get("target_surface_specificity")
            ),
            "acceptance_refs": _text_items(owner_action.get("acceptance_refs")),
            "artifact_first_precedence": {
                "surface_kind": "stage_artifact_index",
                "current_stage": _non_empty_text(index.get("current_stage")),
                "stale_platform_repairs_superseded": bool(stale_platform_repairs),
                "stale_platform_repairs": stale_platform_repairs,
                "stage_count": len(_mapping_items(index.get("stages"))),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _from_stage_native_current_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    action = _mapping_copy(payload.get("stage_native_current_owner_action"))
    if _non_empty_text(action.get("source")) != "stage_native_workspace_next_action":
        return None
    owner = _non_empty_text(action.get("next_owner"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    allowed_actions = _text_items(action.get("allowed_actions"))
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "stage_native_workspace_next_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "action_type": _non_empty_text(action.get("action_type")),
            "allowed_actions": allowed_actions,
            "owner_receipt_required": action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(action.get("required_delta_kind")),
            "target_surface": _mapping_copy(action.get("target_surface")) or None,
            "source_ref": _non_empty_text(action.get("source_ref")),
            "authority_boundary": _mapping_copy(action.get("authority_boundary"))
            or _authority_boundary(),
        }
    )


def _from_domain_transition(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    owner = _non_empty_text(transition.get("owner")) or _non_empty_text(transition.get("route_target"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    action = _non_empty_text(transition.get("controller_action"))
    if owner is None and work_unit_id is None and action is None:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "domain_transition",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": [action] if action is not None else [],
            "owner_receipt_required": True,
            "authority_boundary": _authority_boundary(),
        }
    )


def _current_owner_delta(payload: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping_copy(payload.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping_copy(payload.get("stage_kernel_projection"))
    delta = _mapping_copy(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping_copy(stage_kernel.get("stage_run_kernel"))
    return _mapping_copy(stage_run_kernel.get("current_owner_delta"))


def _readiness_next_action(*, readiness: Mapping[str, Any], delta: Mapping[str, Any]) -> dict[str, Any]:
    next_action = _mapping_copy(delta.get("next_action")) or _mapping_copy(readiness.get("next_action"))
    if not next_action:
        return {}
    return {
        key: value
        for key, value in next_action.items()
        if value not in (None, "", [], {})
    }


def _readiness_surface_key(*, next_action: Mapping[str, Any], delta: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(delta.get("surface_key"))
        or _non_empty_text(next_action.get("surface_key"))
    )


def _readiness_next_action_identifies_followup(
    *,
    next_action: Mapping[str, Any],
    surface_key: str | None,
) -> bool:
    if not next_action:
        return False
    if surface_key is not None:
        return True
    action = _non_empty_text(next_action.get("action_id")) or _non_empty_text(
        next_action.get("action_type")
    )
    if action is not None and action not in {READINESS_ACTION, "continue_managed_execution"}:
        return True
    if _non_empty_text(next_action.get("route_target")) or _non_empty_text(
        next_action.get("next_owner")
    ):
        return True
    if _non_empty_text(next_action.get("work_unit_id")):
        return True
    return bool(_mapping_copy(next_action.get("target_surface")))


def _readiness_action(delta: Mapping[str, Any]) -> str | None:
    return _non_empty_text(delta.get("action")) or _non_empty_text(delta.get("action_type"))


def _stage_kernel_readiness_answer_without_followup(payload: Mapping[str, Any]) -> bool:
    readiness = _mapping_copy(payload.get("medical_paper_readiness"))
    if _non_empty_text(readiness.get("overall_status")) == "ready":
        return False
    delta = _current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return False
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return False
    next_action = _readiness_next_action(readiness=readiness, delta=delta)
    surface_key = _readiness_surface_key(next_action=next_action, delta=delta)
    return not _readiness_next_action_identifies_followup(
        next_action=next_action,
        surface_key=surface_key,
    )


def _stage_kernel_readiness_stable_typed_blocker_answer(payload: Mapping[str, Any]) -> bool:
    delta = _current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return False
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return False
    return _non_empty_text(delta.get("reason")) == "medical_paper_readiness_missing"


def _stage_kernel_owner_answer_recorded_without_next_action(payload: Mapping[str, Any]) -> bool:
    delta = _current_owner_delta(payload)
    hard_gate = _mapping_copy(delta.get("hard_gate"))
    if _non_empty_text(hard_gate.get("state")) == "domain_owner_answer_recorded":
        owner_answer_kind = (
            _non_empty_text(hard_gate.get("owner_answer_kind"))
            or _non_empty_text(delta.get("latest_owner_answer_kind"))
            or _non_empty_text(delta.get("source_kind"))
        )
        if owner_answer_kind not in {"typed_blocker", "owner_receipt"}:
            return False
        return not _stage_kernel_has_explicit_next_owner_action(payload)
    if not _stage_kernel_has_manifest_backed_typed_blocker_answer(payload):
        return False
    return not _stage_kernel_has_explicit_next_owner_action(payload)


def _stage_kernel_has_explicit_next_owner_action(payload: Mapping[str, Any]) -> bool:
    candidates = (
        _mapping_copy(delta_next_action) if (delta_next_action := _current_owner_delta(payload).get("next_owner_action")) else {},
    )
    for candidate in candidates:
        if (
            _non_empty_text(candidate.get("next_owner"))
            or _non_empty_text(candidate.get("owner"))
            or _non_empty_text(candidate.get("work_unit_id"))
            or _non_empty_text(candidate.get("action_type"))
            or _text_items(candidate.get("allowed_actions"))
        ):
            return True
    return False


def _stage_kernel_has_manifest_backed_typed_blocker_answer(payload: Mapping[str, Any]) -> bool:
    stage_kernel = _mapping_copy(payload.get("stage_kernel_projection"))
    stage_run_kernel = _mapping_copy(stage_kernel.get("stage_run_kernel"))
    delta = _current_owner_delta(payload)
    return (
        _non_empty_text(stage_run_kernel.get("status")) == "TypedBlocked"
        and _non_empty_text(delta.get("source_kind")) == "typed_blocker"
        and _non_empty_text(delta.get("source_ref")) is not None
    )


def _is_stage_kernel_typed_blocker_followup(delta: Mapping[str, Any]) -> bool:
    if _non_empty_text(delta.get("source_kind")) == "typed_blocker":
        return True
    if _non_empty_text(delta.get("required_input")) == READINESS_ACTION:
        return True
    if _non_empty_text(delta.get("blocked_surface")) == PUBLICATION_HANDOFF_ACTION:
        return True
    if _non_empty_text(delta.get("latest_owner_answer_kind")) == "typed_blocker":
        return True
    return bool(_text_items(delta.get("typed_blocker_refs")))


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


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


def _dedupe_text(items: list[str | None]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = [
    "SURFACE_KIND",
    "build_current_executable_owner_action",
    "owner_action_next_step",
]
