from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"


def can_preempt_scan(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any],
    readiness_followup: Mapping[str, Any] | None,
    stage_native_action: Mapping[str, Any] | None,
    top_level_study_actions: list[dict[str, Any]],
) -> bool:
    queue_actions = [_mapping(item) for item in study.get("action_queue") or [] if isinstance(item, Mapping)]
    if not queue_actions:
        queue_actions = list(top_level_study_actions)
    if not queue_actions:
        return True
    if _fresh_action_matches_scan_current_action(
        fresh_action=fresh_action,
        queue_actions=queue_actions,
    ):
        return True
    if _fresh_repair_followup_supersedes_previous_repair_queue(
        fresh_action=fresh_action,
        queue_actions=queue_actions,
    ):
        return True
    if any(not _scan_action_is_readiness_or_stage_native_write(action) for action in queue_actions):
        return False
    if readiness_followup is not None:
        return True
    if stage_native_action is not None:
        return True
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    owner_reason = _text(owner_route.get("owner_reason")) or _text(owner_route.get("failure_signature"))
    if owner_reason == "medical_paper_readiness_missing":
        return True
    return _text(fresh_action.get("action_type")) != _text(queue_actions[0].get("action_type"))


def _fresh_action_matches_scan_current_action(
    *,
    fresh_action: Mapping[str, Any],
    queue_actions: list[dict[str, Any]],
) -> bool:
    fresh_action_type = _text(fresh_action.get("action_type"))
    if fresh_action_type is None:
        return False
    fresh_fingerprints = _action_currentness_fingerprints(fresh_action)
    if not fresh_fingerprints:
        return False
    for action in queue_actions:
        if _text(action.get("action_type")) != fresh_action_type:
            continue
        if fresh_fingerprints.intersection(_action_currentness_fingerprints(action)):
            return True
    return False


def _action_currentness_fingerprints(action: Mapping[str, Any]) -> set[str]:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(action.get("owner_route")))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    handoff_packet = _mapping(action.get("handoff_packet"))
    values = (
        action.get("work_unit_fingerprint"),
        action.get("action_fingerprint"),
        owner_route.get("work_unit_fingerprint"),
        owner_route.get("source_fingerprint"),
        source_refs.get("work_unit_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        handoff_packet.get("work_unit_fingerprint"),
        handoff_packet.get("action_fingerprint"),
    )
    return {text for value in values if (text := _text(value)) is not None}


def _fresh_repair_followup_supersedes_previous_repair_queue(
    *,
    fresh_action: Mapping[str, Any],
    queue_actions: list[dict[str, Any]],
) -> bool:
    if _text(fresh_action.get("current_action_source")) != (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    ):
        return False
    if _text(fresh_action.get("action_type")) not in {
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
    }:
        return False
    if not (
        _mapping(fresh_action.get("repair_progress_precedence"))
        or _text(fresh_action.get("source_ref")) is not None
    ):
        return False
    return any(_scan_action_is_previous_repair_or_provider_admission(action) for action in queue_actions)


def _scan_action_is_previous_repair_or_provider_admission(action: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type"))
    if action_type not in {"run_quality_repair_batch", "run_gate_clearing_batch"}:
        return False
    authority = _text(action.get("authority")) or _text(action.get("source_surface"))
    if authority in {
        "mas_provider_admission_identity",
        "stage_native_workspace_next_action",
        "control/next_action.json",
        "stage_artifact_index.next_owner_action",
    }:
        return True
    action_id = _text(action.get("action_id"))
    return bool(action_id and action_id.startswith("provider-admission::"))


def has_current_quality_repair_writer_handoff(
    *,
    profile: WorkspaceProfile | None,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any],
) -> bool:
    if profile is None:
        return False
    if _text(fresh_action.get("action_type")) != "run_quality_repair_batch":
        return False
    study_id = _text(study.get("study_id"))
    if study_id is None:
        return False
    fresh_owner_route = owner_route_part.ensure_owner_route_v2(_mapping(fresh_action.get("owner_route")))
    if _text(fresh_owner_route.get("next_owner")) != "write":
        return False
    if not _requires_manuscript_story_surface_delta(fresh_action.get("required_output_surface")):
        return False
    if not any(_scan_action_is_writer_story_surface_handoff(action) for action in study.get("action_queue") or []):
        return False
    if _owner_route_is_writer_story_surface_route(_mapping(study.get("owner_route"))):
        return True
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    request_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "requests"
        / "quality_repair_batch"
        / "latest.json"
    )
    dispatch = _read_json_mapping(dispatch_path)
    request = _read_json_mapping(request_path)
    if not _dispatch_is_quality_repair_writer_handoff(dispatch, study_id=study_id):
        return False
    if request is not None and not _request_is_quality_repair_writer_handoff(request):
        return False
    dispatch_route = owner_route_part.ensure_owner_route_v2(_mapping(dispatch.get("owner_route")))
    return owner_route_part.owner_route_matches(
        dispatch={"owner_route": dispatch_route},
        current_route=_mapping(study.get("owner_route")),
    ) or owner_route_part.owner_route_matches(
        dispatch={"owner_route": dispatch_route},
        current_route=fresh_owner_route,
    )


def _scan_action_is_readiness_or_stage_native_write(action: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type"))
    if action_type == READINESS_ACTION_TYPE:
        return True
    if action_type != "run_quality_repair_batch":
        return False
    source = _text(action.get("authority")) or _text(action.get("source_surface"))
    return source in {
        "stage_native_workspace_next_action",
        "control/next_action.json",
        "stage_artifact_index.next_owner_action",
    }


def _scan_action_is_writer_story_surface_handoff(action: object) -> bool:
    payload = _mapping(action)
    if _text(payload.get("action_type")) != "run_quality_repair_batch":
        return False
    owner = _text(payload.get("owner")) or _text(payload.get("request_owner")) or _text(payload.get("recommended_owner"))
    if owner != "write":
        return False
    reason = _text(payload.get("reason")) or _text(_mapping(payload.get("handoff_packet")).get("reason"))
    return reason in {"manuscript_story_surface_delta_missing", "quest_waiting_opl_runtime_owner_route"}


def _owner_route_is_writer_story_surface_route(owner_route: Mapping[str, Any]) -> bool:
    route = owner_route_part.ensure_owner_route_v2(owner_route)
    if _text(route.get("next_owner")) != "write":
        return False
    reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if reason not in {"manuscript_story_surface_delta_missing", "quest_waiting_opl_runtime_owner_route"}:
        return False
    return "run_quality_repair_batch" in {
        text for item in route.get("allowed_actions") or [] if (text := _text(item)) is not None
    }


def _dispatch_is_quality_repair_writer_handoff(
    dispatch: Mapping[str, Any] | None,
    *,
    study_id: str,
) -> bool:
    if not dispatch:
        return False
    if _text(dispatch.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if _text(dispatch.get("dispatch_status")) != "ready":
        return False
    if _text(dispatch.get("study_id")) != study_id:
        return False
    if _text(dispatch.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(dispatch.get("next_executable_owner")) != "write":
        return False
    if dispatch.get("medical_claim_authoring_allowed") is not True:
        return False
    source_action = _mapping(dispatch.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return False
    return _text(source_action.get("blocked_reason")) == "manuscript_story_surface_delta_missing"


def _request_is_quality_repair_writer_handoff(request: Mapping[str, Any]) -> bool:
    request_kind = _text(request.get("request_kind")) or _text(request.get("action_type"))
    if request_kind != "run_quality_repair_batch":
        return False
    if _text(request.get("dispatch_authority")) not in {None, "quality_repair_batch_writer_handoff"}:
        return False
    owner = (
        _text(request.get("request_owner"))
        or _text(request.get("expected_owner"))
        or _text(request.get("next_executable_owner"))
    )
    return owner in {None, "write"}


def _requires_manuscript_story_surface_delta(value: object) -> bool:
    text = str(value or "").strip().lower()
    return (
        "canonical manuscript story-surface delta" in text
        and "typed blocker:manuscript_story_surface_delta_missing" in text
    )


def _read_json_mapping(path: Path) -> dict[str, Any] | None:
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


__all__ = [
    "can_preempt_scan",
    "has_current_quality_repair_writer_handoff",
]
