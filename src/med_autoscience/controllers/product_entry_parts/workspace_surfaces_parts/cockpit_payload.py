from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.medical_paper_operator_actions import (
    guarded_operator_authority_contract,
    guarded_operator_command,
    guarded_pending_action_result,
)
from med_autoscience.controllers.medical_paper_ops_health import (
    build_medical_paper_ops_health,
    workspace_medical_paper_ops_health,
)
from med_autoscience.controllers.medical_paper_research_loop import (
    build_medical_paper_research_loop,
    workspace_medical_paper_research_loop,
)
from med_autoscience.controllers.medical_paper_v4_operations import (
    build_v4_operations_dashboard,
    workspace_v4_operations_state,
)

try:
    _non_empty_text
except NameError:
    from med_autoscience.controllers.product_entry_parts import shared as _shared
    from med_autoscience.controllers.product_entry_parts import workspace_surfaces as _workspace_surfaces

    def _module_reexport(module) -> None:
        for name, value in vars(module).items():
            if not name.startswith("__") and name != "_module_reexport":
                globals()[name] = value

    _module_reexport(_shared)
    _module_reexport(_workspace_surfaces)


def _study_item(
    *,
    progress_payload: dict[str, Any],
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    study_id = str(progress_payload.get("study_id") or "").strip()
    commands = {
        "launch": (
            f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
    }
    supervision = dict(progress_payload.get("supervision") or {})
    monitoring = {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")),
        "supervisor_tick_status": _non_empty_text(supervision.get("supervisor_tick_status")),
    }
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    intervention_lane = dict(progress_payload.get("intervention_lane") or {})
    operator_verdict = dict(progress_payload.get("operator_verdict") or {})
    operator_status_card = dict(progress_payload.get("operator_status_card") or {})
    auto_runtime_parked = dict(progress_payload.get("auto_runtime_parked") or {})
    recommended_command = _non_empty_text(progress_payload.get("recommended_command"))
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    autonomy_contract = dict(progress_payload.get("autonomy_contract") or {})
    autonomy_soak_status = dict(progress_payload.get("autonomy_soak_status") or {})
    quality_closure_truth = dict(progress_payload.get("quality_closure_truth") or {})
    quality_execution_lane = dict(progress_payload.get("quality_execution_lane") or {})
    same_line_route_truth = _same_line_route_truth_payload(progress_payload)
    same_line_route_surface = dict(progress_payload.get("same_line_route_surface") or {})
    quality_review_loop = dict(progress_payload.get("quality_review_loop") or {})
    quality_repair_followthrough = dict(progress_payload.get("quality_repair_batch_followthrough") or {})
    quality_review_followthrough = dict(progress_payload.get("quality_review_followthrough") or {})
    gate_clearing_followthrough = _normalized_gate_clearing_followthrough(
        progress_payload,
        fallback_command=commands["progress"],
    )
    ai_first_default_entry_state = dict(progress_payload.get("ai_first_default_entry_state") or {})
    ai_first_operations_dashboard = dict(progress_payload.get("ai_first_operations_dashboard") or {})
    ai_first_feedback_state = dict(progress_payload.get("ai_first_feedback_state") or {})
    ai_first_action_dispatch_lifecycle = dict(
        progress_payload.get("ai_first_action_dispatch_lifecycle") or {}
    )
    dispatch_ledger = dict(progress_payload.get("dispatch_ledger") or {})
    publication_eval = dict(progress_payload.get("publication_eval") or {})
    artifact_runtime_proof_surface = dict(progress_payload.get("artifact_runtime_proof") or {})
    submission_hygiene_truth = dict(progress_payload.get("submission_hygiene_truth") or {})
    product_recommended_flow = dict(progress_payload.get("product_recommended_flow") or {})
    paper_orchestra_operator_projection = dict(progress_payload.get("paper_orchestra_operator_projection") or {})
    open_auto_research_state = dict(progress_payload.get("open_auto_research_projection") or {})
    portable_supervisor_dashboard = dict(progress_payload.get("portable_supervisor_dashboard") or {})
    medical_paper_readiness_surface = _normalized_medical_paper_readiness_projection(
        progress_payload.get("medical_paper_readiness")
    )
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    study_truth_snapshot = _truth_snapshot_summary(progress_payload.get("study_truth_snapshot"))
    runtime_health_snapshot = _runtime_health_snapshot_summary(progress_payload.get("runtime_health_snapshot"))
    control_plane_snapshot = _control_plane_snapshot_summary(progress_payload.get("control_plane_snapshot"))
    research_runtime_control_projection = dict(progress_payload.get("research_runtime_control_projection") or {})
    gate_surface = dict(research_runtime_control_projection.get("research_gate_surface") or {})
    if gate_surface.get("approval_gate_field") == "needs_user_decision":
        gate_surface.setdefault("legacy_approval_gate_field", "needs_physician_decision")
        research_runtime_control_projection["research_gate_surface"] = gate_surface
    return {
        "study_id": study_id,
        "truth_epoch": _non_empty_text(progress_payload.get("truth_epoch"))
        or _non_empty_text((study_truth_snapshot or {}).get("truth_epoch")),
        "study_truth_snapshot": study_truth_snapshot,
        "runtime_health_epoch": _non_empty_text(progress_payload.get("runtime_health_epoch"))
        or _non_empty_text((runtime_health_snapshot or {}).get("runtime_health_epoch")),
        "runtime_health_snapshot": runtime_health_snapshot,
        "control_plane_snapshot": control_plane_snapshot,
        "current_stage": progress_payload.get("current_stage"),
        "current_stage_summary": progress_payload.get("current_stage_summary"),
        "current_blockers": list(progress_payload.get("current_blockers") or []),
        "next_system_action": progress_payload.get("next_system_action"),
        "intervention_lane": intervention_lane or None,
        "operator_verdict": operator_verdict or None,
        "operator_status_card": operator_status_card or None,
        "auto_runtime_parked": auto_runtime_parked or None,
        "parked_state": progress_payload.get("parked_state"),
        "parked_owner": progress_payload.get("parked_owner"),
        "external_owner": progress_payload.get("external_owner"),
        "external_runtime_owner": progress_payload.get("external_runtime_owner"),
        "resource_release_expected": progress_payload.get("resource_release_expected"),
        "awaiting_explicit_wakeup": progress_payload.get("awaiting_explicit_wakeup"),
        "auto_execution_complete": progress_payload.get("auto_execution_complete"),
        "reopen_policy": progress_payload.get("reopen_policy"),
        "legacy_current_stage": progress_payload.get("legacy_current_stage"),
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract or None,
        "autonomy_soak_status": autonomy_soak_status or None,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_review_loop": quality_review_loop or None,
        "quality_repair_followthrough": quality_repair_followthrough or None,
        "quality_review_followthrough": quality_review_followthrough or None,
        "gate_clearing_followthrough": gate_clearing_followthrough or None,
        "ai_first_default_entry_state": ai_first_default_entry_state or None,
        "ai_first_operations_dashboard": ai_first_operations_dashboard or None,
        "ai_first_feedback_state": ai_first_feedback_state or None,
        "ai_first_action_dispatch_lifecycle": ai_first_action_dispatch_lifecycle or None,
        "dispatch_ledger": dispatch_ledger or None,
        "publication_eval": publication_eval or None,
        "artifact_runtime_proof": artifact_runtime_proof_surface or None,
        "submission_hygiene_truth": submission_hygiene_truth or None,
        "product_recommended_flow": product_recommended_flow or None,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection or None,
        "open_auto_research_projection": open_auto_research_state or None,
        "portable_supervisor_dashboard": portable_supervisor_dashboard or None,
        "medical_paper_readiness": medical_paper_readiness_surface or None,
        "research_runtime_control_projection": research_runtime_control_projection or None,
        "recovery_contract": recovery_contract or None,
        "needs_physician_decision": bool(progress_payload.get("needs_physician_decision")),
        "needs_user_decision": bool(progress_payload.get("needs_user_decision")),
        "monitoring": monitoring,
        "task_intake": task_intake or None,
        "progress_freshness": progress_freshness or None,
        "commands": commands,
    }


def _normalized_medical_paper_readiness_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    readiness = dict(value)
    readiness.setdefault("read_model", "medical_paper_readiness_read_model")
    readiness.setdefault("authority", "observability_projection_only")
    readiness["quality_claim_authorized"] = False
    readiness["mechanical_projection_can_authorize_quality"] = False
    readiness["action_cards"] = _medical_paper_readiness_action_cards(readiness)
    return readiness


READINESS_ACTION_CARD_BY_SURFACE = {
    "literature_scout": {
        "action_id": "complete_literature_scout",
        "label": "补文献",
        "summary": "补齐可审计文献 scout、检索日期、anchor papers、guideline 和近邻文献。",
    },
    "literature_provider_runtime": {
        "action_id": "run_provider_literature_scout",
        "label": "联网补文献",
        "summary": "运行 provider-backed 文献摄取，保留 provider provenance、检索日期和 citation ledger refs。",
    },
    "study_line_selection": {
        "action_id": "rescore_study_line",
        "label": "重评分路线",
        "summary": "重新比较候选切入点，并冻结最强 study line 与 stop threshold。",
    },
    "route_decision_orchestrator": {
        "action_id": "materialize_route_decision",
        "label": "写入路线裁决",
        "summary": "把路线选择、route-back 或 switch-line 决策写入 controller decision 投影。",
    },
    "archetype_analysis_contract": {
        "action_id": "freeze_statistical_contract",
        "label": "冻结分析合同",
        "summary": "按 study archetype 冻结统计纪律合同和失败条件。",
    },
    "statistical_discipline_operations": {
        "action_id": "resolve_statistical_blockers",
        "label": "处理统计 blocker",
        "summary": "逐项处理缺失值、precision、外部验证、多重性、临床效用和敏感性分析 blocker/waiver。",
    },
    "bounded_analysis_candidate_board": {
        "action_id": "enter_bounded_analysis",
        "label": "进入 bounded analysis",
        "summary": "把补充分析绑定到 target claim、证据收益、统计风险和决策理由。",
    },
    "stop_loss_memo": {
        "action_id": "decide_stop_loss_or_switch_line",
        "label": "止损换线",
        "summary": "写入 stop-loss memo，决定继续、route-back、止损或换线。",
    },
    "target_journal_writing_layer": {
        "action_id": "start_ai_reviewer_journal_loop",
        "label": "启动 AI reviewer",
        "summary": "冻结目标期刊写作层并启动 AI reviewer 写作/质量闭环。",
    },
    "revision_rebuttal_loop": {
        "action_id": "start_revision_rebuttal_loop",
        "label": "启动返修",
        "summary": "摄取 reviewer comments，生成 rebuttal action matrix、analysis repair 和 AI reviewer recheck。",
    },
    "authoring_runtime_authorization": {
        "action_id": "authorize_manuscript_drafting",
        "label": "授权写作",
        "summary": "检查目标期刊层、claim/display map、ledger 和 AI reviewer provenance 后再授权 full manuscript drafting。",
    },
    "real_study_soak_matrix_evidence": {
        "action_id": "rebuild_submission_package_after_soak",
        "label": "重建投稿包",
        "summary": "补齐多 study soak proof 后从 canonical source 重建投稿包并审计。",
    },
    "real_workspace_soak_monitor": {
        "action_id": "run_real_workspace_soak_monitor",
        "label": "运行真实 soak",
        "summary": "从真实或脱敏 study workspace 只读检查多 study soak ready/partial/blocked 状态。",
    },
}

def _medical_paper_readiness_action_cards(readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
    overall_status = _non_empty_text(readiness.get("overall_status")) or "unknown"
    if overall_status == "ready":
        return []
    cards = _readiness_surface_action_cards(readiness)
    if cards:
        return cards
    return _readiness_next_action_cards(readiness=readiness, overall_status=overall_status)


def _readiness_surface_action_cards(readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for surface in readiness.get("capability_surfaces") or []:
        card = _readiness_surface_action_card(surface)
        if card:
            cards.append(card)
    return cards


def _readiness_surface_action_card(surface: object) -> dict[str, Any] | None:
    if not isinstance(surface, Mapping) or surface.get("status") == "present":
        return None
    surface_key = _non_empty_text(surface.get("surface_key"))
    card = dict(READINESS_ACTION_CARD_BY_SURFACE.get(surface_key or "") or {})
    if not card:
        return None
    return _readiness_action_card_payload(
        card=card,
        surface_key=surface_key,
        status=_non_empty_text(surface.get("status")) or "unknown",
        missing_reason=_non_empty_text(surface.get("missing_reason")),
    )


def _readiness_next_action_cards(
    *,
    readiness: Mapping[str, Any],
    overall_status: str,
) -> list[dict[str, Any]]:
    next_action = dict(readiness.get("next_action") or {})
    surface_key = _non_empty_text(next_action.get("surface_key"))
    card = dict(READINESS_ACTION_CARD_BY_SURFACE.get(surface_key or "") or {})
    if not card:
        return []
    return [_readiness_action_card_payload(card=card, surface_key=surface_key, status=overall_status, missing_reason=None)]


def _readiness_action_card_payload(
    *,
    card: Mapping[str, Any],
    surface_key: str | None,
    status: str,
    missing_reason: str | None,
) -> dict[str, Any]:
    action_id = _non_empty_text(card.get("action_id")) or "inspect_medical_paper_readiness"
    return {
        **dict(card),
        "surface_key": surface_key,
        "status": status,
        "missing_reason": missing_reason,
        "guarded_operator_command": guarded_operator_command(
            action_id=action_id,
            surface_key=surface_key,
        ),
        "action_result": guarded_pending_action_result(
            action_id=action_id,
            surface_key=surface_key,
            missing_reason=missing_reason,
            next_action=_non_empty_text(card.get("summary")) or "",
        ),
        "authority_contract": guarded_operator_authority_contract(),
        "authority": "observability_projection_only",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _readiness_action_card_workflow_step(
    *,
    card: Mapping[str, Any],
    command: str,
) -> dict[str, Any]:
    action_id = _non_empty_text(card.get("action_id")) or "inspect_medical_paper_readiness"
    surface_key = _non_empty_text(card.get("surface_key"))
    return {
        "step_id": action_id,
        "title": _non_empty_text(card.get("label")) or "处理 Medical Paper Readiness 动作",
        "surface_kind": "medical_paper_readiness_action_card",
        "command": command,
        "summary": _non_empty_text(card.get("summary")) or "",
        "requires": ["profile_ref", "study_id"],
        "guarded_operator_command": guarded_operator_command(
            action_id=action_id,
            surface_key=surface_key,
        ),
        "action_result": dict(card.get("action_result") or guarded_pending_action_result(
            action_id=action_id,
            surface_key=surface_key,
            missing_reason=_non_empty_text(card.get("missing_reason")),
            next_action=_non_empty_text(card.get("summary")) or "",
        )),
        "authority_contract": guarded_operator_authority_contract(),
        "authority": "observability_projection_only",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _read_medical_paper_readiness_projection(*, study_root: Path) -> dict[str, Any]:
    readiness = _normalized_medical_paper_readiness_projection(
        medical_paper_readiness.build_medical_paper_readiness_surface(study_root=study_root)
    )
    if readiness:
        readiness.setdefault("source", "read_projection")
    return readiness


def _medical_paper_readiness_entries(
    studies: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [
        (item, dict(item.get("medical_paper_readiness") or {}))
        for item in studies
        if isinstance(item.get("medical_paper_readiness"), Mapping)
    ]


def _medical_paper_readiness_counts(
    *,
    study_count: int,
    entries: list[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[str, int]:
    counts = {
        "study_count": study_count,
        "projected_count": len(entries),
        "ready": 0,
        "attention_required": 0,
        "missing": 0,
    }
    for _, readiness in entries:
        overall_status = _non_empty_text(readiness.get("overall_status")) or "unknown"
        if overall_status == "ready":
            counts["ready"] += 1
        elif overall_status == "missing":
            counts["missing"] += 1
            counts["attention_required"] += 1
        else:
            counts["attention_required"] += 1
    return counts


def _readiness_workflow_steps(
    *,
    item: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> list[dict[str, Any]]:
    commands = dict(item.get("commands") or {})
    command = commands.get("progress") or commands.get("status") or ""
    return [
        _readiness_action_card_workflow_step(card=dict(card), command=command)
        for card in readiness.get("action_cards") or []
        if isinstance(card, Mapping)
    ]


def _readiness_study_summary(
    *,
    item: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "study_id": item.get("study_id"),
        "overall_status": _non_empty_text(readiness.get("overall_status")) or "unknown",
        "ready_count": readiness.get("ready_count"),
        "required_count": readiness.get("required_count"),
        "next_action": dict(readiness.get("next_action") or {}),
        "action_cards": list(readiness.get("action_cards") or []),
        "workflow_steps": _readiness_workflow_steps(item=item, readiness=readiness),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "authority": _non_empty_text(readiness.get("authority")) or "observability_projection_only",
    }


def _workspace_medical_paper_readiness_status(counts: Mapping[str, int]) -> tuple[str, str]:
    if counts["projected_count"] == 0:
        return "not_available", "当前还没有可见 Medical Paper Readiness projection。"
    if counts["attention_required"]:
        return (
            "attention_required",
            f"{counts['projected_count']} 个 study 已接入 Medical Paper Readiness projection；"
            f"{counts['attention_required']} 个仍有 readiness 缺口。",
        )
    return (
        "ready",
        f"{counts['projected_count']} 个 study 已接入 Medical Paper Readiness projection；"
        "当前自动医学论文能力闭环没有新的可见缺口。",
    )


def _workspace_medical_paper_readiness_state(*, studies: list[dict[str, Any]]) -> dict[str, Any]:
    entries = _medical_paper_readiness_entries(studies)
    counts = _medical_paper_readiness_counts(study_count=len(studies), entries=entries)
    study_summaries = [
        _readiness_study_summary(item=item, readiness=readiness)
        for item, readiness in entries
    ]
    status, summary = _workspace_medical_paper_readiness_status(counts)
    return {
        "surface_kind": "workspace_medical_paper_readiness_state",
        "read_model": "medical_paper_readiness_read_model",
        "authority": "observability_projection_only",
        "status": status,
        "summary": summary,
        "counts": counts,
        "studies": study_summaries,
    }


def _workspace_portable_supervisor_queue_dashboard(
    *,
    profile: WorkspaceProfile,
    studies: list[dict[str, Any]],
) -> dict[str, Any]:
    source_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    projected_studies = [
        dict(item.get("portable_supervisor_dashboard") or {})
        for item in studies
        if isinstance(item.get("portable_supervisor_dashboard"), Mapping)
    ]
    counts = {
        "study_count": len(studies),
        "projection_count": len(projected_studies),
        "queued_action_count": 0,
        "blocked": 0,
        "external_supervisor_required": 0,
    }
    for item in projected_studies:
        counts["queued_action_count"] += len(
            [action for action in item.get("action_queue") or [] if isinstance(action, Mapping)]
        )
        if item.get("blocked_reason") or item.get("why_not_applied"):
            counts["blocked"] += 1
        if item.get("external_supervisor_required"):
            counts["external_supervisor_required"] += 1
    status = "not_available"
    if projected_studies:
        status = "blocked" if counts["blocked"] else "ready"
    supervisor_mode: dict[str, Any] = {}
    for item in projected_studies:
        for key in (
            "mode",
            "mode_label",
            "scheduler_owner",
            "codex_app_heartbeat_required",
            "safe_actions_enabled",
            "repo_level_repair_authority",
            "github_user_gate",
        ):
            if key in item and key not in supervisor_mode:
                supervisor_mode[key] = item[key]
    summary = (
        "当前还没有 portable supervisor hourly projection。"
        if not projected_studies
        else (
            f"{counts['projection_count']} 个 study 有 hourly supervisor queue projection；"
            f"{counts['queued_action_count']} 个 queue action；"
            f"{counts['external_supervisor_required']} 个需要 external supervisor。"
        )
    )
    return {
        "surface_kind": "portable_supervisor_queue_dashboard",
        "read_model": "workspace_hourly_supervision_projection",
        "authority": "observability_only",
        "status": status,
        "summary": summary,
        "source_path": str(source_path),
        "supervisor_mode": supervisor_mode,
        "counts": counts,
        "studies": projected_studies,
    }


def _truth_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "truth_epoch",
        "authority_epoch",
        "canonical_next_action",
        "blocking_reasons",
        "dominant_authority_refs",
        "allowed_controller_actions",
        "package_state",
        "writer_epoch",
        "source_signature",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _runtime_health_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
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
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _control_plane_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "control_state",
        "canonical_next_action",
        "canonical_runtime_action",
        "dispatch_gate",
        "route_authorization",
        "blocking_reasons",
        "allowed_controller_actions",
        "authority_refs",
        "quality_gate_relaxation_allowed",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.exists():
        return []
    return [
        study_root
        for study_root in sorted(path for path in profile.studies_root.iterdir() if path.is_dir())
        if (study_root / "study.yaml").exists()
    ]


def _workspace_cockpit_study_snapshot(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
) -> tuple[dict[str, Any], list[str]]:
    progress_payload = study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )
    item = _study_item(progress_payload=progress_payload, profile_ref=profile_ref)
    if not item.get("medical_paper_readiness"):
        item["medical_paper_readiness"] = _read_medical_paper_readiness_projection(study_root=study_root) or None
    readiness = item.get("medical_paper_readiness") if isinstance(item.get("medical_paper_readiness"), Mapping) else {}
    item["medical_paper_v4_operations"] = build_v4_operations_dashboard(readiness)
    item["medical_paper_ops_health"] = build_medical_paper_ops_health(readiness, progress_payload=item)
    item["medical_paper_research_loop"] = build_medical_paper_research_loop(
        readiness,
        ops_health=item["medical_paper_ops_health"],
    )
    alerts = list(item["current_blockers"])
    progress_freshness = dict(item.get("progress_freshness") or {})
    progress_summary = _non_empty_text(progress_freshness.get("summary"))
    if _non_empty_text(progress_freshness.get("status")) in {"stale", "missing"} and progress_summary is not None:
        alerts.append(progress_summary)
    return item, alerts


def read_workspace_cockpit(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    inspect_workspace_supervision = _controller_override("_inspect_workspace_supervision", _inspect_workspace_supervision)
    doctor_report = build_doctor_report_fn(profile)
    workspace_alerts = _workspace_ready_alerts(doctor_report)
    studies: list[dict[str, Any]] = []
    study_roots = _study_roots(profile)
    if study_roots:
        with ThreadPoolExecutor(max_workers=len(study_roots)) as executor:
            futures = [
                executor.submit(
                    _workspace_cockpit_study_snapshot,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_root=study_root,
                )
                for study_root in study_roots
            ]
            for future in futures:
                item, item_alerts = future.result()
                studies.append(item)
                for alert in item_alerts:
                    if alert not in workspace_alerts:
                        workspace_alerts.append(alert)
    service = inspect_workspace_supervision(profile)
    workspace_supervision = _workspace_supervision_summary(studies=studies, service=service)
    if (
        (not bool(service.get("loaded")) or bool(service.get("drift_reasons")))
        and service.get("summary") not in workspace_alerts
    ):
        workspace_alerts.append(str(service.get("summary")))
    baseline_alerts = _workspace_ready_alerts(doctor_report)
    if workspace_alerts and not baseline_alerts:
        workspace_status = "attention_required"
    elif baseline_alerts:
        workspace_status = "blocked"
    else:
        workspace_status = "ready"
    mainline_snapshot = _mainline_snapshot()
    commands = {
        "mainline_status": f"{_command_prefix(profile_ref)} mainline-status",
        "doctor": f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}",
        "bootstrap": f"{_command_prefix(profile_ref)} bootstrap --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
        "service_install": f"{_command_prefix(profile_ref)} runtime-ensure-supervision --profile {_profile_arg(profile_ref)}",
        "service_status": f"{_command_prefix(profile_ref)} runtime-supervision-status --profile {_profile_arg(profile_ref)}",
    }
    attention_queue = _attention_queue(
        workspace_status=workspace_status,
        workspace_supervision=workspace_supervision,
        studies=studies,
        commands=commands,
    )
    medical_paper_readiness_state = _workspace_medical_paper_readiness_state(studies=studies)
    medical_paper_v4_operations_state = workspace_v4_operations_state(studies=studies)
    medical_paper_ops_health_state = workspace_medical_paper_ops_health(studies=studies)
    medical_paper_research_loop_state = workspace_medical_paper_research_loop(studies=studies)
    ai_first_operations_state = _workspace_ai_first_operations_state(studies=studies)
    ai_first_cross_study_completion_projection = _workspace_ai_first_cross_study_completion_projection(
        study_roots=study_roots,
        studies=studies,
    )
    paper_orchestra_operator_projection = build_workspace_paper_orchestra_operator_projection(studies=studies)
    open_auto_research_state = open_auto_research_projection.build_workspace_open_auto_research_projection(
        studies=studies,
    )
    portable_supervisor_queue_dashboard = _workspace_portable_supervisor_queue_dashboard(
        profile=profile,
        studies=studies,
    )
    user_loop = _user_loop(profile=profile, profile_ref=profile_ref)
    operator_brief = _workspace_operator_brief(
        workspace_status=workspace_status,
        workspace_alerts=workspace_alerts,
        attention_queue=attention_queue,
        studies=studies,
        user_loop=user_loop,
        commands=commands,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "workspace_status": workspace_status,
        "mainline_snapshot": mainline_snapshot,
        "workspace_alerts": workspace_alerts,
        "workspace_supervision": workspace_supervision,
        "medical_paper_readiness_state": medical_paper_readiness_state,
        "medical_paper_v4_operations_state": medical_paper_v4_operations_state,
        "medical_paper_ops_health_state": medical_paper_ops_health_state,
        "medical_paper_research_loop_state": medical_paper_research_loop_state,
        "ai_first_operations_state": ai_first_operations_state,
        "ai_first_cross_study_completion_projection": ai_first_cross_study_completion_projection,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection,
        "open_auto_research_projection": open_auto_research_state,
        "portable_supervisor_queue_dashboard": portable_supervisor_queue_dashboard,
        "attention_queue": attention_queue,
        "operator_brief": operator_brief,
        "user_loop": user_loop,
        "phase2_user_product_loop": phase2_user_product_loop,
        "studies": studies,
        "commands": commands,
    }
