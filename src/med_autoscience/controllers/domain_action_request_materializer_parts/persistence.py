from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import default_executor_dispatch_packets
from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.runtime_protocol import domain_authority_refs_index


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def persist_default_executor_dispatches(
    *,
    profile: Any,
    dispatches: list[dict[str, Any]],
) -> list[str]:
    written_files: list[str] = []
    for dispatch in dispatches:
        dispatch_status = _text(dispatch.get("dispatch_status"))
        if dispatch_status != "ready" and not _should_persist_non_ready_dispatch(dispatch):
            continue
        dispatch_path = Path(_mapping(dispatch.get("refs")).get("dispatch_path"))
        if dispatch_status != "ready":
            write_json(dispatch_path, dispatch)
            written_files.append(str(dispatch_path))
            continue
        packet_dispatch = default_executor_dispatch_packets.dispatch_with_immutable_packet_ref(
            dispatch=dispatch,
            dispatch_path=dispatch_path,
        )
        dispatch.clear()
        dispatch.update(packet_dispatch)
        write_json(dispatch_path, dispatch)
        immutable_dispatch_path = default_executor_dispatch_packets.dispatch_stage_packet_path(
            dispatch,
            fallback_dispatch_path=dispatch_path,
        )
        if immutable_dispatch_path != dispatch_path:
            write_json(immutable_dispatch_path, dispatch)
        dispatch["dispatch_id"] = f"dispatch::{_text(dispatch.get('study_id'))}::{_text(dispatch.get('action_type'))}"
        quest_root = profile.runtime_root / (_text(dispatch.get("quest_id")) or _text(dispatch.get("study_id")) or "")
        dispatch["domain_authority_ref_index"] = domain_authority_refs_index.record_dispatch_receipt(
            quest_root=quest_root,
            receipt=dispatch,
            receipt_path=dispatch_path,
            db_path=domain_authority_refs_index.workspace_authority_refs_index_path(profile.workspace_root),
        )
        write_json(dispatch_path, dispatch)
        if immutable_dispatch_path != dispatch_path:
            write_json(immutable_dispatch_path, dispatch)
        written_files.append(str(dispatch_path))
        if immutable_dispatch_path != dispatch_path:
            written_files.append(str(immutable_dispatch_path))
    return written_files


def _should_persist_non_ready_dispatch(dispatch: Mapping[str, Any]) -> bool:
    if _text(dispatch.get("dispatch_authority")) != "ai_reviewer_record_production_handoff":
        return False
    if _text(dispatch.get("dispatch_status")) not in {"repeat_suppressed", "blocked"}:
        return False
    dispatch_path = _text(_mapping(dispatch.get("refs")).get("dispatch_path"))
    if dispatch_path is None:
        return False
    path = Path(dispatch_path).expanduser()
    if not path.is_file():
        return False
    existing = read_json_object(path)
    return _text(_mapping(existing).get("dispatch_status")) == "ready"


def persist_request_packets(request_tasks: list[dict[str, Any]]) -> list[str]:
    written_files: list[str] = []
    for task in request_tasks:
        if _text(task.get("dispatch_status")) != "applied":
            continue
        packet_path = Path(_mapping(task.get("refs")).get("request_packet_path"))
        packet = request_packet_for_persistence(task=task, packet_path=packet_path)
        write_json(packet_path, packet)
        written_files.append(str(packet_path))
    return written_files


def request_packet_for_persistence(
    *,
    task: Mapping[str, Any],
    packet_path: Path,
) -> dict[str, Any]:
    packet = _mapping(task.get("handoff_packet"))
    if _text(task.get("action_type")) == "complete_medical_paper_readiness_surface":
        return medical_paper_readiness_packet_for_persistence(packet=packet)
    if _text(task.get("action_type")) != "return_to_ai_reviewer_workflow":
        return packet
    action = _mapping(task.get("source_action"))
    lifecycle = dict(_mapping(packet.get("request_lifecycle")))
    reason = _text(action.get("reason")) or _text(packet.get("reason"))
    if reason:
        lifecycle["blocked_reason"] = reason
    if stale_record_ref := _text(action.get("stale_record_ref")):
        lifecycle["stale_record_ref"] = stale_record_ref
    required_refs = [ref for ref in action.get("required_currentness_refs") or [] if _text(ref)]
    if required_refs:
        lifecycle["required_currentness_refs"] = required_refs
    if source_ref := _text(action.get("source_ref")):
        lifecycle["source_ref"] = source_ref
    if lifecycle:
        packet["request_lifecycle"] = lifecycle
    source_workflow_ref = source_workflow_ref_for_ai_reviewer_request(
        action=action,
        packet=packet,
        existing_packet=read_json_object(packet_path),
    )
    if source_workflow_ref:
        packet["source_workflow_ref"] = source_workflow_ref
    try:
        study_root = packet_path.parents[4]
    except IndexError:
        return packet
    return domain_action_request_lifecycle.ai_reviewer_request_with_latest_record(
        study_root=study_root,
        packet=packet,
    )


def medical_paper_readiness_packet_for_persistence(*, packet: Mapping[str, Any]) -> dict[str, Any]:
    persisted = dict(packet)
    if persisted.get("operator_payload") is None:
        persisted.pop("operator_payload", None)
    if persisted.get("medical_paper_readiness_payload") is None:
        persisted.pop("medical_paper_readiness_payload", None)
    target = _mapping(persisted.get("payload_authoring_target"))
    if target:
        target = dict(target)
        if target.get("operator_payload") is None:
            target.pop("operator_payload", None)
        persisted["payload_authoring_target"] = target
    return persisted


def source_workflow_ref_for_ai_reviewer_request(
    *,
    action: Mapping[str, Any],
    packet: Mapping[str, Any],
    existing_packet: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source_handoff = _mapping(action.get("handoff_packet"))
    ref = {
        **_mapping(_mapping(existing_packet).get("source_workflow_ref")),
        **_mapping(source_handoff.get("source_workflow_ref")),
        **_mapping(packet.get("source_workflow_ref")),
    }
    if next_work_unit := _text(action.get("next_work_unit")):
        ref["next_work_unit"] = next_work_unit
    if route_back_target := (
        _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(action.get("owner"))
        or _text(_mapping(action.get("owner_route")).get("next_owner"))
        or _text(packet.get("request_owner"))
    ):
        ref["route_back_target"] = route_back_target
    return ref


def persist_consumer_payload(
    *,
    latest_path: Path,
    history_path: Path,
    payload: Mapping[str, Any],
    generated_at: str,
    study_ids: tuple[str, ...],
    request_task_count: int,
    ai_reviewer_request_refresh_count: int,
    written_files: list[str],
    effective_mode: str,
) -> None:
    written_files.append(str(latest_path))
    write_json(latest_path, payload)
    append_json_line(
        history_path,
        {
            "generated_at": generated_at,
            "study_ids": list(study_ids),
            "request_task_count": request_task_count,
            "ai_reviewer_request_refresh_count": ai_reviewer_request_refresh_count,
            "written_files": list(written_files),
            "effective_mode": effective_mode,
        },
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
