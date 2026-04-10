from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
_DEFAULT_EVENT_LIMIT = 6
_PAPER_STAGE_LABELS = {
    "write": "论文写作与结果收紧",
    "analysis-campaign": "补充分析与稳健性验证",
    "review": "独立审阅与质控",
    "finalize": "定稿与投稿收尾",
}
_DECISION_TYPE_LABELS = {
    "continue_same_line": "继续当前主线",
    "relaunch_branch": "重启当前分支",
    "reroute_study": "改换研究主线",
    "stop_loss": "止损停题",
    "promote_to_delivery": "推进到交付线",
}
_CONTROLLER_ACTION_LABELS = {
    "ensure_study_runtime": "继续托管推进当前研究运行",
    "ensure_study_runtime_relaunch_stopped": "显式重启已经停止的研究运行",
    "pause_runtime": "先暂停当前运行",
    "stop_runtime": "停止当前运行",
}
_REASON_LABELS = {
    "publishability_gate_blocked": "论文可发表性门控尚未放行。",
    "quest_completion_requested_before_publication_gate_clear": "运行时过早申请结题，论文门控仍要求继续自修。",
    "quest_parked_on_unchanged_finalize_state": "运行时停在本地 finalize 总结空转保护，MAS 将按控制面路由自动接管。",
    "startup_boundary_not_ready_for_resume": "运行前置条件尚未满足，系统不能直接续跑。",
    "runtime_reentry_not_ready_for_resume": "运行重入条件尚未满足，系统不能直接续跑。",
    "quest_already_running": "托管运行时已经处于自动推进状态。",
}
_WATCH_BLOCKER_LABELS = {
    "missing_post_main_publishability_gate": "论文可发表性门控尚未放行。",
    "medical_publication_surface_blocked": "论文叙事或方法/结果书写面仍有硬阻塞。",
}
_ACTION_LABELS = {
    "return_to_publishability_gate": "先补齐论文证据与叙事，再回到发表门控复核。",
    "controller_review_required": "需要控制面重新判断下一步。",
    "refresh_startup_hydration": "需要刷新运行前置上下文后再继续。",
    "human_confirmation_required": "等待医生或 PI 明确确认下一步。",
    "supervise_runtime_only": "当前以监督托管运行时为主，不直接接管执行。",
}
_SUPERVISOR_TICK_GAP_STATUSES = {"missing", "invalid", "stale"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _status_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if not isinstance(payload, dict):
            raise TypeError("study_progress status surface to_dict() must return a mapping")
        return dict(payload)
    raise TypeError("study_progress requires study_runtime_status to return a mapping-like payload")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _normalize_timestamp(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        return datetime.fromisoformat(raw).isoformat()
    except ValueError:
        return None


def _time_label(timestamp: str | None) -> str | None:
    normalized = _normalize_timestamp(timestamp)
    if normalized is None:
        return None
    instant = datetime.fromisoformat(normalized)
    suffix = "UTC" if instant.utcoffset() == timezone.utc.utcoffset(instant) else instant.strftime("UTC%z")
    return f"{instant.strftime('%Y-%m-%d %H:%M')} {suffix}".replace("UTC+0000", "UTC")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _candidate_path(value: object) -> Path | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return Path(text).expanduser().resolve()


def _humanize_token(token: object) -> str | None:
    text = _non_empty_text(token)
    if text is None:
        return None
    return text.replace("_", " ")


def _paper_stage_label(stage: object) -> str | None:
    text = _non_empty_text(stage)
    if text is None:
        return None
    return _PAPER_STAGE_LABELS.get(text, _humanize_token(text))


def _decision_type_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _DECISION_TYPE_LABELS.get(text, _humanize_token(text))


def _controller_action_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _CONTROLLER_ACTION_LABELS.get(text, _humanize_token(text))


def _reason_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _REASON_LABELS.get(text, _humanize_token(text))


def _action_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _ACTION_LABELS.get(text, _humanize_token(text))


def _watch_blocker_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _WATCH_BLOCKER_LABELS.get(text, _humanize_token(text))


def _append_unique(items: list[str], message: str | None) -> None:
    if not message:
        return
    if message not in items:
        items.append(message)


def _latest_runtime_watch_report(quest_root: Path | None) -> Path | None:
    if quest_root is None:
        return None
    report_root = quest_root / "artifacts" / "reports" / "runtime_watch"
    if not report_root.exists():
        return None
    latest_path = report_root / "latest.json"
    if latest_path.exists():
        return latest_path
    candidates = [
        path
        for path in report_root.glob("*.json")
        if path.name not in {"state.json", "latest.json"}
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


def _details_projection_payload(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    wrapper = _read_json_object(path)
    if wrapper is None:
        return None
    payload = wrapper.get("payload")
    if not isinstance(payload, dict):
        return None
    return payload


def _event(
    *,
    timestamp: str | None,
    category: str,
    title: str,
    summary: str,
    source: str,
    artifact_path: Path | None,
) -> dict[str, Any] | None:
    normalized = _normalize_timestamp(timestamp)
    if normalized is None:
        return None
    return {
        "timestamp": normalized,
        "time_label": _time_label(normalized),
        "category": category,
        "title": title,
        "summary": summary,
        "source": source,
        "artifact_path": str(artifact_path) if artifact_path is not None else None,
    }


def _current_stage(
    *,
    status: dict[str, Any],
    needs_physician_decision: bool,
    publication_supervisor_state: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
) -> str:
    quest_status = _non_empty_text(status.get("quest_status"))
    decision = _non_empty_text(status.get("decision"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if quest_status == "completed" or decision == "completed":
        return "study_completed"
    if runtime_health_status == "recovering":
        return "managed_runtime_recovering"
    if runtime_health_status == "degraded":
        return "managed_runtime_degraded"
    if runtime_health_status == "escalated":
        return "managed_runtime_escalated"
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        return "managed_runtime_supervision_gap"
    if needs_physician_decision:
        return "waiting_physician_decision"
    if isinstance(publication_supervisor_state, dict) and _non_empty_text(
        publication_supervisor_state.get("supervisor_phase")
    ):
        return "publication_supervision"
    if bool((execution_owner_guard or {}).get("supervisor_only")) or bool(
        (autonomous_runtime_notice or {}).get("required")
    ):
        return "managed_runtime_active"
    if decision == "blocked":
        return "runtime_blocked"
    return "runtime_preflight"


def _paper_stage_summary(
    *,
    paper_stage: str | None,
    publication_supervisor_state: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
) -> str:
    parts: list[str] = []
    stage_label = _paper_stage_label(paper_stage)
    if stage_label is not None:
        parts.append(f"论文当前建议推进到“{stage_label}”阶段。")
    controller_stage_note = _non_empty_text((publication_supervisor_state or {}).get("controller_stage_note"))
    if controller_stage_note is not None:
        parts.append(controller_stage_note)
    if bool((publication_supervisor_state or {}).get("bundle_tasks_downstream_only")):
        parts.append("submission bundle 仍属于后续步骤，当前不会抢跑打包。")
    verdict_summary = _non_empty_text(((publication_eval_payload or {}).get("verdict") or {}).get("summary"))
    if verdict_summary is not None:
        parts.append(f"当前发表判断：{verdict_summary}")
    if not parts:
        parts.append("论文主线仍在收敛中，当前尚未形成明确的下一篇章。")
    return " ".join(parts)


def _stage_summary(
    *,
    current_stage: str,
    publication_supervisor_state: dict[str, Any],
    latest_progress_message: str | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
) -> str:
    if current_stage == "study_completed":
        return "研究主线已经进入结题/交付阶段，系统不会继续自动实验。"
    if current_stage in {
        "managed_runtime_recovering",
        "managed_runtime_degraded",
        "managed_runtime_escalated",
    }:
        summary = (
            _non_empty_text((runtime_supervision_payload or {}).get("clinician_update"))
            or _non_empty_text((runtime_supervision_payload or {}).get("summary"))
            or "托管运行时当前处在健康监管状态。"
        )
        next_action_summary = _non_empty_text((runtime_supervision_payload or {}).get("next_action_summary"))
        if current_stage == "managed_runtime_escalated" and next_action_summary is not None:
            if "人工介入" not in summary:
                summary = f"{summary} 当前需要人工介入。"
            return f"{summary} {next_action_summary}"
        return summary
    if current_stage == "managed_runtime_supervision_gap":
        summary = (
            _non_empty_text((supervisor_tick_audit or {}).get("summary"))
            or "MedAutoScience 外环监管心跳异常，当前不能把托管运行视为被持续监管。"
        )
        next_action_summary = _non_empty_text((supervisor_tick_audit or {}).get("next_action_summary"))
        if next_action_summary is not None:
            return f"{summary} {next_action_summary}"
        return summary
    if current_stage == "waiting_physician_decision":
        summary = "系统已经把研究推进到需要医生/PI 明确确认的节点，目前不会越权自动继续。"
        if latest_progress_message:
            summary += f" 最近一次可见推进是：{latest_progress_message}"
        return summary
    if current_stage == "publication_supervision":
        note = _non_empty_text((publication_supervisor_state or {}).get("controller_stage_note"))
        return note or "论文主线当前停在发表监管阶段，系统会先守住可发表性与交付门控。"
    if current_stage == "managed_runtime_active":
        summary = "托管运行时正在自动推进研究，前台当前应以监督为主。"
        if latest_progress_message:
            summary += f" 最近一次可见推进是：{latest_progress_message}"
        return summary
    if current_stage == "runtime_blocked":
        return "自动推进已被硬阻断，需要先补齐前置条件后才能继续。"
    return "研究运行仍处在准备或轻量评估阶段。"


def _interaction_arbitration_action(interaction_arbitration: dict[str, Any] | None) -> str | None:
    return _non_empty_text((interaction_arbitration or {}).get("action"))


def _supervisor_tick_gap_present(supervisor_tick_audit: dict[str, Any]) -> bool:
    if not bool((supervisor_tick_audit or {}).get("required")):
        return False
    return _non_empty_text((supervisor_tick_audit or {}).get("status")) in _SUPERVISOR_TICK_GAP_STATUSES


def _needs_physician_decision(
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> bool:
    controller_requires = bool((controller_decision_payload or {}).get("requires_human_confirmation"))
    if controller_requires:
        return True
    arbitration_action = _interaction_arbitration_action(interaction_arbitration)
    if arbitration_action == "resume":
        return False
    pending_requires = bool(
        (pending_user_interaction or {}).get("guidance_requires_user_decision")
        or (
            bool((pending_user_interaction or {}).get("blocking"))
            and bool((pending_user_interaction or {}).get("expects_reply"))
        )
    )
    if arbitration_action == "block":
        return bool((interaction_arbitration or {}).get("requires_user_input")) or pending_requires
    return pending_requires


def _physician_decision_summary(
    *,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> str | None:
    if bool((controller_decision_payload or {}).get("requires_human_confirmation")):
        return "控制面已经形成正式下一步建议，但该动作需要医生/PI 先确认，系统会停在监管态等待。"
    if _interaction_arbitration_action(interaction_arbitration) == "resume":
        return None
    interaction_summary = _non_empty_text((pending_user_interaction or {}).get("summary"))
    if interaction_summary is not None:
        return interaction_summary
    interaction_message = _non_empty_text((pending_user_interaction or {}).get("message"))
    if interaction_message is not None:
        return interaction_message
    return None


def _next_system_action(
    *,
    needs_physician_decision: bool,
    controller_decision_payload: dict[str, Any] | None,
    publication_supervisor_state: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    status: dict[str, Any],
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
) -> str:
    supervisor_tick_next_action = _non_empty_text((supervisor_tick_audit or {}).get("next_action_summary"))
    if _supervisor_tick_gap_present(supervisor_tick_audit) and supervisor_tick_next_action is not None:
        return supervisor_tick_next_action
    runtime_next_action = _non_empty_text((runtime_supervision_payload or {}).get("next_action_summary"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if runtime_health_status in {"recovering", "degraded", "escalated"} and runtime_next_action is not None:
        return runtime_next_action
    controller_actions = list((controller_decision_payload or {}).get("controller_actions") or [])
    first_action = controller_actions[0] if controller_actions else {}
    action_type = _controller_action_label(first_action.get("action_type"))
    if needs_physician_decision:
        if action_type is not None:
            return f"等待医生/PI 确认后，再{action_type}。"
        return "等待医生/PI 明确确认后，再继续下一步托管推进。"
    publication_action = _action_label((publication_supervisor_state or {}).get("current_required_action"))
    if publication_action is not None:
        return publication_action
    guard_action = _action_label((execution_owner_guard or {}).get("current_required_action"))
    if guard_action is not None:
        return guard_action
    decision = _non_empty_text(status.get("decision"))
    if decision in {"create_and_start", "resume", "relaunch_stopped"}:
        return "系统会继续托管推进当前研究运行。"
    if decision == "blocked":
        reason = _reason_label(status.get("reason"))
        if reason is not None:
            return reason
    return "继续轮询研究状态，并把新的阶段变化投影到前台。"


def _current_blockers(
    *,
    publication_eval_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_escalation_payload: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        _append_unique(
            blockers,
            _non_empty_text((supervisor_tick_audit or {}).get("summary")),
        )
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if runtime_health_status in {"degraded", "escalated"}:
        _append_unique(
            blockers,
            _non_empty_text((runtime_supervision_payload or {}).get("summary"))
            or _non_empty_text((runtime_supervision_payload or {}).get("clinician_update")),
        )
    if bool((controller_decision_payload or {}).get("requires_human_confirmation")):
        _append_unique(blockers, "当前控制面决策需要医生/PI 确认，系统不会自动越权继续。")
    if _interaction_arbitration_action(interaction_arbitration) != "resume" and bool(
        (pending_user_interaction or {}).get("blocking")
    ):
        _append_unique(
            blockers,
            _non_empty_text((pending_user_interaction or {}).get("summary"))
            or _non_empty_text((pending_user_interaction or {}).get("message")),
        )
    for gap in (publication_eval_payload or {}).get("gaps") or []:
        if isinstance(gap, dict):
            _append_unique(blockers, _non_empty_text(gap.get("summary")))
    controller_payload = ((runtime_watch_payload or {}).get("controllers") or {}).get("publication_gate")
    if isinstance(controller_payload, dict):
        for blocker in controller_payload.get("blockers") or []:
            _append_unique(blockers, _watch_blocker_label(blocker))
        _append_unique(blockers, _non_empty_text(controller_payload.get("controller_stage_note")))
    _append_unique(blockers, _reason_label((runtime_escalation_payload or {}).get("reason")))
    return blockers


def _latest_events(
    *,
    launch_report_payload: dict[str, Any] | None,
    launch_report_path: Path,
    runtime_supervision_payload: dict[str, Any] | None,
    runtime_supervision_path: Path | None,
    runtime_escalation_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    publication_eval_payload: dict[str, Any] | None,
    publication_eval_path: Path,
    controller_decision_payload: dict[str, Any] | None,
    controller_decision_path: Path,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_watch_path: Path | None,
    details_projection_payload: dict[str, Any] | None,
    details_projection_path: Path | None,
    bash_summary_payload: dict[str, Any] | None,
    bash_summary_path: Path | None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if runtime_supervision_payload is not None:
        runtime_health_status = _non_empty_text(runtime_supervision_payload.get("health_status")) or "runtime"
        runtime_summary = (
            _non_empty_text(runtime_supervision_payload.get("summary"))
            or _non_empty_text(runtime_supervision_payload.get("clinician_update"))
            or "运行健康状态已刷新。"
        )
        item = _event(
            timestamp=_non_empty_text(runtime_supervision_payload.get("recorded_at")),
            category="runtime_supervision",
            title=f"托管运行监管状态更新（{runtime_health_status}）",
            summary=runtime_summary,
            source="runtime_supervision",
            artifact_path=runtime_supervision_path,
        )
        if item is not None:
            events.append(item)
    latest_session = (bash_summary_payload or {}).get("latest_session")
    if isinstance(latest_session, dict):
        last_progress = latest_session.get("last_progress")
        if isinstance(last_progress, dict):
            summary = _non_empty_text(last_progress.get("message")) or _non_empty_text(last_progress.get("step"))
            if summary is not None:
                item = _event(
                    timestamp=_non_empty_text(last_progress.get("ts")) or _non_empty_text(latest_session.get("updated_at")),
                    category="runtime_progress",
                    title="托管运行时完成一段推进",
                    summary=summary,
                    source="bash_summary",
                    artifact_path=bash_summary_path,
                )
                if item is not None:
                    events.append(item)
    if details_projection_payload is not None:
        status_line = _non_empty_text(((details_projection_payload.get("summary") or {}).get("status_line")))
        if status_line is not None:
            item = _event(
                timestamp=_non_empty_text(((details_projection_payload.get("summary") or {}).get("updated_at")))
                or _non_empty_text((details_projection_payload or {}).get("generated_at")),
                category="paper_projection",
                title="论文进度投影刷新",
                summary=status_line,
                source="details_projection",
                artifact_path=details_projection_path,
            )
            if item is not None:
                events.append(item)
    if controller_decision_payload is not None:
        decision_type = _decision_type_label(controller_decision_payload.get("decision_type")) or "形成控制面决定"
        reason = _non_empty_text(controller_decision_payload.get("reason"))
        summary = f"控制面正式决定：{decision_type}。"
        if reason is not None:
            summary += f" 原因：{reason}"
        item = _event(
            timestamp=_non_empty_text(controller_decision_payload.get("emitted_at")),
            category="controller_decision",
            title="控制面写入下一步决定",
            summary=summary,
            source="controller_decision",
            artifact_path=controller_decision_path,
        )
        if item is not None:
            events.append(item)
    if publication_eval_payload is not None:
        verdict = (publication_eval_payload.get("verdict") or {}) if isinstance(publication_eval_payload, dict) else {}
        verdict_summary = _non_empty_text(verdict.get("summary")) or "发表评估已更新。"
        item = _event(
            timestamp=_non_empty_text(publication_eval_payload.get("emitted_at")),
            category="publication_eval",
            title="发表可行性评估更新",
            summary=verdict_summary,
            source="publication_eval",
            artifact_path=publication_eval_path,
        )
        if item is not None:
            events.append(item)
    if runtime_watch_payload is not None:
        publication_gate = ((runtime_watch_payload.get("controllers") or {}).get("publication_gate"))
        watch_summary = "系统完成一次研究运行巡检。"
        if isinstance(publication_gate, dict):
            controller_note = _non_empty_text(publication_gate.get("controller_stage_note"))
            if controller_note is not None:
                watch_summary = controller_note
            else:
                blockers = [
                    _watch_blocker_label(item)
                    for item in (publication_gate.get("blockers") or [])
                ]
                blockers = [item for item in blockers if item]
                if blockers:
                    watch_summary = blockers[0]
        item = _event(
            timestamp=_non_empty_text(runtime_watch_payload.get("scanned_at")),
            category="runtime_watch",
            title="运行时巡检完成",
            summary=watch_summary,
            source="runtime_watch",
            artifact_path=runtime_watch_path,
        )
        if item is not None:
            events.append(item)
    if runtime_escalation_payload is not None:
        summary = _reason_label(runtime_escalation_payload.get("reason")) or "运行时已把问题升级回控制面。"
        item = _event(
            timestamp=_non_empty_text(runtime_escalation_payload.get("emitted_at")),
            category="runtime_escalation",
            title="运行时发出升级信号",
            summary=summary,
            source="runtime_escalation",
            artifact_path=runtime_escalation_path,
        )
        if item is not None:
            events.append(item)
    if launch_report_payload is not None:
        decision = _humanize_token(launch_report_payload.get("decision")) or "状态回写"
        reason = _reason_label(launch_report_payload.get("reason"))
        summary = f"最近一次运行状态回写结论：{decision}。"
        if reason is not None:
            summary += f" {reason}"
        item = _event(
            timestamp=_non_empty_text(launch_report_payload.get("recorded_at")),
            category="launch_report",
            title="研究运行状态回写",
            summary=summary,
            source="launch_report",
            artifact_path=launch_report_path,
        )
        if item is not None:
            events.append(item)
    events.sort(key=lambda item: item["timestamp"], reverse=True)
    return events[:_DEFAULT_EVENT_LIMIT]


def read_study_progress(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status = _status_payload(
        study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            entry_mode=entry_mode,
        )
    )
    quest_id = _non_empty_text(status.get("quest_id"))
    quest_root = _candidate_path(status.get("quest_root"))
    launch_report_path = (
        _candidate_path(status.get("launch_report_path"))
        or resolved_study_root / "artifacts" / "runtime" / "last_launch_report.json"
    )
    publication_eval_path = resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
    runtime_escalation_path = _candidate_path(((status.get("runtime_escalation_ref") or {}).get("artifact_path")))
    if runtime_escalation_path is None and quest_root is not None:
        runtime_escalation_path = (
            quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
        )
    runtime_watch_path = _latest_runtime_watch_report(quest_root)
    runtime_supervision_path = resolved_study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    bash_summary_path = quest_root / ".ds" / "bash_exec" / "summary.json" if quest_root is not None else None
    details_projection_path = quest_root / ".ds" / "projections" / "details.v1.json" if quest_root is not None else None

    launch_report_payload = _read_json_object(launch_report_path)
    publication_eval_payload = _read_json_object(publication_eval_path)
    controller_decision_payload = _read_json_object(controller_decision_path)
    runtime_supervision_payload = _read_json_object(runtime_supervision_path)
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if runtime_escalation_path is not None and (
        status.get("runtime_escalation_ref") is not None or runtime_health_status in {"degraded", "escalated"}
    ):
        runtime_escalation_payload = _read_json_object(runtime_escalation_path)
    else:
        runtime_escalation_payload = None
    runtime_watch_payload = _read_json_object(runtime_watch_path) if runtime_watch_path is not None else None
    bash_summary_payload = _read_json_object(bash_summary_path) if bash_summary_path is not None else None
    details_projection_wrapper = _read_json_object(details_projection_path) if details_projection_path is not None else None
    details_projection_payload = _details_projection_payload(details_projection_path)

    publication_supervisor_state = (
        dict(status.get("publication_supervisor_state") or {})
        if isinstance(status.get("publication_supervisor_state"), dict)
        else {}
    )
    autonomous_runtime_notice = (
        dict(status.get("autonomous_runtime_notice") or {})
        if isinstance(status.get("autonomous_runtime_notice"), dict)
        else {}
    )
    execution_owner_guard = (
        dict(status.get("execution_owner_guard") or {})
        if isinstance(status.get("execution_owner_guard"), dict)
        else {}
    )
    pending_user_interaction = (
        dict(status.get("pending_user_interaction") or {})
        if isinstance(status.get("pending_user_interaction"), dict)
        else {}
    )
    interaction_arbitration = (
        dict(status.get("interaction_arbitration") or {})
        if isinstance(status.get("interaction_arbitration"), dict)
        else {}
    )
    supervisor_tick_audit = (
        dict(status.get("supervisor_tick_audit") or {})
        if isinstance(status.get("supervisor_tick_audit"), dict)
        else {}
    )
    continuation_state = (
        dict(status.get("continuation_state") or {})
        if isinstance(status.get("continuation_state"), dict)
        else {}
    )
    paper_contract_health = (
        dict((details_projection_payload or {}).get("paper_contract_health") or {})
        if isinstance((details_projection_payload or {}).get("paper_contract_health"), dict)
        else {}
    )
    paper_stage = (
        _non_empty_text(paper_contract_health.get("recommended_next_stage"))
        or _non_empty_text(publication_supervisor_state.get("supervisor_phase"))
    )
    latest_progress_message = None
    latest_session = ((bash_summary_payload or {}).get("latest_session"))
    if isinstance(latest_session, dict) and isinstance(latest_session.get("last_progress"), dict):
        latest_progress_message = _non_empty_text((latest_session.get("last_progress") or {}).get("message"))
    if latest_progress_message is None and isinstance(details_projection_wrapper, dict):
        latest_progress_message = _non_empty_text(
            (((details_projection_payload or {}).get("summary") or {}).get("status_line"))
        )

    needs_physician_decision = _needs_physician_decision(
        controller_decision_payload,
        pending_user_interaction,
        interaction_arbitration,
    )
    current_stage = _current_stage(
        status=status,
        needs_physician_decision=needs_physician_decision,
        publication_supervisor_state=publication_supervisor_state,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root) if quest_root is not None else None,
        "current_stage": current_stage,
        "current_stage_summary": _stage_summary(
            current_stage=current_stage,
            publication_supervisor_state=publication_supervisor_state,
            latest_progress_message=latest_progress_message,
            runtime_supervision_payload=runtime_supervision_payload,
            supervisor_tick_audit=supervisor_tick_audit,
        ),
        "paper_stage": paper_stage,
        "paper_stage_summary": _paper_stage_summary(
            paper_stage=paper_stage,
            publication_supervisor_state=publication_supervisor_state,
            publication_eval_payload=publication_eval_payload,
        ),
        "latest_events": _latest_events(
            launch_report_payload=launch_report_payload,
            launch_report_path=launch_report_path,
            runtime_supervision_payload=runtime_supervision_payload,
            runtime_supervision_path=runtime_supervision_path if runtime_supervision_payload is not None else None,
            runtime_escalation_payload=runtime_escalation_payload,
            runtime_escalation_path=runtime_escalation_path,
            publication_eval_payload=publication_eval_payload,
            publication_eval_path=publication_eval_path,
            controller_decision_payload=controller_decision_payload,
            controller_decision_path=controller_decision_path,
            runtime_watch_payload=runtime_watch_payload,
            runtime_watch_path=runtime_watch_path,
            details_projection_payload=details_projection_payload,
            details_projection_path=details_projection_path,
            bash_summary_payload=bash_summary_payload,
            bash_summary_path=bash_summary_path,
        ),
        "current_blockers": _current_blockers(
            publication_eval_payload=publication_eval_payload,
            runtime_watch_payload=runtime_watch_payload,
            runtime_escalation_payload=runtime_escalation_payload,
            controller_decision_payload=controller_decision_payload,
            pending_user_interaction=pending_user_interaction,
            interaction_arbitration=interaction_arbitration,
            runtime_supervision_payload=runtime_supervision_payload,
            supervisor_tick_audit=supervisor_tick_audit,
        ),
        "next_system_action": _next_system_action(
            needs_physician_decision=needs_physician_decision,
            controller_decision_payload=controller_decision_payload,
            publication_supervisor_state=publication_supervisor_state,
            execution_owner_guard=execution_owner_guard,
            status=status,
            runtime_supervision_payload=runtime_supervision_payload,
            supervisor_tick_audit=supervisor_tick_audit,
        ),
        "needs_physician_decision": needs_physician_decision,
        "physician_decision_summary": _physician_decision_summary(
            controller_decision_payload=controller_decision_payload,
            pending_user_interaction=pending_user_interaction,
            interaction_arbitration=interaction_arbitration,
        ),
        "runtime_decision": _non_empty_text(status.get("decision")),
        "runtime_reason": _non_empty_text(status.get("reason")),
        "continuation_state": continuation_state or None,
        "interaction_arbitration": interaction_arbitration or None,
        "supervision": {
            "browser_url": _non_empty_text(autonomous_runtime_notice.get("browser_url")),
            "quest_session_api_url": _non_empty_text(autonomous_runtime_notice.get("quest_session_api_url")),
            "active_run_id": _non_empty_text(execution_owner_guard.get("active_run_id"))
            or _non_empty_text(autonomous_runtime_notice.get("active_run_id")),
            "health_status": runtime_health_status,
            "supervisor_tick_status": _non_empty_text(supervisor_tick_audit.get("status")),
            "supervisor_tick_required": bool(supervisor_tick_audit.get("required")),
            "supervisor_tick_summary": _non_empty_text(supervisor_tick_audit.get("summary")),
            "supervisor_tick_latest_recorded_at": _non_empty_text(supervisor_tick_audit.get("latest_recorded_at")),
            "launch_report_path": str(launch_report_path),
        },
        "refs": {
            "launch_report_path": str(launch_report_path),
            "publication_eval_path": str(publication_eval_path),
            "controller_decision_path": str(controller_decision_path),
            "runtime_supervision_path": str(runtime_supervision_path) if runtime_supervision_payload is not None else None,
            "runtime_escalation_path": str(runtime_escalation_path) if runtime_escalation_path is not None else None,
            "runtime_watch_report_path": str(runtime_watch_path) if runtime_watch_path is not None else None,
            "bash_summary_path": str(bash_summary_path) if bash_summary_path is not None else None,
            "details_projection_path": str(details_projection_path) if details_projection_path is not None else None,
        },
    }
    return payload


def render_study_progress_markdown(payload: dict[str, Any]) -> str:
    latest_events = [dict(item) for item in (payload.get("latest_events") or []) if isinstance(item, dict)]
    blockers = [str(item) for item in (payload.get("current_blockers") or []) if str(item).strip()]
    continuation_state = dict(payload.get("continuation_state") or {})
    runtime_decision = str(payload.get("runtime_decision") or "unknown").strip()
    runtime_reason = _reason_label(payload.get("runtime_reason")) or str(payload.get("runtime_reason") or "").strip()
    runtime_health = str(((payload.get("supervision") or {}).get("health_status") or "unknown")).strip()
    supervisor_tick_status = str(((payload.get("supervision") or {}).get("supervisor_tick_status") or "")).strip()
    lines = [
        "# 研究进度",
        "",
        f"- study_id: `{str(payload.get('study_id') or '')}`",
        f"- quest_id: `{str(payload.get('quest_id') or 'none')}`",
        f"- 当前阶段: `{str(payload.get('current_stage') or 'unknown')}`",
        f"- 阶段摘要: {str(payload.get('current_stage_summary') or '').strip()}",
        "",
        "## 论文推进",
        "",
        f"- 论文阶段: `{str(payload.get('paper_stage') or 'unknown')}`",
        f"- 论文摘要: {str(payload.get('paper_stage_summary') or '').strip()}",
        "",
        "## 运行监管",
        "",
        f"- 运行健康: `{runtime_health or 'unknown'}`",
        f"- MAS 决策: `{runtime_decision or 'unknown'}`",
    ]
    if supervisor_tick_status:
        lines.append(f"- MAS 监管心跳: `{supervisor_tick_status}`")
    if runtime_reason:
        lines.append(f"- 决策原因: {runtime_reason}")
    continuation_reason = str(continuation_state.get("continuation_reason") or "").strip()
    if continuation_reason:
        lines.append(f"- continuation_reason: `{continuation_reason}`")
    lines.extend(
        [
            "",
        "## 当前阻塞",
        "",
        ]
    )
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 当前没有额外阻塞记录。")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            f"- {str(payload.get('next_system_action') or '').strip()}",
        ]
    )
    if payload.get("physician_decision_summary"):
        lines.extend(
            [
                "",
                "## 医生判断",
                "",
                f"- {str(payload.get('physician_decision_summary') or '').strip()}",
            ]
        )
    lines.extend(["", "## 最近进展", ""])
    if latest_events:
        for item in latest_events:
            time_label = str(item.get("time_label") or item.get("timestamp") or "").strip()
            summary = str(item.get("summary") or "").strip()
            lines.append(f"- {time_label}: {summary}")
    else:
        lines.append("- 目前没有可用的阶段事件。")
    supervision = dict(payload.get("supervision") or {})
    lines.extend(["", "## 监督入口", ""])
    for key in ("browser_url", "quest_session_api_url", "active_run_id", "launch_report_path"):
        value = str(supervision.get(key) or "").strip()
        if value:
            lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"
