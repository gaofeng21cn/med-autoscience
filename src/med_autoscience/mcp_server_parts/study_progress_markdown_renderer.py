from __future__ import annotations

from typing import Any

from med_autoscience.controllers.delivery_visibility_projection import render_delivery_inspection_markdown_lines
from med_autoscience.controllers.medical_paper_v3_action_truth import (
    ACTION_BY_SURFACE as READINESS_ACTION_BY_SURFACE,
    action_truth_for_surface,
)
from med_autoscience.controllers.medical_paper_research_loop import research_loop_markdown_lines
from med_autoscience.mcp_server_parts.open_auto_research_projection import render_mcp_open_auto_research_soak_markdown
from med_autoscience.mcp_server_parts.portable_supervisor_projection import render_mcp_progress_portable_supervisor_dashboard
from med_autoscience.mcp_server_parts.study_progress_markdown_sections import render_mcp_progress_stage


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
        lines.extend(_mcp_medical_paper_guarded_action_lines(item))
        lines.append(_mcp_medical_paper_missing_surface_compat_line(item))
    lines.append(f"- quality_claim_authorized: `{readiness.get('quality_claim_authorized')}`")
    lines.append(
        "- mechanical_projection_can_authorize_quality: "
        f"`{readiness.get('mechanical_projection_can_authorize_quality')}`"
    )
    lines.extend(_render_mcp_medical_paper_v4_operations(readiness.get("v4_operations")))
    lines.extend(research_loop_markdown_lines(readiness.get("research_loop") or {}))
    lines.extend(_render_mcp_medical_paper_ops_health(readiness.get("ops_health")))
    return lines


def _render_mcp_medical_paper_ops_health(value: object) -> list[str]:
    if not isinstance(value, dict):
        return []
    lines = [
        "",
        "## Medical Paper v5 Ops Health",
        f"- status: `{value.get('overall_status') or 'unknown'}`",
    ]
    summary = str(value.get("summary") or "").strip()
    if summary:
        lines.append(f"- summary: {summary}")
    next_action = value.get("next_operator_action") if isinstance(value.get("next_operator_action"), dict) else {}
    if next_action:
        lines.append(f"- next_operator_action: `{next_action.get('summary') or 'none'}`")
    if value.get("last_green_at"):
        lines.append(f"- last_green: `{value.get('last_green_at')}`")
    health = value.get("health") if isinstance(value.get("health"), dict) else {}
    for key in (
        "provider_health",
        "operator_replay_health",
        "soak_drift_health",
        "outcome_learning_health",
        "stat_guideline_health",
    ):
        item = health.get(key) if isinstance(health.get(key), dict) else {}
        if item:
            lines.append(
                f"- {key}: `{item.get('status') or 'unknown'}` "
                f"({item.get('missing_reason') or 'clear'})"
            )
    contract = value.get("authority_contract") if isinstance(value.get("authority_contract"), dict) else {}
    if contract:
        lines.append(
            "- quality/submission/finalize authority: "
            f"`{contract.get('can_authorize_quality')}/"
            f"{contract.get('can_authorize_submission')}/"
            f"{contract.get('can_authorize_finalize')}`"
        )
    return lines


def _render_mcp_medical_paper_v4_operations(value: object) -> list[str]:
    if not isinstance(value, dict):
        return []
    lines = [
        "",
        "## Medical Paper v4 Operations",
        f"- status: `{value.get('overall_status') or 'unknown'}`",
    ]
    summary = str(value.get("summary") or "").strip()
    if summary:
        lines.append(f"- summary: {summary}")
    next_action = value.get("next_action") if isinstance(value.get("next_action"), dict) else {}
    if next_action:
        lines.append(f"- next_action: `{next_action.get('summary') or 'none'}`")
    health = value.get("health") if isinstance(value.get("health"), dict) else {}
    for key in (
        "provider_health",
        "operator_action_health",
        "statistical_blocker_health",
        "ai_reviewer_calibration_health",
        "soak_monitor_health",
    ):
        item = health.get(key) if isinstance(health.get(key), dict) else {}
        if item:
            lines.append(
                f"- {key}: `{item.get('status') or 'unknown'}` "
                f"({item.get('missing_reason') or 'clear'})"
            )
    contract = value.get("authority_contract") if isinstance(value.get("authority_contract"), dict) else {}
    if contract:
        lines.append(
            "- quality/submission/finalize authority: "
            f"`{contract.get('can_authorize_quality')}/"
            f"{contract.get('can_authorize_submission')}/"
            f"{contract.get('can_authorize_finalize')}`"
        )
    return lines


def _render_mcp_progress_open_auto_research(compact: dict[str, Any]) -> list[str]:
    projection = compact.get("open_auto_research_projection")
    if not isinstance(projection, dict):
        return []
    counts = dict(projection.get("counts") or {})
    lines = [
        "",
        "## Open Auto Research",
        f"- status: `{projection.get('status') or 'unknown'}`；"
        f"ready `{counts.get('ready', 0)}`；"
        f"needs_review `{counts.get('needs_review', 0)}`；"
        f"blocked `{counts.get('blocked', 0)}`",
    ]
    summary = str(projection.get("summary") or "").strip()
    if summary:
        lines.append(f"- summary: {summary}")
    for action in projection.get("actions") or []:
        if not isinstance(action, dict):
            continue
        lines.append(
            f"- {action.get('action_id') or 'unknown_action'}: "
            f"`{action.get('status') or 'unknown'}` "
            f"({action.get('surface') or 'unknown_surface'})"
        )
    authority = dict(projection.get("authority") or {})
    if authority:
        lines.append(f"- read_only: `{authority.get('read_only')}`")
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


def _mcp_medical_paper_guarded_action_lines(item: dict[str, Any]) -> list[str]:
    command = item.get("guarded_operator_command") if isinstance(item.get("guarded_operator_command"), dict) else {}
    contract = item.get("authority_contract") if isinstance(item.get("authority_contract"), dict) else {}
    action_id = str((command or {}).get("action_id") or item.get("action_id") or "").strip()
    if not action_id:
        return []
    quality_authorized = str(bool(contract.get("can_authorize_quality"))).lower()
    return [
        f"  guarded action: `{action_id}`",
        f"  authority: product-entry/controller guarded; quality authorization: {quality_authorized}",
    ]


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
    user_visible_projection = (
        compact.get("user_visible_projection")
        if isinstance(compact.get("user_visible_projection"), dict)
        else {}
    )
    evidence = (
        user_visible_projection.get("evidence")
        if isinstance(user_visible_projection.get("evidence"), dict)
        else {}
    )
    user_refs = evidence.get("refs") if isinstance(evidence.get("refs"), dict) else {}
    refs = {**refs, **user_refs}
    if not refs:
        return []
    lines = ["", "## 关键引用"]
    for key in (
        "launch_report_path",
        "publication_eval_path",
        "controller_decision_path",
        "runtime_supervision_path",
        "domain_health_diagnostic_report_path",
        "evaluation_summary_path",
    ):
        value = str((refs or {}).get(key) or "").strip()
        if value:
            lines.append(f"- {key}: `{value}`")
    return lines

