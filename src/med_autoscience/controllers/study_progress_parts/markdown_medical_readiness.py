from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.medical_paper_v3_action_truth import (
    ACTION_BY_SURFACE as READINESS_ACTION_BY_SURFACE,
    LITERATURE_SURFACE_KEYS,
    action_truth_for_surface,
)
from med_autoscience.controllers.medical_paper_ops_health import build_medical_paper_ops_health
from med_autoscience.controllers.medical_paper_research_loop import (
    build_medical_paper_research_loop,
    research_loop_markdown_lines,
)
from med_autoscience.controllers.medical_paper_v4_operations import build_v4_operations_dashboard

from .shared import _non_empty_text


def _append_medical_paper_readiness(lines: list[str], payload: Mapping[str, Any]) -> None:
    readiness = payload.get("medical_paper_readiness")
    if not isinstance(readiness, Mapping):
        return
    lines.extend(_medical_paper_readiness_header(readiness))
    summary = _medical_paper_readiness_next_action_summary(readiness)
    if summary:
        lines.append(f"- 下一动作: {summary}")
    for item in _missing_required_medical_paper_surfaces(readiness):
        lines.append(_medical_paper_readiness_surface_action_line(item))
        lines.extend(_medical_paper_readiness_guarded_action_lines(item))
    quality_authorized = "true" if readiness.get("quality_claim_authorized") is True else "false"
    lines.append(f"- 质量声明授权: `{quality_authorized}`")
    operations = payload.get("medical_paper_v4_operations")
    if not isinstance(operations, Mapping):
        operations = build_v4_operations_dashboard(readiness)
    lines.extend(_medical_paper_v4_operations_lines(operations))
    ops_health = payload.get("medical_paper_ops_health")
    if not isinstance(ops_health, Mapping):
        ops_health = build_medical_paper_ops_health(readiness, progress_payload=payload)
    research_loop = payload.get("medical_paper_research_loop")
    if not isinstance(research_loop, Mapping):
        research_loop = build_medical_paper_research_loop(readiness, ops_health=ops_health)
    lines.extend(research_loop_markdown_lines(research_loop))
    lines.extend(_medical_paper_ops_health_lines(ops_health))


def _medical_paper_ops_health_lines(ops_health: Mapping[str, Any]) -> list[str]:
    lines = [
        "",
        "## v5 运营健康闭环 / Medical Paper Ops Health",
        "",
        f"- 当前状态: `{ops_health.get('overall_status') or 'unknown'}`",
    ]
    summary = _non_empty_text(ops_health.get("summary"))
    if summary:
        lines.append(f"- 摘要: {summary}")
    next_action = ops_health.get("next_operator_action") if isinstance(ops_health.get("next_operator_action"), Mapping) else {}
    if next_action:
        lines.append(f"- 下一动作: {next_action.get('summary') or 'none'}")
    if ops_health.get("last_green_at"):
        lines.append(f"- last-green: `{ops_health.get('last_green_at')}`")
    health = ops_health.get("health") if isinstance(ops_health.get("health"), Mapping) else {}
    for key in (
        "provider_health",
        "operator_replay_health",
        "soak_drift_health",
        "outcome_learning_health",
        "stat_guideline_health",
    ):
        item = health.get(key) if isinstance(health.get(key), Mapping) else {}
        if item:
            lines.append(
                f"- {key}: `{item.get('status') or 'unknown'}`"
                f"（{item.get('missing_reason') or 'clear'}）"
            )
    contract = ops_health.get("authority_contract") if isinstance(ops_health.get("authority_contract"), Mapping) else {}
    if contract:
        lines.append(
            "- authority: projection-only；quality/submission/finalize authorization: "
            f"`{bool(contract.get('can_authorize_quality'))}/"
            f"{bool(contract.get('can_authorize_submission'))}/"
            f"{bool(contract.get('can_authorize_finalize'))}`"
        )
    return lines


def _medical_paper_v4_operations_lines(operations: Mapping[str, Any]) -> list[str]:
    lines = [
        "",
        "## v4 生产运行面 / Medical Paper Operations",
        "",
        f"- 当前状态: `{operations.get('overall_status') or 'unknown'}`",
    ]
    summary = _non_empty_text(operations.get("summary"))
    if summary:
        lines.append(f"- 摘要: {summary}")
    next_action = operations.get("next_action") if isinstance(operations.get("next_action"), Mapping) else {}
    if next_action:
        lines.append(f"- 下一动作: {next_action.get('summary') or 'none'}")
    health = operations.get("health") if isinstance(operations.get("health"), Mapping) else {}
    for key in (
        "provider_health",
        "operator_action_health",
        "statistical_blocker_health",
        "ai_reviewer_calibration_health",
        "soak_monitor_health",
    ):
        item = health.get(key) if isinstance(health.get(key), Mapping) else {}
        if item:
            lines.append(
                f"- {key}: `{item.get('status') or 'unknown'}`"
                f"（{item.get('missing_reason') or 'clear'}）"
            )
    contract = operations.get("authority_contract") if isinstance(operations.get("authority_contract"), Mapping) else {}
    if contract:
        lines.append(
            "- authority: projection-only；quality/submission/finalize authorization: "
            f"`{bool(contract.get('can_authorize_quality'))}/"
            f"{bool(contract.get('can_authorize_submission'))}/"
            f"{bool(contract.get('can_authorize_finalize'))}`"
        )
    return lines


def _medical_paper_readiness_header(readiness: Mapping[str, Any]) -> list[str]:
    return [
        "",
        "## 自动医学论文能力闭环 / Medical Paper Readiness",
        "",
        f"- 当前状态: `{str(readiness.get('overall_status') or 'unknown').strip()}`",
        f"- readiness: `{readiness.get('ready_count')}/{readiness.get('required_count')}`",
    ]


def _medical_paper_readiness_next_action_summary(readiness: Mapping[str, Any]) -> str:
    next_action = readiness.get("next_action") if isinstance(readiness.get("next_action"), Mapping) else {}
    return str((next_action or {}).get("summary") or "").strip()


def _missing_required_medical_paper_surfaces(readiness: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    missing = [
        item
        for item in readiness.get("capability_surfaces") or []
        if isinstance(item, Mapping)
        and bool(item.get("required_for_ready"))
        and str(item.get("status") or "").strip() != "present"
    ]
    literature_missing = [
        item
        for item in missing
        if str(item.get("surface_key") or "").strip() in LITERATURE_SURFACE_KEYS
    ]
    return literature_missing[:1] or missing


def _medical_paper_readiness_surface_action_line(item: Mapping[str, Any]) -> str:
    surface_key = str(item.get("surface_key") or "unknown").strip() or "unknown"
    status = str(item.get("status") or "unknown").strip() or "unknown"
    missing_reason = str(item.get("missing_reason") or "unknown").strip() or "unknown"
    action = READINESS_ACTION_BY_SURFACE.get(surface_key, {})
    semantic_label = action.get("semantic_label") or "缺失 surface"
    action_summary = action.get("action_summary") or missing_reason
    durable_ref = _medical_paper_readiness_surface_durable_ref(item)
    suffix = f"；ref: `{durable_ref}`" if durable_ref else ""
    return (
        f"- {semantic_label}: {action_summary}"
        f"（surface: `{surface_key}`；status: `{status}`；reason: `{missing_reason}`{suffix}）"
    )


def _medical_paper_readiness_guarded_action_lines(item: Mapping[str, Any]) -> list[str]:
    truth = action_truth_for_surface(item)
    if truth is None:
        return []
    command = dict(truth.get("guarded_operator_command") or {})
    contract = dict(truth.get("authority_contract") or {})
    action_id = str(command.get("action_id") or truth.get("action_id") or "").strip()
    if not action_id:
        return []
    quality_authorized = str(bool(contract.get("can_authorize_quality"))).lower()
    return [
        f"  guarded action: `{action_id}`",
        f"  authority: product-entry/controller guarded; quality authorization: {quality_authorized}",
    ]


def _medical_paper_readiness_surface_durable_ref(item: Mapping[str, Any]) -> str:
    evidence_refs = item.get("evidence_refs")
    if isinstance(evidence_refs, list):
        for ref in evidence_refs:
            text = str(ref).strip()
            if text:
                return text
    return str(item.get("artifact_path") or "").strip()


