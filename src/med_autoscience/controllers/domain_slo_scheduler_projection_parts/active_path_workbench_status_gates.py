from __future__ import annotations

from typing import Any


def build_workbench_status_active_path_gates(
    *,
    delete_or_tombstone_after: tuple[str, ...],
    must_not_emit: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    sidecar_focused_test_refs = [
        "tests/test_cli_cases/sidecar_family_adapter_command.py",
        "tests/test_cli_cases/sidecar_family_adapter_command_cases/export_cases.py",
        "tests/test_cli_cases/sidecar_family_adapter_command_cases/dispatch_cases.py",
    ]
    common = {
        "current_disposition": "retain_with_explicit_cleanup_gate",
        "no_active_caller_proven": False,
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(delete_or_tombstone_after),
        "no_alias_facade_compat_wrapper_allowed": True,
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
            ],
            "current_role": "domain_projection_refs_for_opl_workbench",
            "active_caller_status": "active_product_workbench_domain_projection_caller_present",
            "active_caller_count": 3,
            "opl_replacement_parity_status": (
                "generated_workbench_default_projected_not_physical_delete_ready"
            ),
            "domain_receipt_parity_status": "pending_domain_projection_receipt_ref_parity",
            "latest_thinning_evidence": {
                "status": "product_workbench_legacy_human_gate_alias_removed",
                "removed_legacy_aliases": [
                    "needs_physician_decision",
                    "legacy_needs_physician_decision_field",
                    "legacy_approval_gate_field",
                    "study_physician_decision_gate",
                    "study_needs_physician_decision",
                ],
                "retained_field": "needs_user_decision",
                "scope": "product_entry_workspace_cockpit_workbench_projection_shell",
                "does_not_claim_physical_delete": True,
            },
            "active_caller_proof_refs": [
                "physical_retirement_gate_matrix.retirement_candidates.workbench_shell",
                "functional_module_inventory.workbench_portal_generic_shell.active_callers",
            ],
            "focused_test_refs": [
                "tests/product_entry_cases/functional_consumer_boundary.py",
                "tests/test_progress_portal.py",
                "tests/product_entry_cases/product_entry_supervision_and_boundary_cases.py",
            ],
        },
        {
            **common,
            "residue_id": "sidecar_dispatch_adapter",
            "residue_class": "sidecar",
            "current_paths": [
                "src/med_autoscience/controllers/sidecar_family_adapter.py",
                "src/med_autoscience/controllers/sidecar_family_adapter_parts/",
                "src/med_autoscience/controllers/sidecar_family_adapter_parts/export_projection.py",
                "src/med_autoscience/controllers/sidecar_family_adapter_parts/export_study_projection.py",
                "src/med_autoscience/controllers/sidecar_family_adapter_parts/dispatch_orchestration.py",
            ],
            "current_role": "domain_sidecar_dispatch_adapter",
            "active_caller_status": "active_domain_sidecar_dispatch_caller_present",
            "active_caller_count": 1,
            "opl_replacement_parity_status": (
                "opl_generated_sidecar_default_projected_not_physical_delete_ready"
            ),
            "domain_receipt_parity_status": (
                "pending_real_paper_line_owner_receipt_or_stable_typed_blocker"
            ),
            "active_caller_proof_refs": [
                "physical_retirement_gate_matrix.retirement_candidates.sidecar_adapter",
                "sidecar_export.functional_consumer_boundary.generated_surface_handoff",
            ],
            "latest_thinning_evidence": {
                "status": "sidecar_export_projection_split_to_parts_facade_retained",
                "facade_path": "src/med_autoscience/controllers/sidecar_family_adapter.py",
                "facade_role": "dispatch_facade_and_public_export_only",
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
                "retained_active_caller_count": 1,
                "does_not_claim_physical_delete": True,
                "does_not_claim_opl_default_caller": True,
                "does_not_claim_domain_receipt_parity": True,
            },
            "focused_test_refs": sidecar_focused_test_refs,
            "deletion_readiness_worklist": {
                "surface_kind": "mas_sidecar_dispatch_adapter_deletion_readiness",
                "status": "blocked_active_domain_sidecar_dispatch_caller_present",
                "allowed_current_role": "domain_sidecar_dispatch_adapter",
                "can_delete": False,
                "can_archive": False,
                "can_tombstone": False,
                "active_caller_count": 1,
                "active_caller_provenance": "sidecar export and dispatch still expose MAS owner-route refs",
                "missing_gate_inputs": [
                    {
                        "gate": "active_caller_count=0",
                        "status": "blocked",
                        "required_evidence": "no active sidecar export or dispatch domain caller scan",
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
                        "required_evidence": "history/provenance tombstone refs for retired sidecar adapter",
                    },
                ],
                "active_caller_proof_refs": [
                    "physical_retirement_gate_matrix.retirement_candidates.sidecar_adapter",
                    "sidecar_export.functional_consumer_boundary.generated_surface_handoff",
                ],
                "focused_test_refs": sidecar_focused_test_refs,
                "no_forbidden_write_proof_refs": [
                    (
                        "tests/test_cli_cases/sidecar_family_adapter_command_cases/"
                        "dispatch_cases.py::"
                        "test_sidecar_dispatch_accepts_runtime_recovery_without_writing_truth"
                    ),
                    "sidecar_dispatch_response.forbidden_write_guard_proof",
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
                "src/med_autoscience/controllers/study_runtime_status.py",
                "src/med_autoscience/controllers/study_runtime_status_parts/",
            ],
            "current_role": "domain_truth_status_projection",
            "active_caller_status": "active_domain_truth_status_projection_caller_present",
            "active_caller_count": 2,
            "opl_replacement_parity_status": (
                "opl_generated_status_default_projected_not_physical_delete_ready"
            ),
            "domain_receipt_parity_status": "pending_study_runtime_status_truth_ref_parity",
            "active_caller_proof_refs": [
                "physical_retirement_gate_matrix.retirement_candidates.status_projection",
                "functional_module_inventory.study_truth.active_callers",
            ],
            "focused_test_refs": [
                "tests/test_study_runtime_status_evidence_adoption.py",
                "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py",
                "tests/test_runtime_watch_cases/runtime_status_cases.py",
            ],
        },
    )


__all__ = ["build_workbench_status_active_path_gates"]
