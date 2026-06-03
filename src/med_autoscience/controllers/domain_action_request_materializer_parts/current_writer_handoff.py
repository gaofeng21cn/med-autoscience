from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import request_output_surface_for_action_type
from med_autoscience.controllers.quality_repair_batch_parts import writer_handoff as quality_repair_writer_handoff
from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_receipt_consumption,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


def current_quality_repair_writer_handoff_action(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    batch = _read_json_object(
        profile.studies_root / study_id / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    )
    if not batch:
        return None
    if _text(batch.get("status")) != "handoff_ready":
        return None
    if _text(batch.get("next_owner")) != "write":
        return None
    handoff = _mapping(batch.get("writer_worker_handoff"))
    if not _current_quality_repair_writer_handoff_matches(
        profile=profile,
        study_id=study_id,
        batch=batch,
        handoff=handoff,
    ):
        return None
    raw_owner_route = _mapping(handoff.get("owner_route"))
    if default_executor_execution_receipt_consumption(
        study_root=profile.studies_root / study_id,
        owner_route=raw_owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    ):
        return None
    owner_route = owner_route_part.ensure_owner_route_v2(raw_owner_route)
    request = quality_repair_writer_handoff.owner_request_from_handoff(handoff)
    source_action = _mapping(handoff.get("source_action"))
    prompt_contract = _mapping(handoff.get("prompt_contract"))
    next_work_unit = (
        prompt_contract.get("next_work_unit")
        or source_action.get("next_work_unit")
        or _mapping(owner_route.get("source_refs")).get("work_unit_id")
    )
    return {
        "study_id": study_id,
        "quest_id": _text(handoff.get("quest_id")) or _text(batch.get("quest_id")) or study_id,
        "action_type": "run_quality_repair_batch",
        "action_id": _text(handoff.get("action_id")),
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": _text(source_action.get("blocked_reason"))
        or _text(owner_route.get("owner_reason"))
        or "manuscript_story_surface_delta_missing",
        "required_output_surface": _text(handoff.get("required_output_surface"))
        or _text(prompt_contract.get("required_output_surface"))
        or request_output_surface_for_action_type("run_quality_repair_batch"),
        "next_work_unit": next_work_unit,
        "source_eval_id": _current_quality_repair_writer_handoff_eval_id(batch=batch, handoff=handoff),
        "owner_route": owner_route,
        "writer_worker_handoff": dict(handoff),
        "handoff_packet": request,
    }


def _current_quality_repair_writer_handoff_matches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    batch: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    if _text(handoff.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if _text(handoff.get("dispatch_status")) != "ready":
        return False
    if _text(handoff.get("study_id")) != study_id:
        return False
    if _text(handoff.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(handoff.get("next_executable_owner")) != "write":
        return False
    source_action = _mapping(handoff.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return False
    if _text(source_action.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return False
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(handoff.get("owner_route")))
    if _text(owner_route.get("next_owner")) != "write":
        return False
    route_reason = _text(owner_route.get("owner_reason")) or _text(owner_route.get("failure_signature"))
    if route_reason != "manuscript_story_surface_delta_missing":
        return False
    if not owner_route_part.route_allows_action(action=handoff, owner_route=owner_route):
        return False
    eval_id = _current_quality_repair_writer_handoff_eval_id(batch=batch, handoff=handoff)
    if eval_id is None:
        return False
    publication_eval = _read_json_object(profile.studies_root / study_id / "artifacts" / "publication_eval" / "latest.json")
    current_eval_id = _text(_mapping(publication_eval).get("eval_id"))
    return current_eval_id is None or current_eval_id == eval_id


def _current_quality_repair_writer_handoff_eval_id(
    *,
    batch: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> str | None:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(handoff.get("owner_route")))
    source_refs = _mapping(owner_route.get("source_refs"))
    source_action = _mapping(handoff.get("source_action"))
    prompt_contract = _mapping(handoff.get("prompt_contract"))
    prompt_basis = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    return (
        _text(batch.get("source_eval_id"))
        or _text(source_action.get("source_eval_id"))
        or _text(source_refs.get("source_eval_id"))
        or _text(prompt_basis.get("source_eval_id"))
        or _text(handoff.get("source_eval_id"))
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["current_quality_repair_writer_handoff_action"]
