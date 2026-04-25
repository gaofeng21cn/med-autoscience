from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import quest_state, user_message
from med_autoscience.study_decision_record import StudyDecisionRecord

from ..study_runtime_status import (
    StudyRuntimeDecision,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)


_CONTROLLER_DECISION_RUNTIME_AUTHORIZATION_ACTIONS = {
    "ensure_study_runtime",
    "ensure_study_runtime_relaunch_stopped",
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
}
_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY = "last_controller_decision_authorization"
_ROUTE_TARGET_LABELS = {
    "analysis-campaign": "有限补充分析",
    "write": "当前论文主线写作",
    "review": "质量复评",
    "finalize": "finalize / 投稿包收口",
}


def _load_controller_decision_authorization_context(*, study_root: Path) -> dict[str, Any] | None:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    if not decision_path.exists():
        return None
    try:
        payload = json.loads(decision_path.read_text(encoding="utf-8")) or {}
        record = StudyDecisionRecord.from_payload(payload if isinstance(payload, dict) else {})
    except (OSError, ValueError, TypeError):
        return None
    if (
        record.route_target is None
        or record.route_key_question is None
        or record.route_rationale is None
    ):
        return None
    controller_actions = tuple(action.action_type.value for action in record.controller_actions)
    return {
        "decision_id": record.decision_id,
        "decision_type": record.decision_type.value,
        "requires_human_confirmation": record.requires_human_confirmation,
        "controller_actions": controller_actions,
        "decision_path": str(decision_path),
        "route_target": record.route_target,
        "route_target_label": _ROUTE_TARGET_LABELS.get(record.route_target, record.route_target),
        "route_key_question": record.route_key_question,
        "route_rationale": record.route_rationale,
    }


def _load_controller_decision_route_context(*, study_root: Path) -> dict[str, str] | None:
    authorization_context = _load_controller_decision_authorization_context(study_root=study_root)
    if not isinstance(authorization_context, dict):
        return None
    route_context = {
        key: str(authorization_context.get(key) or "").strip()
        for key in ("route_target", "route_target_label", "route_key_question", "route_rationale")
    }
    if not all(route_context.values()):
        return None
    return route_context


def _controller_decision_authorizes_runtime(authorization_context: dict[str, Any] | None) -> bool:
    if not isinstance(authorization_context, dict):
        return False
    if bool(authorization_context.get("requires_human_confirmation")):
        return False
    controller_actions = {
        str(action).strip()
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    }
    return bool(controller_actions & _CONTROLLER_DECISION_RUNTIME_AUTHORIZATION_ACTIONS)


def _active_run_id_from_status_or_state(*, status: StudyRuntimeStatus, runtime_state: dict[str, Any]) -> str | None:
    active_run_id = str(runtime_state.get("active_run_id") or "").strip()
    if active_run_id:
        return active_run_id
    payload = status.extras.get("runtime_liveness_audit")
    if isinstance(payload, dict):
        active_run_id = str(payload.get("active_run_id") or "").strip()
        if active_run_id:
            return active_run_id
        runtime_audit = payload.get("runtime_audit")
        if isinstance(runtime_audit, dict):
            active_run_id = str(runtime_audit.get("active_run_id") or "").strip()
            if active_run_id:
                return active_run_id
    return None


def _controller_decision_authorization_already_relayed(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
    active_run_id: str | None,
) -> bool:
    marker = runtime_state.get(_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY)
    if not isinstance(marker, dict):
        return False
    return (
        str(marker.get("decision_id") or "").strip() == str(authorization_context.get("decision_id") or "").strip()
        and str(marker.get("route_target") or "").strip() == str(authorization_context.get("route_target") or "").strip()
        and (str(marker.get("active_run_id") or "").strip() or None) == active_run_id
    )


def _controller_decision_authorization_message(*, authorization_context: dict[str, Any]) -> str:
    route_target = str(authorization_context.get("route_target") or "").strip()
    route_target_label = str(authorization_context.get("route_target_label") or route_target).strip()
    route_key_question = str(authorization_context.get("route_key_question") or "").strip()
    route_rationale = str(authorization_context.get("route_rationale") or "").strip()
    decision_id = str(authorization_context.get("decision_id") or "").strip()
    decision_path = str(authorization_context.get("decision_path") or "artifacts/controller_decisions/latest.json").strip()
    controller_actions = ", ".join(
        f"`{action}`"
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    )
    return (
        "MAS controller authorization. "
        f"`{decision_path}` is the active MAS authorization for this runtime turn.\n\n"
        f"- decision_id: `{decision_id}`\n"
        f"- controller_actions: {controller_actions}\n"
        f"- route_target: `{route_target}` ({route_target_label})\n"
        f"- route_key_question: {route_key_question}\n"
        f"- route_rationale: {route_rationale}\n"
        "- requires_human_confirmation: false\n"
        "- Runtime instruction: do not park solely because `publication_eval/latest.json` still says "
        "`requires_controller_decision=true`; execute the authorized route_key_question and write durable "
        "evidence, review, or route outputs. Only stop for a true external credential, human-only choice, "
        "or startup boundary."
    )


def _runtime_message_id(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    nested_message = payload.get("message")
    if isinstance(nested_message, dict):
        message_id = str(nested_message.get("id") or nested_message.get("message_id") or "").strip()
        if message_id:
            return message_id
    message_id = str(payload.get("message_id") or payload.get("id") or "").strip()
    return message_id or None


def _write_runtime_state(*, quest_root: Path, runtime_state: dict[str, Any]) -> None:
    runtime_state_path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _mark_controller_decision_authorization_relayed(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    delivery_mode: str,
    message_id: str | None,
    source: str,
) -> None:
    runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY] = {
        "decision_id": str(authorization_context.get("decision_id") or "").strip(),
        "route_target": str(authorization_context.get("route_target") or "").strip(),
        "route_key_question": str(authorization_context.get("route_key_question") or "").strip(),
        "active_run_id": active_run_id,
        "delivery_mode": delivery_mode,
        "message_id": message_id,
        "source": source,
    }
    _write_runtime_state(quest_root=quest_root, runtime_state=runtime_state)


def _relay_controller_decision_authorization_if_required(
    *,
    status: StudyRuntimeStatus,
    context: Any,
) -> dict[str, Any] | None:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return None
    if status.decision not in {StudyRuntimeDecision.NOOP, StudyRuntimeDecision.RESUME, StudyRuntimeDecision.RELAUNCH_STOPPED}:
        return None
    authorization_context = _load_controller_decision_authorization_context(study_root=context.study_root)
    if not _controller_decision_authorizes_runtime(authorization_context):
        return None
    assert authorization_context is not None
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    if int(runtime_state.get("pending_user_message_count") or 0) > 0:
        return None
    runtime_state["quest_id"] = status.quest_id
    active_run_id = _active_run_id_from_status_or_state(status=status, runtime_state=runtime_state)
    if _controller_decision_authorization_already_relayed(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
    ):
        return None

    message = _controller_decision_authorization_message(authorization_context=authorization_context)
    relay: dict[str, Any] = {
        "decision_id": authorization_context.get("decision_id"),
        "route_target": authorization_context.get("route_target"),
        "route_key_question": authorization_context.get("route_key_question"),
        "decision_path": authorization_context.get("decision_path"),
        "active_run_id": active_run_id,
        "delivery_mode": None,
        "message_id": None,
        "source": context.source,
    }
    try:
        response = context.runtime_backend.chat_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            text=message,
            source=context.source,
        )
    except Exception as exc:
        relay["backend_submit_error"] = str(exc)
    else:
        relay["delivery_mode"] = "managed_runtime_chat"
        relay["message_id"] = _runtime_message_id(response)
        _mark_controller_decision_authorization_relayed(
            quest_root=context.quest_root,
            runtime_state=runtime_state,
            authorization_context=authorization_context,
            active_run_id=active_run_id,
            delivery_mode="managed_runtime_chat",
            message_id=relay["message_id"],
            source=context.source,
        )
        status.extras["controller_decision_authorization_relay"] = relay
        return relay

    record = user_message.enqueue_user_message(
        quest_root=context.quest_root,
        runtime_state=runtime_state,
        message=message,
        source=context.source,
    )
    updated_runtime_state = quest_state.load_runtime_state(context.quest_root)
    relay["delivery_mode"] = "durable_queue_fallback"
    relay["message_id"] = record.get("message_id")
    relay["reply_to_interaction_id"] = record.get("reply_to_interaction_id")
    _mark_controller_decision_authorization_relayed(
        quest_root=context.quest_root,
        runtime_state=updated_runtime_state,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        delivery_mode="durable_queue_fallback",
        message_id=str(record.get("message_id") or "").strip() or None,
        source=context.source,
    )
    status.extras["controller_decision_authorization_relay"] = relay
    return relay
