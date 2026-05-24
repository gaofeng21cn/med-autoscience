from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile

from .. import opl_provider_ready_adapter
from ..opl_unique_control_plane_boundary_parts import consumer_migration


def build_sidecar_functional_closure_projection(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    allowed_task_kinds: Mapping[str, str],
    opl_production_proof: Mapping[str, Any] | None,
    opl_production_proof_ref: str | Path | None,
) -> dict[str, Any]:
    provider_ready_contract = opl_provider_ready_adapter.build_opl_provider_ready_contract(
        profile=profile,
        profile_ref=profile_ref,
        allowed_task_kinds=allowed_task_kinds,
        opl_production_proof=opl_production_proof,
        opl_production_proof_ref=opl_production_proof_ref,
    )
    workspace_runtime_evidence_receipt = (
        opl_provider_ready_adapter.build_workspace_runtime_evidence_receipt_surface(profile=profile)
    )
    standard_domain_agent_skeleton = (
        opl_provider_ready_adapter.build_standard_domain_agent_skeleton_surface()
    )
    functional_consumer_boundary = consumer_migration.build_functional_consumer_boundary()
    functional_closure_status_projection = (
        opl_provider_ready_adapter.build_functional_closure_status_projection(
            provider_residency_read_model=provider_ready_contract["provider_residency_read_model"],
            provider_guarded_soak_read_model=provider_ready_contract["provider_guarded_soak_read_model"],
            managed_temporal_state_consistency=provider_ready_contract["managed_temporal_state_consistency"],
            owner_receipt_contract=provider_ready_contract["owner_receipt_contract"],
            lifecycle_guarded_apply_proof=provider_ready_contract["lifecycle_guarded_apply_proof"],
            workspace_runtime_evidence_receipt=workspace_runtime_evidence_receipt,
            standard_domain_agent_skeleton=standard_domain_agent_skeleton,
            standard_agent_purity=functional_consumer_boundary["standard_agent_purity"],
        )
    )
    return {
        "provider_ready_contract": provider_ready_contract,
        "functional_consumer_boundary": functional_consumer_boundary,
        "workspace_runtime_evidence_receipt": workspace_runtime_evidence_receipt,
        "standard_domain_agent_skeleton": standard_domain_agent_skeleton,
        "functional_closure_status_projection": functional_closure_status_projection,
    }


__all__ = ["build_sidecar_functional_closure_projection"]
