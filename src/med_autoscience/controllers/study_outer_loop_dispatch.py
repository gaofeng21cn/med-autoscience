from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


_WORK_UNIT_CONTEXT_KEYS = (
    "specificity_targets",
    "work_unit_targets",
    "blocking_artifact_refs",
    "blocker_details",
    "gate_blocker_details",
    "gaps",
    "source_path",
)


def _work_unit_context(payload: Mapping[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    fingerprint = _non_empty_text(payload.get("work_unit_fingerprint"))
    next_work_unit = payload.get("next_work_unit")
    if fingerprint is not None and isinstance(next_work_unit, Mapping):
        context["work_unit_fingerprint"] = fingerprint
        context["next_work_unit"] = dict(next_work_unit)
    questions = payload.get("specificity_questions")
    if isinstance(questions, list):
        context["specificity_questions"] = [str(item) for item in questions if str(item).strip()]
    if currentness_basis := _non_empty_text(payload.get("currentness_basis")):
        context["currentness_basis"] = currentness_basis
    for key in _WORK_UNIT_CONTEXT_KEYS:
        value = payload.get(key)
        if value not in (None, "", [], {}):
            context[key] = value
    return context


def serialize_outer_loop_dispatch(
    *,
    tick_request: Mapping[str, Any],
    outer_loop_result: Mapping[str, Any],
) -> dict[str, Any]:
    controller_actions = tick_request.get("controller_actions")
    first_controller_action = (
        controller_actions[0]
        if isinstance(controller_actions, list) and controller_actions and isinstance(controller_actions[0], Mapping)
        else {}
    )
    payload = {
        "study_id": _non_empty_text(outer_loop_result.get("study_id")) or _non_empty_text(tick_request.get("study_id")),
        "quest_id": _non_empty_text(outer_loop_result.get("quest_id")) or _non_empty_text(tick_request.get("quest_id")),
        "decision_type": _non_empty_text(tick_request.get("decision_type")),
        "route_target": _non_empty_text(tick_request.get("route_target")),
        "route_key_question": _non_empty_text(tick_request.get("route_key_question")),
        "controller_action_type": _non_empty_text(first_controller_action.get("action_type")),
        "study_decision_ref": _non_empty_text(first_controller_action.get("payload_ref")),
        "dispatch_status": _non_empty_text(outer_loop_result.get("dispatch_status")),
        "source": _non_empty_text(outer_loop_result.get("source")) or _non_empty_text(tick_request.get("source")),
    }
    payload.update(_work_unit_context(tick_request))
    return payload


def _candidate_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser().resolve()


def attach_to_quest_report(
    *,
    quest_report: dict[str, Any],
    dispatch_payload: Mapping[str, Any],
    write_latest_watch_alias: Callable[..., tuple[Path, Path]],
    render_domain_diagnostic_report_markdown: Callable[[dict[str, Any]], str],
) -> None:
    report_dispatch = {
        "study_id": _non_empty_text(dispatch_payload.get("study_id")),
        "quest_id": _non_empty_text(dispatch_payload.get("quest_id")),
        "decision_type": _non_empty_text(dispatch_payload.get("decision_type")),
        "route_target": _non_empty_text(dispatch_payload.get("route_target")),
        "route_key_question": _non_empty_text(dispatch_payload.get("route_key_question")),
        "controller_action_type": _non_empty_text(dispatch_payload.get("controller_action_type")),
        "study_decision_ref": _non_empty_text(dispatch_payload.get("study_decision_ref")),
        "dispatch_status": _non_empty_text(dispatch_payload.get("dispatch_status")),
        "source": _non_empty_text(dispatch_payload.get("source")),
    }
    report_dispatch.update(_work_unit_context(dispatch_payload))
    quest_report["managed_study_outer_loop_dispatch"] = report_dispatch
    latest_report_path = _candidate_path(quest_report.get("latest_report_json")) or _candidate_path(
        quest_report.get("report_json")
    )
    if latest_report_path is None:
        return
    write_latest_watch_alias(
        report_dir=latest_report_path.parent,
        report=quest_report,
        markdown=render_domain_diagnostic_report_markdown(quest_report),
    )
