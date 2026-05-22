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
    "refs_only_adapter",
)

PHYSICAL_DELETE_REQUIRED_GATES = (
    "active_caller_count=0",
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
        "active_caller_cutover": "ready",
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
    mas_retained_role: str,
    parity_ref: str,
    default_caller_owner: str,
) -> dict[str, Any]:
    return {
        "surface_id": surface_id,
        "default_caller_owner": default_caller_owner,
        "target_role": target_role,
        "mas_retained_role": mas_retained_role,
        "parity_ref": parity_ref,
        "active_default_caller_count": 0,
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
        "all_default_callers_migrated": True,
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
                mas_retained_role="domain_handler_target",
                parity_ref="cli_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="mcp",
                target_role="opl_generated_mcp_descriptor_surface",
                mas_retained_role="domain_handler_target",
                parity_ref="mcp_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="skill",
                target_role="opl_generated_skill_descriptor_surface",
                mas_retained_role="direct_skill_target",
                parity_ref="skill_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="product_entry",
                target_role="opl_generated_product_entry_surface",
                mas_retained_role="domain_handler_target",
                parity_ref="product_entry_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="sidecar",
                target_role="opl_generated_sidecar_handoff_surface",
                mas_retained_role="domain_sidecar_dispatch_adapter",
                parity_ref="sidecar_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="status",
                target_role="opl_generated_status_wrapper_over_mas_truth_refs",
                mas_retained_role="domain_truth_status_projection",
                parity_ref="status_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="workbench",
                target_role="opl_hosted_workbench_shell_consuming_mas_refs",
                mas_retained_role="domain_projection_refs",
                parity_ref="workbench_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="projection_shell",
                target_role="opl_generated_projection_shell",
                mas_retained_role="domain_projection_builder",
                parity_ref="projection_descriptor_parity",
                default_caller_owner=replacement_owner,
            ),
            _surface_boundary(
                surface_id="test_lane_harness",
                target_role="opl_generated_harness_consumer_over_mas_pack",
                mas_retained_role="focused_contract_harness",
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
        "active_caller_count=0": False,
        "opl_replacement_parity": opl_replacement_parity,
        "opl_default_caller_readiness": "ready_domain_evidence_required",
        "mas_owner_receipt_parity": mas_owner_receipt_parity,
        "focused_tests_green": "focused_lane_required",
        "tombstone_refs_landed": tombstone_refs_landed,
    }


def _retirement_candidate(
    *,
    surface_id: str,
    code_paths: list[str],
    active_caller_status: str,
    retained_as: str,
    delete_gate_status: str,
    gate_results: dict[str, Any],
    active_domain_or_diagnostic_callers: list[str],
    deletion_readiness_worklist_ref: str | None = None,
    no_forbidden_write_proof_refs: list[str] | None = None,
    latest_thinning_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = {
        "surface_id": surface_id,
        "code_paths": code_paths,
        "active_default_caller_count": 0,
        "active_default_caller_zero_proven": True,
        "active_caller_zero_proven": False,
        "active_caller_status": active_caller_status,
        "active_domain_or_diagnostic_callers": list(active_domain_or_diagnostic_callers),
        "retained_as": retained_as,
        "physical_delete_permitted": False,
        "delete_gate_status": delete_gate_status,
        "no_active_caller_proof": {
            "default_callers": [],
            "full_active_caller_status": "not_proven_retained_domain_or_diagnostic_adapter",
            "physical_delete_allowed": False,
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
                    "src/med_autoscience/controllers/runtime_watch_outer_loop_dispatch.py",
                    "src/med_autoscience/controllers/recovery_intent_ledger.py",
                ],
                active_caller_status="domain_receipt_adapter_active",
                retained_as="domain_receipt_adapter_or_standalone_diagnostic",
                delete_gate_status="blocked_domain_receipt_adapter_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_provider_attempt_queue_retry_parity_required"
                    ),
                    mas_owner_receipt_parity=(
                        "pending_real_paper_line_owner_receipt_or_stable_typed_blocker"
                    ),
                ),
                active_domain_or_diagnostic_callers=[
                    "MAS direct/local runtime diagnostic",
                    "runtime worker activity closeout receipt",
                    "controller recovery intent receipt refs",
                ],
            ),
            _retirement_candidate(
                surface_id="runtime_lifecycle_sqlite",
                code_paths=[
                    "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
                    "src/med_autoscience/runtime_protocol/study_runtime.py",
                    "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
                ],
                active_caller_status="refs_only_domain_sidecar_adapter_active",
                retained_as="refs_only_lifecycle_sidecar_index",
                delete_gate_status="blocked_refs_only_lifecycle_adapter_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_opl_lifecycle_index_parity_required"
                    ),
                    mas_owner_receipt_parity="domain_owner_receipt_ref_parity_required",
                ),
                active_domain_or_diagnostic_callers=[
                    "study_runtime event and snapshot refs",
                    "runtime lifecycle CLI refs",
                    "sidecar/product-entry lifecycle projections",
                ],
            ),
            _retirement_candidate(
                surface_id="workbench_shell",
                code_paths=[
                    "src/med_autoscience/controllers/progress_portal.py",
                    "src/med_autoscience/controllers/progress_portal_parts/",
                    "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
                ],
                active_caller_status="domain_projection_refs_active",
                retained_as="domain_projection_refs_for_opl_workbench",
                delete_gate_status="blocked_domain_projection_refs_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_generated_workbench_default_required"
                    ),
                    mas_owner_receipt_parity="domain_projection_receipt_refs_required",
                    tombstone_refs_landed="landed_for_retired_legacy_only",
                ),
                active_domain_or_diagnostic_callers=[
                    "progress portal CLI projection",
                    "workspace cockpit domain projection",
                    "product-entry manifest read model",
                ],
            ),
            _retirement_candidate(
                surface_id="sidecar_adapter",
                code_paths=[
                    "src/med_autoscience/controllers/sidecar_family_adapter.py",
                    (
                        "src/med_autoscience/controllers/sidecar_family_adapter_parts/"
                        "export_projection.py"
                    ),
                    (
                        "src/med_autoscience/controllers/sidecar_family_adapter_parts/"
                        "export_study_projection.py"
                    ),
                    (
                        "src/med_autoscience/controllers/sidecar_family_adapter_parts/"
                        "dispatch_orchestration.py"
                    ),
                ],
                active_caller_status="domain_sidecar_dispatch_adapter_active",
                retained_as="domain_sidecar_dispatch_adapter",
                delete_gate_status="blocked_domain_dispatch_adapter_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_opl_generated_sidecar_default_required"
                    ),
                    mas_owner_receipt_parity=(
                        "pending_real_paper_line_owner_receipt_or_stable_typed_blocker"
                    ),
                ),
                active_domain_or_diagnostic_callers=[
                    "sidecar export refs-only handoff",
                    "sidecar dispatch guarded owner receipt",
                ],
                deletion_readiness_worklist_ref=(
                    "functional_consumer_boundary.active_path_residue_cleanup_gates."
                    "sidecar_dispatch_adapter.deletion_readiness_worklist"
                ),
                no_forbidden_write_proof_refs=[
                    (
                        "tests/test_cli_cases/sidecar_family_adapter_command_cases/"
                        "dispatch_cases.py::"
                        "test_sidecar_dispatch_accepts_runtime_recovery_without_writing_truth"
                    ),
                    "sidecar_dispatch_response.forbidden_write_guard_proof",
                ],
                latest_thinning_evidence={
                    "status": "sidecar_export_projection_split_to_parts_facade_retained",
                    "facade_path": "src/med_autoscience/controllers/sidecar_family_adapter.py",
                    "extracted_paths": [
                        (
                            "src/med_autoscience/controllers/sidecar_family_adapter_parts/"
                            "export_projection.py"
                        ),
                        (
                            "src/med_autoscience/controllers/sidecar_family_adapter_parts/"
                            "export_study_projection.py"
                        ),
                        (
                            "src/med_autoscience/controllers/sidecar_family_adapter_parts/"
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
                    "src/med_autoscience/controllers/study_runtime_status.py",
                ],
                active_caller_status="domain_truth_status_projection_active",
                retained_as="domain_truth_status_projection",
                delete_gate_status="blocked_domain_truth_status_projection_active",
                gate_results=_not_ready_gate_results(
                    opl_replacement_parity=(
                        "structural_default_caller_ready_opl_generated_status_default_required"
                    ),
                    mas_owner_receipt_parity="study_runtime_status_truth_refs_required",
                    tombstone_refs_landed="landed_for_retired_legacy_only",
                ),
                active_domain_or_diagnostic_callers=[
                    "study_runtime_status domain truth projection",
                    "product-entry status read model",
                ],
            ),
        ],
        "no_active_caller_summary": {
            "active_default_caller_count": 0,
            "active_default_caller_zero_proven": True,
            "full_active_caller_zero_proven": False,
            "physical_delete_candidate_count": 5,
            "physical_delete_ready_count": 0,
        },
        "forbidden_claims": [
            "physical_delete_already_completed",
            "runtime_transport_active_caller_count_zero",
            "sqlite_lifecycle_active_caller_count_zero",
            "sidecar_dispatch_adapter_deleted",
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
