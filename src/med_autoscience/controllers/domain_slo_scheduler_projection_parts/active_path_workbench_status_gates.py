from __future__ import annotations

from typing import Any


def build_workbench_status_active_path_gates(
    *,
    delete_or_tombstone_after: tuple[str, ...],
    must_not_emit: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
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
                "src/med_autoscience/controllers/sidecar_provider.py",
            ],
            "current_role": "domain_sidecar_dispatch_adapter_and_provider_diagnostic",
            "active_caller_status": "active_domain_sidecar_dispatch_or_provider_caller_present",
            "active_caller_count": 2,
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
            "focused_test_refs": [
                "tests/test_cli_cases/sidecar_family_adapter_command.py",
                "tests/test_cli_cases/sidecar_family_adapter_command_cases/export_cases.py",
                "tests/test_sidecar_provider_adapter.py",
            ],
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
