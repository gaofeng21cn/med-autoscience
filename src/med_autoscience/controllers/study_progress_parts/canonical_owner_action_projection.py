from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SURFACE_KIND = "current_executable_owner_action"
CANONICAL_OWNER_ACTION_AUTHORITY = "study_progress.canonical_owner_action_projection"


def build_canonical_owner_action_projection(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    next_action = _mapping(payload.get("next_action"))
    if _non_empty_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return None
    action_family = _non_empty_text(next_action.get("action_family"))
    if action_family not in {"blocked.typed", "paper.package.submission_minimal"}:
        return None
    if submission_authority_owner_gate_readback(payload, next_action=next_action):
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
    paper_facing_delta = _mapping(next_action.get("paper_facing_delta"))
    accepted_answer_shape = _mapping(next_action.get("accepted_answer_shape"))
    route_back = _mapping(next_action.get("route_back"))
    verification = _mapping(next_action.get("verification"))
    executable_owner_route = _mapping(next_action.get("executable_owner_route"))
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
            "paper_facing_delta": paper_facing_delta,
            "accepted_answer_shape": accepted_answer_shape,
            "route_back": route_back,
            "verification": verification,
            "executable_owner_route": executable_owner_route,
            "owner_receipt_required": True,
            "authority": CANONICAL_OWNER_ACTION_AUTHORITY,
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


def is_canonical_owner_action_projection(action: Mapping[str, Any]) -> bool:
    return _non_empty_text(_mapping(action).get("authority")) == CANONICAL_OWNER_ACTION_AUTHORITY


def owner_action_next_step(action: Mapping[str, Any]) -> str | None:
    route = _mapping(action.get("executable_owner_route"))
    answer_shape = _mapping(action.get("accepted_answer_shape")) or _mapping(
        route.get("accepted_answer_shape")
    )
    paper_delta = _mapping(action.get("paper_facing_delta")) or _mapping(
        route.get("paper_facing_delta")
    )
    owner = _non_empty_text(action.get("next_owner"))
    actions = _text_items(action.get("allowed_actions"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    if owner is None and not actions and work_unit_id is None:
        return None
    owner_text = f"{owner} owner" if owner is not None else "当前 owner"
    action_text = f"执行 {actions[0]}" if actions else "处理当前 owner action"
    work_unit_text = f"，处理 work unit {work_unit_id}" if work_unit_id is not None else ""
    delta_kind = _non_empty_text(paper_delta.get("delta_kind"))
    shape_kind = _non_empty_text(answer_shape.get("shape_kind"))
    detail_parts = []
    if delta_kind is not None:
        detail_parts.append(f"paper-facing delta={delta_kind}")
    if shape_kind is not None:
        detail_parts.append(f"accepted answer={shape_kind}")
    detail = f"，{'; '.join(detail_parts)}" if detail_parts else ""
    return f"等待 {owner_text} {action_text}{work_unit_text}{detail}，route-back 到 paper-mission inspect 验证。"


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


def submission_authority_owner_gate_readback(
    payload: Mapping[str, Any],
    *,
    next_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    if closeout_readback := _latest_submission_authority_closeout_readback(payload):
        return closeout_readback
    action_type = _non_empty_text(next_action.get("action_type")) or _first_text(
        next_action.get("allowed_actions")
    )
    if action_type not in {
        "materialize_submission_ready_owner_verdict_or_human_gate",
        "await_human_or_mas_authority_decision_for_submission_blocker",
    }:
        return None
    expected = {
        "study_id": _non_empty_text(next_action.get("study_id"))
        or _non_empty_text(payload.get("study_id")),
        "action_type": action_type,
        "work_unit_id": _non_empty_text(next_action.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(next_action.get("work_unit_fingerprint"))
        or _non_empty_text(next_action.get("semantic_progress_signature"))
        or _non_empty_text(next_action.get("action_id")),
    }
    if any(value is None for value in expected.values()):
        return None
    for event in _owner_gate_decision_events(payload):
        event_payload = _mapping(event.get("payload"))
        if _non_empty_text(event_payload.get("owner_gate_kind")) != "submission_authority_gate":
            continue
        closeout = _mapping(event_payload.get("submission_authority_closeout"))
        if _non_empty_text(closeout.get("status")) != "owner_gate_recorded":
            continue
        if _non_empty_text(event_payload.get("human_gate_ref")) is None:
            continue
        identity = _mapping(event_payload.get("current_owner_identity"))
        if all(_non_empty_text(identity.get(field)) == value for field, value in expected.items()):
            if closeout_readback := _submission_authority_closeout_readback(
                payload,
                owner_gate_decision_ref=_non_empty_text(
                    event_payload.get("owner_gate_decision_ref")
                ),
                base_event=event,
                base_payload=event_payload,
            ):
                return closeout_readback
            closeout = _mapping(event_payload.get("submission_authority_closeout"))
            return _compact(
                {
                    "surface_kind": "submission_authority_owner_gate_readback",
                    "schema_version": 1,
                    "status": "owner_gate_recorded",
                    "study_id": expected["study_id"],
                    "decision": _non_empty_text(event_payload.get("decision")),
                    "current_required_action": _non_empty_text(
                        event_payload.get("current_required_action")
                    ),
                    "owner_gate_decision_ref": _non_empty_text(
                        event_payload.get("owner_gate_decision_ref")
                    ),
                    "human_gate_ref": _non_empty_text(event_payload.get("human_gate_ref")),
                    "event_id": _non_empty_text(event.get("event_id")),
                    "recorded_at": _non_empty_text(event.get("recorded_at")),
                    "source": _non_empty_text(event.get("source")),
                    "current_owner_identity": dict(identity),
                    "submission_authority_closeout": dict(closeout),
                    "authority_materialized": closeout.get("authority_materialized"),
                    "writes_owner_receipt": closeout.get("writes_owner_receipt"),
                    "writes_human_gate_authority": closeout.get("writes_human_gate_authority"),
                    "writes_current_package": closeout.get("writes_current_package"),
                    "writes_publication_eval": closeout.get("writes_publication_eval"),
                    "writes_controller_decision": closeout.get("writes_controller_decision"),
                    "next_legal_action": "await_submission_authority_or_human_gate_closeout",
                    "duplicate_owner_gate_action_retired": True,
                    "projection_only": True,
                }
            )
    return None


def _latest_submission_authority_closeout_readback(
    payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    for event in reversed(_submission_authority_closeout_events(payload)):
        event_payload = _mapping(event.get("payload"))
        return _submission_authority_closeout_readback(
            payload,
            owner_gate_decision_ref=_non_empty_text(event_payload.get("owner_gate_decision_ref")),
            base_event=event,
            base_payload=event_payload,
        )
    return None


def _submission_authority_closeout_readback(
    payload: Mapping[str, Any],
    *,
    owner_gate_decision_ref: str | None,
    base_event: Mapping[str, Any],
    base_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    for event in reversed(_submission_authority_closeout_events(payload)):
        event_payload = _mapping(event.get("payload"))
        if _non_empty_text(event_payload.get("owner_gate_decision_ref")) != owner_gate_decision_ref:
            continue
        closeout = _mapping(event_payload.get("submission_authority_closeout"))
        status = _non_empty_text(closeout.get("status"))
        if status not in {
            "submission_ready_authority_closeout_recorded",
            "submission_blocker_human_gate_recorded",
        }:
            continue
        identity = _mapping(event_payload.get("current_owner_identity")) or _mapping(
            base_payload.get("current_owner_identity")
        )
        return _compact(
            {
                "surface_kind": "submission_authority_owner_gate_readback",
                "schema_version": 1,
                "status": status,
                "study_id": _non_empty_text(event_payload.get("study_id"))
                or _non_empty_text(payload.get("study_id")),
                "decision": _non_empty_text(event_payload.get("decision")),
                "current_required_action": _non_empty_text(
                    event_payload.get("current_required_action")
                ),
                "owner_gate_decision_ref": owner_gate_decision_ref,
                "human_gate_ref": _non_empty_text(event_payload.get("human_gate_ref")),
                "event_id": _non_empty_text(event.get("event_id")),
                "recorded_at": _non_empty_text(event.get("recorded_at")),
                "source": _non_empty_text(event.get("source")),
                "current_owner_identity": dict(identity),
                "submission_authority_closeout": dict(closeout),
                "authority_materialized": closeout.get("authority_materialized"),
                "terminal_gate_materialized": closeout.get("terminal_gate_materialized"),
                "submission_ready_claim_authorized": closeout.get(
                    "submission_ready_claim_authorized"
                ),
                "human_gate_required": closeout.get("human_gate_required"),
                "writes_owner_receipt": closeout.get("writes_owner_receipt"),
                "writes_human_gate_authority": closeout.get("writes_human_gate_authority"),
                "writes_current_package": closeout.get("writes_current_package"),
                "writes_publication_eval": closeout.get("writes_publication_eval"),
                "writes_controller_decision": closeout.get("writes_controller_decision"),
                "next_legal_action": "submission_authority_or_human_gate_closed",
                "duplicate_owner_gate_action_retired": True,
                "closed_owner_gate_event_id": _non_empty_text(base_event.get("event_id")),
                "projection_only": False,
            }
        )
    return None


def _owner_gate_decision_events(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for key in ("study_intervention_events", "intervention_events"):
        for item in payload.get(key) or []:
            event = _mapping(item)
            if _non_empty_text(event.get("intent")) == "owner_gate_decision":
                events.append(event)
    return events


def _submission_authority_closeout_events(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for key in ("study_intervention_events", "intervention_events"):
        for item in payload.get(key) or []:
            event = _mapping(item)
            if _non_empty_text(event.get("intent")) == "submission_authority_closeout":
                events.append(event)
    return events


__all__ = [
    "CANONICAL_OWNER_ACTION_AUTHORITY",
    "SURFACE_KIND",
    "build_canonical_owner_action_projection",
    "is_canonical_owner_action_projection",
    "owner_action_next_step",
    "submission_authority_owner_gate_readback",
]
