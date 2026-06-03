from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


MAS_STAGE_AUTHORITY_TYPES = (
    "source_readiness",
    "reviewer_quality",
    "publication_gate",
    "artifact_package_authority",
    "memory_accept_reject",
    "typed_blocker",
    "medical_owner_receipt",
)

REQUIRED_SCHEMA_REFS = (
    "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
    "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
)

AUTHORITY_CAPABILITY_PREFIX = (
    "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/"
)

MAS_AUTHORITY_SEMANTIC_REF_REQUIREMENTS = {
    "source_readiness": (
        "source_boundary_refs",
        "source_readiness_receipt_refs",
    ),
    "reviewer_quality": (
        "independent_reviewer_record_refs",
        "reviewer_quality_receipt_refs",
    ),
    "publication_gate": (
        "publication_route_decision_refs",
        "publication_gate_receipt_refs",
    ),
    "artifact_package_authority": (
        "artifact_package_refs",
        "artifact_package_authority_receipt_refs",
    ),
    "memory_accept_reject": (
        "memory_route_refs",
        "memory_accept_reject_receipt_refs",
    ),
    "typed_blocker": (
        "typed_blocker_refs",
    ),
    "medical_owner_receipt": (
        "owner_route_refs",
        "medical_owner_receipt_refs",
    ),
}

FORBIDDEN_RECEIPT_BODY_FIELDS = frozenset(
    {
        "artifact_authority_verdict",
        "artifact_authority_verdict_body",
        "artifact_body",
        "body",
        "current_package",
        "current_package_body",
        "manuscript_body",
        "memory_body",
        "paper_package_body",
        "payload",
        "publication_quality_verdict",
        "publication_quality_verdict_body",
        "publication_verdict",
        "publication_verdict_body",
        "quality_verdict",
        "receipt_body",
        "source_readiness_verdict",
        "study_truth_body",
    }
)

_VALIDATION_SCOPE = [
    "receipt_ref",
    "schema_refs",
    "capability_refs",
    "domain_semantic_refs",
]

_READY_CLAIMS = {
    "publication_ready": False,
    "quality_ready": False,
    "submission_ready": False,
    "artifact_mutation_authorized": False,
    "memory_writeback_authorized": False,
}


def validate_mas_stage_semantic_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a MAS stage receipt envelope without opening or trusting body payloads."""

    payload = _mapping(receipt)
    authority_type = _text(payload.get("authority_type"))
    receipt_ref = _text(payload.get("receipt_ref"))
    schema_refs = _text_list(payload.get("schema_refs"))
    capability_refs = _text_list(payload.get("capability_refs"))
    typed_blocker_refs = _text_list(payload.get("typed_blocker_refs"))
    domain_semantic_refs = _domain_semantic_refs(payload.get("domain_semantic_refs"))
    forbidden_body_fields = sorted(_find_forbidden_body_fields(payload))

    required_schema_refs = list(REQUIRED_SCHEMA_REFS)
    required_capability_refs = _required_capability_refs(authority_type)
    required_domain_roles = list(MAS_AUTHORITY_SEMANTIC_REF_REQUIREMENTS.get(authority_type or "", ()))

    missing_schema_refs = [ref for ref in required_schema_refs if ref not in set(schema_refs)]
    missing_capability_refs = [ref for ref in required_capability_refs if ref not in set(capability_refs)]
    missing_domain_semantic_refs = [
        role for role in required_domain_roles if not domain_semantic_refs.get(role)
    ]

    status, fail_closed_reason = _validation_status(
        authority_type=authority_type,
        receipt_ref=receipt_ref,
        forbidden_body_fields=forbidden_body_fields,
        missing_schema_refs=missing_schema_refs,
        missing_capability_refs=missing_capability_refs,
        missing_domain_semantic_refs=missing_domain_semantic_refs,
        typed_blocker_refs=typed_blocker_refs,
    )
    typed_blocker = status == "typed_blocker"
    return {
        "surface_kind": "mas_stage_semantic_receipt_validation",
        "status": status,
        "fail_closed_reason": fail_closed_reason,
        "semantic_receipt_accepted": status == "accepted",
        "typed_blocker_required": status == "fail_closed",
        "typed_blocker_is_domain_outcome_not_runtime_failure": typed_blocker,
        "authority_type": authority_type,
        "stage_id": _text(payload.get("stage_id")),
        "receipt_ref": receipt_ref,
        "schema_refs": schema_refs,
        "required_schema_refs": required_schema_refs,
        "missing_schema_refs": missing_schema_refs,
        "capability_refs": capability_refs,
        "required_capability_refs": required_capability_refs,
        "missing_capability_refs": missing_capability_refs,
        "domain_semantic_refs": domain_semantic_refs,
        "required_domain_semantic_refs": required_domain_roles,
        "missing_domain_semantic_refs": missing_domain_semantic_refs,
        "typed_blocker_refs": typed_blocker_refs,
        "forbidden_body_fields": forbidden_body_fields,
        "domain_validation_owner": "MedAutoScience",
        "validation_scope": list(_VALIDATION_SCOPE),
        "ready_claims": dict(_READY_CLAIMS),
        "manifest_validity_is_semantic_receipt_validity": False,
        "receipt_body_read": False,
        "body_included": False,
    }


def _validation_status(
    *,
    authority_type: str | None,
    receipt_ref: str | None,
    forbidden_body_fields: list[str],
    missing_schema_refs: list[str],
    missing_capability_refs: list[str],
    missing_domain_semantic_refs: list[str],
    typed_blocker_refs: list[str],
) -> tuple[str, str | None]:
    if forbidden_body_fields:
        return "fail_closed", "receipt_body_present"
    if authority_type not in MAS_STAGE_AUTHORITY_TYPES:
        return "fail_closed", "unknown_authority_type"
    if not receipt_ref:
        return "fail_closed", "missing_receipt_ref"
    if missing_schema_refs or missing_capability_refs:
        return "fail_closed", "missing_schema_or_capability_refs"
    if typed_blocker_refs:
        return "typed_blocker", None
    if missing_domain_semantic_refs:
        return "fail_closed", "missing_domain_semantic_refs"
    if authority_type == "typed_blocker":
        return "typed_blocker", None
    return "accepted", None


def _required_capability_refs(authority_type: str | None) -> list[str]:
    if authority_type not in MAS_STAGE_AUTHORITY_TYPES:
        return []
    return [f"{AUTHORITY_CAPABILITY_PREFIX}{authority_type}"]


def _domain_semantic_refs(value: object) -> dict[str, list[str]]:
    payload = _mapping(value)
    return {str(key): refs for key, item in payload.items() if (refs := _text_list(item))}


def _find_forbidden_body_fields(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_RECEIPT_BODY_FIELDS:
                found.add(key_text)
            found.update(_find_forbidden_body_fields(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.update(_find_forbidden_body_fields(child))
    return found


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [text for item in value if (text := _text(item))]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


__all__ = [
    "AUTHORITY_CAPABILITY_PREFIX",
    "FORBIDDEN_RECEIPT_BODY_FIELDS",
    "MAS_AUTHORITY_SEMANTIC_REF_REQUIREMENTS",
    "MAS_STAGE_AUTHORITY_TYPES",
    "REQUIRED_SCHEMA_REFS",
    "validate_mas_stage_semantic_receipt",
]
