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
    ("autonomy_slo_status", Path("artifacts/autonomy/slo_status/latest.json"), "slo_status"),
    ("publication_eval", Path("artifacts/publication_eval/latest.json"), "publication_eval"),
    ("paper_work_unit_outbox_receipts", Path("artifacts/runtime/paper_work_unit_outbox/receipts.jsonl"), "paper_work_unit_receipts"),
    ("owner_route_handoff", Path("artifacts/supervision/owner_route_handoff/latest.json"), "owner_route_handoff"),
)
_OPL_CURRENT_CONTROL_REF = Path("artifacts/supervision/opl_current_control_state/latest.json")
_CURRENTNESS_BASIS_KEYS = (
    "owner_reason",
    "runtime_health_epoch",
    "truth_epoch",
    "work_unit_fingerprint",
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
    current_control_handoff = current_control_owner_route_handoff_record(
        study_root=study_root,
        profile=profile,
        existing_record=mapping(payload.get("owner_route_handoff")),
    )
    if current_control_handoff is not None:
        payload["owner_route_handoff"] = current_control_handoff
    payload["paper_autonomy_loop"] = paper_autonomy_loop_projection(study_root=study_root)
    payload["publication_aftercare"] = publication_aftercare.build_publication_aftercare_plan(
        study_root=study_root,
    )
    payload["memory_paper_soak_proof"] = memory_paper_soak_proof_projection(
        study_root=study_root,
        profile=profile,
    )
    payload["autonomy_continuation"] = autonomy_continuation_projection(payload)
    return payload


def autonomy_continuation_projection(study: Mapping[str, Any]) -> dict[str, Any]:
    slo_status = mapping(study.get("slo_status"))
    progress_pressure = mapping(slo_status.get("progress_pressure"))
    pressure_status = text(progress_pressure.get("status"))
    stop_allowed = progress_pressure.get("stop_allowed") is True
    continuation_required = progress_pressure.get("continuation_required") is True
    if pressure_status == "advance_now" and continuation_required and not stop_allowed:
        return {
            "surface_kind": "mas_autonomy_continuation_projection",
            "eligible_for_auto_dispatch": True,
            "status": "progress_pressure_continue",
            "replacement_owner": "one-person-lab",
            "recommended_task_kind": "domain_route/reconcile-apply",
            "workspace_profile": None,
            "progress_pressure": dict(progress_pressure),
        }
    return {
        "surface_kind": "mas_autonomy_continuation_projection",
        "eligible_for_auto_dispatch": False,
        "status": "retired_runtime_liveness_scheduler_signal",
        "replacement_owner": "one-person-lab",
        "recommended_task_kind": None,
        "workspace_profile": None,
    }


def current_control_owner_route_handoff_record(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
    existing_record: Mapping[str, Any],
) -> dict[str, Any] | None:
    handoff_path = profile.workspace_root / _OPL_CURRENT_CONTROL_REF
    payload = read_json_object(handoff_path)
    if payload is None:
        return None
    matching = _matching_current_control_study(payload, study_id=study_root.name)
    if matching is None:
        return None
    current_recorded_at = text(matching.get("handoff_generated_at")) or text(payload.get("generated_at"))
    if not _current_control_supersedes_existing(
        current_recorded_at=current_recorded_at,
        existing_record=existing_record,
    ):
        return None
    owner_route = mapping(matching.get("owner_route"))
    if text(owner_route.get("next_owner")) != "one-person-lab":
        return None
    reason = text(owner_route.get("owner_reason"))
    if reason is None:
        return None
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    currentness_basis = _currentness_basis(currentness_contract)
    if currentness_basis is None:
        return None
    runtime_health = mapping(matching.get("runtime_health"))
    quest_id = text(matching.get("quest_id")) or study_root.name
    quest_root = text(matching.get("quest_root"))
    runtime_state_path = text(matching.get("runtime_state_path"))
    if runtime_state_path is None and quest_root is not None:
        runtime_state_path = str(Path(quest_root) / ".ds" / "runtime_state.json")
    owner_route_handoff_ref = workspace_relative(handoff_path, workspace_root=profile.workspace_root)
    handoff = {
        "surface_kind": "mas_runtime_owner_route_handoff",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "dispatch_surface": "medautosci domain-handler export -> medautosci domain-handler dispatch",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "runtime_state_path": runtime_state_path,
        "source": "opl_current_control_state_owner_route_handoff",
        "reason": reason,
        "repair_kind": text(runtime_health.get("canonical_runtime_action")) or reason,
        "recorded_at": current_recorded_at,
        "work_unit_fingerprint": currentness_basis["work_unit_fingerprint"],
        "owner_route_currentness_basis": currentness_basis,
        "owner_route_currentness_contract": dict(currentness_contract),
        "owner_route_attempt_protocol": dict(mapping(owner_route.get("owner_route_attempt_protocol"))),
        "owner_route_idempotency_key": text(owner_route.get("idempotency_key")),
        "runtime_health": dict(runtime_health),
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }
    return {
        "surface_kind": "mas_runtime_owner_route_handoff_record",
        "schema_version": 1,
        "source": "opl_current_control_state_owner_route_handoff",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "recorded_at": current_recorded_at,
        "runtime_state_mutated": False,
        "owner_route_handoff_ref": owner_route_handoff_ref,
        "source_ref_role": "opl_current_control_state_owner_route",
        "source_relative_path": str(_OPL_CURRENT_CONTROL_REF),
        "supersedes_recorded_at": _existing_handoff_recorded_at(existing_record),
        "handoff": handoff,
    }


def _matching_current_control_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any] | None:
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping) and text(item.get("study_id")) == study_id:
            return dict(item)
    return None


def _current_control_supersedes_existing(
    *,
    current_recorded_at: str | None,
    existing_record: Mapping[str, Any],
) -> bool:
    existing_recorded_at = _existing_handoff_recorded_at(existing_record)
    if existing_recorded_at is None:
        return True
    if current_recorded_at is None:
        return False
    return current_recorded_at > existing_recorded_at


def _existing_handoff_recorded_at(record: Mapping[str, Any]) -> str | None:
    handoff = mapping(record.get("handoff"))
    return text(handoff.get("recorded_at")) or text(record.get("recorded_at"))


def _currentness_basis(contract: Mapping[str, Any]) -> dict[str, str] | None:
    basis = mapping(contract.get("basis"))
    currentness_basis = {key: text(basis.get(key)) for key in _CURRENTNESS_BASIS_KEYS}
    if any(value is None for value in currentness_basis.values()):
        return None
    missing = contract.get("missing_required_fields")
    if isinstance(missing, list) and any(text(item) for item in missing):
        return None
    return {key: value for key, value in currentness_basis.items() if value is not None}


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
