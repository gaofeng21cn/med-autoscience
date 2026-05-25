from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_runtime_storage_refs_only_adapter_boundary"


def storage_refs_only_adapter_boundary(*, report_mode: str) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "report_mode": report_mode,
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "authority_boundary": "domain_authority_refs_no_generic_cleanup_policy_owner",
        "current_ref_status": "refs_only_storage_audit_adapter_consumes_opl_lifecycle_policy",
        "body_policy": "workspace_refs_sizes_receipts_blockers_only",
        "may_emit": [
            "workspace_artifact_ref",
            "cleanup_receipt_ref",
            "restore_proof_ref",
            "typed_blocker",
            "storage_size_ref",
        ],
        "must_not_emit": [
            "generic_cleanup_policy",
            "restore_ready_verdict",
            "paper_closure_verdict",
            "publication_ready_verdict",
            "artifact_mutation_authorization",
        ],
        "can_claim_generic_cleanup_policy_owner": False,
        "can_claim_restore_ready": False,
        "can_claim_paper_closure": False,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "can_write_current_package": False,
        "generic_cleanup_policy_owner": "one-person-lab",
        "opl_expected_primitives": [
            "opl_artifact_lifecycle_storage_audit_shell",
            "opl_restore_retention_receipt_shell",
            "opl_runtime_lifecycle_cleanup_policy",
        ],
        "retirement_gate_status": "storage_refs_until_opl_cleanup_policy_parity",
    }


__all__ = ["storage_refs_only_adapter_boundary"]
