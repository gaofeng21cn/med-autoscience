from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.controllers.opl_functional_closure_surfaces import (
    build_functional_closure_status_projection,
    build_lifecycle_apply_requests_surface,
    build_lifecycle_guarded_apply_proof_surface,
    build_owner_receipt_contract_surface,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.opl_provider_ready_adapter_parts.lifecycle_inventory import (
    build_opl_lifecycle_inventory_surface,
)
from med_autoscience.controllers.opl_provider_ready_adapter_parts.provider_readiness import (
    DEFAULT_PROVIDER_GUARDED_SOAK_TARGETS,
    DOMAIN_OWNER,
    FORBIDDEN_AUTHORITY_WRITES,
    GUARDED_APPLY_PROOF_SURFACE,
    OPL_OWNER,
    PROVIDER_HOSTED_PROOF_SURFACE,
    TARGET_DOMAIN_ID,
    build_forbidden_write_guard_proof,
    build_legacy_retirement_tombstone_proof,
    build_managed_temporal_state_consistency_read_model,
    build_provider_availability_from_opl_proof,
    build_provider_guarded_soak_read_model,
    build_provider_residency_read_model,
    _provider_residency_receipt_refs_from_availability,
    load_opl_production_proof,
)
from med_autoscience.controllers.opl_provider_ready_adapter_parts.skeleton_mapping import (
    build_domain_agent_skeleton_mapping_surface,
    build_physical_skeleton_layout_audit_surface,
    build_standard_domain_agent_skeleton_surface,
)
from med_autoscience.controllers.opl_provider_ready_adapter_parts.workspace_evidence import (
    build_workspace_runtime_evidence_receipt_surface,
)


SURFACE_KIND = "mas_opl_provider_ready_contract"
VERSION = "mas-opl-provider-ready.v1"

def build_opl_provider_ready_contract(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    allowed_task_kinds: Iterable[str],
    opl_production_proof: Mapping[str, Any] | None = None,
    opl_production_proof_ref: str | Path | None = None,
) -> dict[str, Any]:
    profile_ref_text = str(profile_ref) if profile_ref is not None else "<profile>"
    provider_availability = build_provider_availability_from_opl_proof(
        opl_production_proof=opl_production_proof,
        proof_ref=opl_production_proof_ref,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "provider_ready_skeleton",
        "summary": (
            "MAS exposes a provider-ready OPL/Temporal adapter contract while MAS-owned runtime, "
            "publication, quality, and artifact truth remain in workspace artifacts."
        ),
        "provider_topology": _provider_topology(provider_availability=provider_availability),
        "executor_requirements": {
            "adapter_owner": "one-person-lab",
            "generic_executor_adapter_owner": OPL_OWNER,
            "default_executor_kind": "codex_cli_default",
            "required_adapter": "opl_executor_adapter",
            "accepted_receipts": ["opl_provider_attempt_receipt", "typed_closeout_receipt"],
            "domain_action_authority": DOMAIN_OWNER,
            "mas_builtin_executor_adapter": False,
            "mas_local_codex_cli_scope": "standalone_diagnostics_only",
            "non_default_executor_opt_in_owner": OPL_OWNER,
            "non_default_executor_opt_in_policy": "explicit_opt_in_only_receipt_to_mas",
            "mas_owned_hermes_or_claude_executor": False,
        },
        "direct_mas_path": _direct_mas_path(profile_ref_text),
        "sidecar_contract": _sidecar_contract(profile=profile, profile_ref_text=profile_ref_text),
        "forbidden_write_guard": build_forbidden_write_guard_proof(
            result="configured",
            task_id=None,
            task_kind=None,
            requested_writes=(),
        ),
        "managed_temporal_state_consistency": build_managed_temporal_state_consistency_read_model(
            provider_availability=provider_availability,
        ),
        "provider_guarded_soak_read_model": build_provider_guarded_soak_read_model(
            provider_availability=provider_availability,
        ),
        "provider_residency_read_model": build_provider_residency_read_model(
            provider_available=provider_availability.get("provider_attempt_available") is True,
            receipt_refs=_provider_residency_receipt_refs_from_availability(provider_availability),
        ),
        "owner_receipt_contract": build_owner_receipt_contract_surface(
            provider_availability=provider_availability,
        ),
        "legacy_retirement_tombstone_proof": build_legacy_retirement_tombstone_proof(),
        "workspace_runtime_artifact_root_locator": _workspace_runtime_artifact_root_locator(profile=profile),
        "workspace_runtime_evidence_receipt": build_workspace_runtime_evidence_receipt_surface(profile=profile),
        "lifecycle_inventory": build_opl_lifecycle_inventory_surface(),
        "lifecycle_apply_requests": build_lifecycle_apply_requests_surface(),
        "lifecycle_guarded_apply_proof": build_lifecycle_guarded_apply_proof_surface(),
        "domain_agent_skeleton_mapping": build_domain_agent_skeleton_mapping_surface(),
        "allowed_task_kinds": sorted(str(item) for item in allowed_task_kinds),
        "truth_source_precedence": {
            "direct_mas_skill_path": "authoritative",
            "opl_provider_attempt_history": "transport_receipt_only",
            "opl_runtime_projection": "read_only_index_only",
            "provider_completion_can_advance_paper_progress": False,
            "paper_progress_requires_mas_artifact_delta_or_gate_owner": True,
        },
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def receipt_refs_for_profile(profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_sidecar_receipt_refs",
        "version": "mas-opl-sidecar-receipt-refs.v1",
        "dispatch_receipt_root": "artifacts/runtime/opl_family_sidecar/dispatch_receipts",
        "dispatch_receipt_ref_template": (
            "artifacts/runtime/opl_family_sidecar/dispatch_receipts/<sha256(task_id)[:20]>.json"
        ),
        "export_receipt_ref": "sidecar export response body",
        "workspace_root": str(profile.workspace_root),
        "repo_tracked": False,
        "receipt_authority": DOMAIN_OWNER,
    }


def requested_writes_from_task(task: Mapping[str, Any]) -> list[str]:
    payload = task.get("payload") if isinstance(task.get("payload"), Mapping) else {}
    requested: list[str] = []
    for flag in (
        "domain_truth_write",
        "artifact_gate_override",
        "study_truth_write",
        "publication_quality_verdict",
        "current_package_write",
        "memory_body_write",
        "publication_route_memory_writeback_accept",
        "memory_write_router_accept",
    ):
        if bool(payload.get(flag)):
            requested.append(flag)
    payload_writes = payload.get("requested_writes")
    if isinstance(payload_writes, list):
        requested.extend(str(item) for item in payload_writes if str(item or "").strip())
    return list(dict.fromkeys(requested))


def _provider_topology(*, provider_availability: Mapping[str, Any] | None = None) -> dict[str, Any]:
    provider_available = _mapping(provider_availability).get("provider_attempt_available") is True
    return {
        "target_provider": "temporal",
        "target_provider_owner": "one-person-lab",
        "provider_state": "production_residency_proven" if provider_available else "contract_ready_skeleton",
        "hosted_runtime_policy": "opl_explicit_opt_in_only",
        "provider_attempt_owner": OPL_OWNER,
        "domain_action_owner": DOMAIN_OWNER,
        "provider_attempt_is_truth": False,
    }


def _direct_mas_path(profile_ref_text: str) -> dict[str, Any]:
    return {
        "path_id": "direct_mas_skill_path",
        "status": "authoritative",
        "profile_ref": profile_ref_text,
        "commands": {
            "read_status": f"medautosci study-progress --profile {profile_ref_text} --format json",
            "read_runtime": f"medautosci study-runtime-status --profile {profile_ref_text} --study-id <study_id>",
            "reconcile": f"medautosci runtime-supervisor-reconcile --profile {profile_ref_text} --dry-run",
        },
        "must_converge_with_opl_hosted_path": True,
    }


def _sidecar_contract(*, profile: WorkspaceProfile, profile_ref_text: str) -> dict[str, Any]:
    return {
        "export_command": f"medautosci sidecar export --profile {profile_ref_text} --format json",
        "dispatch_command": "medautosci sidecar dispatch --task <task.json> --format json",
        "queue_hydration_source": "/pending_family_tasks",
        "dispatch_receipt_refs": receipt_refs_for_profile(profile),
        "idempotency_contract": {
            "dedupe_key_required": True,
            "source_fingerprint_required_when_available": True,
            "provider_retry_must_reuse_task_id": True,
            "provider_retry_must_not_mutate_mas_truth": True,
        },
    }


def _workspace_runtime_artifact_root_locator(*, profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "surface_kind": "workspace_runtime_artifact_root_locator",
        "version": "workspace-runtime-artifact-root-locator.v1",
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "studies_root": str(profile.studies_root),
        "repo_root_tracks_real_artifacts": False,
        "locators": {
            "study_artifact_root": "studies/<study_id>/artifacts",
            "runtime_artifact_root": "studies/<study_id>/artifacts/runtime",
            "publication_eval": "studies/<study_id>/artifacts/publication_eval/latest.json",
            "controller_decisions": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "stage_knowledge_packet": "studies/<study_id>/artifacts/stage_knowledge/<stage>/latest.json",
            "dispatch_receipts": "artifacts/runtime/opl_family_sidecar/dispatch_receipts",
            "runtime_lifecycle_sqlite": "artifacts/runtime/runtime_lifecycle.sqlite",
        },
    }


__all__ = [
    "FORBIDDEN_AUTHORITY_WRITES",
    "SURFACE_KIND",
    "VERSION",
    "build_domain_agent_skeleton_mapping_surface",
    "build_forbidden_write_guard_proof",
    "build_functional_closure_status_projection",
    "build_legacy_retirement_tombstone_proof",
    "build_lifecycle_apply_requests_surface",
    "build_lifecycle_guarded_apply_proof_surface",
    "build_managed_temporal_state_consistency_read_model",
    "build_opl_lifecycle_inventory_surface",
    "build_opl_provider_ready_contract",
    "build_owner_receipt_contract_surface",
    "build_provider_availability_from_opl_proof",
    "build_physical_skeleton_layout_audit_surface",
    "build_provider_guarded_soak_read_model",
    "build_provider_residency_read_model",
    "build_standard_domain_agent_skeleton_surface",
    "build_workspace_runtime_evidence_receipt_surface",
    "load_opl_production_proof",
    "receipt_refs_for_profile",
    "requested_writes_from_task",
]
