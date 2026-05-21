from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.ars_learning_projection import build_ars_learning_projection
from med_autoscience.profiles import WorkspaceProfile

from .. import opl_provider_ready_adapter
from .. import publication_aftercare
from .. import reviewer_refinement_loop
from .. import stage_knowledge_plane
from .. import study_domain_transition_table
from ..domain_slo_scheduler_projection_parts import consumer_migration
from .authority_boundary import authority_boundary_payload
from .controller_route_back_tasks import controller_decision_route_back_task
from .dispatch_orchestration import ALLOWED_TASK_KINDS
from .functional_closure import build_sidecar_functional_closure_projection
from .guarded_apply_tasks import DEFAULT_GUARDED_APPLY_TARGETS, provider_hosted_guarded_apply_tasks
from .owner_route_handoff_tasks import owner_route_handoff_task
from .owner_source_refs import owner_controller_decision_refs
from .substrate_adapter import build_opl_substrate_adapter_projection


_STUDY_SOURCE_REFS: tuple[tuple[str, Path, str], ...] = (
    ("runtime_supervision_truth", Path("artifacts/runtime/runtime_supervision/latest.json"), "runtime_supervision"),
    ("runtime_supervision_truth_legacy_ref", Path("artifacts/runtime_supervision/latest.json"), "runtime_supervision"),
    ("autonomy_slo_status", Path("artifacts/autonomy/slo_status/latest.json"), "slo_status"),
    ("worker_lease", Path("artifacts/runtime/worker_lease/latest.json"), "worker_lease"),
    ("runtime_session", Path("artifacts/runtime/runtime_session/latest.json"), "runtime_session"),
    ("recovery_intent", Path("artifacts/runtime/recovery_intent/latest.json"), "recovery_intent"),
    ("safe_reconcile_dry_run", Path("artifacts/supervision/reconcile/latest.json"), "safe_reconcile"),
    ("controller_receipt", Path("artifacts/runtime/supervisor_dispatch_receipt/latest.json"), "controller_receipt"),
    ("controller_decisions", Path("artifacts/controller_decisions/latest.json"), "controller_decisions"),
    ("publication_eval", Path("artifacts/publication_eval/latest.json"), "publication_eval"),
    ("paper_work_unit_outbox_receipts", Path("artifacts/runtime/paper_work_unit_outbox/receipts.jsonl"), "paper_work_unit_receipts"),
    ("owner_route_handoff", Path("artifacts/supervision/owner_route_handoff/latest.json"), "owner_route_handoff"),
)
_AUTO_CONTINUATION_BLOCKING_DECISIONS = {"stop_loss", "terminal_stop", "completed"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _source_ref(*, study_root: Path, role: str, relative_path: Path, workspace_root: Path) -> dict[str, Any]:
    path = study_root / relative_path
    return {"ref_kind": "repo_path", "role": role, "ref": _workspace_relative(path, workspace_root=workspace_root), "exists": path.exists()}


def _study_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    source_refs = [
        _source_ref(
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
            payload[field_name] = _read_json_object(study_root / relative_path)
    payload["paper_autonomy_loop"] = _paper_autonomy_loop_projection(study_root=study_root)
    payload["publication_aftercare"] = publication_aftercare.build_publication_aftercare_plan(
        study_root=study_root,
    )
    payload["memory_paper_soak_proof"] = _memory_paper_soak_proof_projection(
        study_root=study_root,
        profile=profile,
    )
    payload["autonomy_continuation"] = _autonomy_continuation_projection(
        study=payload,
        profile=profile,
    )
    return payload


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path for path in profile.studies_root.iterdir() if path.is_dir())


def export_family_sidecar(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    opl_production_proof_ref: str | Path | None = None,
) -> dict[str, Any]:
    studies = [_study_projection(study_root=study_root, profile=profile) for study_root in _study_roots(profile)]
    generated_at = _now_iso()
    opl_production_proof = opl_provider_ready_adapter.load_opl_production_proof(opl_production_proof_ref)
    provider_availability = opl_provider_ready_adapter.build_provider_availability_from_opl_proof(
        opl_production_proof=opl_production_proof,
        proof_ref=opl_production_proof_ref,
    )
    functional_closure = build_sidecar_functional_closure_projection(
        profile=profile,
        profile_ref=profile_ref,
        allowed_task_kinds=ALLOWED_TASK_KINDS,
        opl_production_proof=opl_production_proof,
        opl_production_proof_ref=opl_production_proof_ref,
    )
    pending_tasks = _pending_family_tasks(
        studies=studies,
        profile=profile,
        profile_ref=profile_ref,
        provider_availability=provider_availability,
        opl_production_proof_ref=opl_production_proof_ref,
    )
    return {
        "surface_kind": "mas_family_sidecar_export",
        "version": "mas-family-sidecar.v1",
        "target_domain_id": "medautoscience",
        "generated_at": generated_at,
        "profile": {
            "profile_name": profile.name,
            "profile_ref": str(profile_ref),
            "hermes_profile_configured": bool(profile.hermes_agent_repo_root or profile.hermes_home_root),
            "hermes_home_root": str(profile.hermes_home_root),
        },
        "workspace": {
            "workspace_root": str(profile.workspace_root),
            "runtime_root": str(profile.runtime_root),
            "studies_root": str(profile.studies_root),
            "workspace_exists": profile.workspace_root.exists(),
            "studies_root_exists": profile.studies_root.exists(),
        },
        "online_runtime_framework": {
            "owner": "one-person-lab",
            "framework_role": "codex_first_stage_led_provider_backed_runtime_framework",
            "stage_semantics": "human_expert_large_task_stage",
            "minimal_executor": "Codex CLI",
            "provider_abstraction": "opl_family_runtime_provider",
            "target_production_provider": "Temporal",
            "executor_adapter_requirement": {
                "owner": "one-person-lab",
                "generic_executor_adapter_owner": "one-person-lab",
                "default_executor_kind": "codex_cli_default",
                "required_capability": "opl_executor_adapter_receipt",
                "mas_accepts": "typed_closeout_or_domain_task_receipt",
                "mas_local_codex_cli_scope": "standalone_diagnostics_only",
                "external_executor_opt_in_policy": "explicit_opl_opt_in_then_typed_receipt_only",
                "mas_owned_hermes_or_claude_executor": False,
                "mas_does_not_provide": [
                    "hosted_executor",
                    "hermes_executor_adapter",
                    "claude_executor_adapter",
                ],
            },
            "optional_executor_adapters": [
                {
                    "adapter_id": "hermes_agent",
                    "display_name": "Hermes-Agent",
                    "classification": "explicit_optional_executor_adapter",
                    "runtime_policy": "explicit_opl_opt_in_then_typed_receipt_only",
                    "executor_policy": "not_a_mas_executor_adapter",
                    "default_provider": False,
                }
            ],
            "role": "stage_attempt_queue_wakeup_retry_dead_letter_human_gate_receipt_projection_transport",
            "not_authority_for": ["study_truth", "publication_quality", "artifact_gate", "paper_package"],
        },
        "dispatch": {
            "entrypoint": "medautosci sidecar dispatch --task <task.json> --format json",
            "allowed_task_kinds": sorted(ALLOWED_TASK_KINDS),
            "receipt_policy": "MAS writes a domain control receipt only; paper, publication, and package truth remain untouched.",
            "receipt_refs": opl_provider_ready_adapter.receipt_refs_for_profile(profile),
        },
        "authority_boundary": authority_boundary_payload(),
        "opl_substrate_adapter": build_opl_substrate_adapter_projection(
            profile=profile,
            studies=studies,
            authority_boundary_payload=authority_boundary_payload,
            workspace_relative=lambda path: _workspace_relative(path, workspace_root=profile.workspace_root),
            text=_text,
            mapping=_mapping,
        ),
        "functional_consumer_boundary": consumer_migration.build_functional_consumer_boundary(),
        "ars_learning_projection": build_ars_learning_projection(),
        "family_transition_spec_descriptor": (
            study_domain_transition_table.build_family_transition_spec_descriptor()
        ),
        "provider_ready_adapter": functional_closure["provider_ready_contract"],
        "managed_temporal_state_consistency": (
            opl_provider_ready_adapter.build_managed_temporal_state_consistency_read_model(
                provider_availability=provider_availability,
            )
        ),
        "owner_receipt_contract": opl_provider_ready_adapter.build_owner_receipt_contract_surface(
            provider_availability=provider_availability,
        ),
        "domain_owner_receipt_contract": opl_provider_ready_adapter.build_owner_receipt_contract_surface(
            provider_availability=provider_availability,
        ),
        "lifecycle_apply_requests": opl_provider_ready_adapter.build_lifecycle_apply_requests_surface(),
        "lifecycle_guarded_apply_proof": (
            opl_provider_ready_adapter.build_lifecycle_guarded_apply_proof_surface()
        ),
        "runtime_transport_handoff_projection": (
            functional_closure["provider_ready_contract"]["runtime_transport_handoff_projection"]
        ),
        "legacy_retirement_tombstone_proof": opl_provider_ready_adapter.build_legacy_retirement_tombstone_proof(),
        "workspace_runtime_evidence_receipt": functional_closure["workspace_runtime_evidence_receipt"],
        "standard_domain_agent_skeleton": functional_closure["standard_domain_agent_skeleton"],
        "mas_functional_closure_status_projection": (
            functional_closure["functional_closure_status_projection"]
        ),
        "family_runtime_supervision": {
            "surface_kind": "family_runtime_supervision",
            "version": "family-runtime-supervision.v1",
            "target_domain_id": "medautoscience",
            "supervision_id": f"{profile.name}_mas_family_runtime_supervision",
            "adapter_id": "opl_family_runtime_provider_wakeup_to_mas_sidecar",
            "cadence": {"interval_seconds": 60},
            "lease_freshness": {"state": "unknown", "observed_at": generated_at, "max_age_seconds": 180},
            "slo_state": {
                "state": _aggregate_slo_state(studies),
                "summary": "MAS exposes SLO state as read-only projection for OPL family-runtime indexing.",
            },
            "repair_command": f"medautosci runtime domain-route-reconcile --profile {profile_ref} --mode developer_apply_safe --dry-run",
            "local_scheduler_tombstone_ref": (
                "contracts/runtime/legacy-active-path-tombstones.json#mas-local-scheduler"
            ),
            "safe_reconcile_hint": (
                "Use OPL provider/runtime manager wakeup plus medautosci sidecar dispatch; "
                "MAS local scheduler is physical-retired tombstone/provenance only."
            ),
            "consumer_migration": consumer_migration.build_consumer_migration_contract(
                adapter_id="opl_family_runtime_provider_wakeup_to_mas_sidecar",
                manager="opl_provider_runtime_manager",
            ),
            "domain_owned_source_refs": _aggregate_domain_refs(studies),
            "read_only_authority_boundary": {
                "projection_owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "runtime_owner": "one-person-lab",
                "scheduler_owner": "one-person-lab",
                "mas_local_scheduler_role": consumer_migration.LOCAL_TOMBSTONE_PATH_ROLE,
                "authority": "read_only_projection",
                "forbidden_authorities": authority_boundary_payload()["forbidden_authorities"],
            },
        },
        "pending_family_tasks": pending_tasks,
        "studies": studies,
    }


def _hard_human_gate_required(controller: Mapping[str, Any]) -> bool:
    if bool(controller.get("requires_human_confirmation")):
        return True
    gates = controller.get("family_human_gates")
    return isinstance(gates, list) and len(gates) > 0


def _terminal_controller_decision(controller: Mapping[str, Any]) -> bool:
    decision_type = _text(controller.get("decision_type"))
    route_target = _text(controller.get("route_target"))
    return decision_type in _AUTO_CONTINUATION_BLOCKING_DECISIONS or route_target == "stop"


def _continuation_reason(study: Mapping[str, Any]) -> str | None:
    slo = _mapping(study.get("slo_status"))
    runtime = _mapping(study.get("runtime_supervision"))
    recovery = _mapping(study.get("recovery_intent"))
    controller = _mapping(study.get("controller_decisions"))
    if _hard_human_gate_required(controller):
        return None
    if _terminal_controller_decision(controller):
        return None
    if _text(slo.get("state")) == "breach":
        return _text(slo.get("breach_reason")) or "slo_breach"
    if _text(runtime.get("runtime_decision")) == "blocked":
        return _text(runtime.get("runtime_reason")) or "runtime_blocked"
    if _text(runtime.get("runtime_liveness_status")) == "parked":
        return _text(runtime.get("runtime_reason")) or "runtime_parked"
    if _text(recovery.get("current_action")) == "safe_reconcile_ready":
        return "safe_reconcile_ready"
    return None


def _paper_autonomy_loop_projection(*, study_root: Path) -> dict[str, Any]:
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
    accept = _mapping(refinement.get("accept"))
    repair_loop = _mapping(refinement.get("repair_loop"))
    repair_plan = _mapping(repair_loop.get("repair_plan"))
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
        "accept_status": _text(accept.get("status")),
        "repair_plan": dict(repair_plan),
        "repair_work_units": work_units,
        "source_eval_id": _text(_mapping(refinement.get("snapshot")).get("source_eval_id")),
        "source_refs": [
            {"role": "publication_eval", "ref": str(publication_eval_path), "exists": True},
        ],
        "authority_boundary": authority_boundary_payload(),
    }


def _memory_paper_soak_proof_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    proof_path = stage_knowledge_plane.paper_soak_memory_apply_proof_path(study_root=study_root)
    proof = _read_json_object(proof_path)
    if proof is None:
        return {
            "surface_kind": "mas_memory_paper_soak_proof_projection",
            "status": "missing",
            "proof_ref": _workspace_relative(proof_path, workspace_root=profile.workspace_root),
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
        "status": _text(proof.get("status")) or "missing",
        "proof_ref": _workspace_relative(proof_path, workspace_root=profile.workspace_root),
        "receipt_refs": receipt_refs,
        "route_memory_ref_count": len(_mapping(proof.get("stage_entry")).get("publication_route_memory_refs") or []),
        "router_receipt_ref_count": len(proof.get("mas_router_receipt_refs") or []),
        "writeback_proposal_ref_count": len(proof.get("typed_closeout_writeback_proposals") or []),
        "source_fingerprint": _text(proof.get("source_fingerprint")),
        "authority_boundary": _mapping(proof.get("authority_boundary")) or authority_boundary_payload(),
        "read_only_display_policy": _mapping(proof.get("read_only_display_policy")),
    }


def _autonomy_continuation_projection(*, study: Mapping[str, Any], profile: WorkspaceProfile) -> dict[str, Any]:
    controller = _mapping(study.get("controller_decisions"))
    reason = _continuation_reason(study)
    return {
        "surface_kind": "mas_autonomy_continuation_projection",
        "eligible_for_auto_dispatch": reason is not None,
        "blocked_by_human_gate": _hard_human_gate_required(controller),
        "blocked_by_terminal_decision": _terminal_controller_decision(controller),
        "reason": reason,
        "recommended_task_kind": "domain_route/reconcile-apply" if reason is not None else None,
        "recommended_domain_owner": "med-autoscience" if reason is not None else None,
        "workspace_profile": profile.name,
    }


def _pending_family_tasks(
    *,
    studies: list[Mapping[str, Any]],
    profile: WorkspaceProfile,
    profile_ref: Path,
    provider_availability: Mapping[str, Any],
    opl_production_proof_ref: str | Path | None,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    tasks.extend(
        provider_hosted_guarded_apply_tasks(
            profile=profile,
            profile_ref=profile_ref,
            provider_availability=provider_availability,
            opl_production_proof_ref=opl_production_proof_ref,
            owner_source_refs_by_target={
                target: owner_controller_decision_refs(
                    profile=profile,
                    target_study_id=target,
                )
                for target in DEFAULT_GUARDED_APPLY_TARGETS
            },
        )
    )
    for study in studies:
        study_id = _text(study.get("study_id"))
        if study_id is None:
            continue
        tasks.extend(
            _paper_autonomy_tasks(
                study=study,
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
            )
        )
        tasks.extend(
            publication_aftercare.build_publication_aftercare_pending_tasks(
                profile_name=profile.name,
                profile_ref=profile_ref,
                study_id=study_id,
                projection=_mapping(study.get("publication_aftercare")),
            )
        )
        handoff_task = owner_route_handoff_task(
            study=study,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        if handoff_task is not None:
            tasks.append(handoff_task)
        controller_task = controller_decision_route_back_task(
            study=study,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        if controller_task is not None:
            tasks.append(controller_task)
        continuation = _mapping(study.get("autonomy_continuation"))
        if not continuation.get("eligible_for_auto_dispatch"):
            continue
        reason = _text(continuation.get("reason")) or "autonomy_continuation"
        task_kind = _text(continuation.get("recommended_task_kind")) or "domain_route/reconcile-apply"
        tasks.append(
            {
                "domain_id": "medautoscience",
                "task_kind": task_kind,
                "priority": 50,
                "source": "mas-sidecar-export",
                "requires_approval": False,
                "dedupe_key": f"mas:{profile.name}:{study_id}:autonomy-continuation:{reason}",
                "payload": {
                    "profile": str(profile_ref),
                    "study_id": study_id,
                    "continuation_reason": reason,
                    "authority_boundary": "mas_owner_reconcile_only",
                },
            }
        )
    return tasks


def _paper_autonomy_tasks(
    *,
    study: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    loop = _mapping(study.get("paper_autonomy_loop"))
    if loop.get("eligible_for_auto_dispatch") is not True:
        return []
    tasks: list[dict[str, Any]] = []
    for unit in loop.get("repair_work_units") or []:
        if not isinstance(unit, Mapping):
            continue
        unit_id = _text(unit.get("unit_id"))
        idempotency_key = _text(unit.get("idempotency_key"))
        if unit_id is None or idempotency_key is None:
            continue
        tasks.append(
            {
                "domain_id": "medautoscience",
                "task_kind": "paper_autonomy/repair-recheck",
                "priority": 40,
                "source": "mas-sidecar-export",
                "requires_approval": False,
                "dedupe_key": idempotency_key,
                "payload": {
                    "profile": str(profile_ref),
                    "study_id": study_id,
                    "paper_autonomy_reason": _text(loop.get("reason")) or "ai_reviewer_repair_recheck_required",
                    "repair_work_unit": dict(unit),
                    "authority_boundary": "mas_owner_reconcile_only",
                },
                "source_refs": list(unit.get("source_refs") or []),
                "dispatch_owner": "med-autoscience",
                "profile_name": profile.name,
            }
        )
    return tasks


def _aggregate_slo_state(studies: list[Mapping[str, Any]]) -> str:
    states = {
        _text(_mapping(study.get("slo_status")).get("state"))
        for study in studies
        if _mapping(study.get("slo_status"))
    }
    if "breach" in states:
        return "breach"
    if "watch" in states:
        return "watch"
    if "met" in states:
        return "met"
    return "unknown"


def _aggregate_domain_refs(studies: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for study in studies:
        for ref in study.get("domain_owned_source_refs") or []:
            if isinstance(ref, dict) and ref.get("exists") is True:
                refs.append(ref)
    return refs[:50]


__all__ = ["export_family_sidecar"]
