from __future__ import annotations

from typing import Any


DEFAULT_CALLER_SURFACES = (
    "cli",
    "mcp",
    "skill",
    "product_entry",
    "sidecar",
    "status",
    "workbench",
    "projection_shell",
    "test_lane_harness",
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

PHYSICAL_DELETE_REQUIRED_GATES = (
    "stale_surface_scan_clean",
    "opl_replacement_parity",
    "mas_owner_receipt_parity",
    "focused_tests_green",
    "no_forbidden_write_proof",
    "tombstone_refs_landed",
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
            "sidecar",
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
                surface_id="sidecar",
                target_role="opl_generated_sidecar_handoff_surface",
                mas_allowed_role="domain_owner_route_handoff_refs",
                parity_ref="sidecar_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="status",
                target_role="opl_generated_status_wrapper_over_mas_truth_refs",
                mas_allowed_role="domain_truth_status_projection",
                parity_ref="status_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="workbench",
                target_role="opl_hosted_workbench_shell_consuming_mas_refs",
                mas_allowed_role="domain_projection_refs",
                parity_ref="workbench_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="projection_shell",
                target_role="opl_generated_projection_shell",
                mas_allowed_role="domain_projection_builder",
                parity_ref="projection_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="test_lane_harness",
                target_role="opl_generated_harness_consumer_over_mas_pack",
                mas_allowed_role="focused_contract_harness",
                parity_ref="test_lane_harness_parity",
                default_caller_owner=replacement_owner,
            ),
        ],
        "proof_refs": [
            "functional_consumer_boundary.generated_surface_handoff",
            "family_action_catalog",
            "family_stage_control_plane_descriptor",
            "product_entry_manifest",
            "sidecar_export",
            "mcp_tool_manifest",
        ],
    }


def _not_ready_gate_results(
    *,
    opl_replacement_parity: str,
    mas_owner_receipt_parity: str,
    tombstone_refs_landed: str = "required_before_delete",
) -> dict[str, Any]:
    return {
        "stale_surface_scan_clean": False,
        "opl_replacement_parity": opl_replacement_parity,
        "opl_default_caller_readiness": "ready_domain_evidence_required",
        "mas_owner_receipt_parity": mas_owner_receipt_parity,
        "focused_tests_green": "focused_lane_required",
        "tombstone_refs_landed": tombstone_refs_landed,
    }


def _ready_gate_results() -> dict[str, Any]:
    return {
        "stale_surface_scan_clean": True,
        "opl_replacement_parity": "satisfied_or_not_runtime_candidate",
        "opl_default_caller_readiness": "ready",
        "mas_owner_receipt_parity": "satisfied_or_not_runtime_candidate",
        "focused_tests_green": "focused_lane_tracks_no_resurrection",
        "tombstone_refs_landed": "not_required_for_no_alias_physical_retirement",
    }


def _retirement_candidate(
    *,
    surface_id: str,
    code_paths: list[str],
    current_ref_status: str,
    mas_role: str,
    delete_gate_status: str,
    gate_results: dict[str, Any],
    domain_or_diagnostic_ref_consumers: list[str],
    stale_surface_scan_clean: bool = False,
    physical_delete_permitted: bool = False,
    deletion_readiness_worklist_ref: str | None = None,
    no_forbidden_write_proof_refs: list[str] | None = None,
    latest_thinning_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = {
        "surface_id": surface_id,
        "code_paths": code_paths,
        "default_runtime_owner": "one-person-lab",
        "mas_default_runtime_owner_allowed": False,
        "stale_surface_scan_clean": stale_surface_scan_clean,
        "current_ref_status": current_ref_status,
        "domain_or_diagnostic_ref_consumers": list(domain_or_diagnostic_ref_consumers),
        "mas_role": mas_role,
        "physical_delete_permitted": physical_delete_permitted,
        "delete_gate_status": delete_gate_status,
        "no_resurrection_proof": {
            "default_runtime_owner": "one-person-lab",
            "current_ref_status": current_ref_status,
            "physical_delete_allowed": physical_delete_permitted,
        },
        "gate_results": gate_results,
    }
    if deletion_readiness_worklist_ref is not None:
        candidate["deletion_readiness_worklist_ref"] = deletion_readiness_worklist_ref
    if no_forbidden_write_proof_refs is not None:
        candidate["no_forbidden_write_proof_refs"] = list(no_forbidden_write_proof_refs)
    if latest_thinning_evidence is not None:
        candidate["latest_thinning_evidence"] = dict(latest_thinning_evidence)
    return candidate


def build_physical_retirement_gate_matrix(
    *,
    schema_version: int,
    replacement_owner: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_generated_caller_retirement_gate_matrix",
        "schema_version": schema_version,
        "status": "physical_delete_blocked_until_all_gate_inputs_hold",
        "default_caller_owner": replacement_owner,
        "default_caller_boundary_ref": "functional_consumer_boundary.generated_default_caller_boundary",
        "opl_default_caller_readiness_ref": (
            "functional_consumer_boundary.generated_default_caller_boundary."
            "opl_default_caller_readiness_evidence"
        ),
        "physical_delete_requires_all_gates": list(PHYSICAL_DELETE_REQUIRED_GATES),
        "retirement_candidates": [
            _retirement_candidate(
                surface_id="runtime_transport",
                code_paths=[
                    "src/med_autoscience/runtime_transport/",
                ],
                current_ref_status="physical_retired_no_alias",
                mas_role="none",
                delete_gate_status="closed_stale_surface_scan_clean",
                gate_results=_ready_gate_results(),
                domain_or_diagnostic_ref_consumers=[],
                stale_surface_scan_clean=True,
                physical_delete_permitted=True,
                latest_thinning_evidence={
                    "status": "runtime_transport_package_physically_absent",
                    "no_alias_guard_ref": "tests/test_adapter_retirement_boundary.py",
                    "does_not_claim_paper_closure": True,
                },
            ),
            _retirement_candidate(
                surface_id="lifecycle_refs_sqlite_index",
                code_paths=[
                    "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter.py",
                    "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter_parts/",
                    "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
                ],
                current_ref_status="physical_retired_no_alias_replaced_by_domain_authority_refs_index",
                mas_role="none",
                delete_gate_status="closed_stale_surface_scan_clean",
                gate_results=_ready_gate_results(),
                domain_or_diagnostic_ref_consumers=[],
                stale_surface_scan_clean=True,
                physical_delete_permitted=True,
                latest_thinning_evidence={
                    "status": "runtime_lifecycle_sqlite_adapter_physically_absent",
                    "replacement_surface": "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
                    "does_not_claim_generic_persistence_owner": True,
                    "does_not_claim_paper_closure": True,
                },
            ),
            _retirement_candidate(
                surface_id="domain_authority_refs_index",
                code_paths=[
                    "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
                    "src/med_autoscience/opl_domain_pack/",
                ],
                current_ref_status="domain_authority_refs_index_active_no_runtime_lifecycle_owner",
                mas_role="domain_authority_refs_only",
                delete_gate_status="not_a_runtime_retirement_candidate",
                gate_results=_ready_gate_results(),
                domain_or_diagnostic_ref_consumers=[
                    "owner receipt refs",
                    "typed blocker refs",
                    "sidecar/product-entry domain authority projections",
                ],
            ),
            _retirement_candidate(
                surface_id="workbench_shell",
                code_paths=[
                    "src/med_autoscience/controllers/progress_portal.py",
                    "src/med_autoscience/controllers/progress_portal_parts/",
                    "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
                ],
                current_ref_status="domain_projection_refs_active",
                mas_role="domain_projection_refs_for_opl_workbench",
                delete_gate_status="blocked_domain_projection_refs_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_generated_workbench_default_required"
                    ),
                    mas_owner_receipt_parity="domain_projection_receipt_refs_required",
                    tombstone_refs_landed="landed_for_retired_legacy_only",
                ),
                domain_or_diagnostic_ref_consumers=[
                    "progress portal CLI projection",
                    "workspace cockpit domain projection",
                    "product-entry manifest read model",
                ],
            ),
            _retirement_candidate(
                surface_id="owner_route_handoff",
                code_paths=[
                    "src/med_autoscience/controllers/owner_route_handoff.py",
                    (
                        "src/med_autoscience/controllers/owner_route_handoff_parts/"
                        "export_projection.py"
                    ),
                    (
                        "src/med_autoscience/controllers/owner_route_handoff_parts/"
                        "export_study_projection.py"
                    ),
                    (
                        "src/med_autoscience/controllers/owner_route_handoff_parts/"
                        "dispatch_orchestration.py"
                    ),
                ],
                current_ref_status="domain_owner_route_handoff_refs_active",
                mas_role="domain_owner_route_handoff_refs",
                delete_gate_status="blocked_domain_dispatch_refs_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_opl_generated_sidecar_default_required"
                    ),
                    mas_owner_receipt_parity=(
                        "pending_real_paper_line_owner_receipt_or_stable_typed_blocker"
                    ),
                ),
                domain_or_diagnostic_ref_consumers=[
                    "sidecar export refs-only handoff",
                    "sidecar dispatch guarded owner receipt",
                ],
                deletion_readiness_worklist_ref=(
                    "functional_consumer_boundary.active_path_residue_cleanup_gates."
                    "owner_route_handoff_domain_ref_entry.deletion_readiness_worklist"
                ),
                no_forbidden_write_proof_refs=[
                    (
                        "tests/test_cli_cases/owner_route_handoff_command_cases/"
                        "dispatch_cases.py::"
                        "test_sidecar_dispatch_accepts_runtime_recovery_without_writing_truth"
                    ),
                    "owner_route_handoff_response.forbidden_write_guard_proof",
                ],
                latest_thinning_evidence={
                    "status": "sidecar_export_projection_split_to_parts_no_runtime_control_alias",
                    "domain_ref_entry_path": "src/med_autoscience/controllers/owner_route_handoff.py",
                    "extracted_paths": [
                        (
                            "src/med_autoscience/controllers/owner_route_handoff_parts/"
                            "export_projection.py"
                        ),
                        (
                            "src/med_autoscience/controllers/owner_route_handoff_parts/"
                            "export_study_projection.py"
                        ),
                        (
                            "src/med_autoscience/controllers/owner_route_handoff_parts/"
                            "dispatch_orchestration.py"
                        ),
                    ],
                    "does_not_claim_physical_delete": True,
                },
            ),
            _retirement_candidate(
                surface_id="status_projection",
                code_paths=[
                    "src/med_autoscience/controllers/product_entry_parts/",
                    "src/med_autoscience/controllers/progress_projection.py",
                ],
                current_ref_status="domain_truth_status_projection_active",
                mas_role="domain_truth_status_projection",
                delete_gate_status="blocked_domain_truth_status_projection_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_opl_generated_status_default_required"
                    ),
                    mas_owner_receipt_parity="progress_projection_truth_refs_required",
                    tombstone_refs_landed="landed_for_retired_legacy_only",
                ),
                domain_or_diagnostic_ref_consumers=[
                    "progress_projection domain truth projection",
                    "product-entry status read model",
                ],
            ),
        ],
        "no_resurrection_summary": {
            "default_runtime_owner": "one-person-lab",
            "mas_default_runtime_owner_allowed": False,
            "all_runtime_control_surfaces_retired_or_opl_owned": True,
            "physical_delete_candidate_count": 6,
            "physical_delete_ready_count": 2,
            "physically_retired_surface_ids": [
                "runtime_transport",
                "lifecycle_refs_sqlite_index",
            ],
            "remaining_surfaces_are_domain_refs_not_runtime_control": True,
        },
        "forbidden_claims": [
            "runtime_transport_reintroduced_as_mas_owner",
            "lifecycle_refs_reintroduced_as_mas_owner",
            "owner_route_handoff_domain_ref_entry_deleted",
            "status_projection_deleted",
            "workbench_shell_deleted",
            "paper_closure_authorized_by_retirement_gate",
        ],
    }


__all__ = [
    "ALLOWED_MAS_PROGRAM_ROLES_AFTER_CUTOVER",
    "DEFAULT_CALLER_SURFACES",
    "PHYSICAL_DELETE_REQUIRED_GATES",
    "build_generated_default_caller_boundary",
    "build_opl_default_caller_readiness_evidence",
    "build_physical_retirement_gate_matrix",
]
