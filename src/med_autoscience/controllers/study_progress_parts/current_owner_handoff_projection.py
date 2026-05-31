from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared import _mapping_copy, _non_empty_text, _paper_stage_label, _timestamp_is_newer


def current_owner_handoff_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    if _handoff_superseded_by_domain_truth(payload, handoff):
        return None
    for item in handoff.get("action_queue") or []:
        action = _mapping_copy(item)
        if not action:
            continue
        status = _non_empty_text(action.get("status"))
        if status not in {None, "queued", "pending", "unconsumed"}:
            continue
        owner = _non_empty_text(action.get("owner"))
        action_type = _non_empty_text(action.get("action_type"))
        if owner is None and action_type is None:
            continue
        return {
            "owner": owner,
            "action_type": action_type,
            "status": status,
            "blocked_reason": _non_empty_text(handoff.get("blocked_reason")),
            "summary": _non_empty_text(action.get("summary")),
            "route_target": _non_empty_text(action.get("route_target")),
            "next_work_units": _next_work_units(payload=payload, action=action),
            "evidence_refs": _evidence_refs(payload=payload, action=action),
            "expected_repair_result": _expected_repair_result(payload=payload, action=action),
            "progress_delta_classification": None,
            "source": "opl_current_control_state.action_queue",
        }
    explicit_owner = _non_empty_text(handoff.get("next_owner"))
    explicit_blocker = _non_empty_text(handoff.get("blocked_reason"))
    if explicit_owner is not None:
        return {
            "owner": explicit_owner,
            "action_type": _external_supervisor_action(handoff)
            if bool(handoff.get("external_supervisor_required"))
            else None,
            "status": _non_empty_text(handoff.get("quest_status")),
            "blocked_reason": explicit_blocker,
            "summary": None,
            "route_target": _non_empty_text(handoff.get("route_target")),
            "next_work_units": _next_work_units(payload=payload, action=handoff),
            "evidence_refs": _evidence_refs(payload=payload, action=handoff),
            "expected_repair_result": _expected_repair_result(payload=payload, action=handoff),
            "progress_delta_classification": None,
            "source": "opl_current_control_state.next_owner",
        }
    terminal_log = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    paper_log = _mapping_copy(terminal_log.get("paper_stage_log"))
    owner = _non_empty_text(paper_log.get("current_owner"))
    action_type = _non_empty_text(terminal_log.get("action_type"))
    if owner is None and action_type is None:
        return None
    return {
        "owner": owner,
        "action_type": action_type,
        "status": _non_empty_text(terminal_log.get("status")),
        "blocked_reason": _non_empty_text(handoff.get("blocked_reason"))
        or _handoff_remaining_blocker_for_current_route(payload, paper_log),
        "summary": _non_empty_text(paper_log.get("problem_summary")),
        "route_target": _non_empty_text(paper_log.get("route_target")),
        "next_work_units": _next_work_units(payload=payload, action=terminal_log, paper_log=paper_log),
        "evidence_refs": _evidence_refs(payload=payload, action=terminal_log, paper_log=paper_log),
        "expected_repair_result": _expected_repair_result(payload=payload, action=terminal_log, paper_log=paper_log),
        "progress_delta_classification": _non_empty_text(paper_log.get("progress_delta_classification")),
        "deliverable_progress_delta": _mapping_copy(paper_log.get("deliverable_progress_delta")),
        "paper_progress_delta": _mapping_copy(paper_log.get("paper_progress_delta")),
        "platform_repair_delta": _mapping_copy(paper_log.get("platform_repair_delta")),
        "changed_paper_surfaces": _string_items(paper_log.get("changed_paper_surfaces")),
        "changed_stage_surfaces": _string_items(paper_log.get("changed_stage_surfaces")),
        "source": "opl_current_control_state.latest_terminal_stage_log",
    }


def _first_remaining_blocker(value: object) -> str | None:
    if isinstance(value, str):
        return _non_empty_text(value)
    if isinstance(value, Mapping):
        for key in ("blocked_reason", "reason", "typed_blocker", "blocker_id"):
            if text := _non_empty_text(value.get(key)):
                return text
    if not isinstance(value, (list, tuple)):
        return None
    for item in value:
        if isinstance(item, Mapping):
            if text := _first_remaining_blocker(item):
                return text
            continue
        if text := _non_empty_text(item):
            return text
    return None


def _handoff_remaining_blocker_for_current_route(
    payload: Mapping[str, Any],
    paper_log: Mapping[str, Any],
) -> str | None:
    remaining_blockers = paper_log.get("remaining_blockers")
    if isinstance(remaining_blockers, Mapping) and not current_owner_redrive_domain_transition(payload):
        return None
    return _first_remaining_blocker(remaining_blockers)


def _next_work_units(
    *,
    payload: Mapping[str, Any],
    action: Mapping[str, Any],
    paper_log: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    work_units: list[dict[str, Any]] = []
    for value in (
        action.get("next_work_units"),
        action.get("next_work_unit"),
        _mapping_copy(paper_log).get("next_work_units"),
        _mapping_copy(paper_log).get("next_work_unit"),
        _mapping_copy(payload.get("domain_transition")).get("next_work_units"),
        _mapping_copy(payload.get("domain_transition")).get("next_work_unit"),
        _mapping_copy(_mapping_copy(payload.get("study_macro_state")).get("details")).get("next_work_unit"),
    ):
        work_units.extend(_work_unit_items(value))
    return _dedupe_work_units(work_units)


def _work_unit_items(value: object) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        unit_id = _non_empty_text(value.get("unit_id")) or _non_empty_text(value.get("work_unit_id"))
        if unit_id is None:
            return []
        result = {"unit_id": unit_id}
        if summary := _non_empty_text(value.get("summary")):
            result["summary"] = summary
        if required_output := _non_empty_text(value.get("required_output_surface")):
            result["required_output_surface"] = required_output
        return [result]
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [{"unit_id": text}] if text is not None else []
    if not isinstance(value, (list, tuple)):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        result.extend(_work_unit_items(item))
    return result


def _dedupe_work_units(work_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in work_units:
        unit_id = _non_empty_text(item.get("unit_id"))
        if unit_id is None or unit_id in seen:
            continue
        seen.add(unit_id)
        result.append(item)
    return result


def _evidence_refs(
    *,
    payload: Mapping[str, Any],
    action: Mapping[str, Any],
    paper_log: Mapping[str, Any] | None = None,
) -> list[str]:
    refs: list[str] = []
    for value in (
        action.get("evidence_refs"),
        action.get("source_refs"),
        _mapping_copy(paper_log).get("evidence_refs"),
        _mapping_copy(payload.get("domain_transition")).get("evidence_refs"),
        _mapping_copy(payload.get("domain_transition")).get("source_refs"),
        payload.get("evidence_refs"),
    ):
        refs.extend(_ref_items(value))
    return list(dict.fromkeys(refs))


def _ref_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_ref_items(item))
        return result
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        result.extend(_ref_items(item))
    return result


def _expected_repair_result(
    *,
    payload: Mapping[str, Any],
    action: Mapping[str, Any],
    paper_log: Mapping[str, Any] | None = None,
) -> str | None:
    for value in (
        action.get("expected_repair_result"),
        action.get("acceptance_criteria"),
        _mapping_copy(paper_log).get("expected_repair_result"),
        _mapping_copy(payload.get("domain_transition")).get("expected_repair_result"),
    ):
        if text := _non_empty_text(value):
            return text
    return None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple)):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]


def _external_supervisor_action(handoff: Mapping[str, Any]) -> str:
    for item in handoff.get("why_not_applied") or []:
        if _non_empty_text(item) == "quest_waiting_opl_runtime_owner_route":
            return "request_opl_handoff_hydration"
    return "supervise_opl_runtime_owner_route"


def _handoff_superseded_by_domain_truth(payload: Mapping[str, Any], handoff: Mapping[str, Any]) -> bool:
    handoff_timestamp = (
        _non_empty_text(handoff.get("generated_at"))
        or _non_empty_text(handoff.get("updated_at"))
        or _non_empty_text(handoff.get("emitted_at"))
        or _non_empty_text(handoff.get("recorded_at"))
    )
    if handoff_timestamp is None:
        return False
    for item in payload.get("latest_events") or []:
        event = _mapping_copy(item)
        category = _non_empty_text(event.get("category"))
        source = _non_empty_text(event.get("source"))
        if category not in {"controller_decision", "publication_eval"} and source not in {
            "controller_decision",
            "publication_eval",
        }:
            continue
        event_timestamp = _non_empty_text(event.get("timestamp"))
        if _timestamp_is_newer(event_timestamp, handoff_timestamp):
            return True
    return False


def current_owner_handoff_next_action(
    payload: Mapping[str, Any],
    *,
    user_visible: Mapping[str, Any],
) -> str | None:
    handoff_action = current_owner_handoff_action(payload)
    if handoff_action is not None:
        if summary := current_owner_handoff_summary(handoff_action):
            return summary
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    transition = _mapping_copy(payload.get("domain_transition"))
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    route_target = _non_empty_text(transition.get("route_target")) or _non_empty_text(intervention_lane.get("route_target"))
    owner = _non_empty_text(transition.get("owner")) or route_target
    if route_summary := (
        _non_empty_text(intervention_lane.get("route_summary"))
        or _non_empty_text(intervention_lane.get("summary"))
    ):
        return route_summary
    if work_unit_id is not None:
        owner_text = f"{owner} owner" if owner is not None else "当前 owner"
        return f"等待 {owner_text} 处理 work unit {work_unit_id}。"
    return _non_empty_text(user_visible.get("next_system_action")) or _non_empty_text(user_visible.get("next_step"))


def apply_current_owner_handoff_user_visible_status(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not current_owner_redrive_domain_transition(payload):
        return dict(payload)
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    handoff_action = current_owner_handoff_action(payload)
    next_step = current_owner_handoff_next_action(payload, user_visible=user_visible)
    if next_step is None:
        return dict(payload)
    updated = dict(payload)
    updated["next_system_action"] = next_step
    route_back_checklist = current_owner_route_back_checklist(updated, handoff_action=handoff_action)
    if route_back_checklist is not None:
        updated["route_back_checklist"] = route_back_checklist
    if user_visible:
        user_visible["next_system_action"] = next_step
        user_visible["next_step"] = next_step
        if handoff_action is not None and (owner := _non_empty_text(handoff_action.get("owner"))) is not None:
            user_visible["next_owner"] = owner
        if route_back_checklist is not None:
            user_visible["route_back_checklist"] = route_back_checklist
        updated["user_visible_projection"] = user_visible
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        status_contract["next_step"] = next_step
        updated["status_narration_contract"] = status_contract
    operator_status = _mapping_copy(updated.get("operator_status_card"))
    if operator_status:
        operator_status["current_focus"] = next_step
        updated["operator_status_card"] = operator_status
    if lane := apply_current_owner_handoff_intervention_lane(
        updated,
        next_step=next_step,
        handoff_action=handoff_action,
    ):
        updated["intervention_lane"] = lane
        for key in ("operator_verdict", "recovery_contract"):
            surface = _mapping_copy(updated.get(key))
            if surface:
                surface["summary"] = next_step
                if "reason_summary" in surface:
                    surface["reason_summary"] = next_step
                for lane_key in (
                    "route_target",
                    "route_target_label",
                    "route_key_question",
                    "recommended_action_id",
                    "handoff_source",
                ):
                    if lane.get(lane_key) not in (None, "", [], {}):
                        surface[lane_key] = lane[lane_key]
                updated[key] = surface
        autonomy_contract = _mapping_copy(updated.get("autonomy_contract"))
        if autonomy_contract:
            autonomy_contract["next_signal"] = next_step
            updated["autonomy_contract"] = autonomy_contract
    return updated


def current_owner_handoff_summary(action: Mapping[str, Any]) -> str | None:
    owner = _non_empty_text(action.get("owner"))
    action_type = _non_empty_text(action.get("action_type"))
    blocked_reason = _non_empty_text(action.get("blocked_reason"))
    if owner is None and action_type is None:
        return _non_empty_text(action.get("summary"))
    owner_text = f"{owner} owner" if owner is not None else "当前 owner"
    action_text = f"执行 {action_type}" if action_type is not None else "处理当前 handoff"
    if blocked_reason is not None:
        return f"等待 {owner_text} {action_text}，关闭 {blocked_reason} 或产出 typed blocker。"
    return f"等待 {owner_text} {action_text}，产出 owner receipt、typed blocker 或下一 owner handoff。"


def apply_current_owner_handoff_intervention_lane(
    payload: Mapping[str, Any],
    *,
    next_step: str,
    handoff_action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if handoff_action is None:
        return None
    existing = _mapping_copy(payload.get("intervention_lane"))
    owner = _non_empty_text(handoff_action.get("owner"))
    action_type = _non_empty_text(handoff_action.get("action_type"))
    blocked_reason = _non_empty_text(handoff_action.get("blocked_reason"))
    if owner is None and action_type is None:
        return None
    route_target = owner or _non_empty_text(existing.get("route_target"))
    lane = {
        **existing,
        "lane_id": _non_empty_text(existing.get("lane_id")) or "current_owner_handoff",
        "title": _non_empty_text(existing.get("title")) or "当前 owner handoff",
        "summary": next_step,
        "recommended_action_id": action_type or _non_empty_text(existing.get("recommended_action_id")) or "inspect_progress",
        "route_target": route_target,
        "route_target_label": _paper_stage_label(route_target) or route_target,
        "route_key_question": blocked_reason or action_type or _non_empty_text(existing.get("route_key_question")),
        "handoff_source": _non_empty_text(handoff_action.get("source")),
    }
    if checklist := current_owner_route_back_checklist(payload, handoff_action=handoff_action):
        lane["route_back_checklist"] = checklist
    return lane


def current_owner_route_back_checklist(
    payload: Mapping[str, Any],
    *,
    handoff_action: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    decision_type = _non_empty_text(transition.get("decision_type"))
    if decision_type not in {"route_back_same_line", "ai_reviewer_re_eval", "publication_gate_blocker"}:
        return None
    action = _mapping_copy(handoff_action)
    blockers = [
        item
        for item in (
            _non_empty_text(action.get("blocked_reason")),
            _handoff_remaining_blocker_for_current_route(
                payload,
                _mapping_copy(
                    _mapping_copy(
                        _mapping_copy(payload.get("opl_current_control_state_handoff")).get(
                            "latest_terminal_stage_log"
                        )
                    ).get("paper_stage_log")
                ),
            ),
            _non_empty_text(transition.get("blocked_reason")),
            _non_empty_text(transition.get("reason")),
        )
        if item is not None
    ]
    route_target = (
        _non_empty_text(action.get("route_target"))
        or _non_empty_text(action.get("owner"))
        or _non_empty_text(transition.get("route_target"))
        or _non_empty_text(transition.get("owner"))
    )
    owner = _non_empty_text(action.get("owner")) or _non_empty_text(transition.get("owner")) or route_target
    next_work_units = list(action.get("next_work_units") or [])
    if not next_work_units:
        next_work_units = _next_work_units(payload=payload, action=transition)
    evidence_refs = list(action.get("evidence_refs") or [])
    if not evidence_refs:
        evidence_refs = _evidence_refs(payload=payload, action=transition)
    expected_repair_result = _non_empty_text(action.get("expected_repair_result")) or _expected_repair_result(
        payload=payload,
        action=transition,
    )
    checklist = {
        "surface_kind": "publication_route_back_checklist",
        "schema_version": 1,
        "route_back_required": True,
        "decision_type": decision_type,
        "blockers": list(dict.fromkeys(blockers)),
        "route_target": route_target,
        "owner": owner,
        "next_work_units": next_work_units,
        "evidence_refs": evidence_refs,
        "expected_repair_result": expected_repair_result,
        "handoff_source": _non_empty_text(action.get("source")),
        "progress_delta_classification": _non_empty_text(action.get("progress_delta_classification")),
        "changed_paper_surfaces": _string_items(action.get("changed_paper_surfaces")),
        "changed_stage_surfaces": _string_items(action.get("changed_stage_surfaces")),
    }
    if action.get("deliverable_progress_delta"):
        checklist["deliverable_progress_delta"] = _mapping_copy(action.get("deliverable_progress_delta"))
    if action.get("paper_progress_delta"):
        checklist["paper_progress_delta"] = _mapping_copy(action.get("paper_progress_delta"))
    if action.get("platform_repair_delta"):
        checklist["platform_repair_delta"] = _mapping_copy(action.get("platform_repair_delta"))
    return checklist


def current_owner_redrive_domain_transition(payload: Mapping[str, Any]) -> bool:
    transition = _mapping_copy(payload.get("domain_transition"))
    return _non_empty_text(transition.get("decision_type")) in {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
        "route_back_same_line",
    }


__all__ = [
    "apply_current_owner_handoff_user_visible_status",
    "apply_current_owner_handoff_intervention_lane",
    "current_owner_handoff_action",
    "current_owner_handoff_next_action",
    "current_owner_route_back_checklist",
    "current_owner_handoff_summary",
    "current_owner_redrive_domain_transition",
]
