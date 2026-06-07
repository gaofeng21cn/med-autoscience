from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared import _mapping_copy, _non_empty_text

SURFACE_KIND = "current_executable_owner_action"
PUBLICATION_HANDOFF_ACTION = "publication_handoff_owner_gate"
READINESS_ACTION = "complete_medical_paper_readiness_surface"
READINESS_BLOCKER = "medical_paper_readiness_not_ready"
READINESS_OWNER = "MedAutoScience"


def build_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    readiness_followup = _from_stage_kernel_readiness_followup(payload)
    if readiness_followup is not None:
        return readiness_followup
    artifact_action = _from_stage_artifact_index(payload)
    if artifact_action is not None:
        return artifact_action
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
    if owner is None and work_unit_id is None and not allowed_actions:
        return _from_domain_transition(payload)
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
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


def _readiness_action(delta: Mapping[str, Any]) -> str | None:
    return _non_empty_text(delta.get("action")) or _non_empty_text(delta.get("action_type"))


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


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = [
    "SURFACE_KIND",
    "build_current_executable_owner_action",
    "owner_action_next_step",
]
