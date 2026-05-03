from __future__ import annotations

from typing import Any

READINESS_ACTION_BY_SURFACE: dict[str, dict[str, str]] = {
    "literature_scout": {
        "action_id": "complete_literature_scout",
        "action_label": "补文献",
        "semantic_label": "补文献",
        "action_summary": "补齐可审计文献 scout、检索日期、anchor papers、guideline 和近邻文献。",
    },
    "literature_provider_runtime": {
        "action_id": "run_provider_literature_scout",
        "action_label": "联网补文献",
        "semantic_label": "补文献",
        "action_summary": "运行 provider-backed 文献摄取，保留 provider provenance、检索日期和 citation ledger refs。",
    },
    "study_line_selection": {
        "action_id": "rescore_study_line",
        "action_label": "重评分路线",
        "semantic_label": "路线裁决",
        "action_summary": "重新比较候选切入点，并冻结最强 study line 与 stop threshold。",
    },
    "route_decision_orchestrator": {
        "action_id": "materialize_route_decision",
        "action_label": "写入路线裁决",
        "semantic_label": "路线裁决",
        "action_summary": "把路线选择、route-back 或 switch-line 决策写入 controller decision 投影。",
    },
    "archetype_analysis_contract": {
        "action_id": "freeze_statistical_contract",
        "action_label": "冻结分析合同",
        "semantic_label": "统计 blocker",
        "action_summary": "按 study archetype 冻结统计纪律合同和失败条件。",
    },
    "statistical_discipline_operations": {
        "action_id": "resolve_statistical_blockers",
        "action_label": "处理统计 blocker",
        "semantic_label": "统计 blocker",
        "action_summary": "逐项处理缺失值、precision、外部验证、多重性、临床效用和敏感性分析 blocker/waiver。",
    },
    "bounded_analysis_candidate_board": {
        "action_id": "enter_bounded_analysis",
        "action_label": "进入 bounded analysis",
        "semantic_label": "统计 blocker",
        "action_summary": "把补充分析绑定到 target claim、证据收益、统计风险和决策理由。",
    },
    "stop_loss_memo": {
        "action_id": "decide_stop_loss_or_switch_line",
        "action_label": "止损换线",
        "semantic_label": "路线裁决",
        "action_summary": "写入 stop-loss memo，决定继续、route-back、止损或换线。",
    },
    "target_journal_writing_layer": {
        "action_id": "start_ai_reviewer_journal_loop",
        "action_label": "启动 AI reviewer",
        "semantic_label": "写作授权",
        "action_summary": "冻结目标期刊写作层并启动 AI reviewer 写作/质量闭环。",
    },
    "revision_rebuttal_loop": {
        "action_id": "start_revision_rebuttal_loop",
        "action_label": "启动返修",
        "semantic_label": "返修",
        "action_summary": "摄取 reviewer comments，生成 rebuttal action matrix、analysis repair 和 AI reviewer recheck。",
    },
    "authoring_runtime_authorization": {
        "action_id": "authorize_manuscript_drafting",
        "action_label": "授权写作",
        "semantic_label": "写作授权",
        "action_summary": "检查目标期刊层、claim/display map、ledger 和 AI reviewer provenance 后再授权 full manuscript drafting。",
    },
    "real_study_soak_matrix_evidence": {
        "action_id": "rebuild_submission_package_after_soak",
        "action_label": "重建投稿包",
        "semantic_label": "真实 soak",
        "action_summary": "补齐多 study soak proof 后从 canonical source 重建投稿包并审计。",
    },
    "real_workspace_soak_monitor": {
        "action_id": "run_real_workspace_soak_monitor",
        "action_label": "运行真实 soak",
        "semantic_label": "真实 soak",
        "action_summary": "从真实或脱敏 study workspace 只读检查多 study soak ready/partial/blocked 状态。",
    },
}


def _compact_string_list(value: Any, *, limit: int = 12) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _compact_record(value: Any, keys: tuple[str, ...]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact: dict[str, Any] = {}
    for key in keys:
        if key in value:
            compact[key] = value[key]
    return compact or None


def _compact_events(value: Any, *, limit: int = 5) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    events: list[dict[str, Any]] = []
    keys = ("timestamp", "time_label", "category", "title", "summary", "source", "artifact_path")
    for item in value:
        event = _compact_record(item, keys)
        if event is not None:
            events.append(event)
        if len(events) >= limit:
            break
    return events


def _compact_task_intake(value: Any) -> dict[str, Any] | None:
    task_intake = _compact_record(
        value,
        (
            "task_id",
            "study_id",
            "emitted_at",
            "entry_mode",
            "task_intent",
            "journal_target",
            "first_cycle_outputs",
        ),
    )
    if task_intake is None:
        return None
    if isinstance(task_intake.get("first_cycle_outputs"), list):
        task_intake["first_cycle_outputs"] = _compact_string_list(task_intake["first_cycle_outputs"], limit=8)
    source = value if isinstance(value, dict) else {}
    constraints = _compact_string_list(source.get("constraints"), limit=8)
    if constraints:
        task_intake["constraints"] = constraints
    revision_intake = _compact_record(
        source.get("revision_intake"),
        ("kind", "status", "handoff_required", "reactivation_required", "checklist"),
    )
    if revision_intake is not None:
        if isinstance(revision_intake.get("checklist"), list):
            revision_intake["checklist"] = _compact_string_list(revision_intake["checklist"], limit=12)
        task_intake["revision_intake"] = revision_intake
    return task_intake


def _compact_runtime_efficiency(value: Any) -> dict[str, Any] | None:
    runtime_efficiency = _compact_record(
        value,
        (
            "run_id",
            "telemetry_path",
            "prompt_bytes",
            "stdout_bytes",
            "tool_result_bytes_total",
            "tool_result_bytes_after_compaction_total",
            "tool_result_bytes_saved_total",
            "compacted_tool_result_count",
            "full_detail_tool_call_count",
            "mcp_tool_call_count",
            "tool_call_budget",
            "tool_call_count",
            "tool_call_budget_remaining",
            "tool_call_budget_exceeded",
            "unique_command_count",
            "read_tool_call_count",
            "repeated_read_result_count",
            "repeated_read_ratio",
            "full_detail_count",
            "evidence_packet_index_path",
            "evidence_packet_count",
            "gate_replay_hit_count",
            "latest_gate_replay_at",
            "gate_replay_status",
            "gate_replay_ref",
            "gate_cache",
            "summary",
        ),
    )
    if runtime_efficiency is None:
        return None
    gate_cache_surfaces = []
    if isinstance(value, dict):
        gate_cache_surfaces = [
            item
            for item in value.get("gate_cache_surfaces", [])
            if isinstance(item, dict)
        ][:5]
    if gate_cache_surfaces:
        runtime_efficiency["gate_cache_surfaces"] = gate_cache_surfaces
    return runtime_efficiency


def _compact_module_surfaces(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    module_surfaces: dict[str, Any] = {}
    keys = (
        "module",
        "surface_kind",
        "summary_id",
        "summary_ref",
        "status_summary",
        "next_action_summary",
        "health_status",
        "runtime_decision",
        "runtime_reason",
        "overall_verdict",
        "primary_claim_status",
        "requires_controller_decision",
    )
    for module_name, module_payload in value.items():
        module_surface = _compact_record(module_payload, keys)
        if module_surface is not None:
            module_surfaces[module_name] = module_surface
    return module_surfaces or None


def _compact_medical_paper_readiness(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        (
            "surface",
            "overall_status",
            "ready_count",
            "required_count",
            "quality_claim_authorized",
            "mechanical_projection_can_authorize_quality",
            "next_action",
        ),
    )
    if compact is None:
        return None
    missing_surfaces: list[dict[str, Any]] = []
    for item in value.get("capability_surfaces") or []:
        if not isinstance(item, dict):
            continue
        if not bool(item.get("required_for_ready")) or item.get("status") == "present":
            continue
        missing = _compact_readiness_missing_surface(item)
        if missing is not None:
            missing_surfaces.append(missing)
    compact["missing_surfaces"] = missing_surfaces[:8]
    return compact


def _compact_readiness_missing_surface(item: dict[str, Any]) -> dict[str, Any] | None:
    missing = _compact_record(
        item,
        ("surface_key", "status", "missing_reason", "artifact_path", "evidence_refs"),
    )
    if missing is None:
        return None
    action = READINESS_ACTION_BY_SURFACE.get(str(missing.get("surface_key") or "").strip())
    if action:
        missing.update(
            {
                "action_id": action["action_id"],
                "action_label": action["action_label"],
                "action_summary": action["action_summary"],
            }
        )
    return missing


def compact_study_progress_projection(payload: dict[str, Any]) -> dict[str, Any]:
    compact_keys = (
        "schema_version",
        "generated_at",
        "truth_epoch",
        "runtime_health_epoch",
        "study_id",
        "study_root",
        "quest_id",
        "quest_root",
        "current_stage",
        "current_stage_summary",
        "paper_stage",
        "paper_stage_summary",
        "next_system_action",
        "auto_runtime_parked",
        "parked_state",
        "parked_owner",
        "resource_release_expected",
        "awaiting_explicit_wakeup",
        "auto_execution_complete",
        "reopen_policy",
        "needs_physician_decision",
        "needs_user_decision",
        "physician_decision_summary",
        "user_decision_summary",
        "runtime_decision",
        "runtime_reason",
        "progress_freshness",
        "recommended_command",
    )
    compact = {key: payload[key] for key in compact_keys if key in payload}
    compact["current_blockers"] = _compact_string_list(payload.get("current_blockers"), limit=12)
    compact["latest_events"] = _compact_events(payload.get("latest_events"))

    for key, keys in {
        "intervention_lane": (
            "lane_id",
            "title",
            "severity",
            "summary",
            "recommended_action_id",
            "repair_mode",
            "route_target",
            "route_target_label",
            "route_key_question",
            "route_summary",
        ),
        "operator_verdict": (
            "surface_kind",
            "study_id",
            "lane_id",
            "severity",
            "decision_mode",
            "needs_intervention",
            "focus_scope",
            "summary",
            "reason_summary",
            "primary_step_id",
            "primary_surface_kind",
            "primary_command",
        ),
        "operator_status_card": (
            "surface_kind",
            "study_id",
            "handling_state",
            "handling_state_label",
            "owner_summary",
            "current_focus",
            "latest_truth_time",
            "latest_truth_source",
            "human_surface_freshness",
            "human_surface_summary",
            "next_confirmation_signal",
            "user_visible_verdict",
            "runtime_efficiency_summary",
            "runtime_efficiency_refs",
            "runtime_efficiency_metrics",
        ),
        "autonomy_soak_status": (
            "surface_kind",
            "status",
            "summary",
            "autonomy_state",
            "dispatch_status",
            "route_target",
            "route_target_label",
            "route_key_question",
            "progress_freshness_status",
            "next_confirmation_signal",
        ),
        "quality_closure_truth": ("state", "summary", "current_required_action", "route_target"),
        "quality_execution_lane": (
            "lane_id",
            "lane_label",
            "repair_mode",
            "route_target",
            "route_key_question",
            "summary",
            "why_now",
        ),
        "quality_review_loop": (
            "policy_id",
            "loop_id",
            "closure_state",
            "lane_id",
            "current_phase",
            "current_phase_label",
            "recommended_next_phase",
            "blocking_issue_count",
            "summary",
            "recommended_next_action",
            "re_review_ready",
        ),
        "supervision": (
            "browser_url",
            "quest_session_api_url",
            "active_run_id",
            "health_status",
            "supervisor_tick_status",
            "supervisor_tick_required",
            "supervisor_tick_summary",
            "supervisor_tick_latest_recorded_at",
            "launch_report_path",
        ),
        "continuation_state": (
            "quest_status",
            "active_run_id",
            "continuation_policy",
            "continuation_anchor",
            "continuation_reason",
            "runtime_state_path",
        ),
    }.items():
        item = _compact_record(payload.get(key), keys)
        if item is not None:
            compact[key] = item

    for key in ("recommended_commands", "refs"):
        value = payload.get(key)
        if isinstance(value, list):
            compact[key] = value[:5]
        elif isinstance(value, dict):
            compact[key] = dict(value)

    for key, builder in {
        "task_intake": _compact_task_intake,
        "runtime_efficiency": _compact_runtime_efficiency,
        "module_surfaces": _compact_module_surfaces,
        "medical_paper_readiness": _compact_medical_paper_readiness,
        "study_truth_snapshot": _compact_study_truth_snapshot,
        "runtime_health_snapshot": _compact_runtime_health_snapshot,
        "control_plane_snapshot": _compact_control_plane_snapshot,
    }.items():
        item = builder(payload.get(key))
        if item is not None:
            compact[key] = item

    compact["mcp_projection"] = {
        "surface_kind": "mcp_compacted_study_progress_projection",
        "source_surface_kind": "study_progress",
        "compacted": True,
        "full_detail_surface": "CLI study-progress --format json",
    }
    return compact


def _compact_study_truth_snapshot(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _compact_record(
        value,
        (
            "truth_epoch",
            "authority_epoch",
            "canonical_next_action",
            "blocking_reasons",
            "dominant_authority_refs",
            "allowed_controller_actions",
            "package_state",
            "writer_epoch",
            "source_signature",
        ),
    )


def _compact_runtime_health_snapshot(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _compact_record(
        value,
        (
            "runtime_health_epoch",
            "canonical_runtime_action",
            "attempt_state",
            "retry_budget_remaining",
            "worker_liveness_state",
            "supervisor_state",
            "dominant_runtime_refs",
            "blocking_reasons",
            "allowed_controller_actions",
            "source_signature",
        ),
    )


def _compact_control_plane_snapshot(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _compact_record(
        value,
        (
            "control_state",
            "canonical_next_action",
            "canonical_runtime_action",
            "dispatch_gate",
            "route_authorization",
            "blocking_reasons",
            "allowed_controller_actions",
            "authority_refs",
            "quality_gate_relaxation_allowed",
        ),
    )


def compact_study_runtime_result_for_mcp(payload: dict[str, Any]) -> dict[str, Any]:
    compact = dict(payload)
    progress_projection = payload.get("progress_projection")
    if isinstance(progress_projection, dict):
        compact["progress_projection"] = compact_study_progress_projection(progress_projection)
        compact["mcp_projection"] = {
            "surface_kind": "mcp_compacted_study_runtime_status",
            "compacted_progress_projection": True,
        }
    return compact


def _render_mcp_progress_identity(compact: dict[str, Any]) -> list[str]:
    lines = [
        "# 研究进度",
        "",
        f"- study_id: `{compact.get('study_id') or 'unknown'}`",
        f"- quest_id: `{compact.get('quest_id') or 'unknown'}`",
    ]
    quest_root = compact.get("quest_root")
    if quest_root:
        lines.append(f"- quest_root: `{quest_root}`")
    return lines


def _render_mcp_progress_stage(compact: dict[str, Any]) -> list[str]:
    current_stage = compact.get("current_stage") or "unknown"
    paper_stage = compact.get("paper_stage") or "unknown"
    lines = [
        f"- 当前阶段: `{current_stage}`",
        f"- 论文阶段: `{paper_stage}`",
    ]
    stage_summary = str(compact.get("current_stage_summary") or "").strip()
    if stage_summary:
        lines.append(f"- 阶段摘要: {stage_summary}")
    paper_summary = str(compact.get("paper_stage_summary") or "").strip()
    if paper_summary:
        lines.append(f"- 论文摘要: {paper_summary}")
    return lines


def _render_mcp_progress_supervision(compact: dict[str, Any]) -> list[str]:
    supervision = compact.get("supervision") if isinstance(compact.get("supervision"), dict) else {}
    active_run_id = str((supervision or {}).get("active_run_id") or "").strip()
    health_status = str((supervision or {}).get("health_status") or "").strip()
    if not active_run_id and not health_status:
        return []
    run_text = active_run_id or "none"
    health_text = health_status or "unknown"
    return [f"- run/health: `{run_text}` / `{health_text}`"]


def _render_mcp_progress_runtime_state(compact: dict[str, Any]) -> list[str]:
    parked_projection = compact.get("auto_runtime_parked")
    parked = (
        parked_projection.get("parked")
        if isinstance(parked_projection, dict)
        else parked_projection
    )
    parked_state = compact.get("parked_state")
    awaiting_wakeup = compact.get("awaiting_explicit_wakeup")
    return [f"- parked: `{parked}`；state: `{parked_state or 'none'}`；awaiting_wakeup: `{awaiting_wakeup}`"]


def _render_mcp_progress_operator_and_action(compact: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    operator_status = (
        compact.get("operator_status_card")
        if isinstance(compact.get("operator_status_card"), dict)
        else {}
    )
    user_visible_verdict = str((operator_status or {}).get("user_visible_verdict") or "").strip()
    if user_visible_verdict:
        lines.append(f"- 操作判断: {user_visible_verdict}")

    next_action = str(compact.get("next_system_action") or "").strip()
    if next_action:
        lines.append(f"- 下一步: {next_action}")
    return lines


def _render_mcp_progress_blockers(compact: dict[str, Any]) -> list[str]:
    blockers = _compact_string_list(compact.get("current_blockers"), limit=8)
    if not blockers:
        return []
    return ["", "## 当前阻塞", *[f"- {item}" for item in blockers]]


def _render_mcp_progress_medical_paper_readiness(compact: dict[str, Any]) -> list[str]:
    readiness = _medical_paper_readiness_payload(compact)
    if not readiness:
        return []
    lines = _mcp_medical_paper_readiness_header(readiness)
    next_action_summary = _mcp_medical_paper_next_action_summary(readiness)
    if next_action_summary:
        lines.append(f"- 下一动作: {next_action_summary}")
    for item in _mcp_medical_paper_missing_surfaces(readiness):
        lines.append(_mcp_medical_paper_missing_surface_line(item))
        lines.append(_mcp_medical_paper_missing_surface_compat_line(item))
    lines.append(f"- quality_claim_authorized: `{readiness.get('quality_claim_authorized')}`")
    lines.append(
        "- mechanical_projection_can_authorize_quality: "
        f"`{readiness.get('mechanical_projection_can_authorize_quality')}`"
    )
    return lines


def _medical_paper_readiness_payload(compact: dict[str, Any]) -> dict[str, Any]:
    return (
        compact.get("medical_paper_readiness")
        if isinstance(compact.get("medical_paper_readiness"), dict)
        else {}
    )


def _mcp_medical_paper_readiness_header(readiness: dict[str, Any]) -> list[str]:
    return [
        "",
        "## Medical Paper Readiness",
        f"- readiness: `{readiness.get('overall_status') or 'unknown'}`；"
        f"`{readiness.get('ready_count')}/{readiness.get('required_count')}`",
    ]


def _mcp_medical_paper_next_action_summary(readiness: dict[str, Any]) -> str:
    next_action = readiness.get("next_action") if isinstance(readiness.get("next_action"), dict) else {}
    return str((next_action or {}).get("summary") or "").strip()


def _mcp_medical_paper_missing_surfaces(readiness: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in readiness.get("missing_surfaces") or [] if isinstance(item, dict)]


def _mcp_medical_paper_missing_surface_line(item: dict[str, Any]) -> str:
    surface_key = str(item.get("surface_key") or "unknown").strip() or "unknown"
    status = str(item.get("status") or "unknown").strip() or "unknown"
    missing_reason = str(item.get("missing_reason") or "unknown").strip() or "unknown"
    action = READINESS_ACTION_BY_SURFACE.get(surface_key, {})
    semantic_label = action.get("semantic_label") or str(item.get("action_label") or "缺失 surface").strip()
    action_summary = str(item.get("action_summary") or "").strip() or missing_reason
    durable_ref = _mcp_readiness_surface_durable_ref(item)
    suffix = f"；ref: `{durable_ref}`" if durable_ref else ""
    return (
        f"- {semantic_label}: {action_summary}"
        f"（surface: `{surface_key}`；status: `{status}`；reason: `{missing_reason}`{suffix}）"
    )


def _mcp_medical_paper_missing_surface_compat_line(item: dict[str, Any]) -> str:
    surface_key = str(item.get("surface_key") or "unknown").strip() or "unknown"
    missing_reason = str(item.get("missing_reason") or "unknown").strip() or "unknown"
    return f"- 缺失 surface: {surface_key} (`{missing_reason}`)"


def _mcp_readiness_surface_durable_ref(item: dict[str, Any]) -> str:
    evidence_refs = item.get("evidence_refs")
    if isinstance(evidence_refs, list):
        for ref in evidence_refs:
            text = str(ref).strip()
            if text:
                return text
    return str(item.get("artifact_path") or "").strip()


def _render_mcp_progress_refs(compact: dict[str, Any]) -> list[str]:
    refs = compact.get("refs") if isinstance(compact.get("refs"), dict) else {}
    if not refs:
        return []
    lines = ["", "## 关键引用"]
    for key in (
        "launch_report_path",
        "publication_eval_path",
        "controller_decision_path",
        "runtime_supervision_path",
        "runtime_watch_report_path",
        "evaluation_summary_path",
    ):
        value = str((refs or {}).get(key) or "").strip()
        if value:
            lines.append(f"- {key}: `{value}`")
    return lines


def render_mcp_study_progress_markdown(payload: dict[str, Any]) -> str:
    compact = compact_study_progress_projection(payload)
    lines: list[str] = []
    lines.extend(_render_mcp_progress_identity(compact))
    lines.extend(_render_mcp_progress_stage(compact))
    lines.extend(_render_mcp_progress_supervision(compact))
    lines.extend(_render_mcp_progress_runtime_state(compact))
    lines.extend(_render_mcp_progress_operator_and_action(compact))
    lines.extend(_render_mcp_progress_blockers(compact))
    lines.extend(_render_mcp_progress_medical_paper_readiness(compact))
    lines.extend(_render_mcp_progress_refs(compact))
    return "\n".join(lines) + "\n"
