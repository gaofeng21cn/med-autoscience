from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.owner_route_handoff.export_study_projection import (
    mapping,
    read_json_object,
    text,
    workspace_relative,
)
from med_autoscience.profiles import WorkspaceProfile


def is_generated_current_work_unit_stage_packet_ref(ref: str | None) -> bool:
    return bool(ref and ref.startswith("mas://current-work-unit/") and ref.endswith("/stage-packet"))


def current_control_action_stage_packet_refs(action: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = mapping(action.get("source_refs"))
    owner_route_refs = mapping(mapping(action.get("owner_route")).get("source_refs"))
    handoff_packet = mapping(action.get("handoff_packet"))
    handoff_refs = mapping(handoff_packet.get("source_refs"))
    current_control_action = mapping(action.get("current_control_action"))
    current_control_refs = mapping(current_control_action.get("source_refs"))
    stage_packet_ref = _first_text_value(
        action.get("stage_packet_ref"),
        source_refs.get("stage_packet_ref"),
        owner_route_refs.get("stage_packet_ref"),
        handoff_packet.get("stage_packet_ref"),
        handoff_refs.get("stage_packet_ref"),
        current_control_action.get("stage_packet_ref"),
        current_control_refs.get("stage_packet_ref"),
    )
    stage_packet_refs = _dedupe_text_items(
        action.get("stage_packet_refs"),
        source_refs.get("stage_packet_refs"),
        owner_route_refs.get("stage_packet_refs"),
        handoff_packet.get("stage_packet_refs"),
        handoff_refs.get("stage_packet_refs"),
        current_control_action.get("stage_packet_refs"),
        current_control_refs.get("stage_packet_refs"),
    )
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = _dedupe_text_items(
        action.get("checkpoint_refs"),
        source_refs.get("checkpoint_refs"),
        owner_route_refs.get("checkpoint_refs"),
        handoff_packet.get("checkpoint_refs"),
        handoff_refs.get("checkpoint_refs"),
        current_control_action.get("checkpoint_refs"),
        current_control_refs.get("checkpoint_refs"),
    ) or list(stage_packet_refs)
    return {
        key: value
        for key, value in {
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": stage_packet_refs,
            "checkpoint_refs": checkpoint_refs,
        }.items()
        if value not in (None, "", [], {})
    }


def current_control_transition_dispatch_refs(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str | None,
    explicit_dispatch_ref: str | None,
) -> dict[str, Any]:
    if action_type is None:
        return {}
    dispatch_path = current_control_transition_dispatch_path(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        explicit_dispatch_ref=explicit_dispatch_ref,
    )
    dispatch = read_json_object(dispatch_path)
    if not dispatch or text(dispatch.get("action_type")) != action_type:
        return {}
    stage_packet_refs = current_control_action_stage_packet_refs(dispatch)
    if not stage_packet_refs:
        return {}
    dispatch_ref = workspace_relative(dispatch_path, workspace_root=profile.workspace_root)
    return {
        "dispatch_ref": dispatch_ref,
        **stage_packet_refs,
    }


def current_control_transition_dispatch_path(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    explicit_dispatch_ref: str | None,
) -> Path:
    ref = text(explicit_dispatch_ref)
    if ref is not None:
        path = Path(ref).expanduser()
        if path.is_absolute():
            return path
        workspace_path = profile.workspace_root / path
        if workspace_path.is_file():
            return workspace_path
    return (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / f"{action_type}.json"
    )


def _first_text_value(*values: object) -> str | None:
    for value in values:
        result = text(value)
        if result is not None:
            return result
    return None


def _dedupe_text_items(*values: object) -> list[str]:
    refs: list[str] = []
    for value in values:
        if isinstance(value, str):
            text_value = text(value)
            if text_value is not None and text_value not in refs:
                refs.append(text_value)
            continue
        if not isinstance(value, list | tuple | set):
            continue
        for item in value:
            text_value = text(item)
            if text_value is not None and text_value not in refs:
                refs.append(text_value)
    return refs
