from __future__ import annotations

import json
import shlex
import sys
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Mapping

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
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.evaluation_summary import (
    build_same_line_route_truth,
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
from med_autoscience.study_task_intake import (
    build_task_intake_progress_override,
    read_latest_task_intake,
    summarize_task_intake,
)


def _controller_override(name: str, default: Any) -> Any:
    controller_module = sys.modules.get("med_autoscience.controllers.study_progress")
    if controller_module is None:
        return default
    return getattr(controller_module, name, default)


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
    "methods_completeness_incomplete": "医学论文方法报告仍不完整，需补齐研究设计、队列、变量、模型、验证和统计分析说明。",
    "statistical_reporting_incomplete": "统计报告仍不完整，需补齐汇总格式、P 值和亚组检验说明。",
    "table_figure_claim_map_missing_or_incomplete": "表图与论文 claim 的对应关系仍未补齐。",
    "clinical_actionability_incomplete": "分型/真实世界论文仍缺少临床可行动性说明，包括治疗缺口和随访或结局相关性。",
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
    "methods_completeness_incomplete": "医学论文方法报告仍不完整，需补齐研究设计、队列、变量、模型、验证和统计分析说明。",
    "statistical_reporting_incomplete": "统计报告仍不完整，需补齐汇总格式、P 值和亚组检验说明。",
    "table_figure_claim_map_missing_or_incomplete": "表图与论文 claim 的对应关系仍未补齐。",
    "clinical_actionability_incomplete": "分型/真实世界论文仍缺少临床可行动性说明，包括治疗缺口和随访或结局相关性。",
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


def _load_controller(module_name: str):
    return import_module(f"med_autoscience.controllers.{module_name}")


class _LazyModuleProxy:
    def __init__(self, loader: Callable[[], Any]) -> None:
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_module", None)

    def _resolve(self):
        module = object.__getattribute__(self, "_module")
        if module is None:
            module = object.__getattribute__(self, "_loader")()
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        setattr(self._resolve(), name, value)


gate_clearing_batch = _LazyModuleProxy(lambda: _load_controller("gate_clearing_batch"))
quality_repair_batch = _LazyModuleProxy(lambda: _load_controller("quality_repair_batch"))
study_runtime_router = _LazyModuleProxy(lambda: _load_controller("study_runtime_router"))
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


def _mapping_copy(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _runtime_control_pickup_refs(
    *,
    evaluation_summary_ref: object = None,
    refs_payload: Mapping[str, Any] | None = None,
    publication_eval_ref: object = None,
    controller_decision_ref: object = None,
    runtime_supervision_ref: object = None,
    runtime_watch_ref: object = None,
) -> list[str]:
    refs = dict(refs_payload or {})
    candidates = [
        _non_empty_text(evaluation_summary_ref),
        _non_empty_text(refs.get("evaluation_summary_path")),
        _non_empty_text(publication_eval_ref),
        _non_empty_text(refs.get("publication_eval_path")),
        _non_empty_text(controller_decision_ref),
        _non_empty_text(refs.get("controller_decision_path")),
        _non_empty_text(runtime_supervision_ref),
        _non_empty_text(refs.get("runtime_supervision_path")),
        _non_empty_text(runtime_watch_ref),
        _non_empty_text(refs.get("runtime_watch_report_path")),
    ]
    ordered_refs: list[str] = []
    for ref in candidates:
        if ref is None or ref in ordered_refs:
            continue
        ordered_refs.append(ref)
    return ordered_refs


def _normalized_research_runtime_control_projection_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    direct_projection = _mapping_copy(payload.get("research_runtime_control_projection"))
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    interrupt_policy = _non_empty_text(intervention_lane.get("recommended_action_id"))
    gate_lane = _non_empty_text(intervention_lane.get("lane_id"))
    gate_summary = _non_empty_text(intervention_lane.get("summary"))
    operator_status_card = _mapping_copy(payload.get("operator_status_card"))
    autonomy_contract = _mapping_copy(payload.get("autonomy_contract"))
    restore_point = _mapping_copy(autonomy_contract.get("restore_point"))
    refs = _mapping_copy(payload.get("refs"))
    pickup_refs = _runtime_control_pickup_refs(refs_payload=refs)
    default_projection: dict[str, Any] = {
        "surface_kind": "research_runtime_control_projection",
        "study_session_owner": {
            "runtime_owner": "upstream_hermes_agent",
            "study_owner": "med-autoscience",
            "executor_owner": "med_deepscientist",
        },
        "session_lineage_surface": {
            "surface_kind": "study_progress",
            "field_path": "family_checkpoint_lineage",
            "resume_contract_field": "family_checkpoint_lineage.resume_contract",
            "continuation_state_field": "continuation_state",
            "active_run_id_field": "supervision.active_run_id",
        },
        "restore_point_surface": {
            "surface_kind": "study_progress",
            "field_path": "autonomy_contract.restore_point",
            "lineage_anchor_field": "family_checkpoint_lineage.resume_contract",
            "summary": _non_empty_text(restore_point.get("summary")),
        },
        "progress_cursor_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
        },
        "progress_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
            "fallback_field_path": "next_system_action",
            "current_focus": _non_empty_text(operator_status_card.get("current_focus")),
        },
        "artifact_inventory_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs",
        },
        "artifact_pickup_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs.evaluation_summary_path",
            "fallback_fields": [
                "refs.publication_eval_path",
                "refs.controller_decision_path",
                "refs.runtime_supervision_path",
                "refs.runtime_watch_report_path",
            ],
            "pickup_refs": pickup_refs,
        },
        "command_templates": {
            "resume": None,
            "check_progress": None,
            "check_runtime_status": None,
        },
        "research_gate_surface": {
            "surface_kind": "study_progress",
            "approval_gate_field": "needs_physician_decision",
            "approval_gate_owner": "mas_controller",
            "approval_gate_required": bool(payload.get("needs_physician_decision")),
            "interrupt_policy_field": "intervention_lane.recommended_action_id",
            "interrupt_policy": interrupt_policy,
            "gate_lane_field": "intervention_lane.lane_id",
            "gate_lane": gate_lane,
            "gate_summary_field": "intervention_lane.summary",
            "gate_summary": gate_summary,
        },
    }
    if not direct_projection:
        return default_projection

    normalized = dict(default_projection)
    normalized.update(direct_projection)

    nested_fields = (
        "study_session_owner",
        "session_lineage_surface",
        "restore_point_surface",
        "progress_cursor_surface",
        "progress_surface",
        "artifact_inventory_surface",
        "artifact_pickup_surface",
        "command_templates",
        "research_gate_surface",
    )
    for field_name in nested_fields:
        merged = _mapping_copy(default_projection.get(field_name))
        merged.update(_mapping_copy(direct_projection.get(field_name)))
        normalized[field_name] = merged

    command_templates = _mapping_copy(normalized.get("command_templates"))
    command_templates.setdefault("resume", None)
    command_templates.setdefault("check_progress", None)
    command_templates.setdefault("check_runtime_status", None)
    normalized["command_templates"] = command_templates

    artifact_pickup_surface = _mapping_copy(normalized.get("artifact_pickup_surface"))
    merged_pickup_refs: list[str] = []
    for ref in pickup_refs:
        if ref not in merged_pickup_refs:
            merged_pickup_refs.append(ref)
    for item in artifact_pickup_surface.get("pickup_refs") or []:
        text = _non_empty_text(item)
        if text is None or text in merged_pickup_refs:
            continue
        merged_pickup_refs.append(text)
    artifact_pickup_surface["pickup_refs"] = merged_pickup_refs
    normalized["artifact_pickup_surface"] = artifact_pickup_surface

    research_gate_surface = _mapping_copy(normalized.get("research_gate_surface"))
    if not isinstance(research_gate_surface.get("approval_gate_required"), bool):
        research_gate_surface["approval_gate_required"] = bool(payload.get("needs_physician_decision"))
    if _non_empty_text(research_gate_surface.get("interrupt_policy")) is None:
        research_gate_surface["interrupt_policy"] = interrupt_policy
    if _non_empty_text(research_gate_surface.get("gate_lane")) is None:
        research_gate_surface["gate_lane"] = gate_lane
    if _non_empty_text(research_gate_surface.get("gate_summary")) is None:
        research_gate_surface["gate_summary"] = gate_summary
    research_gate_surface.setdefault("gate_summary_field", "intervention_lane.summary")
    normalized["research_gate_surface"] = research_gate_surface

    restore_point_surface = _mapping_copy(normalized.get("restore_point_surface"))
    if _non_empty_text(restore_point_surface.get("summary")) is None:
        restore_point_surface["summary"] = _non_empty_text(restore_point.get("summary"))
    normalized["restore_point_surface"] = restore_point_surface

    progress_surface = _mapping_copy(normalized.get("progress_surface"))
    if _non_empty_text(progress_surface.get("current_focus")) is None:
        progress_surface["current_focus"] = _non_empty_text(operator_status_card.get("current_focus"))
    normalized["progress_surface"] = progress_surface

    return normalized


def _normalized_quality_execution_lane_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    direct_lane = _mapping_copy(payload.get("quality_execution_lane"))
    if direct_lane:
        return direct_lane
    module_surfaces = _mapping_copy(payload.get("module_surfaces"))
    eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    fallback_lane = _mapping_copy(eval_hygiene_surface.get("quality_execution_lane"))
    return fallback_lane or None


def _normalized_same_line_route_surface_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    direct_surface = _mapping_copy(payload.get("same_line_route_surface"))
    if direct_surface:
        return direct_surface
    module_surfaces = _mapping_copy(payload.get("module_surfaces"))
    eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    fallback_surface = _mapping_copy(eval_hygiene_surface.get("same_line_route_surface"))
    return fallback_surface or None


def _normalized_same_line_route_truth_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if "same_line_route_truth" in payload and payload.get("same_line_route_truth") is None:
        return None
    direct_truth = _mapping_copy(payload.get("same_line_route_truth"))
    if direct_truth:
        return direct_truth
    module_surfaces = _mapping_copy(payload.get("module_surfaces"))
    eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
    fallback_truth = _mapping_copy(eval_hygiene_surface.get("same_line_route_truth"))
    if fallback_truth:
        return fallback_truth
    derived_truth = build_same_line_route_truth(
        quality_closure_truth=_mapping_copy(payload.get("quality_closure_truth")),
        quality_execution_lane=_normalized_quality_execution_lane_payload(payload) or {},
    )
    return derived_truth or None


def _normalize_study_progress_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    module_surfaces = _mapping_copy(normalized.get("module_surfaces"))
    if module_surfaces:
        eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
        if eval_hygiene_surface:
            eval_hygiene_surface["quality_execution_lane"] = _mapping_copy(
                eval_hygiene_surface.get("quality_execution_lane")
            ) or None
            eval_hygiene_surface["same_line_route_surface"] = _mapping_copy(
                eval_hygiene_surface.get("same_line_route_surface")
            ) or None
            eval_hygiene_surface["same_line_route_truth"] = _mapping_copy(
                eval_hygiene_surface.get("same_line_route_truth")
            ) or build_same_line_route_truth(
                quality_closure_truth=_mapping_copy(eval_hygiene_surface.get("quality_closure_truth")),
                quality_execution_lane=_mapping_copy(eval_hygiene_surface.get("quality_execution_lane")),
            ) or None
            module_surfaces["eval_hygiene"] = eval_hygiene_surface
            normalized["module_surfaces"] = module_surfaces
    normalized["quality_execution_lane"] = _normalized_quality_execution_lane_payload(normalized)
    normalized["same_line_route_truth"] = _normalized_same_line_route_truth_payload(normalized)
    normalized["same_line_route_surface"] = _normalized_same_line_route_surface_payload(normalized)
    normalized["research_runtime_control_projection"] = _normalized_research_runtime_control_projection_payload(normalized)
    if _publication_supervisor_blocks_same_line_route(_mapping_copy(normalized.get("publication_supervisor_state"))):
        normalized["same_line_route_truth"] = None
        normalized["same_line_route_surface"] = None
        if module_surfaces:
            eval_hygiene_surface = _mapping_copy(module_surfaces.get("eval_hygiene"))
            if eval_hygiene_surface:
                eval_hygiene_surface["same_line_route_truth"] = None
                eval_hygiene_surface["same_line_route_surface"] = None
                module_surfaces["eval_hygiene"] = eval_hygiene_surface
                normalized["module_surfaces"] = module_surfaces
    return normalized


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


def _publication_supervisor_blocks_same_line_route(publication_supervisor_state: Mapping[str, Any] | None) -> bool:
    if not isinstance(publication_supervisor_state, Mapping):
        return False
    current_required_action = _non_empty_text(publication_supervisor_state.get("current_required_action"))
    if current_required_action == "return_to_publishability_gate":
        return True
    return bool(publication_supervisor_state.get("bundle_tasks_downstream_only"))


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
