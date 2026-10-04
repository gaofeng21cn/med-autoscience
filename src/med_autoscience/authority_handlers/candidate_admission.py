"""Adjudicate one manifest-bound candidate before manuscript consumption."""

# Private imports below intentionally preserve the historical facade surface.
# ruff: noqa: F401

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._generation_manifest import normalize_generation_manifest, source_input_digest
from ._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
)
from ._record_validation import (
    exact_ref as _exact_ref,
)
from ._record_validation import (
    exact_ref_list as _exact_ref_list,
)
from ._record_validation import (
    typed_ref as _typed_ref,
)
from ._record_validation import (
    typed_ref_list as _typed_ref_list,
)
from .candidate_admission_parts.adjudicator import (
    _adjudicator_refs,
    _normalize_adjudicator_context,
    _normalize_adjudicator_receipt,
    _normalize_adjudicator_refs,
    _normalize_waiver,
    _validate_adjudicator_receipt,
)
from .candidate_admission_parts.candidate import (
    _candidate_exact_ref,
    _normalize_candidate,
    _normalize_claim_scope,
    _normalize_manifest_member,
    _normalize_mission,
    _validate_manifest_membership,
)
from .candidate_admission_parts.currentness import (
    _currentness_issue,
    _normalize_currentness_receipt,
    _validate_currentness_receipt_ref,
)
from .candidate_admission_parts.policy import (
    _ACCEPT_CODES,
    _ALL_DECISION_CODES,
    _AUTHORITY_BOUNDARY,
    _CLAIM_CLASSES,
    _HARD_GATE_KINDS,
    _MANUSCRIPT_SECTIONS,
    _REJECT_CODES,
    _ROUTE_CODES,
    _WAIVER_CODES,
    REQUEST_KIND,
    RESULT_KIND,
    SCHEMA_VERSION,
)
from .candidate_admission_parts.receipt import (
    normalize_candidate_admission_receipt as _normalize_candidate_admission_receipt,
)
from .candidate_admission_parts.receipt_integrity import _validate_embedded_receipt
from .candidate_admission_parts.request import _normalize_hard_gate, _normalize_request
from .candidate_admission_parts.result import (
    _clinical_identity_admission_result,
    _disposition_receipt,
    _finalize,
    _generation_context,
    _human_gate,
    _invalid_host_input,
    _route_back,
    _typed_blocker,
    _waiver_result,
    _with_decision_identity,
)


def evaluate_candidate_admission_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic result only for a current MAS adjudicator receipt."""

    try:
        normalized = _normalize_request(request)
    except RequestShapeError as error:
        return _invalid_host_input(str(error))

    currentness_issue = _currentness_issue(normalized)
    if currentness_issue is not None:
        return _finalize(
            normalized,
            status="typed_blocker",
            typed_blocker=currentness_issue,
        )

    gate = normalized["hard_gate"]
    if gate["kind"] == "human_decision":
        return _finalize(
            normalized,
            status="human_gate",
            human_gate=_human_gate(normalized),
        )
    if gate["kind"] in _HARD_GATE_KINDS:
        return _finalize(
            normalized,
            status="typed_blocker",
            typed_blocker=_typed_blocker(normalized),
        )

    identity_admission = _clinical_identity_admission_result(normalized)
    if identity_admission is not None:
        return identity_admission

    verdict = normalized["adjudicator_receipt"]["verdict"]
    if verdict == "route_back":
        return _finalize(
            normalized,
            status="route_back",
            route_back=_route_back(normalized),
        )
    if verdict == "waived":
        return _finalize(
            normalized,
            status="waived",
            waiver=_waiver_result(normalized),
        )
    return _finalize(
        normalized,
        status=verdict,
        disposition_receipt=_disposition_receipt(normalized),
    )


def normalize_candidate_admission_receipt(
    value: Any,
    field: str = "candidate_admission_receipt",
) -> dict[str, Any]:
    """Validate an exact accepted/rejected receipt for downstream consumption."""

    return _normalize_candidate_admission_receipt(value, field)


__all__ = [
    "evaluate_candidate_admission_authority",
    "normalize_candidate_admission_receipt",
]
