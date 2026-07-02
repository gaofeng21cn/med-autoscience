from __future__ import annotations

from med_autoscience.research_integrity.claim_citation_support_v2 import (
    build_claim_citation_support_matrix_v2,
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
    "build_claim_citation_support_matrix_v2",
    "build_reference_verification_attestation",
    "build_reference_verification_attestation_dict",
]
