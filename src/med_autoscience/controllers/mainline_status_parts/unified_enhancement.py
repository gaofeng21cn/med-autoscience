from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.mas_mds_unified_enhancement_program import (
    build_unified_enhancement_program_board,
)
from med_autoscience.controllers.module_boundary_audit import build_module_boundary_audit_report


BOUNDARY_KIND_BY_AUTHORITY_MODE = {
    "evidence_only": "evidence_source",
    "projection": "user_projection",
    "observability_only": "observability_projection",
    "read_model": "delivery_projection",
    "maintainability_only": "maintainability_audit",
}


def build_unified_enhancement_program_projection() -> dict[str, Any]:
    board = build_unified_enhancement_program_board()
    boundary_audit = build_module_boundary_audit_report()
    authority_boundaries = _mapping(board.get("authority_boundaries"))

    return {
        "surface_kind": "mas_mds_unified_enhancement_program_projection",
        "program_id": board["program_id"],
        "status": "active_integration_program",
        "owner": "MedAutoScience",
        "source_doc": "docs/program/mas_mds_unified_enhancement_program.md",
        "projection_only": True,
        "source_surfaces": [
            board["surface"],
            boundary_audit["surface"],
        ],
        "authority_boundary": (
            "This is a mainline projection for operator readability only. It does not become "
            "quality, submission, delivery, runtime, or controller authority."
        ),
        "authority_surfaces": list(authority_boundaries.get("authority_truth_surfaces") or []),
        "summary": (
            "把自动科研、文件管理和控制面增强建议收敛成 5 条 MAS-owned program lane，"
            "避免 frontdesk、cockpit、progress、delivery、observability 和 controller 各自重复解释下一步。"
        ),
        "lanes": [_project_lane(lane) for lane in board.get("lanes") or [] if isinstance(lane, Mapping)],
        "recommendation_rollup": [
            _project_recommendation(item)
            for item in board.get("recommendation_mapping") or []
            if isinstance(item, Mapping)
        ],
        "parallel_worktree_landing": list(board.get("parallel_worktree_landing") or []),
        "absorb_plan": list(board.get("absorb_plan") or []),
        "status_summary": dict(board.get("status_summary") or {}),
        "engineering_basis": list(board.get("engineering_basis") or []),
        "module_boundary_audit": {
            "surface_kind": "module_boundary_audit_projection",
            "source_surface": boundary_audit["surface"],
            "projection_only": True,
            "summary": "模块边界 audit 只描述 owner 和 read-model 边界，不能写入 authority truth。",
            "target_architecture": dict(boundary_audit.get("target_architecture") or {}),
            "module_group_count": len(boundary_audit.get("module_groups") or []),
            "boundaries": list(boundary_audit.get("truth_boundaries") or []),
        },
    }


def _project_lane(lane: Mapping[str, Any]) -> dict[str, Any]:
    authority_mode = str(lane.get("authority_mode") or "").strip()
    return {
        "lane_id": lane.get("lane_id"),
        "owner": lane.get("owner"),
        "summary": lane.get("title") or lane.get("summary"),
        "authority_boundary": lane.get("authority_boundary"),
        "authority_mode": authority_mode,
        "boundary_kind": BOUNDARY_KIND_BY_AUTHORITY_MODE.get(authority_mode, "program_lane"),
        "status": lane.get("status"),
        "blocks_usable_target": lane.get("blocks_usable_target"),
        "read_model": dict(lane.get("read_model") or {}),
    }


def _project_recommendation(item: Mapping[str, Any]) -> dict[str, Any]:
    projection = {
        "recommendation_id": item.get("recommendation_id"),
        "source_label": item.get("source_label"),
        "lane_id": item.get("lane_id"),
        "summary": item.get("handling"),
    }
    if item.get("secondary_lane_id"):
        projection["secondary_lane_id"] = item.get("secondary_lane_id")
    return projection


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
