from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile

from .. import publication_aftercare
from .. import reviewer_refinement_loop
from .. import stage_knowledge_plane
from .authority_boundary import authority_boundary_payload


_STUDY_SOURCE_REFS: tuple[tuple[str, Path, str], ...] = (
    ("safe_reconcile_dry_run", Path("artifacts/supervision/reconcile/latest.json"), "safe_reconcile"),
    ("controller_receipt", Path("artifacts/runtime/supervisor_dispatch_receipt/latest.json"), "controller_receipt"),
    ("controller_decisions", Path("artifacts/controller_decisions/latest.json"), "controller_decisions"),
    ("publication_eval", Path("artifacts/publication_eval/latest.json"), "publication_eval"),
    ("paper_work_unit_outbox_receipts", Path("artifacts/runtime/paper_work_unit_outbox/receipts.jsonl"), "paper_work_unit_receipts"),
    ("owner_route_handoff", Path("artifacts/supervision/owner_route_handoff/latest.json"), "owner_route_handoff"),
)


def mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def text(value: object) -> str | None:
    value_text = str(value or "").strip()
    return value_text or None


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def source_ref(*, study_root: Path, role: str, relative_path: Path, workspace_root: Path) -> dict[str, Any]:
    path = study_root / relative_path
    return {"ref_kind": "repo_path", "role": role, "ref": workspace_relative(path, workspace_root=workspace_root), "exists": path.exists()}


def build_study_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    source_refs = [
        source_ref(
            study_root=study_root,
            role=role,
            relative_path=relative_path,
            workspace_root=profile.workspace_root,
        )
        for role, relative_path, _ in _STUDY_SOURCE_REFS
    ]
    payload: dict[str, Any] = {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "domain_owned_source_refs": source_refs,
    }
    for _, relative_path, field_name in _STUDY_SOURCE_REFS:
        if field_name not in payload:
            payload[field_name] = read_json_object(study_root / relative_path)
    payload["paper_autonomy_loop"] = paper_autonomy_loop_projection(study_root=study_root)
    payload["publication_aftercare"] = publication_aftercare.build_publication_aftercare_plan(
        study_root=study_root,
    )
    payload["memory_paper_soak_proof"] = memory_paper_soak_proof_projection(
        study_root=study_root,
        profile=profile,
    )
    payload["autonomy_continuation"] = {
        "surface_kind": "mas_autonomy_continuation_projection",
        "eligible_for_auto_dispatch": False,
        "status": "retired_runtime_liveness_scheduler_signal",
        "replacement_owner": "one-person-lab",
        "recommended_task_kind": None,
        "workspace_profile": profile.name,
    }
    return payload


def study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path for path in profile.studies_root.iterdir() if path.is_dir())


def paper_autonomy_loop_projection(*, study_root: Path) -> dict[str, Any]:
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
    "build_study_projection",
    "mapping",
    "study_roots",
    "text",
    "workspace_relative",
]
