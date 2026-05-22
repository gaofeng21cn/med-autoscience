from __future__ import annotations

from typing import Any


def authority_boundary_payload() -> dict[str, Any]:
    return {
        "family_runtime_framework_owner": "one-person-lab",
        "online_runtime_provider_owner": "opl_family_runtime_provider",
        "typed_dispatch_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "memory_body_owner": "med-autoscience",
        "evidence_ledger_owner": "med-autoscience",
        "review_ledger_owner": "med-autoscience",
        "publication_authority_owner": "med-autoscience",
        "quality_gate_owner": "med-autoscience",
        "artifact_authority_owner": "med-autoscience",
        "opl_substrate_authority": "locator_index_lifecycle_projection_only",
        "mas_domain_authority": [
            "study_truth",
            "memory_body",
            "evidence_ledger",
            "review_ledger",
            "runtime_health_truth",
            "publication_quality_verdict",
            "artifact_authority",
            "publication_authority",
            "owner_route_decision",
        ],
        "opl_receipt_policy": "transport_receipt_only_no_domain_truth_authority",
        "writes_domain_truth": False,
        "writes_artifact_gate": False,
        "writes_memory_body": False,
        "writes_evidence_ledger": False,
        "writes_review_ledger": False,
        "writes_publication_authority": False,
        "owns_generic_scheduler": False,
        "owns_generic_daemon": False,
        "owns_generic_queue": False,
        "owns_generic_attempt_ledger": False,
        "owns_generic_locator": False,
        "owns_generic_lifecycle": False,
        "owns_generic_projection": False,
        "owns_generic_runner": False,
        "owns_generic_workbench": False,
        "forbidden_authorities": [
            "study_truth_write",
            "memory_body_write",
            "evidence_ledger_write",
            "review_ledger_write",
            "publication_quality_verdict",
            "artifact_gate_override",
            "publication_authority_write",
            "current_package_write",
        ],
    }


__all__ = ["authority_boundary_payload"]
