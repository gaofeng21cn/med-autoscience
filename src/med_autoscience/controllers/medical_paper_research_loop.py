from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SURFACE = "medical_paper_research_loop"
WORKSPACE_SURFACE = "workspace_medical_paper_research_loop"
READ_MODEL = "medical_paper_research_loop_read_model"


FACET_ORDER = (
    "literature",
    "route_decision",
    "statistical_discipline",
    "stop_loss_switch_line",
    "revision_authoring",
    "real_soak",
)


FACET_LABELS = {
    "literature": "文献缺口 / Literature",
    "route_decision": "路线裁决 / Study Line Decision",
    "statistical_discipline": "统计 blocker / Statistical Discipline",
    "stop_loss_switch_line": "止损/换线 / Stop-loss or Switch-line",
    "revision_authoring": "返修/写作授权 / Revision and Authoring",
    "real_soak": "真实 soak / Real Soak",
}


FACET_SURFACES = {
    "literature": ("literature_provider_runtime", "literature_scout"),
    "route_decision": ("route_decision_orchestrator", "study_line_selection"),
    "statistical_discipline": (
        "statistical_discipline_operations",
        "archetype_analysis_contract",
        "bounded_analysis_candidate_board",
    ),
    "stop_loss_switch_line": ("stop_loss_memo",),
    "revision_authoring": (
        "revision_rebuttal_loop",
        "authoring_runtime_authorization",
        "target_journal_writing_layer",
        "ai_reviewer_outcome_learning_regression",
        "ai_reviewer_calibration_learning_loop",
    ),
    "real_soak": ("real_workspace_soak_monitor", "real_study_soak_matrix_evidence"),
}


def authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_projection_only",
        "read_model_only": True,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def build_medical_paper_research_loop(
    readiness: Mapping[str, Any] | None,
    *,
    ops_health: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = readiness if isinstance(readiness, Mapping) else {}
    surfaces = _surfaces_by_key(source)
    facets = {
        facet_key: _facet_payload(facet_key=facet_key, surfaces=surfaces, ops_health=ops_health)
        for facet_key in FACET_ORDER
    }
    counts = {
        "ready": sum(1 for item in facets.values() if item["status"] == "ready"),
        "partial": sum(1 for item in facets.values() if item["status"] == "partial"),
        "blocked": sum(1 for item in facets.values() if item["status"] == "blocked"),
    }
    status = "blocked" if counts["blocked"] else "partial" if counts["partial"] else "ready"
    next_action = _next_action(source=source, facets=facets, ops_health=ops_health)
    return {
        "surface": SURFACE,
        "read_model": READ_MODEL,
        "overall_status": status,
        "summary": _summary(status=status, counts=counts),
        "counts": counts,
        "facets": facets,
        "next_action": next_action,
        "durable_refs": _unique(ref for facet in facets.values() for ref in facet.get("durable_refs", [])),
        "authority_contract": authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def workspace_medical_paper_research_loop(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    study_items: list[dict[str, Any]] = []
    for study in studies:
        if not isinstance(study, Mapping):
            continue
        readiness = study.get("medical_paper_readiness") if isinstance(study.get("medical_paper_readiness"), Mapping) else {}
        loop = (
            study.get("medical_paper_research_loop")
            if isinstance(study.get("medical_paper_research_loop"), Mapping)
            else build_medical_paper_research_loop(readiness, ops_health=study.get("medical_paper_ops_health"))
        )
        study_items.append(
            {
                "study_id": _text(study.get("study_id")) or "unknown-study",
                "overall_status": loop["overall_status"],
                "summary": loop["summary"],
                "next_action": loop["next_action"],
                "facets": loop["facets"],
                "durable_refs": loop["durable_refs"],
            }
        )
    counts = {
        "study_count": len(study_items),
        "ready": sum(1 for item in study_items if item["overall_status"] == "ready"),
        "partial": sum(1 for item in study_items if item["overall_status"] == "partial"),
        "blocked": sum(1 for item in study_items if item["overall_status"] == "blocked"),
    }
    status = "not_available" if not study_items else "blocked" if counts["blocked"] else "partial" if counts["partial"] else "ready"
    return {
        "surface": WORKSPACE_SURFACE,
        "read_model": READ_MODEL,
        "status": status,
        "summary": _workspace_summary(status=status, counts=counts),
        "counts": counts,
        "studies": study_items,
        "authority_contract": authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def research_loop_markdown_lines(loop: Mapping[str, Any], *, heading: bool = True) -> list[str]:
    if not loop:
        return []
    lines: list[str] = []
    if heading:
        lines.extend(["", "## 自动论文科研闭环 / Medical Paper Research Loop", ""])
    lines.append(f"- 当前状态: `{loop.get('overall_status') or loop.get('status') or 'unknown'}`")
    summary = _text(loop.get("summary"))
    if summary:
        lines.append(f"- 摘要: {summary}")
    next_action = loop.get("next_action") if isinstance(loop.get("next_action"), Mapping) else {}
    if next_action:
        lines.append(f"- 下一动作: {next_action.get('summary') or 'none'}")
    facets = loop.get("facets") if isinstance(loop.get("facets"), Mapping) else {}
    for facet_key in FACET_ORDER:
        facet = facets.get(facet_key) if isinstance(facets.get(facet_key), Mapping) else {}
        if not facet:
            continue
        line = f"- {FACET_LABELS[facet_key]}: `{facet.get('status') or 'unknown'}`"
        missing_reason = _text(facet.get("missing_reason"))
        if missing_reason:
            line += f" ({missing_reason})"
        refs = _list_text(facet.get("durable_refs"))
        if refs:
            line += f"; ref `{refs[0]}`"
        lines.append(line)
    contract = loop.get("authority_contract") if isinstance(loop.get("authority_contract"), Mapping) else {}
    if contract:
        lines.append(
            "- authority contract: quality/submission/finalize/mechanical-quality "
            f"`{bool(contract.get('can_authorize_quality'))}/"
            f"{bool(contract.get('can_authorize_submission'))}/"
            f"{bool(contract.get('can_authorize_finalize'))}/"
            f"{bool(contract.get('mechanical_projection_can_authorize_quality'))}`"
        )
    return lines


def compact_medical_paper_research_loop(loop: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(loop, Mapping):
        return None
    facets = loop.get("facets") if isinstance(loop.get("facets"), Mapping) else {}
    return {
        "surface": loop.get("surface"),
        "overall_status": loop.get("overall_status") or loop.get("status"),
        "summary": loop.get("summary"),
        "counts": dict(loop.get("counts") or {}),
        "next_action": dict(loop.get("next_action") or {}),
        "durable_refs": _list_text(loop.get("durable_refs"))[:8],
        "facets": {
            facet_key: {
                "status": facet.get("status"),
                "missing_reason": facet.get("missing_reason"),
                "next_action": facet.get("next_action"),
                "durable_refs": _list_text(facet.get("durable_refs"))[:4],
            }
            for facet_key in FACET_ORDER
            if isinstance((facet := facets.get(facet_key)), Mapping)
        },
        "authority_contract": dict(loop.get("authority_contract") or {}),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _facet_payload(
    *,
    facet_key: str,
    surfaces: Mapping[str, Mapping[str, Any]],
    ops_health: Mapping[str, Any] | None,
) -> dict[str, Any]:
    candidates = [surfaces[key] for key in FACET_SURFACES[facet_key] if key in surfaces]
    statuses = [_surface_status(item) for item in candidates]
    status = _facet_status(statuses)
    missing_reason = _first_text(item.get("missing_reason") for item in candidates)
    durable_refs = _unique(ref for item in candidates for ref in _durable_refs(item))
    if facet_key == "literature" and not candidates:
        status, missing_reason = _health_fallback(ops_health, "provider_health")
    if facet_key == "statistical_discipline":
        health_status, health_reason = _health_fallback(ops_health, "stat_guideline_health")
        if health_status == "blocked":
            status = "blocked"
            missing_reason = health_reason or missing_reason
    if facet_key == "real_soak":
        health_status, health_reason = _health_fallback(ops_health, "soak_drift_health")
        if health_status in {"blocked", "partial"}:
            status = health_status
            missing_reason = health_reason or missing_reason
    if not candidates and status == "unknown":
        status = "blocked"
        missing_reason = f"{facet_key}_surface_missing"
    return {
        "facet_key": facet_key,
        "label": FACET_LABELS[facet_key],
        "status": status,
        "missing_reason": missing_reason,
        "next_action": _facet_next_action(facet_key=facet_key, status=status),
        "durable_refs": durable_refs,
        "surface_keys": [str(item.get("surface_key") or "") for item in candidates if _text(item.get("surface_key"))],
        "authority_contract": authority_contract(),
    }


def _surfaces_by_key(readiness: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in readiness.get("capability_surfaces") or []:
        if not isinstance(item, Mapping):
            continue
        surface_key = _text(item.get("surface_key"))
        if surface_key:
            result[surface_key] = item
    return result


def _surface_status(surface: Mapping[str, Any]) -> str:
    status = _text(surface.get("overall_status")) or _text(surface.get("status"))
    if status in {"present", "ready"}:
        return "ready"
    if status == "partial":
        return "partial"
    return "blocked"


def _facet_status(statuses: Sequence[str]) -> str:
    if not statuses:
        return "unknown"
    if "blocked" in statuses:
        return "blocked"
    if "partial" in statuses:
        return "partial"
    return "ready"


def _facet_next_action(*, facet_key: str, status: str) -> str:
    if status == "ready":
        return "continue_managed_execution"
    return {
        "literature": "补文献并刷新 citation ledger",
        "route_decision": "写入路线裁决或切换更强路线",
        "statistical_discipline": "处理统计 blocker/waiver",
        "stop_loss_switch_line": "形成 stop-loss、switch-line 或 human gate memo",
        "revision_authoring": "补返修矩阵、写作授权和 AI reviewer recheck",
        "real_soak": "运行真实/脱敏 workspace 只读 soak monitor",
    }[facet_key]


def _next_action(
    *,
    source: Mapping[str, Any],
    facets: Mapping[str, Mapping[str, Any]],
    ops_health: Mapping[str, Any] | None,
) -> dict[str, Any]:
    source_next = source.get("next_action") if isinstance(source.get("next_action"), Mapping) else {}
    summary = _text(source_next.get("summary"))
    for facet_key in FACET_ORDER:
        facet = facets[facet_key]
        if facet["status"] in {"blocked", "partial"}:
            return {
                "facet_key": facet_key,
                "summary": summary or facet["next_action"],
                "missing_reason": facet.get("missing_reason") or "",
            }
    ops_next = ops_health.get("next_operator_action") if isinstance(ops_health, Mapping) and isinstance(ops_health.get("next_operator_action"), Mapping) else {}
    return {
        "facet_key": "none",
        "summary": _text(ops_next.get("summary")) or summary or "continue_managed_execution",
        "missing_reason": _text(ops_next.get("missing_reason")),
    }


def _health_fallback(ops_health: Mapping[str, Any] | None, key: str) -> tuple[str, str]:
    health = ops_health.get("health") if isinstance(ops_health, Mapping) and isinstance(ops_health.get("health"), Mapping) else {}
    item = health.get(key) if isinstance(health.get(key), Mapping) else {}
    return _text(item.get("status")) or "unknown", _text(item.get("missing_reason"))


def _summary(*, status: str, counts: Mapping[str, int]) -> str:
    return (
        f"自动论文科研闭环 {status}；"
        f"ready {counts['ready']}，partial {counts['partial']}，blocked {counts['blocked']}。"
    )


def _workspace_summary(*, status: str, counts: Mapping[str, int]) -> str:
    if counts["study_count"] == 0:
        return "当前还没有可见自动论文科研闭环投影。"
    return (
        f"{counts['study_count']} 个 study 已接入自动论文科研闭环；"
        f"ready {counts['ready']}，partial {counts['partial']}，blocked {counts['blocked']}；"
        f"workspace status {status}。"
    )


def _durable_refs(surface: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("evidence_refs", "durable_refs", "required_calibration_refs"):
        refs.extend(_list_text(surface.get(key)))
    for key in ("artifact_path", "durable_ref", "replay_ref"):
        value = _text(surface.get(key))
        if value:
            refs.append(value)
    return _unique(refs)


def _list_text(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return _unique(str(item).strip() for item in value if str(item).strip())


def _unique(values: object) -> list[str]:
    result: list[str] = []
    for value in values or []:
        text = str(value).strip()
        if text and text not in result:
            result.append(text)
    return result


def _first_text(values: object) -> str:
    for value in values or []:
        text = _text(value)
        if text:
            return text
    return ""


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


__all__ = [
    "FACET_LABELS",
    "FACET_ORDER",
    "SURFACE",
    "WORKSPACE_SURFACE",
    "authority_contract",
    "build_medical_paper_research_loop",
    "compact_medical_paper_research_loop",
    "research_loop_markdown_lines",
    "workspace_medical_paper_research_loop",
]
