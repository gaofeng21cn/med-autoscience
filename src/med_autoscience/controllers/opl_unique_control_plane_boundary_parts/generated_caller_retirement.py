from __future__ import annotations

from typing import Any


DEFAULT_CALLER_SURFACES = (
    "cli",
    "mcp",
    "skill",
    "product_entry",
    "product_status",
    "product_session",
    "domain_handler",
    "workbench",
)

ALLOWED_MAS_PROGRAM_ROLES_AFTER_CUTOVER = (
    "direct_skill_target",
    "domain_handler",
    "owner_receipt_signer",
    "typed_blocker",
    "ai_first_validator",
    "diagnostic",
    "domain_authority_refs",
)

OPL_DEFAULT_CALLER_READINESS_COMMAND = (
    "opl agents default-callers --agent mas=/Users/gaofeng/workspace/med-autoscience --json"
)
OPL_DEFAULT_CALLER_READINESS_SURFACE = "opl_agent_generated_default_caller_readiness_report"


def build_opl_default_caller_readiness_evidence(*, replacement_owner: str) -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_default_caller_readiness_evidence",
        "schema_version": 1,
        "owner": replacement_owner,
        "source_command": OPL_DEFAULT_CALLER_READINESS_COMMAND,
        "source_surface_kind": OPL_DEFAULT_CALLER_READINESS_SURFACE,
        "status": "ready_domain_evidence_required",
        "default_caller_owner": replacement_owner,
        "generated_default_caller_surface_count": 8,
        "ready_surface_count": 8,
        "blocked_surface_count": 0,
        "structural_replacement_evidence_ready": True,
        "replacement_parity": "ready",
        "default_surface_cutover": "ready",
        "domain_owner_receipt_or_typed_blocker": (
            "required_from_mas_owner_before_physical_delete"
        ),
        "no_forbidden_write_proof": "required_before_physical_delete",
        "tombstone_or_provenance_ref": "required_before_physical_delete",
        "physical_delete_authorized": False,
        "authority_boundary": {
            "can_claim_domain_ready": False,
            "can_claim_quality_verdict": False,
            "can_claim_artifact_authority": False,
            "can_claim_production_ready": False,
            "can_authorize_physical_delete": False,
            "mas_truth_verdict_artifact_and_owner_receipt_stay_in_mas": True,
        },
        "consumed_surface_ids": [
            "cli",
            "mcp",
            "skill",
            "product_entry",
            "product_status",
            "product_session",
            "domain_handler",
            "workbench",
        ],
    }


def _surface_boundary(
    *,
    surface_id: str,
    target_role: str,
    mas_allowed_role: str,
    parity_ref: str,
    default_caller_owner: str,
) -> dict[str, Any]:
    return {
        "surface_id": surface_id,
        "default_caller_owner": default_caller_owner,
        "target_role": target_role,
        "mas_allowed_role": mas_allowed_role,
        "parity_ref": parity_ref,
        "default_runtime_owner": "one-person-lab",
        "mas_generic_owner_allowed": False,
        "physical_delete_is_not_implied": True,
    }


def build_generated_default_caller_boundary(
    *,
    schema_version: int,
    replacement_owner: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_generated_default_caller_boundary",
        "schema_version": schema_version,
        "status": "opl_generated_hosted_shell_is_default_caller",
        "default_caller_owner": replacement_owner,
        "mas_handwritten_shell_default_caller_allowed": False,
        "mas_handwritten_shell_expansion_allowed": False,
        "all_default_surfaces_generated": True,
        "physical_delete_is_not_implied": True,
        "opl_default_caller_readiness_evidence": build_opl_default_caller_readiness_evidence(
            replacement_owner=replacement_owner,
        ),
        "default_caller_surfaces": list(DEFAULT_CALLER_SURFACES),
        "allowed_mas_program_roles_after_cutover": list(ALLOWED_MAS_PROGRAM_ROLES_AFTER_CUTOVER),
        "surface_boundaries": [
            _surface_boundary(
                surface_id="cli",
                target_role="opl_generated_command_surface",
                mas_allowed_role="domain_handler_target",
                parity_ref="cli_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="mcp",
                target_role="opl_generated_mcp_descriptor_surface",
                mas_allowed_role="domain_handler_target",
                parity_ref="mcp_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="skill",
                target_role="opl_generated_skill_descriptor_surface",
                mas_allowed_role="direct_skill_target",
                parity_ref="skill_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="product_entry",
                target_role="opl_generated_product_entry_surface",
                mas_allowed_role="domain_handler_target",
                parity_ref="product_entry_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="product_status",
                target_role="opl_generated_status_read_model_surface",
                mas_allowed_role="domain_truth_status_projection",
                parity_ref="product_status_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="product_session",
                target_role="opl_generated_product_session_surface",
                mas_allowed_role="domain_handler_target",
                parity_ref="product_session_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="domain_handler",
                target_role="opl_generated_domain_handler_dispatch_shell",
                mas_allowed_role="domain_handler_target",
                parity_ref="domain_handler_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="workbench",
                target_role="opl_hosted_workbench_shell_consuming_mas_refs",
                mas_allowed_role="domain_projection_refs",
                parity_ref="workbench_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
        ],
        "proof_refs": [
            "functional_consumer_boundary.generated_surface_handoff",
            "family_action_catalog",
            "family_stage_control_plane_descriptor",
            "product_entry_manifest",
            "domain_handler_export",
            "mcp_tool_manifest",
        ],
    }

__all__ = [
    "ALLOWED_MAS_PROGRAM_ROLES_AFTER_CUTOVER",
    "DEFAULT_CALLER_SURFACES",
    "build_generated_default_caller_boundary",
    "build_opl_default_caller_readiness_evidence",
]
