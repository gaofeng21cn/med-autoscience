from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.medical_paper_operator_actions import (
    guarded_operator_command as build_guarded_operator_command,
)


SCHEMA_VERSION = 1
COMMAND_SURFACE = "medical_paper_v3_guarded_operator_command"


ACTION_BY_SURFACE: dict[str, dict[str, str]] = {
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
LITERATURE_SURFACE_KEYS = ("literature_provider_runtime", "literature_scout")


def compact_authority_contract() -> dict[str, bool]:
    return {
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def guarded_operator_command(*, action_id: str, surface_key: str) -> dict[str, Any]:
    return build_guarded_operator_command(action_id=action_id, surface_key=surface_key)


def action_truth_for_surface(surface: Mapping[str, Any]) -> dict[str, Any] | None:
    surface_key = str(surface.get("surface_key") or "").strip()
    if not surface_key:
        return None
    action = ACTION_BY_SURFACE.get(surface_key)
    if not action:
        return None
    action_id = action["action_id"]
    return {
        "surface": "medical_paper_v3_action_truth",
        "schema_version": SCHEMA_VERSION,
        "surface_key": surface_key,
        "status": str(surface.get("status") or "unknown").strip() or "unknown",
        "missing_reason": str(surface.get("missing_reason") or "unknown").strip() or "unknown",
        "artifact_path": surface.get("artifact_path"),
        "evidence_refs": list(surface.get("evidence_refs") or [])
        if isinstance(surface.get("evidence_refs"), list)
        else [],
        "action_id": action_id,
        "action_label": action["action_label"],
        "semantic_label": action["semantic_label"],
        "action_summary": action["action_summary"],
        "next_action_summary": action["action_summary"],
        "guarded_operator_command": guarded_operator_command(action_id=action_id, surface_key=surface_key),
        "authority_contract": compact_authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def action_truths_for_readiness(readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
    truths: list[dict[str, Any]] = []
    actionable_surfaces = [
        item
        for item in readiness.get("capability_surfaces") or []
        if _is_actionable_surface(item)
    ]
    literature_surfaces = [
        item
        for item in actionable_surfaces
        if str(item.get("surface_key") or "").strip() in LITERATURE_SURFACE_KEYS
    ]
    for item in literature_surfaces[:1] or actionable_surfaces:
        truth = action_truth_for_surface(item)
        if truth is not None:
            truths.append(truth)
    return truths


def _is_actionable_surface(item: object) -> bool:
    return (
        isinstance(item, Mapping)
        and bool(item.get("required_for_ready"))
        and str(item.get("status") or "").strip() != "present"
    )


def compact_missing_surface_with_action_truth(item: Mapping[str, Any]) -> dict[str, Any] | None:
    truth = action_truth_for_surface(item)
    if truth is None:
        return None
    compact: dict[str, Any] = {
        "surface_key": truth["surface_key"],
        "status": truth["status"],
        "missing_reason": truth["missing_reason"],
        "action_id": truth["action_id"],
        "action_label": truth["action_label"],
        "action_summary": truth["action_summary"],
        "semantic_label": truth["semantic_label"],
        "next_action_summary": truth["next_action_summary"],
        "guarded_operator_command": truth["guarded_operator_command"],
        "authority_contract": truth["authority_contract"],
    }
    if truth.get("artifact_path"):
        compact["artifact_path"] = truth["artifact_path"]
    if truth.get("evidence_refs"):
        compact["evidence_refs"] = truth["evidence_refs"]
    return compact


__all__ = [
    "ACTION_BY_SURFACE",
    "COMMAND_SURFACE",
    "action_truth_for_surface",
    "action_truths_for_readiness",
    "compact_authority_contract",
    "compact_missing_surface_with_action_truth",
    "guarded_operator_command",
]
