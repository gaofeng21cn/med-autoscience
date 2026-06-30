from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SURFACE_KIND = "current_executable_owner_action"


def build_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    next_action = _mapping(payload.get("next_action"))
    if _non_empty_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return None
    action_family = _non_empty_text(next_action.get("action_family"))
    if action_family not in {"blocked.typed", "paper.package.submission_minimal"}:
        return None
    study_id = _non_empty_text(next_action.get("study_id")) or _non_empty_text(
        payload.get("study_id")
    )
    work_unit_id = (
        _non_empty_text(next_action.get("work_unit_id"))
        or "paper_mission_typed_blocker_resolution"
    )
    fingerprint = (
        _non_empty_text(next_action.get("work_unit_fingerprint"))
        or _non_empty_text(next_action.get("semantic_progress_signature"))
        or _non_empty_text(next_action.get("action_id"))
    )
    source_ref = _non_empty_text(next_action.get("outcome_ref")) or _first_ref(
        next_action.get("diagnostic_refs")
    )
    blocked_typed = action_family == "blocked.typed"
    action_type = (
        "materialize_typed_blocker_or_route_redesign"
        if blocked_typed
        else (
            _non_empty_text(next_action.get("action_type"))
            or _first_text(next_action.get("allowed_actions"))
            or "consume_submission_package_successor_owner_action"
        )
    )
    allowed_actions = (
        [action_type]
        if blocked_typed
        else (_text_items(next_action.get("allowed_actions")) or [action_type])
    )
    next_owner = (
        "mas_authority_kernel"
        if blocked_typed
        else (
            _non_empty_text(next_action.get("owner"))
            or _non_empty_text(next_action.get("next_owner"))
            or "mas_authority_kernel"
        )
    )
    target_surface = (
        {
            "ref_kind": "mas_study_owner_gate_decision",
            "surface_ref": "study-owner-gate-decision",
            **({"source_ref": source_ref} if source_ref is not None else {}),
        }
        if not blocked_typed
        and action_type
        in {
            "materialize_submission_ready_owner_verdict_or_human_gate",
            "await_human_or_mas_authority_decision_for_submission_blocker",
        }
        else {
            "ref_kind": "mas_ops_resolution_packet",
            "surface_ref": "ops/medautoscience/paper_mission_typed_blocker_resolution",
            **({"source_ref": source_ref} if source_ref is not None else {}),
        }
    )
    target_surface_specificity = (
        "submission_authority_owner_gate_decision"
        if target_surface["ref_kind"] == "mas_study_owner_gate_decision"
        else "typed_blocker_resolution"
    )
    required_delta_kind = (
        "submission_authority_owner_gate_decision"
        if target_surface["ref_kind"] == "mas_study_owner_gate_decision"
        else "typed_blocker_resolution_owner_action"
    )
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": (
                "paper_mission.next_action.blocked_typed"
                if blocked_typed
                else "paper_mission.next_action.owner_successor"
            ),
            "source_ref": source_ref,
            "study_id": study_id,
            "next_owner": next_owner,
            "owner": next_owner,
            "action_type": action_type,
            "allowed_actions": allowed_actions,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "required_delta_kind": required_delta_kind,
            "target_surface": target_surface,
            "target_surface_specificity": target_surface_specificity,
            "acceptance_refs": [
                ref
                for ref in (
                    source_ref,
                    (
                        "study_owner_gate_decision_ref"
                        if target_surface["ref_kind"] == "mas_study_owner_gate_decision"
                        else "typed_blocker_resolution_packet_ref"
                    ),
                )
                if ref is not None
            ],
            "owner_receipt_required": True,
            "authority": "study_progress.current_executable_owner_action",
            "authority_boundary": {
                "projection_only": True,
                "can_write_owner_receipt": False,
                "can_write_typed_blocker": False,
                "can_write_human_gate": False,
                "can_write_current_package": False,
                "can_start_provider_attempt": False,
            },
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


def _non_empty_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_ref(value: object) -> str | None:
    if not isinstance(value, list):
        return None
    for item in value:
        payload = _mapping(item)
        text = _non_empty_text(payload.get("ref"))
        if text is not None:
            return text
    return None


def _first_text(value: object) -> str | None:
    for item in _text_items(value):
        return item
    return None


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, [], {})}


__all__ = [
    "SURFACE_KIND",
    "build_current_executable_owner_action",
    "owner_action_next_step",
]
