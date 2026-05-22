from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.paper_progress_state import build_paper_progress_state

from .shared import _mapping_copy, _non_empty_text

USER_VISIBLE_PROJECTION_SURFACE = "study_progress_user_visible_projection"
USER_VISIBLE_PROJECTION_READ_MODEL = "study_progress_user_visible_read_model"

_ANSWER_FOCUS = (
    "writer_state",
    "package_delivered",
    "actual_write_active",
    "meaningful_artifact_delta",
    "next_owner",
    "why_not_progressing",
    "user_next",
    "user_action_required",
    "evidence",
)
_EVIDENCE_REF_KEYS = (
    "publication_eval_path",
    "controller_decision_path",
    "controller_confirmation_summary_path",
    "runtime_supervision_path",
    "domain_health_diagnostic_report_path",
    "runtime_status_summary_path",
    "evaluation_summary_path",
    "medical_paper_readiness_path",
    "study_truth_snapshot_path",
    "runtime_health_snapshot_path",
    "bash_summary_path",
    "details_projection_path",
)

_ACTIVE_TOP_LEVEL_STAGES = frozenset(
    {
        "managed_runtime_active",
    }
)

_QUALITY_REPAIR_LABEL = "质量修复/复审中"

_RUNTIME_REDRIVE_DOMAIN_TRANSITIONS = frozenset(
    {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
        "route_back_same_line",
    }
)


def build_user_visible_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    macro_state = _macro_state(payload)
    evidence = _evidence_projection(payload)
    if macro_state is None:
        return _conflict_projection(
            payload,
            reason="missing_macro_state",
            message="缺少 canonical study_macro_state；需要重新生成 canonical progress projection。",
            evidence=evidence,
        )
    if _top_level_writer_conflicts(payload, macro_state):
        return _conflict_projection(
            payload,
            reason="macro_state_conflict",
            message="旧 top-level writer 字段与 study_macro_state 冲突；需要重新生成 canonical progress projection。",
            evidence=evidence,
            macro_state=macro_state,
        )

    writer_state = _non_empty_text(macro_state.get("writer_state")) or "conflict"
    user_next = _non_empty_text(macro_state.get("user_next")) or "inspect"
    reason = _non_empty_text(macro_state.get("reason")) or "truth_conflict"
    details = _mapping_copy(macro_state.get("details"))
    paper_progress_state = build_paper_progress_state(payload)
    package_delivered = bool(details.get("package_delivered")) or bool(paper_progress_state.get("package_delivered"))
    terminal_delivery = _non_empty_text(paper_progress_state.get("state")) == "terminal_delivered"
    actual_write_active = _actual_write_active(writer_state=writer_state, macro_state=macro_state, payload=payload)
    meaningful_artifact_delta = _meaningful_artifact_delta(payload)
    next_owner = _non_empty_text(paper_progress_state.get("next_owner")) or _next_owner(payload=payload, details=details)
    why_not_progressing = _non_empty_text(paper_progress_state.get("why_not_progressing")) or _why_not_progressing(
        payload=payload,
        actual_write_active=actual_write_active,
        meaningful_artifact_delta=meaningful_artifact_delta,
        next_owner=next_owner,
    )
    quality_owner_pending = _quality_owner_pending(
        payload=payload,
        terminal_delivery=terminal_delivery,
        next_owner=next_owner,
    )
    user_action_required = _user_action_required(
        user_next=user_next,
        reason=reason,
        terminal_delivery=terminal_delivery,
    )
    state_label = _state_label(
        writer_state=writer_state,
        user_next=user_next,
        reason=reason,
        package_delivered=package_delivered,
        terminal_delivery=terminal_delivery,
        quality_owner_pending=quality_owner_pending,
    )
    current_blockers = _current_blockers(
        writer_state=writer_state,
        user_next=user_next,
        reason=reason,
        details=details,
        terminal_delivery=terminal_delivery,
        quality_owner_pending=quality_owner_pending,
    )
    state_summary = _state_summary(
        state_label=state_label,
        writer_state=writer_state,
        user_next=user_next,
        reason=reason,
        package_delivered=package_delivered,
        actual_write_active=actual_write_active,
        user_action_required=user_action_required,
        current_blockers=current_blockers,
    )
    next_step = _next_step(
        writer_state=writer_state,
        user_next=user_next,
        reason=reason,
        terminal_delivery=terminal_delivery,
        details=details,
        quality_owner_pending=quality_owner_pending,
    )

    return {
        "surface": USER_VISIBLE_PROJECTION_SURFACE,
        "read_model": USER_VISIBLE_PROJECTION_READ_MODEL,
        "schema_version": 2,
        "authority": "truth_projection",
        "projection_only": True,
        "answer_focus": list(_ANSWER_FOCUS),
        "study_id": _non_empty_text(payload.get("study_id")),
        "quest_id": _non_empty_text(payload.get("quest_id")),
        "state": _state_key(writer_state=writer_state, user_next=user_next, reason=reason),
        "writer_state": writer_state,
        "user_next": user_next,
        "reason": reason,
        "package_delivered": package_delivered,
        "actual_write_active": actual_write_active,
        "meaningful_artifact_delta": meaningful_artifact_delta,
        "next_owner": next_owner,
        "why_not_progressing": why_not_progressing,
        "user_action_required": user_action_required,
        "state_label": state_label,
        "state_summary": state_summary,
        "current_stage": writer_state,
        "current_stage_label": state_label,
        "current_stage_summary": state_summary,
        "status_summary": state_summary,
        "paper_stage": _non_empty_text(details.get("paper_stage")) or _non_empty_text(payload.get("paper_stage")),
        "paper_stage_summary": state_summary,
        "current_blockers": current_blockers,
        "next_system_action": next_step,
        "next_step": next_step,
        "needs_user_decision": user_action_required,
        "needs_physician_decision": user_action_required,
        "study_macro_state": dict(macro_state),
        "supervision": _supervision_projection(payload),
        "paper_progress_state": paper_progress_state,
        "evidence": evidence,
        "evidence_refs": dict(evidence["refs"]),
        "conditions": _projection_conditions(
            writer_state=writer_state,
            user_next=user_next,
            reason=reason,
            package_delivered=package_delivered,
            actual_write_active=actual_write_active,
            meaningful_artifact_delta=meaningful_artifact_delta,
            next_owner=next_owner,
            why_not_progressing=why_not_progressing,
            user_action_required=user_action_required,
            current_blockers=current_blockers,
            next_step=next_step,
            supervision=_mapping_copy(payload.get("supervision")),
            evidence=evidence,
        ),
    }


def _normalized_texts(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in items:
            items.append(text)
    return items


def _macro_state(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    macro_state = payload.get("study_macro_state")
    if not isinstance(macro_state, Mapping):
        return None
    writer_state = _non_empty_text(macro_state.get("writer_state"))
    user_next = _non_empty_text(macro_state.get("user_next"))
    reason = _non_empty_text(macro_state.get("reason"))
    if writer_state is None or user_next is None or reason is None:
        return None
    return dict(macro_state)


def _top_level_writer_conflicts(payload: Mapping[str, Any], macro_state: Mapping[str, Any]) -> bool:
    writer_state = _non_empty_text(macro_state.get("writer_state"))
    if writer_state == "conflict":
        return True
    if _current_runtime_redrive_route(payload) and writer_state != "live":
        return False
    active_run_id = (
        _non_empty_text(payload.get("active_run_id"))
        or _non_empty_text(_mapping_copy(payload.get("supervision")).get("active_run_id"))
    )
    if active_run_id and writer_state != "live":
        return True
    top_level_stage = _non_empty_text(payload.get("current_stage"))
    if top_level_stage in _ACTIVE_TOP_LEVEL_STAGES and writer_state not in {"live", "queued"}:
        return True
    return False


def _conflict_projection(
    payload: Mapping[str, Any],
    *,
    reason: str,
    message: str,
    evidence: dict[str, Any],
    macro_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    state_summary = f"状态需要检查；{message}"
    return {
        "surface": USER_VISIBLE_PROJECTION_SURFACE,
        "read_model": USER_VISIBLE_PROJECTION_READ_MODEL,
        "schema_version": 2,
        "authority": "truth_projection",
        "projection_only": True,
        "answer_focus": list(_ANSWER_FOCUS),
        "study_id": _non_empty_text(payload.get("study_id")),
        "quest_id": _non_empty_text(payload.get("quest_id")),
        "state": "inspect/conflict",
        "writer_state": "conflict",
        "user_next": "inspect",
        "reason": "truth_conflict",
        "conflict_reason": reason,
        "package_delivered": False,
        "actual_write_active": False,
        "meaningful_artifact_delta": False,
        "next_owner": _next_owner(payload=payload, details={}),
        "why_not_progressing": message,
        "user_action_required": False,
        "state_label": "状态需要检查",
        "state_summary": state_summary,
        "current_stage": "inspect/conflict",
        "current_stage_label": "状态需要检查",
        "current_stage_summary": state_summary,
        "status_summary": state_summary,
        "paper_stage": None,
        "paper_stage_summary": state_summary,
        "current_blockers": [message],
        "next_system_action": "重新生成 canonical progress projection。",
        "next_step": "重新生成 canonical progress projection。",
        "needs_user_decision": False,
        "needs_physician_decision": False,
        "study_macro_state": dict(macro_state) if macro_state is not None else None,
        "supervision": _supervision_projection(payload),
        "evidence": evidence,
        "evidence_refs": dict(evidence["refs"]),
        "conditions": [
            _condition("macro_state_available", bool(macro_state), reason, message),
            _condition("state_conflict", True, reason, message),
        ],
    }


def _actual_write_active(*, writer_state: str, macro_state: Mapping[str, Any], payload: Mapping[str, Any]) -> bool:
    if writer_state != "live":
        return False
    if _runtime_health_requires_artifact_delta_recovery(payload):
        return False
    progress_freshness = _mapping_copy(payload.get("progress_freshness"))
    activity_timeout = _mapping_copy(progress_freshness.get("activity_timeout"))
    if _non_empty_text(activity_timeout.get("state")) in {"timed_out", "at_risk", "watching_new_run"}:
        return False
    artifact_delta_freshness = _mapping_copy(progress_freshness.get("meaningful_artifact_delta_freshness"))
    if artifact_delta_freshness:
        if _non_empty_text(artifact_delta_freshness.get("status")) != "fresh":
            return False
        if _non_empty_text(artifact_delta_freshness.get("latest_progress_at")) is None:
            return False
    return bool(
        _non_empty_text(_mapping_copy(macro_state.get("details")).get("active_run_id"))
        or _non_empty_text(payload.get("active_run_id"))
        or _non_empty_text(_mapping_copy(payload.get("supervision")).get("active_run_id"))
    )


def _runtime_health_requires_artifact_delta_recovery(payload: Mapping[str, Any]) -> bool:
    if _fresh_artifact_delta_present(payload):
        return False
    runtime_health = _mapping_copy(payload.get("runtime_health_snapshot"))
    worker_liveness_state = _mapping_copy(runtime_health.get("worker_liveness_state"))
    blocking_reasons = set(_normalized_texts(runtime_health.get("blocking_reasons")))
    if _non_empty_text(worker_liveness_state.get("state")) == "activity_timeout":
        return True
    if _non_empty_text(runtime_health.get("canonical_runtime_action")) == "recover_runtime":
        return True
    if _non_empty_text(runtime_health.get("attempt_state")) == "recovering":
        return True
    if blocking_reasons.intersection({"live_worker_meaningful_artifact_delta_timeout", "same_fingerprint_loop"}):
        return True

    dashboard = _mapping_copy(payload.get("portable_supervisor_dashboard"))
    artifact_delta = _mapping_copy(dashboard.get("artifact_delta"))
    if _non_empty_text(artifact_delta.get("status")) in {"missing", "not_observed", "stale"}:
        return True
    return False


def _fresh_artifact_delta_present(payload: Mapping[str, Any]) -> bool:
    progress_freshness = _mapping_copy(payload.get("progress_freshness"))
    artifact_delta_freshness = _mapping_copy(progress_freshness.get("meaningful_artifact_delta_freshness"))
    return (
        _non_empty_text(artifact_delta_freshness.get("status")) == "fresh"
        and _non_empty_text(artifact_delta_freshness.get("latest_progress_at")) is not None
    )


def _meaningful_artifact_delta(payload: Mapping[str, Any]) -> bool:
    return _fresh_artifact_delta_present(payload)


def _next_owner(*, payload: Mapping[str, Any], details: Mapping[str, Any]) -> str | None:
    impact = _mapping_copy(payload.get("production_blocker_impact"))
    owner_route = _mapping_copy(payload.get("owner_route"))
    paper_progress_stall = _mapping_copy(payload.get("paper_progress_stall"))
    interaction_arbitration = _mapping_copy(payload.get("interaction_arbitration"))
    portable_supervisor = _mapping_copy(payload.get("portable_supervisor_dashboard"))
    ai_repair_lifecycle = _mapping_copy(payload.get("ai_repair_lifecycle"))
    return (
        _non_empty_text(impact.get("next_owner"))
        or _non_empty_text(owner_route.get("next_owner"))
        or _non_empty_text(details.get("decision_owner"))
        or _non_empty_text(paper_progress_stall.get("next_owner"))
        or _non_empty_text(interaction_arbitration.get("next_owner"))
        or _non_empty_text(portable_supervisor.get("next_owner"))
        or _non_empty_text(ai_repair_lifecycle.get("next_owner"))
    )


def _why_not_progressing(
    *,
    payload: Mapping[str, Any],
    actual_write_active: bool,
    meaningful_artifact_delta: bool,
    next_owner: str | None,
) -> str | None:
    if actual_write_active and meaningful_artifact_delta:
        return None
    impact = _mapping_copy(payload.get("production_blocker_impact"))
    progress_freshness = _mapping_copy(payload.get("progress_freshness"))
    activity_timeout = _mapping_copy(progress_freshness.get("activity_timeout"))
    artifact_delta_freshness = _mapping_copy(progress_freshness.get("meaningful_artifact_delta_freshness"))
    paper_progress_stall = _mapping_copy(payload.get("paper_progress_stall"))
    interaction_arbitration = _mapping_copy(payload.get("interaction_arbitration"))
    portable_supervisor = _mapping_copy(payload.get("portable_supervisor_dashboard"))
    ai_repair_lifecycle = _mapping_copy(payload.get("ai_repair_lifecycle"))
    return (
        _non_empty_text(interaction_arbitration.get("blocked_reason"))
        or _non_empty_text(portable_supervisor.get("blocked_reason"))
        or _non_empty_text(ai_repair_lifecycle.get("blocked_reason"))
        or _non_empty_text(impact.get("why_not_running"))
        or _non_empty_text(paper_progress_stall.get("why_not_running"))
        or _non_empty_text(paper_progress_stall.get("summary"))
        or (f"next owner is {next_owner}; waiting for owner-consumable paper progress." if next_owner else None)
        or _non_empty_text(activity_timeout.get("summary"))
        or _non_empty_text(artifact_delta_freshness.get("summary"))
    )


def _user_action_required(*, user_next: str, reason: str, terminal_delivery: bool) -> bool:
    if user_next in {"submit_info", "revise"}:
        return True
    if reason in {"user_stop", "stop_loss"}:
        return True
    return bool(terminal_delivery and user_next == "submit_info")


def _quality_owner_pending(*, payload: Mapping[str, Any], terminal_delivery: bool, next_owner: str | None) -> bool:
    if terminal_delivery:
        return False
    if _current_runtime_redrive_route(payload):
        return True
    paper_progress = build_paper_progress_state(payload)
    if _non_empty_text(paper_progress.get("state")) in {
        "awaiting_callable_owner",
        "awaiting_controller_redrive",
        "downstream_only",
    }:
        return True
    if _non_empty_text(paper_progress.get("state")) == "blocked_controller_route" and next_owner:
        return True
    request_lifecycle = _mapping_copy(payload.get("ai_reviewer_request_lifecycle"))
    if _non_empty_text(request_lifecycle.get("state")) in {"requested", "assigned"}:
        return True
    return bool(next_owner and next_owner not in {"external_supervisor", "user"})


def _state_key(*, writer_state: str, user_next: str, reason: str) -> str:
    if writer_state == "conflict" or user_next == "inspect" and reason == "truth_conflict":
        return "inspect/conflict"
    return f"{writer_state}/{user_next}/{reason}"


def _state_label(
    *,
    writer_state: str,
    user_next: str,
    reason: str,
    package_delivered: bool,
    terminal_delivery: bool,
    quality_owner_pending: bool = False,
) -> str:
    if writer_state == "conflict" or reason == "truth_conflict":
        return "状态需要检查"
    if writer_state == "live":
        return "自动运行中"
    if user_next == "submit_info" and reason == "external_info" and package_delivered:
        return "投稿包已交付，等待外部投稿信息"
    if quality_owner_pending:
        return _QUALITY_REPAIR_LABEL
    if terminal_delivery and writer_state == "parked":
        return "投稿包已交付，自动停驻"
    if reason == "user_stop":
        return "用户暂停/手动停驻"
    if reason == "stop_loss":
        return "止损/终止"
    if reason == "quality" or user_next in {"repair", "revise"}:
        return _QUALITY_REPAIR_LABEL
    if writer_state == "queued":
        return "系统排队处理中"
    return "用户暂停/手动停驻" if writer_state == "parked" else "状态需要检查"


def _state_summary(
    *,
    state_label: str,
    writer_state: str,
    user_next: str,
    reason: str,
    package_delivered: bool,
    actual_write_active: bool,
    user_action_required: bool,
    current_blockers: list[str],
) -> str:
    if state_label == "自动运行中":
        if actual_write_active:
            return "自动运行中；系统有实际 writer/run 正在推进。"
        return "自动运行中；worker 已接管，但尚未观察到论文产物级有效增量。"
    if state_label == "系统排队处理中":
        return "系统排队处理中；当前没有实际写入，但 MAS 已有明确 owner/action。"
    if state_label == "投稿包已交付，等待外部投稿信息":
        return "投稿包已交付，系统已自动停驻并释放运行资源；等待补齐外部投稿信息。"
    if state_label == "投稿包已交付，自动停驻":
        return "投稿包已交付，系统已自动停驻并释放运行资源。"
    if state_label == "用户暂停/手动停驻":
        return "用户暂停/手动停驻；当前没有实际写入，需显式恢复或给出新方案。"
    if state_label == _QUALITY_REPAIR_LABEL:
        return "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。"
    if state_label == "止损/终止":
        return "止损/终止；当前论文线不再自动推进，需新计划或明确重开。"
    if current_blockers:
        return f"{state_label}；{current_blockers[0]}"
    write_text = "有实际写入" if actual_write_active else "没有实际写入"
    delivered_text = "投稿包已交付" if package_delivered else "投稿包未交付"
    user_text = "需要用户动作" if user_action_required else "当前不需要用户补东西"
    return f"{state_label}；{write_text}，{delivered_text}，{user_text}（{writer_state}/{user_next}/{reason}）。"


def _current_blockers(
    *,
    writer_state: str,
    user_next: str,
    reason: str,
    details: Mapping[str, Any],
    terminal_delivery: bool,
    quality_owner_pending: bool = False,
) -> list[str]:
    if writer_state == "live":
        return []
    if writer_state == "conflict" or reason == "truth_conflict":
        return ["study_macro_state 显示状态冲突，需要重新生成 canonical projection。"]
    if user_next == "submit_info" and reason == "external_info":
        missing = _normalized_texts(details.get("missing_external_info"))
        if missing:
            return [f"缺少外部投稿信息: {', '.join(missing)}"]
        return ["缺少外部投稿信息。"]
    if reason == "user_stop":
        return ["用户暂停或手动停驻，需显式恢复或新方案。"]
    if reason == "stop_loss":
        return ["当前论文线已止损/终止，需新计划或明确重开。"]
    if quality_owner_pending:
        return ["质量、artifact 或 runtime 修复 owner 已接管。"]
    if reason == "quality" or user_next in {"repair", "revise"}:
        return ["质量、artifact 或 runtime 修复 owner 已接管。"]
    if writer_state == "queued":
        return ["系统已有明确 owner/action，等待处理。"]
    if terminal_delivery:
        return []
    return ["状态需要检查。"]


def _next_step(
    *,
    writer_state: str,
    user_next: str,
    reason: str,
    terminal_delivery: bool,
    details: Mapping[str, Any],
    quality_owner_pending: bool = False,
) -> str:
    if writer_state == "live":
        return "观察自动运行推进。"
    if user_next == "submit_info" and reason == "external_info":
        missing = _normalized_texts(details.get("missing_external_info"))
        suffix = f": {', '.join(missing)}" if missing else ""
        return f"补齐外部投稿信息{suffix}。"
    if quality_owner_pending:
        return "等待质量修复/复审 owner 完成处理。"
    if writer_state == "queued":
        return "等待 MAS 已登记的 owner/action 处理。"
    if terminal_delivery:
        return "投稿包已交付；系统保持自动停驻。"
    if reason == "user_stop":
        return "等待用户显式恢复或给出新方案。"
    if reason == "stop_loss":
        return "等待新计划或明确重开。"
    if reason == "quality" or user_next in {"repair", "revise"}:
        return "等待质量修复/复审 owner 完成处理。"
    return "检查并重新生成 canonical progress projection。"


def _evidence_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = _mapping_copy(payload.get("refs"))
    return {
        "latest_events": [
            dict(item)
            for item in payload.get("latest_events") or []
            if isinstance(item, dict)
        ],
        "refs": {key: refs.get(key) for key in _EVIDENCE_REF_KEYS if refs.get(key) is not None},
    }


def _supervision_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    supervision = _mapping_copy(payload.get("supervision"))
    return {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")),
        "supervisor_tick_status": _non_empty_text(supervision.get("supervisor_tick_status")),
    }


def _current_runtime_redrive_route(payload: Mapping[str, Any]) -> bool:
    transition = _mapping_copy(payload.get("domain_transition"))
    return _non_empty_text(transition.get("decision_type")) in _RUNTIME_REDRIVE_DOMAIN_TRANSITIONS


def _projection_conditions(
    *,
    writer_state: str,
    user_next: str,
    reason: str,
    package_delivered: bool,
    actual_write_active: bool,
    meaningful_artifact_delta: bool,
    next_owner: str | None,
    why_not_progressing: str | None,
    user_action_required: bool,
    current_blockers: list[str],
    next_step: str,
    supervision: dict[str, Any],
    evidence: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        _condition(
            "macro_state_known",
            True,
            f"{writer_state}/{user_next}/{reason}",
            "用户可见状态来自 study_macro_state。",
        ),
        _condition(
            "package_delivered",
            package_delivered,
            "package_delivered" if package_delivered else "package_not_delivered",
            "投稿包已交付。" if package_delivered else "投稿包未交付。",
        ),
        _condition(
            "actual_write_active",
            actual_write_active,
            "writer_active" if actual_write_active else "writer_inactive",
            "系统有实际 writer/run 正在写入。" if actual_write_active else "当前没有实际写入。",
        ),
        _condition(
            "meaningful_artifact_delta",
            meaningful_artifact_delta,
            "artifact_delta_present" if meaningful_artifact_delta else "artifact_delta_absent",
            "已观察到论文产物级有效增量。" if meaningful_artifact_delta else "尚未观察到论文产物级有效增量。",
        ),
        _condition(
            "next_owner",
            bool(next_owner),
            "next_owner_present" if next_owner else "next_owner_missing",
            next_owner,
        ),
        _condition(
            "why_not_progressing",
            bool(why_not_progressing),
            "why_not_progressing_present" if why_not_progressing else "progressing_or_unknown",
            why_not_progressing,
        ),
        _condition(
            "blocked",
            bool(current_blockers),
            "blockers_present" if current_blockers else "no_current_blockers",
            current_blockers[0] if current_blockers else "当前没有新的卡点。",
        ),
        _condition(
            "next_action_known",
            bool(next_step),
            "next_action_present" if next_step else "next_action_missing",
            next_step,
        ),
        _condition(
            "evidence_available",
            bool(evidence.get("latest_events") or evidence.get("refs")),
            "evidence_refs_present" if evidence.get("latest_events") or evidence.get("refs") else "evidence_missing",
            "关键证据引用可用。" if evidence.get("latest_events") or evidence.get("refs") else "缺少关键证据引用。",
        ),
        _condition(
            "user_action_required",
            user_action_required,
            "user_action_present" if user_action_required else "user_action_absent",
            "当前需要用户补充或决策。" if user_action_required else "当前不需要用户补东西。",
        ),
        _condition(
            "runtime_supervised",
            bool(
                _non_empty_text(supervision.get("active_run_id"))
                or _non_empty_text(supervision.get("health_status"))
                or _non_empty_text(supervision.get("supervisor_tick_status"))
            ),
            "supervision_signal_present",
            _non_empty_text(supervision.get("health_status")) or _non_empty_text(supervision.get("active_run_id")),
        ),
    ]


def _condition(condition_type: str, status: bool, reason: str, message: str | None) -> dict[str, str]:
    return {
        "type": condition_type,
        "status": "true" if status else "false",
        "reason": reason,
        "message": message or "",
    }
