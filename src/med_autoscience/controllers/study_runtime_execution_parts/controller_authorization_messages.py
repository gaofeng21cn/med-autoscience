from __future__ import annotations

import json
from typing import Any

from .controller_authorization_context import _WORK_UNIT_TARGET_CONTEXT_KEYS


def _controller_decision_authorization_message(*, authorization_context: dict[str, Any]) -> str:
    route_target = str(authorization_context.get("route_target") or "").strip()
    route_target_label = str(authorization_context.get("route_target_label") or route_target).strip()
    route_key_question = str(authorization_context.get("route_key_question") or "").strip()
    route_rationale = str(authorization_context.get("route_rationale") or "").strip()
    decision_id = str(authorization_context.get("decision_id") or "").strip()
    decision_path = str(authorization_context.get("decision_path") or "artifacts/controller_decisions/latest.json").strip()
    controller_actions = _controller_actions_markdown(authorization_context)
    work_unit_lines = _controller_work_unit_message_lines(authorization_context)
    return (
        "MAS controller authorization. "
        f"`{decision_path}` is the active MAS authorization for this runtime turn.\n\n"
        f"- decision_id: `{decision_id}`\n"
        f"- controller_actions: {controller_actions}\n"
        f"- route_target: `{route_target}` ({route_target_label})\n"
        f"- route_key_question: {route_key_question}\n"
        f"- route_rationale: {route_rationale}\n"
        f"{work_unit_lines}"
        "- requires_human_confirmation: false\n"
        "- Runtime instruction: do not park solely because `publication_eval/latest.json` still says "
        "`requires_controller_decision=true`; execute the authorized route_key_question / active_work_unit_id and write durable "
        "evidence, review, or route outputs. Only stop for a true external credential, human-only choice, "
        "or startup boundary."
    )


def _controller_actions_markdown(authorization_context: dict[str, Any]) -> str:
    return ", ".join(
        f"`{action}`"
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    )


def _controller_work_unit_message_lines(authorization_context: dict[str, Any]) -> str:
    source_route_key_question = str(authorization_context.get("source_route_key_question") or "").strip()
    route_key_question = str(authorization_context.get("route_key_question") or "").strip()
    work_unit_id = str(authorization_context.get("work_unit_id") or "").strip()
    work_unit_fingerprint = str(authorization_context.get("work_unit_fingerprint") or "").strip()
    lines: list[str] = []
    _append_optional_line(lines, "active_work_unit_id", work_unit_id, code=True)
    _append_optional_line(lines, "work_unit_fingerprint", work_unit_fingerprint, code=True)
    _append_json_line(lines, "next_work_unit", authorization_context.get("next_work_unit"))
    _append_json_line(lines, "blocking_work_units", authorization_context.get("blocking_work_units"))
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        _append_json_line(lines, key, authorization_context.get(key))
    if source_route_key_question and source_route_key_question != route_key_question:
        lines.append(f"- source_route_key_question: {source_route_key_question}")
    return "\n".join(lines) + ("\n" if lines else "")


def _append_optional_line(lines: list[str], key: str, value: str, *, code: bool = False) -> None:
    if not value:
        return
    rendered = f"`{value}`" if code else value
    lines.append(f"- {key}: {rendered}")


def _append_json_line(lines: list[str], key: str, value: Any) -> None:
    if isinstance(value, dict) and value:
        lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}")
    elif isinstance(value, list) and value:
        lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}")
