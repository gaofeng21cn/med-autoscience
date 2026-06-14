from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile

from .. import publication_aftercare
from .. import reviewer_refinement_loop
from .. import stage_knowledge_plane
from .authority_boundary import authority_boundary_payload
from .export_study_projection_common import mapping, read_json_object, text, workspace_relative


def paper_autonomy_loop_projection(
    *,
    study_root: Path,
    current_owner_route_handoff_exists: bool = False,
) -> dict[str, Any]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    if not publication_eval_path.exists():
        return {
            "surface_kind": "mas_paper_autonomy_loop_projection",
            "status": "missing_publication_eval",
            "eligible_for_auto_dispatch": False,
            "reason": None,
            "repair_work_units": [],
            "source_refs": [
                {"role": "publication_eval", "ref": str(publication_eval_path), "exists": False},
            ],
        }
    try:
        refinement = reviewer_refinement_loop.build_reviewer_refinement_loop_read_model(study_root=study_root)
    except (OSError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        return {
            "surface_kind": "mas_paper_autonomy_loop_projection",
            "status": "blocked",
            "eligible_for_auto_dispatch": False,
            "reason": "reviewer_refinement_loop_unreadable",
            "blockers": [f"reviewer_refinement_loop_unreadable:{exc.__class__.__name__}"],
            "repair_work_units": [],
            "source_refs": [
                {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
            ],
        }
    if current_owner_route_handoff_exists:
        return {
            "surface_kind": "mas_paper_autonomy_loop_projection",
            "status": "superseded_by_opl_current_owner_route",
            "eligible_for_auto_dispatch": False,
            "reason": "opl_current_owner_route_handoff_active",
            "accept_status": text(mapping(refinement.get("accept")).get("status")),
            "repair_plan": dict(mapping(mapping(refinement.get("repair_loop")).get("repair_plan"))),
            "repair_work_units": [],
            "source_eval_id": text(mapping(refinement.get("snapshot")).get("source_eval_id")),
            "source_refs": [
                {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
            ],
            "currentness_status": "superseded_by_opl_current_owner_route",
            "authority_boundary": authority_boundary_payload(),
        }
    accept = mapping(refinement.get("accept"))
    repair_loop = mapping(refinement.get("repair_loop"))
    repair_plan = mapping(repair_loop.get("repair_plan"))
    accepted = accept.get("accepted") is True
    repair_required = any(
        repair_plan.get(key) is True
        for key in (
            "analysis_repair_required",
            "text_repair_required",
            "ai_reviewer_recheck_required",
        )
    )
    work_units = [dict(unit) for unit in refinement.get("repair_work_units") or [] if isinstance(unit, Mapping)]
    eligible = not accepted and repair_required and bool(work_units)
    return {
        "surface_kind": "mas_paper_autonomy_loop_projection",
        "status": "repair_recheck_ready" if eligible else ("accepted" if accepted else "blocked"),
        "eligible_for_auto_dispatch": eligible,
        "reason": "ai_reviewer_repair_recheck_required" if eligible else None,
        "accept_status": text(accept.get("status")),
        "repair_plan": dict(repair_plan),
        "repair_work_units": work_units,
        "source_eval_id": text(mapping(refinement.get("snapshot")).get("source_eval_id")),
        "source_refs": [
            {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
        ],
        "authority_boundary": authority_boundary_payload(),
    }


def publication_aftercare_projection(
    *,
    study_root: Path,
    current_owner_route_handoff_exists: bool = False,
) -> dict[str, Any]:
    projection = publication_aftercare.build_publication_aftercare_plan(study_root=study_root)
    if not current_owner_route_handoff_exists:
        return projection
    result = dict(projection)
    result["currentness_status"] = "superseded_by_opl_current_owner_route"
    for entry_key in ("analysis_queue_entry", "reviewer_refresh_entry"):
        entry = mapping(result.get(entry_key))
        if not entry:
            continue
        result[entry_key] = {
            **dict(entry),
            "eligible_for_owner_route_task_ref": False,
            "currentness_status": "superseded_by_opl_current_owner_route",
        }
    return result


def memory_paper_soak_proof_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    proof_path = stage_knowledge_plane.paper_soak_memory_apply_proof_path(study_root=study_root)
    proof = read_json_object(proof_path)
    if proof is None:
        return {
            "surface_kind": "mas_memory_paper_soak_proof_projection",
            "status": "missing",
            "proof_ref": workspace_relative(proof_path, workspace_root=profile.workspace_root),
            "receipt_refs": [],
            "authority_boundary": authority_boundary_payload(),
            "read_only_display_policy": {
                "consumer": "OPL/Aion",
                "body_included": False,
                "can_write_mas_truth": False,
            },
        }
    receipt_refs = [
        dict(ref)
        for ref in proof.get("opl_aion_readonly_receipt_refs") or []
        if isinstance(ref, Mapping)
    ]
    return {
        "surface_kind": "mas_memory_paper_soak_proof_projection",
        "status": text(proof.get("status")) or "missing",
        "proof_ref": workspace_relative(proof_path, workspace_root=profile.workspace_root),
        "receipt_refs": receipt_refs,
        "route_memory_ref_count": len(mapping(proof.get("stage_entry")).get("publication_route_memory_refs") or []),
        "router_receipt_ref_count": len(proof.get("mas_router_receipt_refs") or []),
        "writeback_proposal_ref_count": len(proof.get("typed_closeout_writeback_proposals") or []),
        "source_fingerprint": text(proof.get("source_fingerprint")),
        "authority_boundary": mapping(proof.get("authority_boundary")) or authority_boundary_payload(),
        "read_only_display_policy": mapping(proof.get("read_only_display_policy")),
    }


__all__ = [
    "memory_paper_soak_proof_projection",
    "paper_autonomy_loop_projection",
    "publication_aftercare_projection",
]
