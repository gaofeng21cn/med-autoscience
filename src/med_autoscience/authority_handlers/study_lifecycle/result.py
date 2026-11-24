"""Finalize study lifecycle reactivation authority results."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .constants import (
    RESULT_KIND,
    SCHEMA_VERSION,
    _AUTHORITY_BOUNDARY,
)
from .primitives import _strict_fingerprint


def _typed_blocker(
    request: Mapping[str, Any], *, reason_code: str, resume_condition: str
) -> dict[str, Any]:
    current = request["current_lifecycle"]
    return _finalize(
        request,
        status="typed_blocker",
        typed_blocker={
            "blocker_kind": "mas_study_lifecycle_reactivation_typed_blocker",
            "gate_kind": "source_currentness",
            "reason_code": reason_code,
            "current_lifecycle_ref": current["lifecycle_ref"],
            "current_lifecycle_sha256": current["lifecycle_sha256"],
            "reviewer_revision_intake_ref": request["reviewer_revision_intake"][
                "intake_ref"
            ],
            "reviewer_revision_intake_sha256": request[
                "reviewer_revision_intake"
            ]["intake_sha256"],
            "next_owner": "MedAutoScience",
            "resume_condition": resume_condition,
            "authorizes_lifecycle_transition": False,
            "authorizes_attempt_admission": False,
            "requires_host_exact_byte_persistence": True,
        },
    )


def _invalid_host_input(detail: str) -> dict[str, Any]:
    return _finalize(
        None,
        status="invalid_host_input",
        error={
            "error_kind": "mas_study_lifecycle_reactivation_invalid_host_input",
            "code": "invalid_host_input",
            "detail": detail,
            "retryable": False,
        },
    )


def _finalize(
    request: Mapping[str, Any] | None,
    *,
    status: str,
    reactivation_receipt: Mapping[str, Any] | None = None,
    cas_authorization: Mapping[str, Any] | None = None,
    host_request: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    error: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "study_identity": (
            deepcopy(request["study_identity"]) if request is not None else None
        ),
        "reactivation_receipt": (
            deepcopy(reactivation_receipt) if reactivation_receipt is not None else None
        ),
        "mas_lifecycle_cas_mutation_authorization": (
            deepcopy(cas_authorization) if cas_authorization is not None else None
        ),
        "opl_host_materialization_request": (
            deepcopy(host_request) if host_request is not None else None
        ),
        "typed_blocker": deepcopy(typed_blocker) if typed_blocker is not None else None,
        "error": deepcopy(error) if error is not None else None,
        "authority_boundary": deepcopy(_AUTHORITY_BOUNDARY),
    }
    decision_fingerprint = _strict_fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-study-lifecycle-reactivation-decision:"
            f"{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }
