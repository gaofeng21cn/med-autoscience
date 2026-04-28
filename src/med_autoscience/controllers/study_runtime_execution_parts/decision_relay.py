from __future__ import annotations

from typing import Any

from med_autoscience.runtime_protocol import quest_state, user_message

from .controller_authorization import _load_controller_decision_route_context
from ..study_runtime_status import (
    StudyRuntimeAuditStatus,
    StudyRuntimeDecision,
    StudyRuntimeReason,
    StudyRuntimeStatus,
)


_LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD = 3
_LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON = {
    StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL: "return_to_publishability_gate",
    StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY: "continue_write_stage",
}


def _append_route_context_to_message(*, message: str, route_context: dict[str, str] | None) -> str:
    if not isinstance(route_context, dict):
        return message
    route_target_label = str(route_context.get("route_target_label") or "").strip()
    route_key_question = str(route_context.get("route_key_question") or "").strip()
    route_rationale = str(route_context.get("route_rationale") or "").strip()
    if not route_target_label or not route_key_question or not route_rationale:
        return message
    return (
        f"{message} 当前正式 route 是“{route_target_label}”；"
        f"当前关键问题是：{route_key_question}；"
        f"这样推进的理由是：{route_rationale}"
    )


def _controller_owned_interaction_reply_message(
    *,
    status: StudyRuntimeStatus,
    route_context: dict[str, str] | None = None,
) -> str | None:
    if status.reason is StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL:
        return _append_route_context_to_message(
            message=(
                "MAS publication gate 尚未放行写作。请停止当前 manuscript / finalize 漂移，"
                "回到 publishability blockers 与科学锚点映射，清除门控后再继续写作或申请 completion。"
            ),
            route_context=route_context,
        )
    if status.reason is StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY:
        return _append_route_context_to_message(
            message=(
                "MAS publication gate 已放行写作。请结束旧的 decision 续跑点，"
                "回到当前 manuscript 主线，继续 write stage 并更新 results / figures / tables。"
            ),
            route_context=route_context,
        )
    pending_payload = status.extras.get("pending_user_interaction")
    arbitration_payload = status.extras.get("interaction_arbitration")
    if not isinstance(pending_payload, dict) or not isinstance(arbitration_payload, dict):
        return None
    pending_interaction_id = str(pending_payload.get("interaction_id") or "").strip()
    if not pending_interaction_id or not bool(pending_payload.get("relay_required")):
        return None
    if bool(arbitration_payload.get("requires_user_input")):
        return None
    if str(arbitration_payload.get("action") or "").strip() != StudyRuntimeDecision.RESUME.value:
        return None

    classification = str(arbitration_payload.get("classification") or "").strip()
    if classification == "premature_completion_request":
        return (
            "暂不结题。MAS publication gate 尚未 clear，请继续处理当前论文的 publishability blockers；"
            "等 publication gate 清除后，再重新申请 completion。"
        )
    if classification == "submission_metadata_only":
        return (
            "不要因 submission metadata 暂缺而阻塞当前 quest。请继续推进论文主稿与科学交付，"
            "并把缺失的投稿元数据保留在待补清单中。"
        )
    if classification == "invalid_blocking":
        return "当前交互不应阻塞 MAS 托管流程。请不要等待用户输入，按现有 study contract 继续自主推进下一步。"
    return None


def _relay_controller_owned_runtime_reply_if_required(
    *,
    status: StudyRuntimeStatus,
    context: Any,
) -> dict[str, Any] | None:
    route_context = _load_controller_decision_route_context(study_root=context.study_root)
    message = _controller_owned_interaction_reply_message(status=status, route_context=route_context)
    if message is None:
        return None
    pending_payload = status.extras.get("pending_user_interaction")
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    runtime_state["quest_id"] = status.quest_id
    if isinstance(pending_payload, dict):
        runtime_state.setdefault(
            "active_interaction_id",
            str(pending_payload.get("interaction_id") or "").strip() or None,
        )
    record = user_message.enqueue_user_message(
        quest_root=context.quest_root,
        runtime_state=runtime_state,
        message=message,
        source=context.source,
    )
    status.extras["controller_owned_runtime_reply"] = {
        "message_id": record.get("message_id"),
        "reply_to_interaction_id": record.get("reply_to_interaction_id"),
        "content": record.get("content"),
        "source": record.get("source"),
        "route_context": route_context,
    }
    return record


def _should_skip_redundant_resume_for_live_controller_reroute(*, status: StudyRuntimeStatus) -> bool:
    if status.reason not in _LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON:
        return False
    payload = status.extras.get("runtime_liveness_audit")
    if not isinstance(payload, dict):
        return False
    runtime_audit = payload.get("runtime_audit")
    resolved_active_run_id = str(payload.get("active_run_id") or "").strip() or None
    if resolved_active_run_id is None and isinstance(runtime_audit, dict):
        resolved_active_run_id = str(runtime_audit.get("active_run_id") or "").strip() or None
    if resolved_active_run_id is None:
        return False
    if str(payload.get("status") or "").strip().lower() != StudyRuntimeAuditStatus.LIVE.value:
        return False
    return isinstance(runtime_audit, dict) and runtime_audit.get("worker_running") is True


def _should_force_restart_for_live_controller_reroute(
    *,
    status: StudyRuntimeStatus,
    context: Any,
) -> bool:
    if not _should_skip_redundant_resume_for_live_controller_reroute(status=status):
        return False
    publication_supervisor_state = status.extras.get("publication_supervisor_state")
    if not isinstance(publication_supervisor_state, dict):
        return False
    current_required_action = str(publication_supervisor_state.get("current_required_action") or "").strip()
    expected_action = _LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON.get(status.reason)
    if expected_action is None or current_required_action != expected_action:
        return False
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    if int(runtime_state.get("pending_user_message_count") or 0) > 0:
        return False
    continuation_anchor = str(runtime_state.get("continuation_anchor") or "").strip()
    continuation_reason = str(runtime_state.get("continuation_reason") or "").strip()
    if (
        status.reason is not StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL
        and (continuation_anchor != "decision" or not continuation_reason.startswith("decision:"))
    ):
        return False
    same_fingerprint_auto_turn_count = int(runtime_state.get("same_fingerprint_auto_turn_count") or 0)
    return same_fingerprint_auto_turn_count >= _LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD

