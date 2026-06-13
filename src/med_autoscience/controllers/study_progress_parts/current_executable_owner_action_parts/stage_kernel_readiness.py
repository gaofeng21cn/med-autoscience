from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)


PUBLICATION_HANDOFF_ACTION = "publication_handoff_owner_gate"
READINESS_ACTION = "complete_medical_paper_readiness_surface"
READINESS_BLOCKER = "medical_paper_readiness_not_ready"
READINESS_OWNER = "MedAutoScience"


def owner_action_from_stage_kernel_readiness_followup(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    readiness = _mapping_copy(payload.get("medical_paper_readiness"))
    if _non_empty_text(readiness.get("overall_status")) == "ready":
        return None
    delta = current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return None
    if not is_stage_kernel_typed_blocker_followup(delta):
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
            "surface_kind": surface_kind,
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


def current_owner_delta(payload: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping_copy(payload.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping_copy(payload.get("stage_kernel_projection"))
    delta = _mapping_copy(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping_copy(stage_kernel.get("stage_run_kernel"))
    return _mapping_copy(stage_run_kernel.get("current_owner_delta"))


def stage_kernel_readiness_answer_without_followup(payload: Mapping[str, Any]) -> bool:
    readiness = _mapping_copy(payload.get("medical_paper_readiness"))
    if _non_empty_text(readiness.get("overall_status")) == "ready":
        return False
    delta = current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return False
    if not is_stage_kernel_typed_blocker_followup(delta):
        return False
    next_action = _readiness_next_action(readiness=readiness, delta=delta)
    surface_key = _readiness_surface_key(next_action=next_action, delta=delta)
    return not _readiness_next_action_identifies_followup(
        next_action=next_action,
        surface_key=surface_key,
    )


def stage_kernel_readiness_stable_typed_blocker_answer(payload: Mapping[str, Any]) -> bool:
    delta = current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return False
    if not is_stage_kernel_typed_blocker_followup(delta):
        return False
    return _non_empty_text(delta.get("reason")) == "medical_paper_readiness_missing"


def stage_kernel_owner_answer_recorded_without_next_action(payload: Mapping[str, Any]) -> bool:
    delta = current_owner_delta(payload)
    hard_gate = _mapping_copy(delta.get("hard_gate"))
    if _non_empty_text(hard_gate.get("state")) == "domain_owner_answer_recorded":
        owner_answer_kind = (
            _non_empty_text(hard_gate.get("owner_answer_kind"))
            or _non_empty_text(delta.get("latest_owner_answer_kind"))
            or _non_empty_text(delta.get("source_kind"))
        )
        if owner_answer_kind not in {"typed_blocker", "owner_receipt"}:
            return False
        return not stage_kernel_has_explicit_next_owner_action(payload)
    if not stage_kernel_has_manifest_backed_typed_blocker_answer(payload):
        return False
    return not stage_kernel_has_explicit_next_owner_action(payload)


def stage_kernel_has_explicit_next_owner_action(payload: Mapping[str, Any]) -> bool:
    candidates = (
        _mapping_copy(delta_next_action) if (delta_next_action := current_owner_delta(payload).get("next_owner_action")) else {},
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


def stage_kernel_has_manifest_backed_typed_blocker_answer(payload: Mapping[str, Any]) -> bool:
    stage_kernel = _mapping_copy(payload.get("stage_kernel_projection"))
    stage_run_kernel = _mapping_copy(stage_kernel.get("stage_run_kernel"))
    delta = current_owner_delta(payload)
    return (
        _non_empty_text(stage_run_kernel.get("status")) == "TypedBlocked"
        and _non_empty_text(delta.get("source_kind")) == "typed_blocker"
        and _non_empty_text(delta.get("source_ref")) is not None
    )


def is_stage_kernel_typed_blocker_followup(delta: Mapping[str, Any]) -> bool:
    if _non_empty_text(delta.get("source_kind")) == "typed_blocker":
        return True
    if _non_empty_text(delta.get("required_input")) == READINESS_ACTION:
        return True
    if _non_empty_text(delta.get("blocked_surface")) == PUBLICATION_HANDOFF_ACTION:
        return True
    if _non_empty_text(delta.get("latest_owner_answer_kind")) == "typed_blocker":
        return True
    return bool(_text_items(delta.get("typed_blocker_refs")))


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
    "READINESS_ACTION",
    "current_owner_delta",
    "is_stage_kernel_typed_blocker_followup",
    "owner_action_from_stage_kernel_readiness_followup",
    "stage_kernel_has_explicit_next_owner_action",
    "stage_kernel_has_manifest_backed_typed_blocker_answer",
    "stage_kernel_owner_answer_recorded_without_next_action",
    "stage_kernel_readiness_answer_without_followup",
    "stage_kernel_readiness_stable_typed_blocker_answer",
]
