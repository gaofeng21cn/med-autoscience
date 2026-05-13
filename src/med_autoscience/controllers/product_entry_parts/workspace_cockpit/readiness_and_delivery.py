from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_readiness
from med_autoscience.controllers.delivery_visibility_projection import compact_delivery_inspection_projection
from med_autoscience.controllers.medical_paper_operator_actions import (
    guarded_operator_authority_contract,
    guarded_operator_command,
    guarded_pending_action_result,
)
from med_autoscience.controllers.medical_paper_v3_action_truth import LITERATURE_SURFACE_KEYS
from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.product_entry_parts.shared_labels import _non_empty_text


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
    surfaces = [
        surface
        for surface in readiness.get("capability_surfaces") or []
        if isinstance(surface, Mapping) and surface.get("status") != "present"
    ]
    surfaces = sorted(surfaces, key=_readiness_action_surface_priority)
    literature_surfaces = [
        surface
        for surface in surfaces
        if _non_empty_text(surface.get("surface_key")) in LITERATURE_SURFACE_KEYS
    ]
    for surface in literature_surfaces[:1] or surfaces:
        card = _readiness_surface_action_card(surface)
        if card:
            return [card]
    return []


def _readiness_action_surface_priority(surface: Mapping[str, Any]) -> tuple[int, int, str]:
    surface_key = _non_empty_text(surface.get("surface_key")) or ""
    status = _non_empty_text(surface.get("status")) or "unknown"
    family_priority = {
        "literature_provider_runtime": 0,
        "literature_scout": 0,
        "statistical_discipline_operations": 1,
        "route_decision_orchestrator": 2,
        "stop_loss_memo": 3,
        "revision_rebuttal_loop": 4,
        "authoring_runtime_authorization": 5,
        "real_workspace_soak_monitor": 6,
    }.get(surface_key, 50)
    status_priority = {"missing": 0, "blocked": 1, "partial": 2}.get(status, 9)
    return family_priority, status_priority, surface_key


def _readiness_all_surface_action_cards(readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    surfaces = [
        surface for surface in readiness.get("capability_surfaces") or [] if isinstance(surface, Mapping)
    ]
    for surface in sorted(surfaces, key=_readiness_action_surface_priority):
        card = _readiness_surface_action_card(surface)
        surface_key = _non_empty_text(card.get("surface_key")) if card else ""
        if card and surface_key not in seen:
            cards.append(card)
            seen.add(surface_key)
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
        "title": _readiness_workflow_title(card),
        "display_label": _readiness_workflow_display_label(card),
        "surface_kind": "medical_paper_readiness_action_card",
        "command": command,
        "summary": _non_empty_text(card.get("summary")) or "",
        "status": _non_empty_text(card.get("status")) or "unknown",
        "missing_reason": _non_empty_text(card.get("missing_reason")) or None,
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


def _readiness_workflow_title(card: Mapping[str, Any]) -> str:
    surface_key = _non_empty_text(card.get("surface_key")) or ""
    return {
        "route_decision_orchestrator": "路线裁决",
        "stop_loss_memo": "止损/换线",
    }.get(surface_key, _non_empty_text(card.get("label")) or "处理 Medical Paper Readiness 动作")


def _readiness_workflow_display_label(card: Mapping[str, Any]) -> str:
    surface_key = _non_empty_text(card.get("surface_key")) or ""
    return {
        "stop_loss_memo": "止损/换线",
    }.get(surface_key, _non_empty_text(card.get("label")) or _readiness_workflow_title(card))


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
    cards = _readiness_all_surface_action_cards(readiness) or [
        card for card in readiness.get("action_cards") or [] if isinstance(card, Mapping)
    ]
    return [
        _readiness_action_card_workflow_step(card=dict(card), command=command)
        for card in cards
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


def _delivery_inspection_entries(studies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in studies:
        projection = compact_delivery_inspection_projection(item.get("delivery_inspection"))
        if projection is None:
            continue
        projection.setdefault("study_id", item.get("study_id"))
        entries.append(projection)
    return entries


def _workspace_delivery_inspection_state(*, studies: list[dict[str, Any]]) -> dict[str, Any]:
    entries = _delivery_inspection_entries(studies)
    counts = {
        "study_count": len(studies),
        "projected_count": len(entries),
        "attention_required": 0,
        "layout_migration_pending_sync": 0,
    }
    for entry in entries:
        status = _non_empty_text(entry.get("status")) or "unknown"
        layout_migration_pending = bool(entry.get("layout_migration_pending_sync"))
        if status == "layout_migration_pending_sync" or layout_migration_pending:
            counts["layout_migration_pending_sync"] += 1
        if status == "layout_migration_pending_sync":
            counts["attention_required"] += 1
        elif status not in {"current", "ready"}:
            counts["attention_required"] += 1
    if not entries:
        status = "not_available"
        summary = "当前还没有 Delivery Inspection projection。"
    elif counts["attention_required"]:
        status = "attention_required"
        summary = (
            f"{counts['projected_count']} 个 study 已接入 Delivery Inspection；"
            f"{counts['layout_migration_pending_sync']} 个 layout migration 等待下一次 authorized sync 升级。"
        )
    else:
        status = "ready"
        summary = f"{counts['projected_count']} 个 study 已接入 Delivery Inspection；delivery mirror 当前可见。"
    return {
        "surface_kind": "workspace_delivery_inspection_state",
        "read_model": "delivery_inspection_read_model",
        "authority": "observability_projection_only",
        "status": status,
        "summary": summary,
        "counts": counts,
        "studies": entries,
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
