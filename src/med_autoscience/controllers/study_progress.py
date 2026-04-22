from __future__ import annotations

import json
import shlex
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping

from opl_harness_shared.status_narration import (
    PROGRESS_ANSWER_CHECKLIST,
    build_status_narration_contract,
    build_status_narration_human_view,
)

from med_autoscience.controller_confirmation_summary import (
    materialize_controller_confirmation_summary,
    read_controller_confirmation_summary,
    stable_controller_confirmation_summary_path,
)
from med_autoscience.controller_summary import read_controller_summary, stable_controller_summary_path
from med_autoscience.controllers import gate_clearing_batch, study_runtime_router
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.evaluation_summary import (
    materialize_evaluation_summary_artifacts,
    read_evaluation_summary,
    stable_evaluation_summary_path,
    stable_promotion_gate_path,
)
from med_autoscience.human_gate_policy import controller_human_gate_allowed
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_status_summary import (
    build_runtime_status_summary,
    materialize_runtime_status_summary,
)
from med_autoscience.study_charter import stable_study_charter_path
from med_autoscience.study_manual_finish import resolve_effective_study_manual_finish_contract
from med_autoscience.study_task_intake import read_latest_task_intake, summarize_task_intake


SCHEMA_VERSION = 1
_DEFAULT_EVENT_LIMIT = 6
_PAPER_STAGE_LABELS = {
    "write": "论文写作与结果收紧",
    "analysis-campaign": "补充分析与稳健性验证",
    "review": "独立审阅与质控",
    "finalize": "定稿与投稿收尾",
    "scientific_anchor_missing": "科学锚点仍缺失",
    "write_stage_ready": "论文写作阶段已放行",
    "publishability_gate_blocked": "论文可发表性门控未放行",
    "bundle_stage_blocked": "投稿打包阶段存在硬阻塞",
    "bundle_stage_ready": "投稿打包阶段已放行",
}
_CURRENT_STAGE_LABELS = {
    "study_completed": "研究已进入收尾/交付",
    "manual_finishing": "人工收尾与兼容保护",
    "managed_runtime_recovering": "托管运行恢复中",
    "managed_runtime_degraded": "托管运行健康降级",
    "managed_runtime_escalated": "托管运行已升级告警",
    "managed_runtime_supervision_gap": "Hermes-hosted 托管监管存在缺口",
    "waiting_physician_decision": "等待医生或 PI 判断",
    "publication_supervision": "论文可发表性监管",
    "managed_runtime_active": "托管运行正在推进",
    "runtime_blocked": "自动推进被阻断",
    "runtime_preflight": "研究准备或预检阶段",
}
_DECISION_TYPE_LABELS = {
    "continue_same_line": "继续当前主线",
    "bounded_analysis": "有限补充分析",
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
    "quest_waiting_for_submission_metadata": "浅层投稿包已经交付，当前只差作者、单位、伦理、基金和声明等人工前置信息；系统已停车，等待显式唤醒。",
    "quest_drifting_into_write_without_gate_approval": "运行时已经漂进写作/定稿，但发表门控尚未放行，MAS 正在把它拉回论文门控主线。",
    "quest_stale_decision_after_write_stage_ready": "论文写作阶段已经放行，但运行时仍停在旧 decision，MAS 正在把它切回写作主线。",
    "quest_stopped_by_controller_guard": "运行时被 MAS 纠偏控制器短暂停下，MAS 将自动继续修复当前论文硬阻塞。",
    "quest_stopped_requires_explicit_rerun": "当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。",
    "study_completion_contract_not_ready": "study-level 完成声明已存在，但 final submission 证据还未补齐，当前不能按完成态收口。",
    "startup_boundary_not_ready_for_resume": "运行前置条件尚未满足，系统不能直接续跑。",
    "runtime_reentry_not_ready_for_resume": "运行重入条件尚未满足，系统不能直接续跑。",
    "quest_already_running": "托管运行时已经处于自动推进状态。",
}
_WATCH_BLOCKER_LABELS = {
    "active_run_drifting_into_write_without_gate_approval": "当前 live run 已经漂进写作或定稿，但发表门控仍未放行，必须先拉回论文门控主线。",
    "missing_post_main_publishability_gate": "论文可发表性门控尚未放行。",
    "medical_publication_surface_blocked": "论文叙事或方法/结果书写面仍有硬阻塞。",
    "registry_contract_mismatch": "论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。",
    "claim_evidence_map_missing_or_incomplete": "关键 claim-to-evidence 对照仍不完整。",
    "figure_loop_budget_exceeded": "图表推进陷入重复打磨循环，当前 run 应被拉回主线。",
    "figure_reopened_after_resolution": "已经收住的图表又被重新打开，当前 run 存在质量回退风险。",
    "accepted_figure_reopened": "已接受的图表又被重新打开，当前 run 存在质量回退风险。",
    "references_below_floor_during_figure_loop": "图表循环期间参考文献数量低于下限，当前稿件质量不达标。",
    "reference_gaps_present": "关键参考文献仍有缺口。",
    "missing_reporting_guideline_checklist": "报告规范核对表仍未补齐。",
    "forbidden_manuscript_terms_present": "当前稿件仍含不允许的术语表达，需要清理。",
    "figure_catalog_missing_or_incomplete": "关键图表目录仍不完整。",
    "table_catalog_missing_or_incomplete": "关键表格目录仍不完整。",
    "required_display_catalog_coverage_incomplete": "论文关键展示面覆盖仍不完整。",
    "public_evidence_decisions_missing_or_incomplete": "公开数据进入论文前缺少明确的 earned/drop 决策记录。",
    "paper_facing_public_data_without_earned_evidence": "公开数据已经写入论文面，但还没有真正 earned 的结果支撑。",
    "ama_pdf_defaults_missing": "AMA 稿件导出默认配置仍未补齐。",
    "results_narrative_map_missing_or_incomplete": "结果叙事映射仍不完整。",
    "methods_section_structure_missing_or_incomplete": "方法学章节结构仍不完整。",
    "figure_semantics_manifest_missing_or_incomplete": "图表语义清单仍不完整。",
    "derived_analysis_manifest_missing_or_incomplete": "衍生分析清单仍不完整。",
    "submission_checklist_contains_unclassified_blocking_items": "投稿检查清单里仍有未归类的硬阻塞。",
}
_BLOCKER_LABELS = {
    "active_run_drifting_into_write_without_gate_approval": "当前 live run 已经漂进写作或定稿，但发表门控仍未放行，必须先拉回论文门控主线。",
    "missing_submission_minimal": "缺少最小投稿包导出。",
    "submission_grade_active_figure_floor_unmet": "活跃主稿图数量仍低于投稿级下限，当前图证不足以支撑投稿级稿件。",
    "registry_contract_mismatch": "论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。",
    "stale_study_delivery_mirror": "study 目录里的投稿包镜像已经过期，仍停在旧版本，不能当作当前包。",
    "medical_publication_surface_blocked": "论文叙事或方法/结果书写面仍有硬阻塞。",
    "forbidden_manuscript_terminology": "当前稿件仍含不允许的术语表达，需要清理。",
    "public_evidence_decisions_missing_or_incomplete": "公开数据进入论文前缺少明确的 earned/drop 决策记录。",
    "paper_facing_public_data_without_earned_evidence": "公开数据已经写入论文面，但还没有真正 earned 的结果支撑。",
    "submission_checklist_contains_unclassified_blocking_items": "投稿检查清单里仍有未归类的硬阻塞。",
}
_ACTION_LABELS = {
    "return_to_publishability_gate": "先补齐论文证据与叙事，再回到发表门控复核。",
    "continue_write_stage": "继续当前论文写作阶段。",
    "continue_bundle_stage": "继续当前投稿打包阶段。",
    "complete_bundle_stage": "完成当前投稿打包阶段。",
    "controller_review_required": "需要控制面重新判断下一步。",
    "refresh_startup_hydration": "需要刷新运行前置上下文后再继续。",
    "human_confirmation_required": "等待医生或 PI 明确确认下一步。",
    "supervise_runtime_only": "当前以监督托管运行时为主，不直接接管执行。",
}
_ROUTE_REPAIR_ACTION_TYPES = {"continue_same_line", "route_back_same_line", "bounded_analysis"}
_ROUTE_REPAIR_MODE_LABELS = {
    "same_line_route_back": "同线质量修复",
    "bounded_analysis": "有限补充分析",
}
_RUNTIME_DECISION_LABELS = {
    "noop": "无需额外动作",
    "blocked": "当前被阻断",
    "resume": "继续托管续跑",
    "relaunch_stopped": "重新拉起已停止运行",
    "create_and_start": "创建并启动新运行",
    "create_only": "仅创建研究运行",
    "completed": "研究运行已完成",
    "lightweight": "仅做轻量监管",
}
_RUNTIME_HEALTH_LABELS = {
    "live": "运行健康在线",
    "recovering": "恢复中",
    "degraded": "健康降级",
    "escalated": "已升级告警",
    "unknown": "状态未知",
    "none": "未检测到在线 worker",
}
_SUPERVISOR_TICK_STATUS_LABELS = {
    "fresh": "监管心跳新鲜",
    "stale": "监管心跳已陈旧",
    "missing": "监管心跳缺失",
    "invalid": "监管心跳记录无效",
    "not_required": "当前不要求监管心跳",
}
_PROGRESS_FRESHNESS_STATUS_LABELS = {
    "fresh": "研究推进信号新鲜",
    "stale": "研究推进信号已陈旧",
    "missing": "研究推进信号缺失",
    "not_required": "当前不要求新的自动推进信号",
}
_INTERVENTION_SEVERITY_LABELS = {
    "critical": "高优先级",
    "warning": "需要尽快处理",
    "handoff": "等待人工判断",
    "observe": "继续监督",
}
_RECOVERY_ACTION_MODE_LABELS = {
    "refresh_supervision": "优先恢复 Hermes-hosted 托管监管",
    "continue_or_relaunch": "继续或重新拉起当前 study",
    "inspect_progress": "先读取当前进度与阻塞",
    "human_decision_review": "等待医生或 PI 判断",
    "maintain_compatibility_guard": "保持人工收尾兼容保护",
    "monitor_only": "继续监督当前 study",
}
_OPERATOR_STATUS_HANDLING_LABELS = {
    "runtime_supervision_recovering": "监管恢复中",
    "runtime_recovering": "运行恢复中",
    "paper_surface_refresh_in_progress": "人类查看面刷新中",
    "scientific_or_quality_repair_in_progress": "论文硬阻塞处理中",
    "waiting_human_decision": "等待医生或 PI 判断",
    "manual_finishing": "人工收尾兼容保护",
    "monitor_only": "持续监督中",
}
_OPERATOR_STATUS_TRUTH_SOURCE_LABELS = {
    "runtime_supervision": "runtime_supervision/latest.json",
    "supervisor_tick_audit": "supervisor_tick_audit",
    "publication_eval": "publication_eval/latest.json",
    "controller_confirmation": "controller_confirmation_summary.json",
    "controller_decision": "controller_decisions/latest.json",
    "runtime_watch": "runtime_watch",
    "latest_event": "latest_events[0]",
}
_CONTINUATION_REASON_LABELS = {
    "unchanged_finalize_state": "运行停在未变化的定稿总结态",
}
_TEXT_LABELS = {
    "bundle suggestions are downstream-only until the publication gate allows write": "在发表门控放行写作前，投稿包相关建议都只是后续件。",
    "the publication gate allows write; writing-stage work is now on the critical path": "发表门控已经放行写作，论文写作阶段进入关键路径。",
    "bundle-stage work is unlocked and can proceed on the critical path": "投稿打包阶段已被全局门控放行，可以进入关键路径。",
    "bundle-stage blockers are now on the critical path for this paper line": "当前论文线的关键路径已经进入投稿打包阻塞修复。",
    "paper bundle exists, but the active blockers still belong to the publishability surface; bundle suggestions stay downstream-only until the gate clears": "论文包雏形已经存在，但当前硬阻塞仍在论文可发表性面；在门控放行前，投稿包相关建议都只是后续件。",
}
_TEXT_REPLACEMENTS = (
    ("paper bundle exists", "论文包雏形已经存在"),
    ("the active blockers still belong to the publishability surface", "当前硬阻塞仍在论文可发表性面"),
    ("bundle suggestions stay downstream-only until the gate clears", "在门控放行前，投稿包相关建议都只是后续件"),
    ("publishability surface", "论文可发表性面"),
    ("publication gate allows write", "发表门控放行写作"),
    ("gate clears", "门控放行"),
    ("submission bundle", "最小投稿包"),
    ("bundle 相关建议", "投稿包相关建议"),
    ("publishability gate blocked", "论文可发表性门控未放行"),
    ("missing submission minimal", "缺少最小投稿包导出"),
    ("forbidden manuscript terminology", "当前稿件仍含不允许的术语表达，需要清理"),
    ("live 状态", "在线状态"),
    (", but ", "，但"),
    ("; ", "；"),
)
_SUPERVISOR_TICK_GAP_STATUSES = {"missing", "invalid", "stale"}
_PROGRESS_STALE_AFTER_SECONDS = 12 * 60 * 60
_QUALITY_CLOSURE_BASIS_LABELS = {
    "clinical_significance": "临床意义",
    "evidence_strength": "证据强度",
    "novelty_positioning": "创新性定位",
    "human_review_readiness": "人工审阅准备度",
    "publication_gate": "发表门控",
}
_QUALITY_REVISION_DIMENSION_LABELS = {
    **_QUALITY_CLOSURE_BASIS_LABELS,
}
_QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS = {
    "auto_re_review_pending": "等待系统自动复评",
    "auto_re_review_blocked": "自动复评暂未继续",
    "not_in_re_review_waiting": "当前不在等待复评阶段",
}
_LATEST_EVENT_DISPLAY_TIERS = {
    "runtime_supervision": 0,
    "runtime_progress": 0,
    "paper_projection": 0,
    "controller_decision": 0,
    "publication_eval": 0,
    "runtime_escalation": 0,
    "runtime_watch": 1,
    "launch_report": 2,
}
_HUMAN_SURFACE_REFRESH_BLOCKER_LABELS = {
    _BLOCKER_LABELS["stale_study_delivery_mirror"],
    _BLOCKER_LABELS["missing_submission_minimal"],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _progress_freshness_now() -> datetime:
    return datetime.now(timezone.utc)


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


def _duration_hours_label(seconds: int) -> str:
    hours = max(1, round(seconds / 3600))
    return f"{hours} 小时"


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _timestamp_is_newer(candidate: object, baseline: object) -> bool:
    candidate_text = _normalize_timestamp(candidate)
    if candidate_text is None:
        return False
    baseline_text = _normalize_timestamp(baseline)
    if baseline_text is None:
        return True
    return datetime.fromisoformat(candidate_text) > datetime.fromisoformat(baseline_text)


def _publication_eval_semantically_stale_against_gate(
    *,
    publication_eval_payload: dict[str, Any] | None,
    publishability_gate_payload: dict[str, Any] | None,
) -> bool:
    if not isinstance(publication_eval_payload, dict) or not isinstance(publishability_gate_payload, dict):
        return False
    if _non_empty_text(publishability_gate_payload.get("status")) != "clear":
        return False
    verdict_payload = publication_eval_payload.get("verdict")
    overall_verdict = (
        _non_empty_text(verdict_payload.get("overall_verdict"))
        if isinstance(verdict_payload, dict)
        else None
    )
    if overall_verdict not in {"promising", "clear", "ready", "pass", "approved"}:
        return True
    for gap in publication_eval_payload.get("gaps") or []:
        if not isinstance(gap, dict):
            continue
        severity = _non_empty_text(gap.get("severity"))
        summary = _non_empty_text(gap.get("summary"))
        if summary == "stale_study_delivery_mirror":
            return True
        if severity and severity != "optional":
            return True
    return False


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


def _quote_cli_arg(value: str | Path | None) -> str:
    text = str(value or "").strip()
    if not text:
        return "<profile>"
    return shlex.quote(text)


def _command_prefix(profile_ref: str | Path | None) -> str:
    del profile_ref
    return "uv run python -m med_autoscience.cli"


def _profile_arg(profile_ref: str | Path | None) -> str:
    return _quote_cli_arg(Path(profile_ref).expanduser().resolve() if profile_ref is not None else None)


def _study_selector(*, study_id: str) -> str:
    return f"--study-id {_quote_cli_arg(study_id)}"


def _display_text(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text in _TEXT_LABELS:
        return _TEXT_LABELS[text]
    for source, target in _TEXT_REPLACEMENTS:
        text = text.replace(source, target)
    for token, label in (
        *_CURRENT_STAGE_LABELS.items(),
        *_PAPER_STAGE_LABELS.items(),
        *_BLOCKER_LABELS.items(),
    ):
        text = text.replace(token, label)
    return text


def _status_narration_human_view(payload: Mapping[str, Any]) -> dict[str, Any]:
    return build_status_narration_human_view(
        payload,
        fallback_current_stage=_non_empty_text(payload.get("current_stage")),
        fallback_latest_update=_display_text(payload.get("current_stage_summary"))
        or _non_empty_text(payload.get("current_stage_summary")),
        fallback_next_step=_display_text(payload.get("next_system_action"))
        or _non_empty_text(payload.get("next_system_action")),
        fallback_blockers=payload.get("current_blockers") or [],
    )


def _current_stage_label(stage: object) -> str | None:
    text = _non_empty_text(stage)
    if text is None:
        return None
    return _CURRENT_STAGE_LABELS.get(text, _humanize_token(text))


def _paper_stage_label(stage: object) -> str | None:
    text = _non_empty_text(stage)
    if text is None:
        return None
    return _PAPER_STAGE_LABELS.get(text, _humanize_token(text))


def _route_repair_mode(action_type: str) -> str:
    if action_type == "bounded_analysis":
        return "bounded_analysis"
    return "same_line_route_back"


def _route_repair_summary(route_repair: dict[str, Any] | None, *, include_rationale: bool = False) -> str | None:
    if not isinstance(route_repair, dict):
        return None
    route_label = _non_empty_text(route_repair.get("route_target_label"))
    key_question = _non_empty_text(route_repair.get("route_key_question"))
    if route_label is None or key_question is None:
        return None
    repair_mode = _non_empty_text(route_repair.get("repair_mode"))
    if repair_mode == "bounded_analysis":
        summary = f"进入“{route_label}”有限补充分析，先回答“{key_question}”。"
    else:
        summary = f"回到“{route_label}”，回答“{key_question}”。"
    rationale = _non_empty_text(route_repair.get("route_rationale"))
    if include_rationale and rationale is not None:
        summary = f"{summary} 理由：{rationale}"
    return summary


def _publication_eval_route_repair(publication_eval_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    actions = (publication_eval_payload or {}).get("recommended_actions") or []
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        action_type = _non_empty_text(action.get("action_type"))
        if action_type not in _ROUTE_REPAIR_ACTION_TYPES:
            continue
        route_target = _non_empty_text(action.get("route_target"))
        route_key_question = _non_empty_text(action.get("route_key_question"))
        route_rationale = _non_empty_text(action.get("route_rationale"))
        if route_target is None or route_key_question is None or route_rationale is None:
            continue
        route_label = _paper_stage_label(route_target) or route_target
        repair_mode = _route_repair_mode(action_type)
        priority = _non_empty_text(action.get("priority")) or "next"
        candidate = {
            "action_id": _non_empty_text(action.get("action_id")),
            "action_type": action_type,
            "priority": priority,
            "repair_mode": repair_mode,
            "repair_mode_label": _ROUTE_REPAIR_MODE_LABELS.get(repair_mode),
            "route_target": route_target,
            "route_target_label": route_label,
            "route_key_question": route_key_question,
            "route_rationale": route_rationale,
        }
        route_summary = _route_repair_summary(candidate)
        if route_summary is not None:
            candidate["route_summary"] = route_summary
        candidates.append((0 if priority == "now" else 1, index, candidate))
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


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


def _runtime_decision_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _RUNTIME_DECISION_LABELS.get(text, _humanize_token(text))


def _manual_finish_active(manual_finish_contract: dict[str, Any] | None) -> bool:
    return bool((manual_finish_contract or {}).get("compatibility_guard_only"))


def _manual_finish_runtime_decision_summary(manual_finish_contract: dict[str, Any] | None) -> str:
    del manual_finish_contract
    return "兼容性监督中"


def _manual_finish_runtime_reason_summary(manual_finish_contract: dict[str, Any] | None) -> str:
    summary = _non_empty_text((manual_finish_contract or {}).get("summary"))
    if summary is not None:
        return _display_text(summary) or summary
    return "当前 study 已转入人工收尾；MAS 只保持兼容性与监督入口。"


def _runtime_health_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _RUNTIME_HEALTH_LABELS.get(text, _humanize_token(text))


def _supervisor_tick_status_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _SUPERVISOR_TICK_STATUS_LABELS.get(text, _humanize_token(text))


def _continuation_reason_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text.startswith("decision:"):
        return "运行停在待处理的决策节点"
    if text.startswith("latest_user_requirement:"):
        return "最新用户要求已接管当前优先级"
    return _CONTINUATION_REASON_LABELS.get(text, _humanize_token(text))


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


def _blocker_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    normalized = text.replace(" ", "_")
    direct_label = _BLOCKER_LABELS.get(text) or _BLOCKER_LABELS.get(normalized)
    if direct_label is not None:
        return direct_label
    watch_label = _WATCH_BLOCKER_LABELS.get(text) or _WATCH_BLOCKER_LABELS.get(normalized)
    if watch_label is not None:
        return watch_label
    reason_label = _REASON_LABELS.get(text) or _REASON_LABELS.get(normalized)
    if reason_label is not None:
        return reason_label
    return _display_text(text) or _humanize_token(text)


def _humanized_blockers(items: list[str]) -> list[str]:
    blockers: list[str] = []
    for item in items:
        label = _blocker_label(item) or str(item)
        if label not in blockers:
            blockers.append(label)
    return blockers


def _append_unique(items: list[str], message: str | None) -> None:
    if not message:
        return
    if message not in items:
        items.append(message)


def _publication_eval_gap_is_blocking(gap: dict[str, Any]) -> bool:
    summary = _non_empty_text(gap.get("summary"))
    if summary is None:
        return False
    severity = _non_empty_text(gap.get("severity"))
    if severity in {"optional", "advisory", "watch", "info", "informational"}:
        return False
    return True


def _publication_supervisor_state_marker(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    supervisor_phase = _non_empty_text(payload.get("supervisor_phase"))
    if supervisor_phase is None:
        return None
    return {
        "supervisor_phase": supervisor_phase,
        "bundle_tasks_downstream_only": bool(payload.get("bundle_tasks_downstream_only")),
        "current_required_action": _non_empty_text(payload.get("current_required_action")),
    }


def _publication_supervisor_state_conflicts(
    *,
    current: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> bool:
    current_marker = _publication_supervisor_state_marker(current)
    candidate_marker = _publication_supervisor_state_marker(candidate)
    if current_marker is None or candidate_marker is None:
        return False
    return any(candidate_marker[key] != current_marker[key] for key in current_marker)


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


def _runtime_module_surface(
    *,
    generated_at: str,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    launch_report_path: Path,
    runtime_supervision_path: Path,
    runtime_supervision_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    runtime_watch_path: Path | None,
    recovery_contract: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    publication_supervisor_state: dict[str, Any],
    current_stage_summary: str,
    next_system_action: str,
    needs_physician_decision: bool,
    status: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
) -> dict[str, Any]:
    summary = build_runtime_status_summary(
        study_id=study_id,
        quest_id=quest_id,
        generated_at=generated_at,
        runtime_status_ref=(
            str(runtime_supervision_path.resolve())
            if runtime_supervision_payload is not None
            else str(launch_report_path.resolve())
        ),
        runtime_artifact_ref=str(launch_report_path.resolve()),
        runtime_escalation_record_ref=(
            str(runtime_escalation_path.resolve()) if runtime_escalation_path is not None else None
        ),
        runtime_watch_ref=str(runtime_watch_path.resolve()) if runtime_watch_path is not None else None,
        health_status=_non_empty_text((runtime_supervision_payload or {}).get("health_status")) or "unknown",
        runtime_decision=_non_empty_text(status.get("decision")) or "noop",
        runtime_reason=_non_empty_text(status.get("reason")),
        recovery_action_mode=_non_empty_text(recovery_contract.get("action_mode")) or "monitor_only",
        supervisor_tick_status=_non_empty_text(supervisor_tick_audit.get("status")),
        current_required_action=(
            _non_empty_text(execution_owner_guard.get("current_required_action"))
            or _non_empty_text((runtime_supervision_payload or {}).get("next_action"))
        ),
        controller_stage_note=(
            _non_empty_text(execution_owner_guard.get("controller_stage_note"))
            or _non_empty_text(publication_supervisor_state.get("controller_stage_note"))
        ),
        status_summary=(
            _display_text((runtime_supervision_payload or {}).get("summary"))
            or current_stage_summary
            or next_system_action
        ),
        next_action_summary=(
            _display_text((runtime_supervision_payload or {}).get("next_action_summary"))
            or next_system_action
            or current_stage_summary
        ),
        needs_human_intervention=(
            bool((runtime_supervision_payload or {}).get("needs_human_intervention")) or needs_physician_decision
        ),
    )
    summary_ref = materialize_runtime_status_summary(study_root=study_root, summary=summary)
    return {
        "module": "runtime",
        "surface_kind": "runtime_module_surface",
        "summary_id": summary_ref["summary_id"],
        "summary_ref": summary_ref["artifact_path"],
        "runtime_status_ref": summary["runtime_status_ref"],
        "runtime_artifact_ref": summary["runtime_artifact_ref"],
        "runtime_escalation_record_ref": summary["runtime_escalation_record_ref"],
        "runtime_watch_ref": summary["runtime_watch_ref"],
        "health_status": summary["health_status"],
        "runtime_decision": summary["runtime_decision"],
        "runtime_reason": summary["runtime_reason"],
        "recovery_action_mode": summary["recovery_action_mode"],
        "status_summary": summary["status_summary"],
        "next_action_summary": summary["next_action_summary"],
        "needs_human_intervention": summary["needs_human_intervention"],
    }


def _publishability_gate_report_path(
    *,
    runtime_watch_payload: dict[str, Any] | None,
    quest_root: Path | None,
) -> Path | None:
    publication_gate = (
        dict((((runtime_watch_payload or {}).get("controllers") or {}).get("publication_gate") or {}))
        if isinstance(((runtime_watch_payload or {}).get("controllers") or {}).get("publication_gate"), dict)
        else {}
    )
    report_json = _non_empty_text(publication_gate.get("report_json"))
    if report_json is not None:
        candidate = Path(report_json).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        if quest_root is not None:
            return (quest_root / candidate).resolve()
    if quest_root is None:
        return None
    candidate = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    return candidate.resolve() if candidate.exists() else None


def _refresh_publication_surfaces_from_gate_report(
    *,
    study_root: Path,
    study_id: str,
    quest_root: Path | None,
    quest_id: str | None,
    publication_eval_path: Path,
    runtime_escalation_path: Path | None,
    runtime_watch_payload: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, Path | None, dict[str, Any] | None]:
    publishability_gate_path = _publishability_gate_report_path(
        runtime_watch_payload=runtime_watch_payload,
        quest_root=quest_root,
    )
    publishability_gate_payload = (
        _read_json_object(publishability_gate_path)
        if publishability_gate_path is not None
        else None
    )
    publication_eval_payload = _read_json_object(publication_eval_path)
    gate_generated_at = _non_empty_text((publishability_gate_payload or {}).get("generated_at"))
    eval_emitted_at = _non_empty_text((publication_eval_payload or {}).get("emitted_at"))
    if (
        publishability_gate_path is not None
        and publishability_gate_payload is not None
        and quest_root is not None
        and _non_empty_text(publishability_gate_payload.get("gate_kind")) == "publishability_control"
        and (
            _timestamp_is_newer(gate_generated_at, eval_emitted_at)
            or _publication_eval_semantically_stale_against_gate(
                publication_eval_payload=publication_eval_payload,
                publishability_gate_payload=publishability_gate_payload,
            )
        )
    ):
        try:
            decision_module = import_module("med_autoscience.controllers.study_runtime_decision")
            decision_module._materialize_publication_eval_from_gate_report(
                study_root=study_root,
                study_id=study_id,
                quest_root=quest_root,
                quest_id=quest_id,
                publication_gate_report=publishability_gate_payload,
            )
            publication_eval_payload = _read_json_object(publication_eval_path)
        except (AttributeError, ImportError, OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    refreshed_eval_emitted_at = _non_empty_text((publication_eval_payload or {}).get("emitted_at"))
    evaluation_summary_path = stable_evaluation_summary_path(study_root=study_root)
    evaluation_summary_payload = _read_json_object(evaluation_summary_path)
    evaluation_summary_emitted_at = _non_empty_text((evaluation_summary_payload or {}).get("emitted_at"))
    if (
        publication_eval_payload is not None
        and publishability_gate_path is not None
        and runtime_escalation_path is not None
        and runtime_escalation_path.exists()
        and refreshed_eval_emitted_at is not None
        and refreshed_eval_emitted_at != evaluation_summary_emitted_at
    ):
        try:
            materialize_evaluation_summary_artifacts(
                study_root=study_root,
                runtime_escalation_ref=runtime_escalation_path,
                publishability_gate_report_ref=publishability_gate_path,
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return publication_eval_payload, publishability_gate_path, publishability_gate_payload


def _controller_module_surface(*, study_root: Path) -> dict[str, Any] | None:
    summary_path = stable_controller_summary_path(study_root=study_root)
    if not summary_path.exists():
        return None
    summary = read_controller_summary(study_root=study_root, ref=summary_path)
    confirmation_summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    confirmation_summary = (
        read_controller_confirmation_summary(study_root=study_root, ref=confirmation_summary_path)
        if confirmation_summary_path.exists()
        else None
    )
    controller_policy = dict(summary.get("controller_policy") or {})
    route_trigger_authority = dict(summary.get("route_trigger_authority") or {})
    decision_policy = _non_empty_text(route_trigger_authority.get("decision_policy")) or "unknown"
    launch_profile = _non_empty_text(route_trigger_authority.get("launch_profile")) or "unknown"
    required_first_anchor = _non_empty_text(controller_policy.get("required_first_anchor"))
    human_confirmation_surface = (
        {
            "gate_id": confirmation_summary["gate_id"],
            "status": confirmation_summary["status"],
            "requested_at": confirmation_summary["requested_at"],
            "question_for_user": confirmation_summary["question_for_user"],
            "allowed_responses": list(confirmation_summary.get("allowed_responses") or []),
            "next_action_if_approved": confirmation_summary["next_action_if_approved"],
            "summary_ref": str(confirmation_summary_path),
        }
        if confirmation_summary is not None
        else None
    )
    status_summary = (
        "研究合同已冻结；当前控制面决策等待医生/PI 确认。"
        if human_confirmation_surface is not None
        else f"研究合同已冻结；决策策略 {decision_policy}，启动入口 {launch_profile}。"
    )
    next_action_summary = (
        f"{human_confirmation_surface['question_for_user']} 确认后系统将{human_confirmation_surface['next_action_if_approved']}。"
        if human_confirmation_surface is not None
        else (
            f"从 {required_first_anchor} 锚点继续推进当前研究。"
            if required_first_anchor
            else "沿 controller contract 继续推进当前研究。"
        )
    )
    return {
        "module": "controller_charter",
        "surface_kind": "controller_module_surface",
        "summary_id": summary["summary_id"],
        "summary_ref": str(summary_path),
        "study_charter_ref": dict(summary.get("study_charter_ref") or {}),
        "decision_policy": decision_policy,
        "launch_profile": launch_profile,
        "status_summary": status_summary,
        "next_action_summary": next_action_summary,
        "human_confirmation": human_confirmation_surface,
    }


def _evaluation_module_surface(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    runtime_watch_payload: dict[str, Any] | None,
    quest_root: Path | None,
) -> dict[str, Any] | None:
    evaluation_summary_path = stable_evaluation_summary_path(study_root=study_root)
    promotion_gate_path = stable_promotion_gate_path(study_root=study_root)
    if not evaluation_summary_path.exists():
        gate_report_path = _publishability_gate_report_path(
            runtime_watch_payload=runtime_watch_payload,
            quest_root=quest_root,
        )
        charter_path = stable_study_charter_path(study_root=study_root)
        if (
            publication_eval_payload is None
            or runtime_escalation_path is None
            or not runtime_escalation_path.exists()
            or gate_report_path is None
            or not gate_report_path.exists()
            or not charter_path.exists()
        ):
            return None
        materialize_evaluation_summary_artifacts(
            study_root=study_root,
            runtime_escalation_ref=runtime_escalation_path,
            publishability_gate_report_ref=gate_report_path,
        )
    if not evaluation_summary_path.exists():
        return None
    summary = read_evaluation_summary(study_root=study_root, ref=evaluation_summary_path)
    promotion_gate_status = dict(summary.get("promotion_gate_status") or {})
    quality_closure_truth = dict(summary.get("quality_closure_truth") or {})
    quality_execution_lane = dict(summary.get("quality_execution_lane") or {})
    quality_closure_basis = dict(summary.get("quality_closure_basis") or {})
    quality_review_agenda = dict(summary.get("quality_review_agenda") or {})
    quality_revision_plan = dict(summary.get("quality_revision_plan") or {})
    quality_review_loop = dict(summary.get("quality_review_loop") or {})
    current_required_action = _non_empty_text(promotion_gate_status.get("current_required_action"))
    plan_items = [
        dict(item)
        for item in (quality_revision_plan.get("items") or [])
        if isinstance(item, dict)
    ]
    plan_next_action = (
        _display_text((plan_items[0] or {}).get("action")) if plan_items else None
    ) or (_non_empty_text((plan_items[0] or {}).get("action")) if plan_items else None)
    review_loop_next_action = _display_text(quality_review_loop.get("recommended_next_action")) or _non_empty_text(
        quality_review_loop.get("recommended_next_action")
    )
    next_action_summary = (
        review_loop_next_action
        or plan_next_action
        or (
        _display_text(quality_review_agenda.get("suggested_revision"))
        or _non_empty_text(quality_review_agenda.get("suggested_revision"))
        or _ACTION_LABELS.get(current_required_action or "", "")
        or current_required_action
        or "按当前 eval hygiene 结论继续推进。"
        )
    )
    return {
        "module": "eval_hygiene",
        "surface_kind": "evaluation_module_surface",
        "summary_id": summary["summary_id"],
        "summary_ref": str(evaluation_summary_path),
        "promotion_gate_ref": str(promotion_gate_path) if promotion_gate_path.exists() else None,
        "overall_verdict": summary["overall_verdict"],
        "primary_claim_status": summary["primary_claim_status"],
        "stop_loss_pressure": summary["stop_loss_pressure"],
        "requires_controller_decision": bool(summary.get("requires_controller_decision")),
        "status_summary": summary["verdict_summary"],
        "next_action_summary": next_action_summary,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "quality_closure_basis": quality_closure_basis or None,
        "quality_review_agenda": quality_review_agenda or None,
        "quality_revision_plan": quality_revision_plan or None,
        "quality_review_loop": quality_review_loop or None,
    }


def _quality_review_followthrough_projection(
    *,
    quality_review_loop: Mapping[str, Any],
    needs_physician_decision: bool,
    interaction_arbitration: Mapping[str, Any],
    runtime_decision: str | None,
    quest_status: str | None,
    current_blockers: list[str],
    next_system_action: str,
) -> dict[str, Any] | None:
    if not quality_review_loop:
        return None
    waiting_auto_re_review = bool(quality_review_loop.get("re_review_ready")) or _non_empty_text(
        quality_review_loop.get("current_phase")
    ) == "re_review_required"
    if not waiting_auto_re_review:
        return {
            "surface_kind": "quality_review_followthrough",
            "state": "not_in_re_review_waiting",
            "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["not_in_re_review_waiting"],
            "waiting_auto_re_review": False,
            "auto_continue_expected": False,
            "summary": "当前质量闭环不在自动复评等待态，系统会按现有修订线继续推进。",
            "blocking_reason": None,
            "next_confirmation_signal": "看下一次质量评审结论是否继续收窄当前修订线。",
            "user_intervention_required_now": False,
        }

    requires_user_input = needs_physician_decision or bool(interaction_arbitration.get("requires_user_input"))
    runtime_active = quest_status in {"running", "active", "waiting_for_user"}
    runtime_recovery_requested = runtime_decision in {"create_and_start", "resume", "relaunch_stopped"}
    runtime_blocks_auto = runtime_decision in {"blocked", "completed", "create_only"}
    auto_continue_expected = (runtime_active or runtime_recovery_requested) and not runtime_blocks_auto and not requires_user_input
    if auto_continue_expected:
        return {
            "surface_kind": "quality_review_followthrough",
            "state": "auto_re_review_pending",
            "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["auto_re_review_pending"],
            "waiting_auto_re_review": True,
            "auto_continue_expected": True,
            "summary": "当前在等系统自动发起下一轮复评，主线会自动继续。",
            "blocking_reason": None,
            "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
            "user_intervention_required_now": False,
        }

    if requires_user_input:
        blocking_reason = "当前需要医生或 PI 先确认下一步，系统不会直接自动复评。"
    elif runtime_decision == "blocked":
        blocking_reason = "当前运行被控制面阻断，需先解除阻断后才会继续复评。"
    elif quest_status in {"stopped", "failed", "completed"}:
        blocking_reason = "当前运行不在自动推进状态，需要先恢复运行后才会继续复评。"
    else:
        blocking_reason = _non_empty_text(current_blockers[0] if current_blockers else None) or next_system_action
    return {
        "surface_kind": "quality_review_followthrough",
        "state": "auto_re_review_blocked",
        "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["auto_re_review_blocked"],
        "waiting_auto_re_review": True,
        "auto_continue_expected": False,
        "summary": "当前停在等待复评，系统暂时不会自动继续。",
        "blocking_reason": blocking_reason,
        "next_confirmation_signal": "先解除当前卡点，再看 publication_eval/latest.json 是否出现新的复评结论。",
        "user_intervention_required_now": True,
    }


def _apply_quality_review_followthrough_to_operator_status(
    *,
    operator_status_card: Mapping[str, Any],
    followthrough: Mapping[str, Any] | None,
) -> dict[str, Any]:
    card = dict(operator_status_card or {})
    follow = dict(followthrough or {})
    if not card or not follow or not bool(follow.get("waiting_auto_re_review")):
        return card
    card["quality_review_followthrough"] = follow
    card["current_focus"] = _non_empty_text(follow.get("summary")) or card.get("current_focus")
    next_signal = _non_empty_text(follow.get("next_confirmation_signal"))
    if next_signal is not None:
        card["next_confirmation_signal"] = next_signal
    intervention_required = bool(follow.get("user_intervention_required_now"))
    card["user_intervention_required_now"] = intervention_required
    if intervention_required:
        card["user_visible_verdict"] = "当前停在等待复评，系统不会自动继续；你现在需要先处理卡点。"
    else:
        card["user_visible_verdict"] = "当前在等系统自动复评；你现在不用介入，先等待复评回写。"
    return card


def _gate_clearing_batch_followthrough(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    record_path = gate_clearing_batch.stable_gate_clearing_batch_path(study_root=study_root)
    record = _read_json_object(record_path)
    if record is None:
        return None
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    source_eval_id = _non_empty_text(record.get("source_eval_id"))
    if current_eval_id is None or source_eval_id is None or current_eval_id != source_eval_id:
        return None
    unit_results = [
        dict(item)
        for item in (record.get("unit_results") or [])
        if isinstance(item, dict)
    ]
    failed_units = [item for item in unit_results if _non_empty_text(item.get("status")) == "failed"]
    gate_replay = dict(record.get("gate_replay") or {})
    gate_replay_status = _non_empty_text(gate_replay.get("status")) or "unknown"
    if failed_units:
        summary = "最近一轮 gate-clearing batch 已执行，但仍有修复单元失败，当前不能继续自动前推。"
        next_confirmation_signal = "先修掉失败 repair unit，再看 publication_eval/latest.json 是否进入新的复评或放行结论。"
        user_intervention_required_now = True
    elif gate_replay_status == "clear":
        summary = "最近一轮 gate-clearing batch 已执行，并已把发表门控回放到放行状态。"
        next_confirmation_signal = "看 publication_eval/latest.json 是否刷新为新的放行结论，并确认当前 study 已进入下一阶段。"
        user_intervention_required_now = False
    else:
        blockers = [
            _non_empty_text(item)
            for item in (gate_replay.get("blockers") or [])
            if _non_empty_text(item) is not None
        ]
        blocker_summary = f"当前仍剩 {len(blockers)} 个 gate blocker。" if blockers else "当前 gate replay 仍未完全收口。"
        summary = f"最近一轮 gate-clearing batch 已执行；{blocker_summary}"
        next_confirmation_signal = "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。"
        user_intervention_required_now = False
    return {
        "surface_kind": "gate_clearing_batch_followthrough",
        "status": _non_empty_text(record.get("status")) or "executed",
        "summary": summary,
        "gate_replay_status": gate_replay_status,
        "blocking_issue_count": len(gate_replay.get("blockers") or []),
        "failed_unit_count": len(failed_units),
        "next_confirmation_signal": next_confirmation_signal,
        "user_intervention_required_now": user_intervention_required_now,
        "latest_record_path": str(record_path),
    }


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


def _latest_event_display_tier(category: object) -> int:
    text = _non_empty_text(category)
    if text is None:
        return 0
    return _LATEST_EVENT_DISPLAY_TIERS.get(text, 0)


def _progress_freshness_status_label(status: object) -> str | None:
    text = _non_empty_text(status)
    if text is None:
        return None
    return _PROGRESS_FRESHNESS_STATUS_LABELS.get(text, _humanize_token(text))


def _progress_freshness_required(current_stage: str) -> bool:
    return current_stage not in {
        "study_completed",
        "manual_finishing",
        "waiting_physician_decision",
    }


def _append_progress_signal(
    *,
    signals: list[dict[str, Any]],
    timestamp: object,
    source: str,
    summary: object,
) -> None:
    normalized_timestamp = _normalize_timestamp(timestamp)
    rendered_summary = _display_text(summary)
    if normalized_timestamp is None or rendered_summary is None:
        return
    signals.append(
        {
            "timestamp": normalized_timestamp,
            "time_label": _time_label(normalized_timestamp),
            "source": source,
            "summary": rendered_summary,
        }
    )


def _latest_progress_signal(
    *,
    bash_summary_payload: dict[str, Any] | None,
    details_projection_payload: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    signals: list[dict[str, Any]] = []
    latest_session = (bash_summary_payload or {}).get("latest_session")
    if isinstance(latest_session, dict):
        last_progress = latest_session.get("last_progress")
        if isinstance(last_progress, dict):
            _append_progress_signal(
                signals=signals,
                timestamp=_non_empty_text(last_progress.get("ts")) or _non_empty_text(latest_session.get("updated_at")),
                source="bash_summary",
                summary=_non_empty_text(last_progress.get("message")) or _non_empty_text(last_progress.get("step")),
            )
    if details_projection_payload is not None:
        _append_progress_signal(
            signals=signals,
            timestamp=_non_empty_text(((details_projection_payload.get("summary") or {}).get("updated_at")))
            or _non_empty_text((details_projection_payload or {}).get("generated_at")),
            source="details_projection",
            summary=_non_empty_text(((details_projection_payload.get("summary") or {}).get("status_line"))),
        )
    if controller_decision_payload is not None:
        decision_type = _decision_type_label(controller_decision_payload.get("decision_type")) or "形成控制面决定"
        reason = _display_text(controller_decision_payload.get("reason"))
        summary = f"控制面正式决定：{decision_type}。"
        if reason:
            summary += f" 原因：{reason}"
        _append_progress_signal(
            signals=signals,
            timestamp=controller_decision_payload.get("emitted_at"),
            source="controller_decision",
            summary=summary,
        )
    if publication_eval_payload is not None:
        verdict = (publication_eval_payload.get("verdict") or {}) if isinstance(publication_eval_payload, dict) else {}
        _append_progress_signal(
            signals=signals,
            timestamp=publication_eval_payload.get("emitted_at"),
            source="publication_eval",
            summary=_non_empty_text(verdict.get("summary")) or "发表评估已更新。",
        )
    if not signals:
        return None
    return max(signals, key=lambda item: item["timestamp"])


def _progress_freshness(
    *,
    current_stage: str,
    bash_summary_payload: dict[str, Any] | None,
    details_projection_payload: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    required = _progress_freshness_required(current_stage)
    latest_signal = _latest_progress_signal(
        bash_summary_payload=bash_summary_payload,
        details_projection_payload=details_projection_payload,
        controller_decision_payload=controller_decision_payload,
        publication_eval_payload=publication_eval_payload,
    )
    if not required:
        summary = "当前阶段以人工判断或收尾为主，不要求系统继续产出新的自动推进信号。"
        return {
            "status": "not_required",
            "required": False,
            "summary": summary,
            "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
            "latest_progress_at": latest_signal.get("timestamp") if latest_signal else None,
            "latest_progress_time_label": latest_signal.get("time_label") if latest_signal else None,
            "latest_progress_source": latest_signal.get("source") if latest_signal else None,
            "latest_progress_summary": latest_signal.get("summary") if latest_signal else None,
            "seconds_since_latest_progress": None,
        }
    if latest_signal is None:
        return {
            "status": "missing",
            "required": True,
            "summary": "当前还没有看到明确的研究推进记录，用户现在只能看到监管或状态面。",
            "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
            "latest_progress_at": None,
            "latest_progress_time_label": None,
            "latest_progress_source": None,
            "latest_progress_summary": None,
            "seconds_since_latest_progress": None,
        }

    age_seconds = max(
        0,
        int((_progress_freshness_now() - datetime.fromisoformat(str(latest_signal["timestamp"]))).total_seconds()),
    )
    if age_seconds > _PROGRESS_STALE_AFTER_SECONDS:
        summary = (
            f"距离上一次明确研究推进已经超过 {_duration_hours_label(_PROGRESS_STALE_AFTER_SECONDS)}，"
            "当前要重点排查是否卡住或空转。"
        )
        status = "stale"
    else:
        summary = f"最近 {_duration_hours_label(_PROGRESS_STALE_AFTER_SECONDS)}内仍有明确研究推进记录。"
        status = "fresh"
    return {
        "status": status,
        "required": True,
        "summary": summary,
        "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
        "latest_progress_at": latest_signal["timestamp"],
        "latest_progress_time_label": latest_signal["time_label"],
        "latest_progress_source": latest_signal["source"],
        "latest_progress_summary": latest_signal["summary"],
        "seconds_since_latest_progress": age_seconds,
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
    manual_finish_contract: dict[str, Any] | None,
) -> str:
    quest_status = _non_empty_text(status.get("quest_status"))
    decision = _non_empty_text(status.get("decision"))
    runtime_reason = _non_empty_text(status.get("reason"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if decision == "completed" or (quest_status == "completed" and decision != "blocked"):
        return "study_completed"
    if bool((manual_finish_contract or {}).get("compatibility_guard_only")):
        return "manual_finishing"
    if needs_physician_decision:
        return "waiting_physician_decision"
    if runtime_health_status == "recovering":
        return "managed_runtime_recovering"
    if runtime_health_status == "degraded":
        return "managed_runtime_degraded"
    if runtime_health_status == "escalated":
        return "managed_runtime_escalated"
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        return "managed_runtime_supervision_gap"
    if decision == "blocked":
        return "runtime_blocked"
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
    status: dict[str, Any],
    current_stage: str,
    publication_supervisor_state: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
    latest_progress_message: str | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
) -> str:
    if current_stage == "study_completed":
        return "研究主线已经进入结题/交付阶段，系统不会继续自动实验。"
    if current_stage == "manual_finishing":
        return (
            _non_empty_text((manual_finish_contract or {}).get("summary"))
            or "当前 study 已转入人工收尾；MAS 只保持兼容性与监督入口，不再把它视为默认自动续跑对象。"
        )
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
        route_repair = _publication_eval_route_repair(publication_eval_payload)
        route_summary = _route_repair_summary(route_repair, include_rationale=True)
        if route_summary is not None:
            return f"论文质量监管已转入结构化修复：{route_summary}"
        note = _non_empty_text((publication_supervisor_state or {}).get("controller_stage_note"))
        return note or "论文主线当前停在发表监管阶段，系统会先守住可发表性与交付门控。"
    if current_stage == "managed_runtime_active":
        summary = "托管运行时正在自动推进研究，前台当前应以监督为主。"
        if latest_progress_message:
            summary += f" 最近一次可见推进是：{latest_progress_message}"
        return summary
    if current_stage == "runtime_blocked":
        reason = _reason_label(status.get("reason"))
        if reason is not None:
            return reason
        return "自动推进已被硬阻断，需要先补齐前置条件后才能继续。"
    return "研究运行仍处在准备或轻量评估阶段。"


def _interaction_arbitration_action(interaction_arbitration: dict[str, Any] | None) -> str | None:
    return _non_empty_text((interaction_arbitration or {}).get("action"))


def _resume_arbitration_external_metadata_wait(
    *,
    status: dict[str, Any],
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> bool:
    if _interaction_arbitration_action(interaction_arbitration) != "resume":
        return False
    if _non_empty_text(status.get("reason")) != "quest_parked_on_unchanged_finalize_state":
        return False
    if _non_empty_text((pending_user_interaction or {}).get("kind")) != "progress":
        return False
    if _non_empty_text((pending_user_interaction or {}).get("decision_type")) is not None:
        return False
    if not bool((pending_user_interaction or {}).get("relay_required")):
        return False
    if not bool((pending_user_interaction or {}).get("guidance_requires_user_decision")):
        return False
    if not bool((pending_user_interaction or {}).get("expects_reply")):
        return False
    return True


def _supervisor_tick_gap_present(supervisor_tick_audit: dict[str, Any]) -> bool:
    if not bool((supervisor_tick_audit or {}).get("required")):
        return False
    return _non_empty_text((supervisor_tick_audit or {}).get("status")) in _SUPERVISOR_TICK_GAP_STATUSES


def _controller_confirmation_pending(
    *,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
) -> bool:
    summary_status = _non_empty_text((controller_confirmation_summary or {}).get("status"))
    if summary_status is not None:
        return summary_status == "pending" and _controller_human_gate_allowed_from_payload(
            controller_confirmation_summary or {}
        )
    if not bool((controller_decision_payload or {}).get("requires_human_confirmation")):
        return False
    return _controller_human_gate_allowed_from_payload(controller_decision_payload or {})


def _controller_human_gate_allowed_from_payload(payload: dict[str, Any]) -> bool:
    decision_type = _non_empty_text(payload.get("decision_type"))
    if decision_type is None:
        return False
    action_types = payload.get("controller_action_types")
    if not isinstance(action_types, list):
        raw_actions = payload.get("controller_actions")
        action_types = [
            _non_empty_text(action.get("action_type"))
            for action in raw_actions
            if isinstance(action, dict)
        ] if isinstance(raw_actions, list) else []
    try:
        return controller_human_gate_allowed(
            decision_type=decision_type,
            controller_action_types=[action_type for action_type in action_types if action_type],
        )
    except (TypeError, ValueError):
        return False


def _controller_confirmation_summary_text(
    controller_confirmation_summary: dict[str, Any] | None,
) -> str | None:
    if controller_confirmation_summary is None:
        return None
    question = _non_empty_text(controller_confirmation_summary.get("question_for_user"))
    next_action = _non_empty_text(controller_confirmation_summary.get("next_action_if_approved"))
    reason = _non_empty_text(controller_confirmation_summary.get("request_reason"))
    details: list[str] = []
    if question is not None:
        details.append(question)
    if next_action is not None:
        details.append(f"确认后系统将{next_action}。")
    if reason is not None:
        details.append(f"控制面理由：{reason}。")
    return " ".join(details) if details else None


def _needs_physician_decision(
    *,
    status: dict[str, Any],
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> bool:
    controller_requires = _controller_confirmation_pending(
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
    )
    if controller_requires:
        return True
    if _resume_arbitration_external_metadata_wait(
        status=status,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    ):
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
    status: dict[str, Any],
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
) -> str | None:
    if _controller_confirmation_pending(
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
    ):
        return (
            _controller_confirmation_summary_text(controller_confirmation_summary)
            or "控制面已经形成正式下一步建议，但该动作需要医生/PI 先确认，系统会停在监管态等待。"
        )
    if _resume_arbitration_external_metadata_wait(
        status=status,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    ):
        return _non_empty_text((pending_user_interaction or {}).get("summary")) or _non_empty_text(
            (pending_user_interaction or {}).get("message")
        )
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
    publication_eval_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    current_blockers: list[str],
    execution_owner_guard: dict[str, Any],
    status: dict[str, Any],
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
) -> str:
    if bool((manual_finish_contract or {}).get("compatibility_guard_only")):
        return (
            _non_empty_text((manual_finish_contract or {}).get("next_action_summary"))
            or "继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。"
        )
    if needs_physician_decision:
        controller_actions = list((controller_decision_payload or {}).get("controller_actions") or [])
        first_action = controller_actions[0] if controller_actions else {}
        action_type = _controller_action_label(first_action.get("action_type"))
        if action_type is not None:
            return f"等待医生/PI 确认后，再{action_type}。"
        return "等待医生/PI 明确确认后，再继续下一步托管推进。"
    supervisor_tick_next_action = _non_empty_text((supervisor_tick_audit or {}).get("next_action_summary"))
    if _supervisor_tick_gap_present(supervisor_tick_audit) and supervisor_tick_next_action is not None:
        return supervisor_tick_next_action
    runtime_next_action = _non_empty_text((runtime_supervision_payload or {}).get("next_action_summary"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if runtime_health_status in {"recovering", "degraded", "escalated"} and runtime_next_action is not None:
        return runtime_next_action
    decision = _non_empty_text(status.get("decision"))
    if decision == "blocked":
        reason = _reason_label(status.get("reason"))
        if reason is not None:
            return reason
    publication_action_key = _non_empty_text((publication_supervisor_state or {}).get("current_required_action"))
    route_repair = _publication_eval_route_repair(publication_eval_payload)
    route_repair_action = _route_repair_summary(route_repair)
    if (
        current_blockers
        and route_repair_action is not None
        and _quality_blocker_present(
            publication_eval_payload=publication_eval_payload,
            runtime_watch_payload=runtime_watch_payload,
        )
    ):
        return route_repair_action
    if (
        current_blockers
        and publication_action_key in {"continue_bundle_stage", "complete_bundle_stage"}
        and _quality_blocker_present(
            publication_eval_payload=publication_eval_payload,
            runtime_watch_payload=runtime_watch_payload,
        )
    ):
        return "先修正当前质量阻塞，再决定是否继续投稿打包。"
    publication_action = _action_label(publication_action_key)
    if publication_action is not None:
        return publication_action
    guard_action = _action_label((execution_owner_guard or {}).get("current_required_action"))
    if guard_action is not None:
        return guard_action
    if decision in {"create_and_start", "resume", "relaunch_stopped"}:
        return "系统会继续托管推进当前研究运行。"
    return "继续轮询研究状态，并把新的阶段变化投影到前台。"


def _current_blockers(
    *,
    status: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_escalation_payload: dict[str, Any] | None,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    pending_user_interaction: dict[str, Any],
    interaction_arbitration: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    progress_freshness: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    manual_finish_active = _manual_finish_active(manual_finish_contract)
    metadata_wait = _resume_arbitration_external_metadata_wait(
        status=status,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    )
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        _append_unique(
            blockers,
            _non_empty_text((supervisor_tick_audit or {}).get("summary")),
        )
    if _non_empty_text((progress_freshness or {}).get("status")) in {"stale", "missing"}:
        _append_unique(
            blockers,
            _non_empty_text((progress_freshness or {}).get("summary")),
        )
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if runtime_health_status in {"degraded", "escalated"}:
        _append_unique(
            blockers,
            _non_empty_text((runtime_supervision_payload or {}).get("summary"))
            or _non_empty_text((runtime_supervision_payload or {}).get("clinician_update")),
        )
    if manual_finish_active:
        return blockers
    if _non_empty_text(status.get("decision")) == "blocked" and not manual_finish_active:
        _append_unique(
            blockers,
            _reason_label(status.get("reason")) or _non_empty_text(status.get("reason")),
        )
    if _controller_confirmation_pending(
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
    ):
        _append_unique(
            blockers,
            _controller_confirmation_summary_text(controller_confirmation_summary)
            or "当前控制面决策需要医生/PI 确认，系统不会自动越权继续。",
        )
    if metadata_wait:
        _append_unique(
            blockers,
            _non_empty_text((pending_user_interaction or {}).get("summary"))
            or _non_empty_text((pending_user_interaction or {}).get("message")),
        )
    if _interaction_arbitration_action(interaction_arbitration) != "resume" and bool(
        (pending_user_interaction or {}).get("blocking")
    ):
        _append_unique(
            blockers,
            _non_empty_text((pending_user_interaction or {}).get("summary"))
            or _non_empty_text((pending_user_interaction or {}).get("message")),
        )
    for gap in (publication_eval_payload or {}).get("gaps") or []:
        if isinstance(gap, dict) and _publication_eval_gap_is_blocking(gap):
            _append_unique(blockers, _non_empty_text(gap.get("summary")))
    controllers_payload = (runtime_watch_payload or {}).get("controllers") or {}
    if isinstance(controllers_payload, dict):
        for controller_payload in controllers_payload.values():
            if not isinstance(controller_payload, dict):
                continue
            for blocker in controller_payload.get("blockers") or []:
                _append_unique(blockers, _watch_blocker_label(blocker))
            if _non_empty_text(controller_payload.get("status")) == "blocked":
                _append_unique(
                    blockers,
                    _non_empty_text(controller_payload.get("controller_stage_note"))
                    or _non_empty_text(controller_payload.get("controller_note")),
                )
    _append_unique(blockers, _reason_label((runtime_escalation_payload or {}).get("reason")))
    return blockers


def _quality_blocker_present(
    *,
    publication_eval_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
) -> bool:
    for gap in (publication_eval_payload or {}).get("gaps") or []:
        if isinstance(gap, dict) and _publication_eval_gap_is_blocking(gap):
            return True
    controllers_payload = (runtime_watch_payload or {}).get("controllers") or {}
    if not isinstance(controllers_payload, dict):
        return False
    for controller_payload in controllers_payload.values():
        if not isinstance(controller_payload, dict):
            continue
        blockers = list(controller_payload.get("blockers") or [])
        if blockers:
            return True
        if _non_empty_text(controller_payload.get("status")) == "blocked" and (
            _non_empty_text(controller_payload.get("controller_stage_note"))
            or _non_empty_text(controller_payload.get("controller_note"))
        ):
            return True
    return False


def _intervention_lane(
    *,
    current_stage: str,
    current_stage_summary: str,
    current_blockers: list[str],
    next_system_action: str,
    needs_physician_decision: bool,
    progress_freshness: dict[str, Any],
    publication_eval_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    blocker_summary = _non_empty_text(current_blockers[0] if current_blockers else None)
    progress_status = _non_empty_text((progress_freshness or {}).get("status"))
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))

    if _manual_finish_active(manual_finish_contract):
        return {
            "lane_id": "manual_finishing",
            "title": "保持人工收尾兼容保护",
            "severity": "observe",
            "summary": (
                _non_empty_text((manual_finish_contract or {}).get("summary"))
                or current_stage_summary
                or next_system_action
            ),
            "recommended_action_id": "maintain_compatibility_guard",
        }
    if _supervisor_tick_gap_present(supervisor_tick_audit):
        return {
            "lane_id": "workspace_supervision_gap",
            "title": "优先恢复 Hermes-hosted 托管监管",
            "severity": "critical",
            "summary": (
                _non_empty_text((supervisor_tick_audit or {}).get("summary"))
                or current_stage_summary
                or blocker_summary
                or next_system_action
            ),
            "recommended_action_id": "refresh_supervision",
        }
    if runtime_health_status in {"recovering", "degraded", "escalated"}:
        return {
            "lane_id": "runtime_recovery_required",
            "title": "优先处理 runtime recovery",
            "severity": "critical" if runtime_health_status in {"degraded", "escalated"} else "warning",
            "summary": (
                _non_empty_text((runtime_supervision_payload or {}).get("summary"))
                or _non_empty_text((runtime_supervision_payload or {}).get("clinician_update"))
                or current_stage_summary
                or blocker_summary
                or next_system_action
            ),
            "recommended_action_id": "continue_or_relaunch",
        }
    if _quality_blocker_present(
        publication_eval_payload=publication_eval_payload,
        runtime_watch_payload=runtime_watch_payload,
    ):
        route_repair = _publication_eval_route_repair(publication_eval_payload)
        route_summary = _route_repair_summary(route_repair)
        payload = {
            "lane_id": "quality_floor_blocker",
            "title": (
                "优先完成有限补充分析"
                if _non_empty_text((route_repair or {}).get("repair_mode")) == "bounded_analysis"
                else "优先收口同线质量硬阻塞"
                if route_repair is not None
                else "优先收口质量硬阻塞"
            ),
            "severity": "critical",
            "summary": route_summary or blocker_summary or current_stage_summary or next_system_action,
            "recommended_action_id": _non_empty_text((route_repair or {}).get("action_type")) or "inspect_progress",
        }
        if route_repair is not None:
            payload.update(route_repair)
        return payload
    if needs_physician_decision:
        return {
            "lane_id": "human_decision_gate",
            "title": "等待医生或 PI 判断",
            "severity": "handoff",
            "summary": current_stage_summary or blocker_summary or next_system_action,
            "recommended_action_id": "inspect_progress",
        }
    if progress_status in {"stale", "missing"}:
        return {
            "lane_id": "study_progress_gap",
            "title": "优先检查研究是否卡住",
            "severity": "warning",
            "summary": (
                _non_empty_text((progress_freshness or {}).get("summary"))
                or current_stage_summary
                or blocker_summary
                or next_system_action
            ),
            "recommended_action_id": "inspect_progress",
        }
    if current_stage == "runtime_blocked":
        return {
            "lane_id": "runtime_blocker",
            "title": "优先恢复或重启当前 study",
            "severity": "warning",
            "summary": current_stage_summary or blocker_summary or next_system_action,
            "recommended_action_id": "continue_or_relaunch",
        }
    return {
        "lane_id": "monitor_only",
        "title": "继续监督当前 study",
        "severity": "observe",
        "summary": current_stage_summary or next_system_action or "当前 study 没有新的接管动作。",
        "recommended_action_id": "inspect_progress",
    }


def _recovery_step(
    *,
    step_id: str,
    title: str,
    surface_kind: str,
    command: str,
) -> dict[str, str]:
    return {
        "step_id": step_id,
        "title": title,
        "surface_kind": surface_kind,
        "command": command,
    }


def _study_command_surfaces(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    profile_ref: str | Path | None,
) -> dict[str, str]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    selector = _study_selector(study_id=study_id)
    return {
        "workspace_cockpit": f"{prefix} workspace cockpit --profile {profile_arg}",
        "study_progress": f"{prefix} study progress --profile {profile_arg} {selector}",
        "study_runtime_status": f"{prefix} study-runtime-status --profile {profile_arg} {selector}",
        "launch_study": f"{prefix} study launch --profile {profile_arg} {selector}",
        "refresh_supervision": (
            f"{prefix} runtime watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {profile_arg} --ensure-study-runtimes --apply"
        ),
    }


def _recovery_contract(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    profile_ref: str | Path | None,
    intervention_lane: dict[str, Any],
    current_stage_summary: str,
    next_system_action: str,
    current_blockers: list[str],
) -> tuple[str | None, list[dict[str, str]], dict[str, Any]]:
    commands = _study_command_surfaces(profile=profile, study_id=study_id, profile_ref=profile_ref)
    lane_id = _non_empty_text(intervention_lane.get("lane_id")) or "monitor_only"
    summary = (
        _non_empty_text(intervention_lane.get("summary"))
        or _non_empty_text(current_blockers[0] if current_blockers else None)
        or current_stage_summary
        or next_system_action
        or "当前 study 没有新的接管动作。"
    )

    if lane_id == "workspace_supervision_gap":
        steps = [
            _recovery_step(
                step_id="refresh_supervision",
                title="刷新 Hermes-hosted supervision tick",
                surface_kind="runtime_watch_refresh",
                command=commands["refresh_supervision"],
            ),
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
        ]
        action_mode = "refresh_supervision"
    elif lane_id in {"runtime_recovery_required", "runtime_blocker"}:
        steps = [
            _recovery_step(
                step_id="continue_or_relaunch",
                title="继续或重新拉起当前 study",
                surface_kind="launch_study",
                command=commands["launch_study"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
        ]
        action_mode = "continue_or_relaunch"
    elif lane_id == "human_decision_gate":
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="open_workspace_cockpit",
                title="返回 workspace cockpit",
                surface_kind="workspace_cockpit",
                command=commands["workspace_cockpit"],
            ),
        ]
        action_mode = "human_decision_review"
    elif lane_id == "manual_finishing":
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="open_workspace_cockpit",
                title="返回 workspace cockpit",
                surface_kind="workspace_cockpit",
                command=commands["workspace_cockpit"],
            ),
        ]
        action_mode = "maintain_compatibility_guard"
    elif lane_id in {"quality_floor_blocker", "study_progress_gap"}:
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
            _recovery_step(
                step_id="open_workspace_cockpit",
                title="返回 workspace cockpit",
                surface_kind="workspace_cockpit",
                command=commands["workspace_cockpit"],
            ),
        ]
        action_mode = "inspect_progress"
    else:
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
        ]
        action_mode = "monitor_only"

    recovery_contract = {
        "contract_kind": "study_recovery_contract",
        "lane_id": lane_id,
        "action_mode": action_mode,
        "summary": summary,
        "recommended_step_id": steps[0]["step_id"] if steps else None,
        "steps": steps,
    }
    recommended_command = steps[0]["command"] if steps else None
    return recommended_command, steps, recovery_contract


def _restore_point(
    *,
    continuation_state: dict[str, Any],
    family_checkpoint_lineage: dict[str, Any],
    needs_physician_decision: bool,
) -> dict[str, Any]:
    resume_contract_payload = family_checkpoint_lineage.get("resume_contract")
    resume_contract = dict(resume_contract_payload) if isinstance(resume_contract_payload, dict) else {}
    resume_mode = _non_empty_text(resume_contract.get("resume_mode"))
    continuation_policy = _non_empty_text(continuation_state.get("continuation_policy"))
    continuation_reason = (
        _continuation_reason_label(continuation_state.get("continuation_reason"))
        or _non_empty_text(continuation_state.get("continuation_reason"))
    )
    if isinstance(resume_contract.get("human_gate_required"), bool):
        human_gate_required = bool(resume_contract.get("human_gate_required"))
    else:
        human_gate_required = needs_physician_decision
    if resume_mode is not None or continuation_policy is not None or continuation_reason is not None:
        summary_parts: list[str] = []
        if resume_mode is not None:
            summary_parts.append(f"当前恢复点采用 {resume_mode}")
        else:
            summary_parts.append("当前恢复点已冻结")
        if continuation_policy is not None:
            summary_parts.append(f"continuation policy 为 {continuation_policy}")
        if continuation_reason is not None:
            summary_parts.append(f"最近一次续跑原因是{continuation_reason}")
        if human_gate_required:
            summary_parts.append("恢复前仍需人工确认")
        summary = "；".join(summary_parts) + "。"
    elif human_gate_required:
        summary = "当前还没有额外 checkpoint resume contract；恢复前仍需人工确认。"
    else:
        summary = "当前还没有额外 checkpoint resume contract；可以直接回到 MAS 主线继续恢复或重启当前 study。"
    return {
        "resume_mode": resume_mode,
        "continuation_policy": continuation_policy,
        "continuation_reason": continuation_reason,
        "human_gate_required": human_gate_required,
        "summary": summary,
    }


def _latest_outer_loop_dispatch(
    *,
    study_id: str,
    runtime_watch_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    dispatch_block = (
        dict((runtime_watch_payload or {}).get("managed_study_outer_loop_dispatch") or {})
        if isinstance((runtime_watch_payload or {}).get("managed_study_outer_loop_dispatch"), dict)
        else {}
    )
    if dispatch_block and _non_empty_text(dispatch_block.get("study_id")) == study_id:
        dispatches: list[dict[str, Any]] = [dispatch_block]
    else:
        dispatches = [
            dict(item)
            for item in ((runtime_watch_payload or {}).get("managed_study_outer_loop_dispatches") or [])
            if isinstance(item, dict)
        ]
    for item in reversed(dispatches):
        if _non_empty_text(item.get("study_id")) != study_id:
            continue
        route_target = _non_empty_text(item.get("route_target"))
        if route_target is None:
            continue
        route_target_label = _paper_stage_label(route_target) or route_target
        route_key_question = _display_text(item.get("route_key_question")) or _non_empty_text(item.get("route_key_question"))
        decision_type = _non_empty_text(item.get("decision_type"))
        verb = "进入" if decision_type == "bounded_analysis" else "转到"
        if route_key_question is not None:
            summary = f"最近一次自治外环已{verb}“{route_target_label}”，当前关键问题是“{route_key_question}”。"
        else:
            summary = f"最近一次自治外环已{verb}“{route_target_label}”。"
        return {
            "decision_type": decision_type,
            "route_target": route_target,
            "route_target_label": route_target_label,
            "route_key_question": route_key_question,
            "dispatch_status": _non_empty_text(item.get("dispatch_status")),
            "summary": summary,
        }
    return None


def _autonomy_contract(
    *,
    study_id: str,
    intervention_lane: dict[str, Any],
    recovery_contract: dict[str, Any],
    recommended_command: str | None,
    current_stage_summary: str,
    next_system_action: str,
    continuation_state: dict[str, Any],
    family_checkpoint_lineage: dict[str, Any],
    runtime_watch_payload: dict[str, Any] | None,
    needs_physician_decision: bool,
    manual_finish_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    restore_point = _restore_point(
        continuation_state=continuation_state,
        family_checkpoint_lineage=family_checkpoint_lineage,
        needs_physician_decision=needs_physician_decision,
    )
    latest_outer_loop_dispatch = _latest_outer_loop_dispatch(
        study_id=study_id,
        runtime_watch_payload=runtime_watch_payload,
    )
    lane_id = _non_empty_text(intervention_lane.get("lane_id")) or "monitor_only"
    if _manual_finish_active(manual_finish_contract):
        autonomy_state = "compatibility_guard"
    elif needs_physician_decision:
        autonomy_state = "human_gate"
    elif lane_id in {"workspace_supervision_gap", "runtime_recovery_required", "runtime_blocker"}:
        autonomy_state = "runtime_recovery"
    else:
        autonomy_state = "autonomous_progress"
    if autonomy_state == "autonomous_progress" and latest_outer_loop_dispatch is not None:
        summary = str(latest_outer_loop_dispatch.get("summary") or "").strip()
    elif autonomy_state == "autonomous_progress" and restore_point.get("resume_mode"):
        summary = f"恢复点已冻结；当前停在 {restore_point.get('resume_mode')}，下一次确认看恢复信号。"
    else:
        summary = (
            _non_empty_text(intervention_lane.get("summary"))
            or _non_empty_text(recovery_contract.get("summary"))
            or current_stage_summary
            or next_system_action
            or str(restore_point.get("summary") or "").strip()
        )
    return {
        "contract_kind": "study_autonomy_contract",
        "autonomy_state": autonomy_state,
        "summary": summary,
        "recommended_command": recommended_command,
        "next_signal": next_system_action or str(restore_point.get("summary") or "").strip(),
        "restore_point": restore_point,
        "latest_outer_loop_dispatch": latest_outer_loop_dispatch,
    }


def _autonomy_soak_status(
    *,
    autonomy_contract: dict[str, Any],
    progress_freshness: dict[str, Any],
    runtime_watch_path: Path | None,
    controller_decision_path: Path,
) -> dict[str, Any] | None:
    latest_outer_loop_dispatch = dict(autonomy_contract.get("latest_outer_loop_dispatch") or {})
    if not latest_outer_loop_dispatch:
        return None
    return {
        "surface_kind": "study_autonomy_soak_status",
        "status": "autonomous_dispatch_visible",
        "summary": str(latest_outer_loop_dispatch.get("summary") or "").strip(),
        "autonomy_state": _non_empty_text(autonomy_contract.get("autonomy_state")),
        "dispatch_status": _non_empty_text(latest_outer_loop_dispatch.get("dispatch_status")),
        "route_target": _non_empty_text(latest_outer_loop_dispatch.get("route_target")),
        "route_target_label": _non_empty_text(latest_outer_loop_dispatch.get("route_target_label")),
        "route_key_question": _non_empty_text(latest_outer_loop_dispatch.get("route_key_question")),
        "progress_freshness_status": _non_empty_text(progress_freshness.get("status")),
        "next_confirmation_signal": _non_empty_text(autonomy_contract.get("next_signal")),
        "proof_refs": [
            ref
            for ref in (
                str(runtime_watch_path) if runtime_watch_path is not None else None,
                str(controller_decision_path),
            )
            if ref is not None
        ],
    }


def _operator_verdict(
    *,
    study_id: str,
    intervention_lane: dict[str, Any],
    recovery_contract: dict[str, Any],
    recommended_command: str | None,
    current_stage_summary: str,
    next_system_action: str,
    current_blockers: list[str],
) -> dict[str, Any]:
    lane_id = _non_empty_text(intervention_lane.get("lane_id")) or "monitor_only"
    severity = _non_empty_text(intervention_lane.get("severity")) or "observe"
    summary = (
        _non_empty_text(intervention_lane.get("summary"))
        or _non_empty_text(current_blockers[0] if current_blockers else None)
        or current_stage_summary
        or next_system_action
        or "当前 study 没有新的接管动作。"
    )
    primary_step_id = _non_empty_text((recovery_contract or {}).get("recommended_step_id"))
    primary_surface_kind = None
    for step in (recovery_contract or {}).get("steps") or []:
        if not isinstance(step, dict):
            continue
        if _non_empty_text(step.get("step_id")) == primary_step_id:
            primary_surface_kind = _non_empty_text(step.get("surface_kind"))
            break

    if lane_id in {"workspace_supervision_gap", "runtime_recovery_required", "runtime_blocker"}:
        decision_mode = "intervene_now"
    elif lane_id == "human_decision_gate":
        decision_mode = "human_decision_required"
    elif lane_id == "manual_finishing":
        decision_mode = "compatibility_guard_only"
    else:
        decision_mode = "monitor_only"

    payload = {
        "surface_kind": "study_operator_verdict",
        "verdict_id": f"study_operator_verdict::{study_id}::{lane_id}",
        "study_id": study_id,
        "lane_id": lane_id,
        "severity": severity,
        "decision_mode": decision_mode,
        "needs_intervention": decision_mode in {"intervene_now", "human_decision_required"},
        "focus_scope": "workspace" if lane_id == "workspace_supervision_gap" else "study",
        "summary": summary,
        "reason_summary": summary,
        "primary_step_id": primary_step_id,
        "primary_surface_kind": primary_surface_kind,
        "primary_command": recommended_command,
    }
    for field_name in (
        "repair_mode",
        "repair_mode_label",
        "route_target",
        "route_target_label",
        "route_key_question",
        "route_rationale",
        "route_summary",
    ):
        value = _non_empty_text(intervention_lane.get(field_name))
        if value is not None:
            payload[field_name] = value
    return payload


def _operator_status_handling_state(
    *,
    current_stage: str,
    intervention_lane: dict[str, Any],
    needs_physician_decision: bool,
    current_blockers: list[str],
    manual_finish_contract: dict[str, Any] | None,
) -> str:
    lane_id = _non_empty_text((intervention_lane or {}).get("lane_id")) or "monitor_only"
    if _manual_finish_active(manual_finish_contract):
        return "manual_finishing"
    if lane_id == "workspace_supervision_gap":
        return "runtime_supervision_recovering"
    if lane_id in {"runtime_recovery_required", "runtime_blocker"} or current_stage in {
        "managed_runtime_recovering",
        "managed_runtime_degraded",
        "managed_runtime_escalated",
        "runtime_blocked",
    }:
        return "runtime_recovering"
    if needs_physician_decision or lane_id == "human_decision_gate":
        return "waiting_human_decision"
    if any(str(item or "").strip() in _HUMAN_SURFACE_REFRESH_BLOCKER_LABELS for item in current_blockers):
        return "paper_surface_refresh_in_progress"
    if lane_id == "quality_floor_blocker":
        return "scientific_or_quality_repair_in_progress"
    return "monitor_only"


def _latest_event_snapshot(latest_events: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for item in latest_events:
        if not isinstance(item, dict):
            continue
        timestamp = _non_empty_text(item.get("timestamp"))
        if timestamp is None:
            continue
        source = _non_empty_text(item.get("source")) or _non_empty_text(item.get("category")) or "latest_event"
        return "latest_event", timestamp if source is None else timestamp
    return None, None


def _operator_status_truth_snapshot(
    *,
    handling_state: str,
    latest_events: list[dict[str, Any]],
    publication_eval_payload: dict[str, Any] | None,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
) -> tuple[str | None, str | None]:
    latest_event_source, latest_event_time = _latest_event_snapshot(latest_events)
    candidates_by_state = {
        "runtime_supervision_recovering": (
            ("supervisor_tick_audit", _non_empty_text((supervisor_tick_audit or {}).get("latest_recorded_at"))),
            ("runtime_supervision", _non_empty_text((runtime_supervision_payload or {}).get("recorded_at"))),
            (latest_event_source, latest_event_time),
        ),
        "runtime_recovering": (
            ("runtime_supervision", _non_empty_text((runtime_supervision_payload or {}).get("recorded_at"))),
            ("supervisor_tick_audit", _non_empty_text((supervisor_tick_audit or {}).get("latest_recorded_at"))),
            (latest_event_source, latest_event_time),
        ),
        "paper_surface_refresh_in_progress": (
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
            (latest_event_source, latest_event_time),
        ),
        "scientific_or_quality_repair_in_progress": (
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
            (latest_event_source, latest_event_time),
        ),
        "waiting_human_decision": (
            ("controller_confirmation", _non_empty_text((controller_confirmation_summary or {}).get("requested_at"))),
            ("controller_decision", _non_empty_text((controller_decision_payload or {}).get("emitted_at"))),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            (latest_event_source, latest_event_time),
        ),
        "manual_finishing": (
            (latest_event_source, latest_event_time),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
        ),
        "monitor_only": (
            (latest_event_source, latest_event_time),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
        ),
    }
    for source, timestamp in candidates_by_state.get(handling_state, ((latest_event_source, latest_event_time),)):
        if source is not None and timestamp is not None:
            return source, timestamp
    return None, None


def _operator_status_human_surface_summary(handling_state: str) -> tuple[str, str]:
    if handling_state == "paper_surface_refresh_in_progress":
        return "stale", "给人看的投稿包镜像仍落后于当前论文真相。"
    if handling_state == "waiting_human_decision":
        return "pending_decision", "当前主要等待人工判断，给人看的稿件状态以论文门控为准。"
    if handling_state in {"runtime_supervision_recovering", "runtime_recovering"}:
        return "monitoring_runtime", "当前优先看结构化监管真相，给人看的稿件表面还不是主判断面。"
    return "current", "给人看的稿件表面当前没有额外刷新告警。"


def _operator_status_verdict(handling_state: str) -> str:
    if handling_state == "runtime_supervision_recovering":
        return "MAS 正在恢复外环监管，当前 study 仍处在受管修复中。"
    if handling_state == "runtime_recovering":
        return "MAS 正在处理 runtime recovery，当前 study 仍处在受管修复中。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在处理论文可发表性硬阻塞，给人看的稿件还没到放行状态。"
    if handling_state == "waiting_human_decision":
        return "MAS 已经把自动侧能做的部分推进完成，当前在等医生或 PI 判断。"
    if handling_state == "manual_finishing":
        return "MAS 当前保持人工收尾兼容保护，并继续提供监督入口。"
    return "MAS 正在持续监管当前 study。"


def _operator_status_owner_summary(handling_state: str) -> str:
    if handling_state == "runtime_supervision_recovering":
        return "MAS 正在恢复 workspace 级监管心跳，托管执行仍由 runtime 持有。"
    if handling_state == "runtime_recovering":
        return "MAS 正在根据 runtime supervision 真相继续处理恢复。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "MAS 正在根据 publication gate 真相刷新给人看的投稿包镜像。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在收口论文可发表性与质量硬阻塞。"
    if handling_state == "waiting_human_decision":
        return "MAS 已把下一步提升到医生或 PI 决策面，并继续保持监管。"
    if handling_state == "manual_finishing":
        return "MAS 当前只保持人工收尾兼容保护和监督入口。"
    return "MAS 正在持续监管当前 study。"


def _operator_status_focus_summary(
    *,
    handling_state: str,
    intervention_lane: dict[str, Any],
    next_system_action: str,
    current_stage_summary: str,
) -> str:
    if handling_state == "paper_surface_refresh_in_progress":
        return "优先把人类查看面同步到当前论文真相，再继续盯论文门控。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        route_summary = _non_empty_text((intervention_lane or {}).get("route_summary"))
        if route_summary is not None:
            return route_summary
    return (
        _non_empty_text(next_system_action)
        or _non_empty_text((intervention_lane or {}).get("summary"))
        or _non_empty_text(current_stage_summary)
        or "继续按当前 study 的结构化真相推进。"
    )


def _operator_status_next_confirmation_signal(handling_state: str, intervention_lane: dict[str, Any]) -> str:
    if handling_state == "runtime_supervision_recovering":
        return "看 supervisor tick 是否回到 fresh，并确认监管缺口告警从 attention queue 消失。"
    if handling_state == "runtime_recovering":
        return "看 runtime_supervision/latest.json 的 health_status 回到 live，或最近明确推进时间刷新。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "看 manuscript/delivery_manifest.json、current_package，或 submission_minimal 是否被刷新到最新真相。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        route_label = _non_empty_text((intervention_lane or {}).get("route_target_label"))
        key_question = _non_empty_text((intervention_lane or {}).get("route_key_question"))
        if route_label is not None and key_question is not None:
            return (
                f"看 publication_eval/latest.json 是否把“{route_label}”这条修复线继续收窄，"
                f"以及“{key_question}”是否已经被关闭。"
            )
        return "看 publication_eval/latest.json 或 runtime_watch 里的 blocker 是否减少。"
    if handling_state == "waiting_human_decision":
        return "看 controller_confirmation_summary 是否清空或变化，或 controller_decisions/latest.json 是否写出人工确认后的下一步。"
    if handling_state == "manual_finishing":
        return "看人工收尾是否写出新的明确结论，或兼容保护是否仍然保持 active。"
    return "看下一条 runtime progress / publication_eval 更新。"


def _operator_status_card(
    *,
    study_id: str,
    current_stage: str,
    current_stage_summary: str,
    intervention_lane: dict[str, Any],
    needs_physician_decision: bool,
    current_blockers: list[str],
    next_system_action: str,
    latest_events: list[dict[str, Any]],
    publication_eval_payload: dict[str, Any] | None,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    handling_state = _operator_status_handling_state(
        current_stage=current_stage,
        intervention_lane=intervention_lane,
        needs_physician_decision=needs_physician_decision,
        current_blockers=current_blockers,
        manual_finish_contract=manual_finish_contract,
    )
    latest_truth_source, latest_truth_time = _operator_status_truth_snapshot(
        handling_state=handling_state,
        latest_events=latest_events,
        publication_eval_payload=publication_eval_payload,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        runtime_watch_payload=runtime_watch_payload,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
    )
    human_surface_freshness, human_surface_summary = _operator_status_human_surface_summary(handling_state)
    return {
        "surface_kind": "study_operator_status_card",
        "study_id": study_id,
        "handling_state": handling_state,
        "handling_state_label": _OPERATOR_STATUS_HANDLING_LABELS.get(handling_state),
        "owner_summary": _operator_status_owner_summary(handling_state),
        "current_focus": _operator_status_focus_summary(
            handling_state=handling_state,
            intervention_lane=intervention_lane,
            next_system_action=next_system_action,
            current_stage_summary=current_stage_summary,
        ),
        "latest_truth_time": latest_truth_time,
        "latest_truth_source": latest_truth_source,
        "latest_truth_source_label": (
            _OPERATOR_STATUS_TRUTH_SOURCE_LABELS.get(latest_truth_source)
            if latest_truth_source is not None
            else None
        ),
        "human_surface_freshness": human_surface_freshness,
        "human_surface_summary": human_surface_summary,
        "next_confirmation_signal": _operator_status_next_confirmation_signal(handling_state, intervention_lane),
        "user_visible_verdict": _operator_status_verdict(handling_state),
    }


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
    publication_supervisor_state: dict[str, Any] | None = None,
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
        verdict_summary = (
            _display_text(_non_empty_text(verdict.get("summary")))
            or _non_empty_text(verdict.get("summary"))
            or "发表评估已更新。"
        )
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
        if not _publication_supervisor_state_conflicts(
            current=publication_supervisor_state,
            candidate=publication_gate if isinstance(publication_gate, dict) else None,
        ):
            watch_summary = "系统完成一次研究运行巡检。"
            if isinstance(publication_gate, dict):
                controller_note = _non_empty_text(publication_gate.get("controller_stage_note"))
                if controller_note is not None:
                    watch_summary = _display_text(controller_note) or controller_note
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
        decision = (
            _runtime_decision_label(launch_report_payload.get("decision"))
            or _humanize_token(launch_report_payload.get("decision"))
            or "状态回写"
        )
        reason = _reason_label(launch_report_payload.get("reason"))
        summary = f"最近一次运行状态回写结论：{decision}。"
        if reason is not None:
            summary += f" {reason}"
        if not _publication_supervisor_state_conflicts(
            current=publication_supervisor_state,
            candidate=(
                launch_report_payload.get("publication_supervisor_state")
                if isinstance(launch_report_payload.get("publication_supervisor_state"), dict)
                else None
            ),
        ):
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
    # “最近进展”优先展示具体推进，再展示轮询/状态回写类摘要。
    events.sort(key=lambda item: _latest_event_display_tier(item.get("category")))
    return events[:_DEFAULT_EVENT_LIMIT]


def build_study_progress_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_payload: dict[str, Any] | Any,
    profile_ref: str | Path | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    del entry_mode
    status = _status_payload(status_payload)
    existing_projection = status.get("progress_projection")
    if isinstance(existing_projection, dict) and _non_empty_text(existing_projection.get("study_id")) == study_id:
        return dict(existing_projection)

    resolved_study_id = study_id
    resolved_study_root = study_root
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
    controller_decision_payload = _read_json_object(controller_decision_path)
    if controller_decision_payload is not None:
        try:
            materialize_controller_confirmation_summary(
                study_root=resolved_study_root,
                decision_ref=controller_decision_path,
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    controller_confirmation_summary_path = stable_controller_confirmation_summary_path(study_root=resolved_study_root)
    try:
        controller_confirmation_summary = (
            read_controller_confirmation_summary(
                study_root=resolved_study_root,
                ref=controller_confirmation_summary_path,
            )
            if controller_confirmation_summary_path.exists()
            else None
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        controller_confirmation_summary = None
    runtime_supervision_payload = _read_json_object(runtime_supervision_path)
    runtime_health_status = _non_empty_text((runtime_supervision_payload or {}).get("health_status"))
    if runtime_escalation_path is not None and (
        status.get("runtime_escalation_ref") is not None or runtime_health_status in {"degraded", "escalated"}
    ):
        runtime_escalation_payload = _read_json_object(runtime_escalation_path)
    else:
        runtime_escalation_payload = None
    runtime_watch_payload = _read_json_object(runtime_watch_path) if runtime_watch_path is not None else None
    publication_eval_payload, _publishability_gate_path, _publishability_gate_payload = (
        _refresh_publication_surfaces_from_gate_report(
            study_root=resolved_study_root,
            study_id=resolved_study_id,
            quest_root=quest_root,
            quest_id=quest_id,
            publication_eval_path=publication_eval_path,
            runtime_escalation_path=runtime_escalation_path,
            runtime_watch_payload=runtime_watch_payload,
        )
    )
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
    family_checkpoint_lineage = (
        dict(status.get("family_checkpoint_lineage") or {})
        if isinstance(status.get("family_checkpoint_lineage"), dict)
        else {}
    )
    quest_root_for_manual_finish = _candidate_path(status.get("quest_root"))
    try:
        manual_finish = resolve_effective_study_manual_finish_contract(
            study_root=resolved_study_root,
            quest_root=quest_root_for_manual_finish,
        )
    except ValueError:
        manual_finish = None
    manual_finish_contract = (
        {
            "status": manual_finish.status.value,
            "summary": manual_finish.summary,
            "next_action_summary": manual_finish.next_action_summary,
            "compatibility_guard_only": manual_finish.compatibility_guard_only,
        }
        if manual_finish is not None
        else None
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
    task_intake = summarize_task_intake(read_latest_task_intake(study_root=resolved_study_root))
    latest_progress_message = None
    latest_session = ((bash_summary_payload or {}).get("latest_session"))
    if isinstance(latest_session, dict) and isinstance(latest_session.get("last_progress"), dict):
        latest_progress_message = _non_empty_text((latest_session.get("last_progress") or {}).get("message"))
    if latest_progress_message is None and isinstance(details_projection_wrapper, dict):
        latest_progress_message = _non_empty_text(
            (((details_projection_payload or {}).get("summary") or {}).get("status_line"))
        )

    needs_physician_decision = _needs_physician_decision(
        status=status,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    )
    if _manual_finish_active(manual_finish_contract):
        needs_physician_decision = False
    current_stage = _current_stage(
        status=status,
        needs_physician_decision=needs_physician_decision,
        publication_supervisor_state=publication_supervisor_state,
        autonomous_runtime_notice=autonomous_runtime_notice,
        execution_owner_guard=execution_owner_guard,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
    )
    progress_freshness = _progress_freshness(
        current_stage=current_stage,
        bash_summary_payload=bash_summary_payload,
        details_projection_payload=details_projection_payload,
        controller_decision_payload=controller_decision_payload,
        publication_eval_payload=publication_eval_payload,
    )
    current_stage_summary = _display_text(_stage_summary(
        status=status,
        current_stage=current_stage,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
        latest_progress_message=latest_progress_message,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
    )) or ""
    paper_stage_summary = _display_text(_paper_stage_summary(
        paper_stage=paper_stage,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
    )) or ""
    current_blockers = _humanized_blockers(
        _current_blockers(
            status=status,
            publication_eval_payload=publication_eval_payload,
            runtime_watch_payload=runtime_watch_payload,
            runtime_escalation_payload=runtime_escalation_payload,
            controller_confirmation_summary=controller_confirmation_summary,
            controller_decision_payload=controller_decision_payload,
            pending_user_interaction=pending_user_interaction,
            interaction_arbitration=interaction_arbitration,
            runtime_supervision_payload=runtime_supervision_payload,
            supervisor_tick_audit=supervisor_tick_audit,
            progress_freshness=progress_freshness,
            manual_finish_contract=manual_finish_contract,
        )
    )
    next_system_action = _display_text(_next_system_action(
        needs_physician_decision=needs_physician_decision,
        controller_decision_payload=controller_decision_payload,
        publication_supervisor_state=publication_supervisor_state,
        publication_eval_payload=publication_eval_payload,
        runtime_watch_payload=runtime_watch_payload,
        current_blockers=current_blockers,
        execution_owner_guard=execution_owner_guard,
        status=status,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
    )) or ""
    physician_decision_summary = _display_text(_physician_decision_summary(
        status=status,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        pending_user_interaction=pending_user_interaction,
        interaction_arbitration=interaction_arbitration,
    )) if needs_physician_decision else None
    intervention_lane = _intervention_lane(
        current_stage=current_stage,
        current_stage_summary=current_stage_summary,
        current_blockers=current_blockers,
        next_system_action=next_system_action,
        needs_physician_decision=needs_physician_decision,
        progress_freshness=progress_freshness,
        publication_eval_payload=publication_eval_payload,
        runtime_watch_payload=runtime_watch_payload,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
    )
    recommended_command, recommended_commands, recovery_contract = _recovery_contract(
        profile=profile,
        study_id=resolved_study_id,
        profile_ref=profile_ref,
        intervention_lane=intervention_lane,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        current_blockers=current_blockers,
    )
    autonomy_contract = _autonomy_contract(
        study_id=resolved_study_id,
        intervention_lane=intervention_lane,
        recovery_contract=recovery_contract,
        recommended_command=recommended_command,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        continuation_state=continuation_state,
        family_checkpoint_lineage=family_checkpoint_lineage,
        runtime_watch_payload=runtime_watch_payload,
        needs_physician_decision=needs_physician_decision,
        manual_finish_contract=manual_finish_contract,
    )
    operator_verdict = _operator_verdict(
        study_id=resolved_study_id,
        intervention_lane=intervention_lane,
        recovery_contract=recovery_contract,
        recommended_command=recommended_command,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        current_blockers=current_blockers,
    )
    latest_events = _latest_events(
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
        publication_supervisor_state=publication_supervisor_state,
    )
    operator_status_card = _operator_status_card(
        study_id=resolved_study_id,
        current_stage=current_stage,
        current_stage_summary=current_stage_summary,
        intervention_lane=intervention_lane,
        needs_physician_decision=needs_physician_decision,
        current_blockers=current_blockers,
        next_system_action=next_system_action,
        latest_events=latest_events,
        publication_eval_payload=publication_eval_payload,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        runtime_watch_payload=runtime_watch_payload,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
        manual_finish_contract=manual_finish_contract,
    )
    status_narration_contract = build_status_narration_contract(
        contract_id=f"study-progress::{resolved_study_id}",
        surface_kind="study_progress",
        stage={
            "current_stage": current_stage,
            "paper_stage": paper_stage,
            "intervention_lane": str(intervention_lane.get("lane_id") or "").strip() or None,
        },
        readiness={
            "needs_physician_decision": needs_physician_decision,
            "progress_freshness": str(progress_freshness.get("status") or "").strip() or None,
        },
        current_blockers=current_blockers[:8],
        latest_update=latest_progress_message or current_stage_summary,
        next_step=next_system_action,
        facts={
            "study_id": resolved_study_id,
            "quest_id": quest_id,
            "paper_stage_summary": paper_stage_summary,
        },
        answer_checklist=PROGRESS_ANSWER_CHECKLIST,
    )
    generated_at = _utc_now()
    controller_module_surface = _controller_module_surface(study_root=resolved_study_root)
    evaluation_module_surface = _evaluation_module_surface(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        runtime_escalation_path=runtime_escalation_path,
        runtime_watch_payload=runtime_watch_payload,
        quest_root=quest_root,
    )
    runtime_module_surface = _runtime_module_surface(
        generated_at=generated_at,
        study_id=resolved_study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        launch_report_path=launch_report_path,
        runtime_supervision_path=runtime_supervision_path,
        runtime_supervision_payload=runtime_supervision_payload,
        runtime_escalation_path=runtime_escalation_path,
        runtime_watch_path=runtime_watch_path,
        recovery_contract=recovery_contract,
        execution_owner_guard=execution_owner_guard,
        publication_supervisor_state=publication_supervisor_state,
        current_stage_summary=current_stage_summary,
        next_system_action=next_system_action,
        needs_physician_decision=needs_physician_decision,
        status=status,
        supervisor_tick_audit=supervisor_tick_audit,
    )
    module_surfaces: dict[str, Any] = {}
    if controller_module_surface is not None:
        module_surfaces["controller_charter"] = controller_module_surface
    module_surfaces["runtime"] = runtime_module_surface
    if evaluation_module_surface is not None:
        module_surfaces["eval_hygiene"] = evaluation_module_surface
    quality_closure_truth = (
        dict(evaluation_module_surface.get("quality_closure_truth") or {})
        if evaluation_module_surface is not None
        else {}
    )
    quality_execution_lane = (
        dict(evaluation_module_surface.get("quality_execution_lane") or {})
        if evaluation_module_surface is not None
        else {}
    )
    quality_closure_basis = (
        dict(evaluation_module_surface.get("quality_closure_basis") or {})
        if evaluation_module_surface is not None
        else {}
    )
    quality_review_agenda = (
        dict(evaluation_module_surface.get("quality_review_agenda") or {})
        if evaluation_module_surface is not None
        else {}
    )
    quality_revision_plan = (
        dict(evaluation_module_surface.get("quality_revision_plan") or {})
        if evaluation_module_surface is not None
        else {}
    )
    quality_review_loop = (
        dict(evaluation_module_surface.get("quality_review_loop") or {})
        if evaluation_module_surface is not None
        else {}
    )
    gate_clearing_batch_followthrough = _gate_clearing_batch_followthrough(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
    )
    quality_review_followthrough = _quality_review_followthrough_projection(
        quality_review_loop=quality_review_loop,
        needs_physician_decision=needs_physician_decision,
        interaction_arbitration=interaction_arbitration,
        runtime_decision=_non_empty_text(status.get("decision")),
        quest_status=_non_empty_text(status.get("quest_status")),
        current_blockers=current_blockers,
        next_system_action=next_system_action,
    )
    operator_status_card = _apply_quality_review_followthrough_to_operator_status(
        operator_status_card=operator_status_card,
        followthrough=quality_review_followthrough,
    )
    autonomy_soak_status = _autonomy_soak_status(
        autonomy_contract=autonomy_contract,
        progress_freshness=progress_freshness,
        runtime_watch_path=runtime_watch_path,
        controller_decision_path=controller_decision_path,
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root) if quest_root is not None else None,
        "current_stage": current_stage,
        "current_stage_summary": current_stage_summary,
        "paper_stage": paper_stage,
        "paper_stage_summary": paper_stage_summary,
        "status_narration_contract": status_narration_contract,
        "latest_events": latest_events,
        "current_blockers": current_blockers,
        "next_system_action": next_system_action,
        "intervention_lane": intervention_lane,
        "operator_verdict": operator_verdict,
        "operator_status_card": operator_status_card,
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract,
        "autonomy_soak_status": autonomy_soak_status,
        "recovery_contract": recovery_contract,
        "needs_physician_decision": needs_physician_decision,
        "physician_decision_summary": physician_decision_summary,
        "runtime_decision": _non_empty_text(status.get("decision")),
        "runtime_reason": _non_empty_text(status.get("reason")),
        "continuation_state": continuation_state or None,
        "family_checkpoint_lineage": family_checkpoint_lineage or None,
        "interaction_arbitration": interaction_arbitration or None,
        "manual_finish_contract": manual_finish_contract,
        "task_intake": task_intake,
        "progress_freshness": progress_freshness,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "quality_closure_basis": quality_closure_basis or None,
        "quality_review_agenda": quality_review_agenda or None,
        "quality_revision_plan": quality_revision_plan or None,
        "quality_review_loop": quality_review_loop or None,
        "gate_clearing_batch_followthrough": gate_clearing_batch_followthrough or None,
        "quality_review_followthrough": quality_review_followthrough or None,
        "module_surfaces": module_surfaces,
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
            "controller_confirmation_summary_path": (
                str(controller_confirmation_summary_path) if controller_confirmation_summary is not None else None
            ),
            "controller_summary_path": (
                controller_module_surface["summary_ref"] if controller_module_surface is not None else None
            ),
            "runtime_supervision_path": str(runtime_supervision_path) if runtime_supervision_payload is not None else None,
            "runtime_escalation_path": str(runtime_escalation_path) if runtime_escalation_path is not None else None,
            "runtime_watch_report_path": str(runtime_watch_path) if runtime_watch_path is not None else None,
            "runtime_status_summary_path": runtime_module_surface["summary_ref"],
            "evaluation_summary_path": (
                evaluation_module_surface["summary_ref"] if evaluation_module_surface is not None else None
            ),
            "promotion_gate_path": (
                evaluation_module_surface["promotion_gate_ref"] if evaluation_module_surface is not None else None
            ),
            "bash_summary_path": str(bash_summary_path) if bash_summary_path is not None else None,
            "details_projection_path": str(details_projection_path) if details_projection_path is not None else None,
        },
    }
    return payload


def read_study_progress(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status = study_runtime_router.study_runtime_status(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        entry_mode=entry_mode,
        include_progress_projection=False,
    )
    return build_study_progress_projection(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        status_payload=status,
        profile_ref=profile_ref,
        entry_mode=entry_mode,
    )


def render_study_progress_markdown(payload: dict[str, Any]) -> str:
    latest_events = [dict(item) for item in (payload.get("latest_events") or []) if isinstance(item, dict)]
    blockers: list[str] = []
    for item in payload.get("current_blockers") or []:
        if not str(item).strip():
            continue
        label = _blocker_label(item) or str(item)
        if label not in blockers:
            blockers.append(label)
    continuation_state = dict(payload.get("continuation_state") or {})
    manual_finish_contract = (
        dict(payload.get("manual_finish_contract") or {})
        if isinstance(payload.get("manual_finish_contract"), dict)
        else None
    )
    if _manual_finish_active(manual_finish_contract):
        runtime_decision = _manual_finish_runtime_decision_summary(manual_finish_contract)
        runtime_reason = _manual_finish_runtime_reason_summary(manual_finish_contract)
        continuation_reason = ""
    else:
        runtime_decision = _runtime_decision_label(payload.get("runtime_decision")) or "未知"
        runtime_reason = _reason_label(payload.get("runtime_reason")) or _display_text(payload.get("runtime_reason")) or ""
        continuation_reason = (
            _continuation_reason_label(continuation_state.get("continuation_reason"))
            or str(continuation_state.get("continuation_reason") or "").strip()
        )
    runtime_health = _runtime_health_label(((payload.get("supervision") or {}).get("health_status"))) or "未知"
    supervisor_tick_status = _supervisor_tick_status_label(((payload.get("supervision") or {}).get("supervisor_tick_status"))) or ""
    progress_freshness = dict(payload.get("progress_freshness") or {})
    task_intake = dict(payload.get("task_intake") or {})
    status_human_view = _status_narration_human_view(payload)
    has_status_contract = isinstance(payload.get("status_narration_contract"), Mapping)
    current_stage = _non_empty_text(status_human_view.get("current_stage_label")) or _current_stage_label(
        payload.get("current_stage")
    ) or "未知"
    if has_status_contract:
        current_judgment = _non_empty_text(status_human_view.get("status_summary")) or _non_empty_text(
            status_human_view.get("latest_update")
        )
    else:
        current_judgment = _non_empty_text(status_human_view.get("latest_update")) or _non_empty_text(
            status_human_view.get("status_summary")
        )
    if not current_judgment:
        current_judgment = _display_text(payload.get("current_stage_summary")) or str(
            payload.get("current_stage_summary") or ""
        ).strip()
    next_step_summary = _non_empty_text(status_human_view.get("next_step")) or str(
        payload.get("next_system_action") or ""
    ).strip()
    paper_stage = _paper_stage_label(payload.get("paper_stage")) or "未知"
    intervention_lane = dict(payload.get("intervention_lane") or {})
    intervention_title = _non_empty_text(intervention_lane.get("title"))
    intervention_summary = _display_text(intervention_lane.get("summary")) or _non_empty_text(
        intervention_lane.get("summary")
    )
    intervention_severity = _INTERVENTION_SEVERITY_LABELS.get(
        _non_empty_text(intervention_lane.get("severity")) or "",
        "",
    )
    operator_status_card = dict(payload.get("operator_status_card") or {})
    autonomy_contract = dict(payload.get("autonomy_contract") or {})
    quality_closure_truth = dict(payload.get("quality_closure_truth") or {})
    quality_execution_lane = dict(payload.get("quality_execution_lane") or {})
    quality_closure_basis = dict(payload.get("quality_closure_basis") or {})
    quality_review_agenda = dict(payload.get("quality_review_agenda") or {})
    quality_revision_plan = dict(payload.get("quality_revision_plan") or {})
    quality_review_loop = dict(payload.get("quality_review_loop") or {})
    gate_clearing_batch_followthrough = dict(payload.get("gate_clearing_batch_followthrough") or {})
    quality_review_followthrough = dict(payload.get("quality_review_followthrough") or {})
    recovery_contract = dict(payload.get("recovery_contract") or {})
    module_surfaces = dict(payload.get("module_surfaces") or {})
    if bool(quality_review_followthrough.get("waiting_auto_re_review")):
        current_judgment = _non_empty_text(quality_review_followthrough.get("summary")) or current_judgment
        next_step_summary = (
            _non_empty_text(quality_review_followthrough.get("blocking_reason"))
            or _non_empty_text(quality_review_followthrough.get("next_confirmation_signal"))
            or next_step_summary
        )
    recovery_action_mode = _RECOVERY_ACTION_MODE_LABELS.get(
        _non_empty_text(recovery_contract.get("action_mode")) or "",
        "",
    )
    recovery_steps = [
        dict(item)
        for item in (payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    lines = [
        "# 研究进度",
        "",
        f"- study_id: `{str(payload.get('study_id') or '')}`",
        f"- quest_id: `{str(payload.get('quest_id') or 'none')}`",
        f"- 当前阶段: {current_stage}",
    ]
    if current_judgment:
        lines.append(f"- 当前判断: {current_judgment}")
    if intervention_title or intervention_summary:
        label = intervention_title or "继续监督当前 study"
        if intervention_severity:
            label = f"{label}（{intervention_severity}）"
        lines.extend(
            [
                f"- 干预类型: {label}",
            ]
        )
        if intervention_summary:
            lines.append(f"- 干预摘要: {intervention_summary}")
    if task_intake:
        lines.extend(
            [
                "",
                "## 当前任务",
                "",
                f"- 任务意图: {task_intake.get('task_intent') or '未提供'}",
            ]
        )
        if task_intake.get("journal_target"):
            lines.append(f"- 目标期刊: {task_intake.get('journal_target')}")
        if task_intake.get("entry_mode"):
            lines.append(f"- 入口模式: {task_intake.get('entry_mode')}")
        if task_intake.get("emitted_at"):
            lines.append(f"- 任务写入时间: {task_intake.get('emitted_at')}")
        first_cycle_outputs = [str(item).strip() for item in task_intake.get("first_cycle_outputs") or [] if str(item).strip()]
        if first_cycle_outputs:
            lines.append(f"- 首轮输出要求: {', '.join(first_cycle_outputs)}")
    lines.extend(
        [
            "",
            "## 论文推进",
            "",
            f"- 论文阶段: {paper_stage}",
            f"- 论文摘要: {_display_text(payload.get('paper_stage_summary')) or str(payload.get('paper_stage_summary') or '').strip()}",
            "",
            "## 运行监管",
            "",
            f"- 运行健康: {runtime_health}",
            f"- MAS 决策: {runtime_decision}",
        ]
    )
    if supervisor_tick_status:
        lines.append(f"- MAS 监管心跳: {supervisor_tick_status}")
    progress_freshness_summary = _display_text(progress_freshness.get("summary")) or _non_empty_text(progress_freshness.get("summary"))
    if progress_freshness_summary:
        progress_status_label = _progress_freshness_status_label(progress_freshness.get("status"))
        if progress_status_label:
            lines.append(f"- 研究进度信号: {progress_status_label}；{progress_freshness_summary}")
        else:
            lines.append(f"- 研究进度信号: {progress_freshness_summary}")
    if progress_freshness.get("latest_progress_time_label") and progress_freshness.get("latest_progress_summary"):
        lines.append(
            f"- 最近明确推进: {progress_freshness.get('latest_progress_time_label')}，"
            f"{progress_freshness.get('latest_progress_summary')}"
        )
    if runtime_reason:
        lines.append(f"- 决策原因: {runtime_reason}")
    if continuation_reason:
        lines.append(f"- continuation_reason: {continuation_reason}")
    if operator_status_card:
        lines.extend(
            [
                "",
                "## 操作员状态卡",
                "",
                f"- 当前处理态: {operator_status_card.get('handling_state_label') or operator_status_card.get('handling_state') or '未知'}",
                f"- 用户可见结论: {operator_status_card.get('user_visible_verdict') or 'none'}",
                f"- 当前聚焦: {operator_status_card.get('current_focus') or 'none'}",
            ]
        )
        if operator_status_card.get("owner_summary"):
            lines.append(f"- 责任说明: {operator_status_card.get('owner_summary')}")
        if operator_status_card.get("latest_truth_source_label") or operator_status_card.get("latest_truth_time"):
            truth_source = operator_status_card.get("latest_truth_source_label") or operator_status_card.get("latest_truth_source") or "unknown"
            truth_time = operator_status_card.get("latest_truth_time") or "unknown"
            lines.append(f"- 当前真相源: {truth_source} @ {truth_time}")
        if operator_status_card.get("human_surface_summary"):
            lines.append(
                f"- 人类查看面: `{operator_status_card.get('human_surface_freshness') or 'unknown'}`；"
                f"{operator_status_card.get('human_surface_summary')}"
            )
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    if bool(quality_review_followthrough.get("waiting_auto_re_review")):
        lines.extend(
            [
                "",
                "## 自动复评后续",
                "",
                f"- 当前状态: {quality_review_followthrough.get('state_label') or quality_review_followthrough.get('state') or '未知'}",
                (
                    "- 系统自动继续: 会"
                    if bool(quality_review_followthrough.get("auto_continue_expected"))
                    else "- 系统自动继续: 不会"
                ),
            ]
        )
        if quality_review_followthrough.get("summary"):
            lines.append(f"- 后续摘要: {quality_review_followthrough.get('summary')}")
        if quality_review_followthrough.get("blocking_reason"):
            lines.append(f"- 未自动继续原因: {quality_review_followthrough.get('blocking_reason')}")
        if quality_review_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {quality_review_followthrough.get('next_confirmation_signal')}")
    if gate_clearing_batch_followthrough:
        lines.extend(
            [
                "",
                "## Gate-Clearing Batch",
                "",
                f"- 当前状态: {gate_clearing_batch_followthrough.get('status') or 'unknown'}",
            ]
        )
        if gate_clearing_batch_followthrough.get("summary"):
            lines.append(f"- 当前判断: {gate_clearing_batch_followthrough.get('summary')}")
        if gate_clearing_batch_followthrough.get("failed_unit_count") is not None:
            lines.append(f"- 失败单元数: {gate_clearing_batch_followthrough.get('failed_unit_count')}")
        if gate_clearing_batch_followthrough.get("blocking_issue_count") is not None:
            lines.append(f"- 剩余 gate blocker: {gate_clearing_batch_followthrough.get('blocking_issue_count')}")
        if gate_clearing_batch_followthrough.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {gate_clearing_batch_followthrough.get('next_confirmation_signal')}")
    if module_surfaces:
        lines.extend(
            [
                "",
                "## 主线模块",
                "",
            ]
        )
        for module_name in ("controller_charter", "runtime", "eval_hygiene"):
            module_surface = dict(module_surfaces.get(module_name) or {})
            if not module_surface:
                continue
            lines.append(
                "- "
                + module_name
                + ": "
                + (module_surface.get("status_summary") or "none")
                + " 下一动作："
                + (module_surface.get("next_action_summary") or "none")
                + " ref: `"
                + (module_surface.get("summary_ref") or "none")
                + "`"
            )
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
            f"- 下一步建议: {next_step_summary}",
        ]
    )
    if autonomy_contract:
        lines.extend(["", "## 自治合同", ""])
        if autonomy_contract.get("summary"):
            lines.append(
                f"- 当前自治判断: {_display_text(autonomy_contract.get('summary')) or autonomy_contract.get('summary')}"
            )
        if autonomy_contract.get("next_signal"):
            lines.append(
                f"- 下一确认信号: {_display_text(autonomy_contract.get('next_signal')) or autonomy_contract.get('next_signal')}"
            )
        if autonomy_contract.get("recommended_command"):
            lines.append(f"- 恢复/续跑命令: `{autonomy_contract.get('recommended_command')}`")
        restore_point = dict(autonomy_contract.get("restore_point") or {})
        if restore_point.get("summary"):
            lines.append(
                f"- 恢复点: {_display_text(restore_point.get('summary')) or restore_point.get('summary')}"
            )
        latest_outer_loop_dispatch = dict(autonomy_contract.get("latest_outer_loop_dispatch") or {})
        if latest_outer_loop_dispatch.get("summary"):
            lines.append(
                "- 最近一次自治续跑: "
                + (
                    _display_text(latest_outer_loop_dispatch.get("summary"))
                    or latest_outer_loop_dispatch.get("summary")
                )
            )
    autonomy_soak_status = dict(payload.get("autonomy_soak_status") or {})
    if autonomy_soak_status:
        lines.extend(["", "## 自治 Proof / Soak", ""])
        if autonomy_soak_status.get("summary"):
            lines.append(
                f"- 当前自治证据: {_display_text(autonomy_soak_status.get('summary')) or autonomy_soak_status.get('summary')}"
            )
        if autonomy_soak_status.get("progress_freshness_status"):
            lines.append(f"- 进度新鲜度: `{autonomy_soak_status.get('progress_freshness_status')}`")
        if autonomy_soak_status.get("next_confirmation_signal"):
            lines.append(
                "- 下一确认信号: "
                + (
                    _display_text(autonomy_soak_status.get("next_confirmation_signal"))
                    or autonomy_soak_status.get("next_confirmation_signal")
                )
            )
    if quality_closure_truth:
        lines.extend(["", "## 质量闭环", ""])
        if quality_closure_truth.get("summary"):
            lines.append(
                f"- 当前质量判断: {_display_text(quality_closure_truth.get('summary')) or quality_closure_truth.get('summary')}"
            )
        if quality_execution_lane.get("summary"):
            lines.append(
                f"- 当前质量执行线: {_display_text(quality_execution_lane.get('summary')) or quality_execution_lane.get('summary')}"
            )
        for key in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "human_review_readiness",
            "publication_gate",
        ):
            basis_item = dict(quality_closure_basis.get(key) or {})
            summary = _display_text(basis_item.get("summary")) or basis_item.get("summary")
            if summary:
                lines.append(f"- {_QUALITY_CLOSURE_BASIS_LABELS.get(key, key)}: {summary}")
    if quality_review_agenda:
        lines.extend(["", "## 质量评审议程", ""])
        top_priority_issue = _display_text(quality_review_agenda.get("top_priority_issue")) or _non_empty_text(
            quality_review_agenda.get("top_priority_issue")
        )
        suggested_revision = _display_text(quality_review_agenda.get("suggested_revision")) or _non_empty_text(
            quality_review_agenda.get("suggested_revision")
        )
        next_review_focus = _display_text(quality_review_agenda.get("next_review_focus")) or _non_empty_text(
            quality_review_agenda.get("next_review_focus")
        )
        if top_priority_issue:
            lines.append(f"- 当前优先问题: {top_priority_issue}")
        if suggested_revision:
            lines.append(f"- 建议修订动作: {suggested_revision}")
        if next_review_focus:
            lines.append(f"- 下一轮复评重点: {next_review_focus}")
    if quality_review_loop:
        lines.extend(["", "## 质量评审闭环", ""])
        current_phase_label = _display_text(quality_review_loop.get("current_phase_label")) or _non_empty_text(
            quality_review_loop.get("current_phase_label")
        )
        recommended_next_phase_label = _display_text(
            quality_review_loop.get("recommended_next_phase_label")
        ) or _non_empty_text(quality_review_loop.get("recommended_next_phase_label"))
        summary = _display_text(quality_review_loop.get("summary")) or _non_empty_text(quality_review_loop.get("summary"))
        recommended_next_action = _display_text(quality_review_loop.get("recommended_next_action")) or _non_empty_text(
            quality_review_loop.get("recommended_next_action")
        )
        if current_phase_label:
            lines.append(f"- 当前闭环阶段: {current_phase_label}")
        if recommended_next_phase_label:
            lines.append(f"- 下一跳: {recommended_next_phase_label}")
        if isinstance(quality_review_loop.get("blocking_issue_count"), int):
            lines.append(f"- 当前阻塞数: {quality_review_loop.get('blocking_issue_count')}")
        if summary:
            lines.append(f"- 闭环摘要: {summary}")
        if recommended_next_action:
            lines.append(f"- 下一动作: {recommended_next_action}")
        for item in [
            _display_text(issue) or _non_empty_text(issue)
            for issue in (quality_review_loop.get("blocking_issues") or [])
        ]:
            if item:
                lines.append(f"- 当前阻塞项: {item}")
        for focus in [
            _display_text(item) or _non_empty_text(item)
            for item in (quality_review_loop.get("next_review_focus") or [])
        ]:
            if focus:
                lines.append(f"- 复评关注点: {focus}")
    if quality_revision_plan:
        lines.extend(["", "## 质量修订计划", ""])
        overall_diagnosis = _display_text(quality_revision_plan.get("overall_diagnosis")) or _non_empty_text(
            quality_revision_plan.get("overall_diagnosis")
        )
        if overall_diagnosis:
            lines.append(f"- 总体诊断: {overall_diagnosis}")
        for item in [dict(entry) for entry in (quality_revision_plan.get("items") or []) if isinstance(entry, dict)]:
            priority = (_non_empty_text(item.get("priority")) or "p1").upper()
            dimension = _QUALITY_REVISION_DIMENSION_LABELS.get(
                _non_empty_text(item.get("dimension")) or "",
                _humanize_token(item.get("dimension")) or "未命名维度",
            )
            route_target = _display_text(item.get("route_target")) or _non_empty_text(item.get("route_target"))
            item_title = f"{priority} [{dimension}]"
            if route_target:
                item_title = f"{item_title} -> {route_target}"
            action = _display_text(item.get("action")) or _non_empty_text(item.get("action"))
            rationale = _display_text(item.get("rationale")) or _non_empty_text(item.get("rationale"))
            done_criteria = _display_text(item.get("done_criteria")) or _non_empty_text(item.get("done_criteria"))
            if action:
                lines.append(f"- {item_title}: {action}")
            else:
                lines.append(f"- {item_title}")
            if rationale:
                lines.append(f"- 修订理由: {rationale}")
            if done_criteria:
                lines.append(f"- 完成标准: {done_criteria}")
        for focus in [
            _display_text(item) or _non_empty_text(item)
            for item in (quality_revision_plan.get("next_review_focus") or [])
        ]:
            if focus:
                lines.append(f"- 下一轮复评关注: {focus}")
    if recovery_contract:
        lines.extend(["", "## 恢复合同", ""])
        if recovery_action_mode:
            lines.append(f"- 恢复模式: {recovery_action_mode}")
        if recovery_contract.get("summary"):
            lines.append(
                f"- 合同摘要: {_display_text(recovery_contract.get('summary')) or recovery_contract.get('summary')}"
            )
        for item in recovery_steps:
            title = _non_empty_text(item.get("title")) or _humanize_token(item.get("step_id")) or "未命名步骤"
            surface_label = (_non_empty_text(item.get("surface_kind")) or "unknown").replace("_", "-")
            command = _non_empty_text(item.get("command")) or "none"
            lines.append(f"- {title} [{surface_label}]: `{command}`")
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
            summary = _display_text(item.get("summary")) or str(item.get("summary") or "").strip()
            lines.append(f"- {time_label}: {summary}")
    else:
        lines.append("- 目前没有可用的阶段事件。")
    supervision = dict(payload.get("supervision") or {})
    lines.extend(["", "## 监督入口", ""])
    supervision_labels = {
        "browser_url": "监控入口",
        "quest_session_api_url": "会话接口",
        "active_run_id": "active_run_id",
        "launch_report_path": "launch_report_path",
    }
    for key in ("browser_url", "quest_session_api_url", "active_run_id", "launch_report_path"):
        value = str(supervision.get(key) or "").strip()
        if value:
            lines.append(f"- {supervision_labels[key]}: `{value}`")
    return "\n".join(lines) + "\n"
