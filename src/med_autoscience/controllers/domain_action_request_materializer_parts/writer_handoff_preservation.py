from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_owner_action_dispatch_parts import (
    dispatch_contract,
    persisted_dispatches,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


def preserved_quality_repair_writer_handoff_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    action: Mapping[str, Any],
    dispatch_path: Path,
    owner_route: Mapping[str, Any],
    apply: bool,
    forbidden_surfaces: list[str],
) -> dict[str, Any] | None:
    if not apply:
        return None
    if action_type != "run_quality_repair_batch":
        return None
    payload = _read_json_object(dispatch_path)
    if not payload:
        return None
    if _text(payload.get("surface")) != "default_executor_dispatch_request":
        return None
    if _text(payload.get("dispatch_status")) != "ready":
        return None
    if _text(payload.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return None
    if _text(payload.get("study_id")) != study_id:
        return None
    if _text(payload.get("action_type")) != action_type:
        return None
    if _text(payload.get("next_executable_owner")) != "write":
        return None
    if payload.get("medical_claim_authoring_allowed") is not True:
        return None
    source_action = _mapping(payload.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return None
    if _text(source_action.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return None
    if not owner_route_part.owner_route_matches(dispatch=payload, current_route=owner_route):
        return None
    if not owner_route_part.route_allows_action(action=payload, owner_route=owner_route):
        return None
    if not persisted_dispatches.owner_request_matches_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=payload,
    ):
        return None
    prompt_contract = _mapping(payload.get("prompt_contract"))
    if not prompt_contract:
        return None
    if dispatch_contract.prompt_contract_error(
        prompt_contract,
        forbidden_surfaces=forbidden_surfaces,
    ) is not None:
        return None
    current_work_unit_id = _work_unit_id(action.get("next_work_unit"))
    handoff_work_unit_id = _work_unit_id(source_action.get("next_work_unit"))
    if current_work_unit_id is not None and handoff_work_unit_id is not None and current_work_unit_id != handoff_work_unit_id:
        return None
    return {
        **payload,
        "refs": {
            **_mapping(payload.get("refs")),
            "dispatch_path": str(dispatch_path),
        },
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["preserved_quality_repair_writer_handoff_dispatch"]
