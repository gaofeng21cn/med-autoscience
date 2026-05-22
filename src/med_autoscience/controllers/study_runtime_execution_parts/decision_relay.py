from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent
from med_autoscience.runtime_protocol import quest_state, user_message

from .controller_authorization_context import _load_controller_decision_route_context
from ..progress_projection import (
    StudyRuntimeAuditStatus,
    StudyRuntimeDecision,
    StudyRuntimeReason,
    ProgressProjectionStatus,
)


_LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD = 3
_LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON = {
    StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL: "return_to_publishability_gate",
    StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY: "continue_write_stage",
}
_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY = "last_live_controller_reroute_restart"
_CONTROL_INTENT_LIFECYCLE_STATE_KEY = "control_intent_lifecycle"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _texts(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        return tuple(sorted({text for item in value if (text := _text(item))}))
    text = _text(value)
    return (text,) if text is not None else ()


def _runtime_state_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"


def _write_runtime_state(*, quest_root: Path, runtime_state: dict[str, Any]) -> None:
    path = _runtime_state_path(quest_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _live_controller_reroute_fingerprint(*, status: ProgressProjectionStatus) -> str:
    publication_supervisor_state = status.extras.get("publication_supervisor_state")
    supervisor_payload = publication_supervisor_state if isinstance(publication_supervisor_state, dict) else {}
    canonical_payload = {
        "reason": status.reason.value if status.reason is not None else None,
        "supervisor_phase": _text(supervisor_payload.get("supervisor_phase")),
        "phase_owner": _text(supervisor_payload.get("phase_owner")),
        "current_required_action": _text(supervisor_payload.get("current_required_action")),
        "gate_fingerprint": _text(supervisor_payload.get("gate_fingerprint")),
        "evaluated_source_signature": _text(
            supervisor_payload.get("evaluated_source_signature")
            or supervisor_payload.get("submission_minimal_evaluated_source_signature")
        ),
        "authority_source_signature": _text(
            supervisor_payload.get("authority_source_signature")
            or supervisor_payload.get("submission_minimal_authority_source_signature")
        ),
        "blockers": list(_texts(supervisor_payload.get("blockers"))),
    }
    encoded = json.dumps(canonical_payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return f"live-controller-reroute:{hashlib.sha256(encoded).hexdigest()[:24]}"


def _live_controller_reroute_identity(*, status: ProgressProjectionStatus) -> control_intent.ControlIntentIdentity:
    publication_supervisor_state = status.extras.get("publication_supervisor_state")
    supervisor_payload = publication_supervisor_state if isinstance(publication_supervisor_state, dict) else {}
    current_required_action = _text(supervisor_payload.get("current_required_action")) or (
        _LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON.get(status.reason) or "live_controller_reroute"
    )
    route_target = "publication_gate" if current_required_action == "return_to_publishability_gate" else "write"
    return control_intent.build_control_intent_identity(
        study_id=status.study_id,
        quest_id=status.quest_id,
        route_target=route_target,
        work_unit_id=current_required_action,
        blocker_authority_fingerprint=_live_controller_reroute_fingerprint(status=status),
        controller_actions=("live_controller_reroute",),
        source_kind="live_controller_reroute",
    )


def _study_root_for_lifecycle(*, status: ProgressProjectionStatus, context: Any) -> Path | None:
    value = getattr(context, "study_root", None) or status.study_root
    text = str(value or "").strip()
    return Path(text).expanduser().resolve() if text else None


def _live_controller_reroute_restart_already_recorded(
    *,
    status: ProgressProjectionStatus,
    runtime_state: dict[str, Any],
) -> bool:
    marker = runtime_state.get(_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY)
    if not isinstance(marker, dict):
        return False
    reason = status.reason.value if status.reason is not None else ""
    restart_count = int(marker.get("restart_count") or 0)
    return (
        restart_count > 0
        and str(marker.get("reason") or "").strip() == reason
        and str(marker.get("fingerprint") or "").strip() == _live_controller_reroute_fingerprint(status=status)
    )


def _mark_live_controller_reroute_restart(
    *,
    status: ProgressProjectionStatus,
    context: Any,
    same_fingerprint_auto_turn_count: int,
) -> None:
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    previous = runtime_state.get(_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY)
    fingerprint = _live_controller_reroute_fingerprint(status=status)
    restart_count = 1
    if isinstance(previous, dict) and str(previous.get("fingerprint") or "").strip() == fingerprint:
        restart_count = int(previous.get("restart_count") or 0) + 1
    runtime_state[_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY] = {
        "reason": status.reason.value if status.reason is not None else None,
        "fingerprint": fingerprint,
        "restart_count": restart_count,
        "same_fingerprint_auto_turn_count": same_fingerprint_auto_turn_count,
    }
    _write_runtime_state(quest_root=context.quest_root, runtime_state=runtime_state)


def _reset_same_fingerprint_count_for_changed_live_controller_intent(
    *,
    runtime_state: dict[str, Any],
    identity: control_intent.ControlIntentIdentity,
) -> bool:
    lifecycle = runtime_state.get(_CONTROL_INTENT_LIFECYCLE_STATE_KEY)
    if not isinstance(lifecycle, dict):
        return False
    previous_key = str(lifecycle.get("control_intent_key") or "").strip()
    if not previous_key or previous_key == identity.business_key:
        return False
    runtime_state["same_fingerprint_auto_turn_count"] = 0
    runtime_state.pop(_CONTROL_INTENT_LIFECYCLE_STATE_KEY, None)
    runtime_state.pop(_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY, None)
    return True


def _mark_live_controller_reroute_awaiting_artifact_delta(
    *,
    status: ProgressProjectionStatus,
    context: Any,
    identity: control_intent.ControlIntentIdentity,
    same_fingerprint_auto_turn_count: int,
) -> None:
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    runtime_state[_CONTROL_INTENT_LIFECYCLE_STATE_KEY] = {
        "state": control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
        "control_intent_key": identity.business_key,
        "control_intent_identity": identity.to_dict(),
        "fingerprint": _live_controller_reroute_fingerprint(status=status),
        "same_fingerprint_auto_turn_count": same_fingerprint_auto_turn_count,
    }
    _write_runtime_state(quest_root=context.quest_root, runtime_state=runtime_state)
    study_root = _study_root_for_lifecycle(status=status, context=context)
    if study_root is None:
        return
    latest = control_intent.latest_event(study_root=study_root, business_key=identity.business_key)
    if isinstance(latest, dict) and str(latest.get("event_type") or "").strip() == control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY:
        return
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type=control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
        payload={
            "reason": status.reason.value if status.reason is not None else None,
            "fingerprint": _live_controller_reroute_fingerprint(status=status),
            "same_fingerprint_auto_turn_count": same_fingerprint_auto_turn_count,
        },
    )


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
    status: ProgressProjectionStatus,
    route_context: dict[str, str] | None = None,
) -> str | None:
    if status.reason is StudyRuntimeReason.DOMAIN_TRANSITION_AI_REVIEWER_RE_EVAL:
        domain_transition = status.extras.get("domain_transition")
        next_work_unit = domain_transition.get("next_work_unit") if isinstance(domain_transition, dict) else None
        next_summary = str(next_work_unit.get("summary") or "").strip() if isinstance(next_work_unit, dict) else ""
        summary_clause = f"具体 work unit 是：{next_summary}。" if next_summary else ""
        return _append_route_context_to_message(
            message=(
                "MAS 当前 route 归 AI reviewer 质量 owner。请保持当前 live runtime，"
                f"回到 AI reviewer manuscript-quality review，关闭 reviewer-owned publication evaluation 缺口。{summary_clause}"
            ),
            route_context=route_context,
        )
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
    status: ProgressProjectionStatus,
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


def _has_live_running_worker(*, status: ProgressProjectionStatus) -> bool:
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
    if isinstance(runtime_audit, dict) and runtime_audit.get("worker_running") is True:
        return True
    return payload.get("worker_running") is True


def _should_skip_redundant_resume_for_live_controller_reroute(*, status: ProgressProjectionStatus) -> bool:
    if status.reason not in _LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON:
        return False
    return _has_live_running_worker(status=status)


def _should_skip_redundant_resume_for_live_domain_redrive(*, status: ProgressProjectionStatus) -> bool:
    if status.reason is not StudyRuntimeReason.DOMAIN_TRANSITION_AI_REVIEWER_RE_EVAL:
        return False
    return _has_live_running_worker(status=status)


def _should_force_restart_for_live_controller_reroute(
    *,
    status: ProgressProjectionStatus,
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
    if _live_controller_reroute_restart_already_recorded(status=status, runtime_state=runtime_state):
        return False
    identity = _live_controller_reroute_identity(status=status)
    if _reset_same_fingerprint_count_for_changed_live_controller_intent(
        runtime_state=runtime_state,
        identity=identity,
    ):
        _write_runtime_state(quest_root=context.quest_root, runtime_state=runtime_state)
        status.extras["control_intent_lifecycle"] = {
            "state": "superseded",
            "control_intent_key": identity.business_key,
            "same_fingerprint_auto_turn_count": 0,
        }
        return False
    same_fingerprint_auto_turn_count = int(runtime_state.get("same_fingerprint_auto_turn_count") or 0)
    if same_fingerprint_auto_turn_count < _LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD:
        return False
    study_root = _study_root_for_lifecycle(status=status, context=context)
    lifecycle = (
        control_intent.lifecycle_state(study_root=study_root, identity=identity)
        if study_root is not None
        else {"artifact_delta_observed": False}
    )
    if not bool(lifecycle.get("artifact_delta_observed")):
        _mark_live_controller_reroute_awaiting_artifact_delta(
            status=status,
            context=context,
            identity=identity,
            same_fingerprint_auto_turn_count=same_fingerprint_auto_turn_count,
        )
        status.extras["control_intent_lifecycle"] = {
            "state": control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
            "control_intent_key": identity.business_key,
            "fingerprint": _live_controller_reroute_fingerprint(status=status),
            "same_fingerprint_auto_turn_count": same_fingerprint_auto_turn_count,
            "allowed_next_actions": [
                "publication_gate_replay",
                "gate_needs_specificity",
                "explicit_recovery",
            ],
        }
        return False
    return True
