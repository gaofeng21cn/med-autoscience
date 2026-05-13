from __future__ import annotations

from typing import Any


LEGACY_RESIDUE_SURFACE_KIND = "mas_legacy_residue_audit"


def build_legacy_residue_audit() -> dict[str, Any]:
    findings = [
        _finding(
            residue_id="hermes_agent_executor_adapter",
            current_role="explicit_optional_executor_adapter",
            default_caller=False,
            replacement_proof_refs=[
                "product_entry_manifest/opl_provider_ready_contract",
                "product_entry_manifest/provider_residency_read_model",
            ],
            retention_reason="kept for explicit provider/executor proof lane and diagnostics",
            disposition="retain_reference",
        ),
        _finding(
            residue_id="hermes_gateway_cron_scheduler",
            current_role="explicit_optional_scheduler_adapter",
            default_caller=False,
            replacement_proof_refs=[
                "runtime-supervision-status manager=local",
                "MAS supervision scheduler contract local adapter",
            ],
            retention_reason="kept for migration/parity diagnostics until optional jobs are removed with receipts",
            disposition="retire_after_parity",
        ),
        _finding(
            residue_id="med_deepscientist_backend_reference",
            current_role="historical_fixture_provenance_parity_oracle",
            default_caller=False,
            replacement_proof_refs=[
                "docs/references/med-deepscientist/source_provenance.json",
                "MAS monolith closeout guard",
            ],
            retention_reason="kept only as source archive, backend audit, fixture, and parity reference",
            disposition="retain_reference",
        ),
        _finding(
            residue_id="workspace_local_scheduler_wording",
            current_role="mas_local_diagnostics",
            default_caller=False,
            replacement_proof_refs=[
                "OPL Temporal production provider residency blocker/readiness surface",
                "MAS sidecar export/dispatch bridge",
            ],
            retention_reason="kept as local diagnostics while OPL production residency remains pending",
            disposition="retain_diagnostics",
        ),
        _finding(
            residue_id="hosted_runtime_binding_wording",
            current_role="tombstoned_history_or_provider_readiness_context",
            default_caller=False,
            replacement_proof_refs=[
                "provider_runtime_residency_read_model",
                "provider_guarded_soak_read_model",
                "contracts/runtime/legacy-active-path-tombstones.json",
            ],
            retention_reason="tombstone landed; active docs must use explicit provider-readiness context",
            disposition="tombstoned",
        ),
    ]
    return {
        "surface_kind": LEGACY_RESIDUE_SURFACE_KIND,
        "version": "mas-legacy-residue-audit.v1",
        "status": "default_callers_retired_with_references_retained",
        "scan_policy": {
            "docs_are_not_machine_truth": True,
            "stale_term_scan_is_review_input_only": True,
            "delete_only_when_replacement_proof_and_no_default_caller": True,
        },
        "replacement_surfaces": [
            "opl_provider_ready_contract",
            "provider_runtime_residency_read_model",
            "provider_guarded_soak_read_model",
            "standard_domain_agent_skeleton",
            "runtime-supervision-status manager=local",
        ],
        "findings": findings,
        "summary": {
            "finding_count": len(findings),
            "default_caller_count": sum(1 for item in findings if item["default_caller"]),
            "cleanup_pending_count": sum(1 for item in findings if item["disposition"] == "cleanup_pending"),
            "tombstoned_count": sum(1 for item in findings if item["disposition"] == "tombstoned"),
            "retained_reference_count": sum(1 for item in findings if item["disposition"] == "retain_reference"),
            "retained_diagnostics_count": sum(1 for item in findings if item["disposition"] == "retain_diagnostics"),
            "retire_after_parity_count": sum(1 for item in findings if item["disposition"] == "retire_after_parity"),
        },
        "authority_boundary": {
            "audit_can_delete_code": False,
            "audit_can_change_runtime_defaults": False,
            "mas_truth_owner": "med-autoscience",
            "opl_provider_owner": "one-person-lab",
        },
    }


def _finding(
    *,
    residue_id: str,
    current_role: str,
    default_caller: bool,
    replacement_proof_refs: list[str],
    retention_reason: str,
    disposition: str,
) -> dict[str, Any]:
    return {
        "residue_id": residue_id,
        "current_role": current_role,
        "default_caller": default_caller,
        "replacement_proof_refs": replacement_proof_refs,
        "retention_reason": retention_reason,
        "disposition": disposition,
        "delete_allowed": disposition == "cleanup_pending" and default_caller is False,
        "body_included": False,
    }


__all__ = ["LEGACY_RESIDUE_SURFACE_KIND", "build_legacy_residue_audit"]
