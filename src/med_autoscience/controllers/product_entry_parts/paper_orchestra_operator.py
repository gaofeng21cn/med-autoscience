from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared_labels import _non_empty_text


def _paper_orchestra_operator_projection_from_study(item: Mapping[str, Any]) -> dict[str, Any] | None:
    projection = dict(item.get("paper_orchestra_operator_projection") or {})
    if not projection:
        return None
    return {
        "study_id": item.get("study_id"),
        "status": _non_empty_text(projection.get("status")) or "unknown",
        "current_dag_stage": dict(projection.get("current_dag_stage") or {}),
        "parallel_sections": [
            dict(section)
            for section in (projection.get("parallel_sections") or [])
            if isinstance(section, Mapping)
        ],
        "parallel_section_count": _coerce_int(projection.get("parallel_section_count")),
        "blocking_gates": [
            dict(gate)
            for gate in (projection.get("blocking_gates") or [])
            if isinstance(gate, Mapping)
        ],
        "blocking_gate_count": _coerce_int(projection.get("blocking_gate_count")),
        "next_owner": dict(projection.get("next_owner") or {}),
        "pending_integration_surfaces": [
            text
            for text in (_non_empty_text(item) for item in (projection.get("pending_integration_surfaces") or []))
            if text is not None
        ],
        "authority": dict(projection.get("authority") or {}),
    }


def build_workspace_paper_orchestra_operator_projection(
    *,
    studies: list[dict[str, Any]],
) -> dict[str, Any]:
    study_projections = [
        projection
        for projection in (_paper_orchestra_operator_projection_from_study(item) for item in studies)
        if projection is not None
    ]
    blocked_count = sum(1 for item in study_projections if item.get("status") == "blocked")
    parallel_section_count = sum(_coerce_int(item.get("parallel_section_count")) for item in study_projections)
    blocking_gate_count = sum(_coerce_int(item.get("blocking_gate_count")) for item in study_projections)
    if not study_projections:
        status = "not_available"
        summary = "当前还没有可汇总的论文写作 DAG operator projection。"
    elif blocked_count:
        status = "blocked"
        summary = (
            f"{len(study_projections)} 个 study 暴露论文写作 DAG；"
            f"{blocked_count} 个仍有 gate 阻塞；"
            f"{parallel_section_count} 个 section 可并行。"
        )
    else:
        status = "ready_for_parallel_writing"
        summary = (
            f"{len(study_projections)} 个 study 暴露论文写作 DAG；"
            f"{parallel_section_count} 个 section 可并行；当前没有可见 gate 阻塞。"
        )
    return {
        "surface_kind": "workspace_paper_orchestra_operator_projection",
        "read_model": "paper_orchestra_operator_projection_read_model",
        "authority": "observability_only",
        "status": status,
        "summary": summary,
        "counts": {
            "study_count": len(studies),
            "projection_count": len(study_projections),
            "blocked_count": blocked_count,
            "parallel_section_count": parallel_section_count,
            "blocking_gate_count": blocking_gate_count,
        },
        "study_projections": study_projections,
    }


def render_paper_orchestra_operator_projection_lines(projection: Mapping[str, Any]) -> list[str]:
    if not projection:
        return []
    counts = dict(projection.get("counts") or {})
    lines = [
        "",
        "## 论文写作 DAG",
        "",
        f"- 当前摘要: {projection.get('summary') or 'none'}",
        (
            "- 当前计数: "
            f"已接入 {counts.get('projection_count', 0)}；"
            f"阻塞 study {counts.get('blocked_count', 0)}；"
            f"可并行 section {counts.get('parallel_section_count', 0)}；"
            f"阻塞 gate {counts.get('blocking_gate_count', 0)}"
        ),
    ]
    for item in projection.get("study_projections") or []:
        if not isinstance(item, Mapping):
            continue
        stage = dict(item.get("current_dag_stage") or {})
        next_owner = dict(item.get("next_owner") or {})
        sections = [
            _non_empty_text(section.get("section_id"))
            for section in (item.get("parallel_sections") or [])
            if isinstance(section, Mapping)
        ]
        section_text = ", ".join(section for section in sections if section) or "none"
        lines.append(f"- `{item.get('study_id') or 'unknown-study'}` 当前卡点: {stage.get('label') or stage.get('stage_id') or 'unknown'}")
        lines.append(f"  可并行 section: {section_text}")
        if next_owner:
            lines.append(f"  下一责任方: {next_owner.get('owner') or 'unknown'}")
    return lines


def _coerce_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
