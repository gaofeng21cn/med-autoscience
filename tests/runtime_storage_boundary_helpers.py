from __future__ import annotations


def assert_storage_refs_only_adapter_boundary(
    payload: dict[str, object],
    *,
    report_mode: str,
) -> None:
    boundary = payload["storage_refs_only_adapter_boundary"]
    assert isinstance(boundary, dict)
    assert {key: boundary[key] for key in (
        "surface_kind",
        "report_mode",
        "authority_boundary",
        "classification",
        "migration_class",
        "body_policy",
        "generic_cleanup_policy_owner",
    )} == {
        "surface_kind": "mas_runtime_storage_refs_only_adapter_boundary",
        "report_mode": report_mode,
        "authority_boundary": "domain_authority_refs_no_generic_cleanup_policy_owner",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "body_policy": "workspace_refs_sizes_receipts_blockers_only",
        "generic_cleanup_policy_owner": "one-person-lab",
    }
    assert boundary["can_claim_generic_cleanup_policy_owner"] is False
    assert boundary["can_claim_restore_ready"] is False
    assert boundary["can_claim_paper_closure"] is False
    assert boundary["can_write_domain_truth"] is False
    assert boundary["can_write_publication_eval"] is False
    assert boundary["can_write_controller_decision"] is False
    assert boundary["can_write_current_package"] is False
    assert {
        "storage_size_ref",
        "cleanup_receipt_ref",
        "restore_proof_ref",
    } <= set(boundary["may_emit"])
    assert {
        "generic_cleanup_policy",
        "restore_ready_verdict",
        "paper_closure_verdict",
        "publication_ready_verdict",
        "artifact_mutation_authorization",
    } <= set(boundary["must_not_emit"])
