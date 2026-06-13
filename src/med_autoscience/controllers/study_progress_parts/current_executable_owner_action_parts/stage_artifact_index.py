from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)


def owner_action_from_stage_artifact_index(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    if _runtime_or_current_owner_surface_already_selected(payload):
        return None
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
            "surface_kind": surface_kind,
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


def _runtime_or_current_owner_surface_already_selected(payload: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("surface_kind")) == "current_work_unit":
        return True
    envelope = _mapping_copy(payload.get("current_execution_envelope"))
    if _non_empty_text(envelope.get("state_kind")) in {
        "executable_owner_action",
        "running_provider_attempt",
        "typed_blocker",
        "parked",
    }:
        return True
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    if handoff.get("running_provider_attempt") is True:
        return True
    if any(isinstance(item, Mapping) for item in handoff.get("action_queue") or []):
        return True
    if _mapping_copy(handoff.get("typed_blocker")):
        return True
    if _non_empty_text(handoff.get("blocked_reason")) is not None:
        return True
    return False


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


__all__ = ["owner_action_from_stage_artifact_index"]
