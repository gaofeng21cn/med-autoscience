from __future__ import annotations

from med_autoscience.research_integrity.claim_citation_support_v2 import (
    build_claim_citation_support_matrix_v2,
)
from med_autoscience.research_integrity.gate_bundle import (
    build_research_integrity_gate_input_bundle,
)
from med_autoscience.research_integrity.manuscript_consistency import (
    build_manuscript_consistency_meta_review,
)
from med_autoscience.research_integrity.provider_lookup import (
    ProviderLookupConfig,
    build_reference_provider_lookup_bundle,
    lookup_reference_provider_evidence,
)
from med_autoscience.research_integrity.reference_verification import (
    build_reference_verification_payload,
)
from med_autoscience.research_integrity.reference_authenticity import (
    ReferenceVerificationAttestation,
    ReferenceVerificationStatus,
    build_reference_verification_attestation,
    build_reference_verification_attestation_dict,
)

__all__ = [
    "ReferenceVerificationAttestation",
    "ReferenceVerificationStatus",
    "ProviderLookupConfig",
    "build_claim_citation_support_matrix_v2",
    "build_manuscript_consistency_meta_review",
    "build_reference_provider_lookup_bundle",
    "build_reference_verification_payload",
    "build_reference_verification_attestation",
    "build_reference_verification_attestation_dict",
    "build_research_integrity_gate_input_bundle",
    "lookup_reference_provider_evidence",
]
