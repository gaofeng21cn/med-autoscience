from __future__ import annotations

from typing import Any


def build_workbench_status_active_path_gates(
    *,
    delete_or_tombstone_after: tuple[str, ...],
    must_not_emit: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    sidecar_focused_test_refs = [
        "tests/test_cli_cases/owner_route_handoff_command.py",
        "tests/test_cli_cases/owner_route_handoff_command_cases/export_cases.py",
        "tests/test_cli_cases/owner_route_handoff_command_cases/dispatch_cases.py",
    ]
    common = {
        "current_disposition": "domain_projection_refs_only_no_runtime_control_alias",
        "stale_surface_scan_clean": False,
        "no_resurrection_guard": True,
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(delete_or_tombstone_after),
        "no_resurrection_alias_or_wrapper_allowed": False,
        "must_not_emit": list(must_not_emit),
    }
    return (
        {
            **common,
            "residue_id": "workbench_shell_domain_projection_refs",
            "residue_class": "workbench_status",
            "current_paths": [
                "src/med_autoscience/controllers/progress_portal.py",
                "src/med_autoscience/controllers/progress_portal_parts/",
                "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
                "src/med_autoscience/controllers/product_entry_parts/attention_projection.py",
                "src/med_autoscience/controllers/product_entry_parts/generated_status_projection.py",
            ],
            "current_role": "domain_projection_refs_for_opl_workbench",
            "current_ref_status": "domain_projection_refs_no_runtime_control_owner",
            "domain_ref_consumer_count": 3,
            "opl_replacement_parity_status": (
                "generated_workbench_default_projected_not_physical_delete_ready"
            ),
            "domain_receipt_parity_status": "pending_domain_projection_receipt_ref_parity",
            "latest_thinning_evidence": {
                "status": "product_status_workbench_projection_assembly_split",
                "prior_thinning_status": "product_workbench_legacy_human_gate_alias_removed",
                "extracted_paths": [
                    "src/med_autoscience/controllers/product_entry_parts/generated_status_projection.py",
                    "src/med_autoscience/controllers/product_entry_parts/attention_projection.py",
                ],
                "retired_combined_portal_runtime_soak_provenance": {
                    "status": "physically_retired_no_alias",
                    "scope": "retired_read_model_evidence_shell_provenance",
                    "retired_paths": [
                        "retired_combined_portal_runtime_soak_entry_removed_no_alias",
                        "retired_combined_portal_runtime_soak_parts_removed_no_alias",
                    ],
                    "legacy_surface_ref_count": 0,
                    "replacement_owner": "one-person-lab",
                    "replacement_surface": "opl_current_control_state_or_app_workbench_soak",
                    "does_not_claim_active_entry": True,
                    "does_not_touch_publication_or_package_authority": True,
                },
                "domain_projection_entry_shells": [
                    "src/med_autoscience/controllers/product_entry_parts/program_surfaces.py",
                    "src/med_autoscience/controllers/product_entry_parts/workspace_attention.py",
                    "src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py",
                ],
                "domain_projection_field": "needs_user_decision",
                "scope": "product_entry_workspace_cockpit_workbench_projection_shell",
                "does_not_claim_physical_delete": True,
                "does_not_claim_opl_default_caller": True,
                "does_not_touch_publication_or_package_authority": True,
            },
            "domain_ref_consumer_refs": [
                "physical_retirement_gate_matrix.retirement_candidates.workbench_shell",
                "functional_module_inventory.workbench_portal_generic_shell.domain_ref_consumers",
            ],
            "focused_test_refs": [
                "tests/product_entry_cases/functional_consumer_boundary.py",
                "tests/test_progress_portal.py",
                "tests/product_entry_cases/product_entry_supervision_and_boundary_cases.py",
            ],
        },
        {
            **common,
            "residue_id": "owner_route_handoff_domain_ref_entry",
            "residue_class": "sidecar",
            "current_paths": [
                "src/med_autoscience/controllers/owner_route_handoff.py",
                "src/med_autoscience/controllers/owner_route_handoff_parts/",
                "src/med_autoscience/controllers/owner_route_handoff_parts/export_projection.py",
                "src/med_autoscience/controllers/owner_route_handoff_parts/export_study_projection.py",
                "src/med_autoscience/controllers/owner_route_handoff_parts/dispatch_orchestration.py",
            ],
            "current_role": "domain_owner_route_handoff_refs",
            "current_ref_status": "domain_owner_route_handoff_refs_no_runtime_control_owner",
            "domain_ref_consumer_count": 1,
            "opl_replacement_parity_status": (
                "opl_generated_sidecar_default_projected_not_physical_delete_ready"
            ),
            "domain_receipt_parity_status": (
                "pending_real_paper_line_owner_receipt_or_stable_typed_blocker"
            ),
            "domain_ref_consumer_refs": [
                "physical_retirement_gate_matrix.retirement_candidates.owner_route_handoff",
                "sidecar_export.functional_consumer_boundary.generated_surface_handoff",
            ],
            "latest_thinning_evidence": {
                "status": "sidecar_export_projection_split_to_parts_no_runtime_control_alias",
                "domain_ref_entry_path": "src/med_autoscience/controllers/owner_route_handoff.py",
                "entry_role": "dispatch_export_for_domain_refs_only",
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
                "domain_ref_consumer_count": 1,
                "does_not_claim_physical_delete": True,
                "does_not_claim_opl_default_caller": True,
                "does_not_claim_domain_receipt_parity": True,
            },
            "focused_test_refs": sidecar_focused_test_refs,
            "deletion_readiness_worklist": {
                "surface_kind": "mas_owner_route_handoff_domain_ref_entry_deletion_readiness",
                "status": "blocked_domain_owner_route_handoff_ref_consumer_present_no_runtime_control_owner",
                "allowed_current_role": "domain_owner_route_handoff_refs",
                "can_delete": False,
                "can_archive": False,
                "can_tombstone": False,
                "domain_ref_consumer_count": 1,
                "domain_ref_consumer_provenance": "sidecar export and dispatch still expose MAS owner-route refs",
                "missing_gate_inputs": [
                    {
                        "gate": "opl_generated_sidecar_consumes_domain_refs",
                        "status": "blocked",
                        "required_evidence": "OPL generated sidecar consumes MAS owner-route refs without domain-owned runtime control",
                    },
                    {
                        "gate": "opl_replacement_parity_proven",
                        "status": "blocked",
                        "required_evidence": "OPL generated sidecar default caller consuming MAS refs",
                    },
                    {
                        "gate": "domain_receipt_parity_proven",
                        "status": "blocked",
                        "required_evidence": (
                            "real paper-line owner receipt or stable typed blocker parity"
                        ),
                    },
                    {
                        "gate": "focused_tests_green",
                        "status": "required_before_delete",
                        "required_evidence": "sidecar export and dispatch focused tests",
                    },
                    {
                        "gate": "no_forbidden_write_proof",
                        "status": "required_before_delete",
                        "required_evidence": (
                            "dispatch writes only MAS dispatch receipt refs and no truth/package body"
                        ),
                    },
                    {
                        "gate": "history_tombstone_refs_recorded",
                        "status": "required_before_delete",
                "required_evidence": "history/provenance tombstone refs for retired owner-route handoff domain-ref entry",
                    },
                ],
                "domain_ref_consumer_refs": [
                    "physical_retirement_gate_matrix.retirement_candidates.owner_route_handoff",
                    "sidecar_export.functional_consumer_boundary.generated_surface_handoff",
                ],
                "focused_test_refs": sidecar_focused_test_refs,
                "no_forbidden_write_proof_refs": [
                    (
                        "tests/test_cli_cases/owner_route_handoff_command_cases/"
                        "dispatch_cases.py::"
                        "test_sidecar_dispatch_accepts_runtime_recovery_without_writing_truth"
                    ),
                    "owner_route_handoff_response.forbidden_write_guard_proof",
                ],
                "must_not_write": [
                    ".ds/user_message_queue.json",
                    "runtime quest root",
                    "artifacts/controller_decisions/latest.json",
                    "artifacts/publication_eval/latest.json",
                    "manuscript/current_package",
                    "current_package.zip",
                ],
                "must_not_claim": [
                    "domain_ready",
                    "publication_ready",
                    "artifact_mutation_authorized",
                    "physical_delete_complete",
                ],
            },
        },
        {
            **common,
            "residue_id": "status_projection_domain_truth_refs",
            "residue_class": "status_projection",
            "current_paths": [
                "src/med_autoscience/controllers/product_entry_parts/",
                "src/med_autoscience/controllers/progress_projection.py",
                "src/med_autoscience/controllers/progress_projection_parts/",
            ],
            "current_role": "domain_truth_status_projection",
            "current_ref_status": "domain_truth_status_projection_refs_no_runtime_control_owner",
            "domain_ref_consumer_count": 2,
            "opl_replacement_parity_status": (
                "opl_generated_status_default_projected_not_physical_delete_ready"
            ),
            "domain_receipt_parity_status": "pending_progress_projection_truth_ref_parity",
            "domain_ref_consumer_refs": [
                "physical_retirement_gate_matrix.retirement_candidates.status_projection",
                "functional_module_inventory.study_truth.domain_ref_consumers",
            ],
            "focused_test_refs": [
                "tests/test_progress_projection_evidence_adoption.py",
                "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py",
                "tests/test_domain_health_diagnostic_cases/runtime_status_cases.py",
            ],
        },
    )


__all__ = ["build_workbench_status_active_path_gates"]
