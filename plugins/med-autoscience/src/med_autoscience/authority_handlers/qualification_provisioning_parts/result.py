"""Finalize qualification decisions and typed blockers without performing I/O."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from .values import (
    DOMAIN_ID,
    DOMAIN_OWNER,
    RESULT_KIND,
    SCHEMA_VERSION,
    _AUTHORITY_BOUNDARY,
    _fingerprint,
)


def _typed_blocker(
    normalized: Mapping[str, Any],
    identity: Mapping[str, str],
    *,
    reason_code: str,
    resume_condition: str,
) -> dict[str, Any]:
    authority = normalized["qualification_authority"]
    blocker = {
        "surface_kind": "mas_qualification_work_item_provisioning_typed_blocker",
        "schema_version": SCHEMA_VERSION,
        "reason_code": reason_code,
        "resume_condition": resume_condition,
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "qualification_authority_ref": authority["record"]["authority_ref"],
        "qualification_authority_sha256": authority["authority_sha256"],
    }
    return _finalize(
        status="typed_blocker",
        study_identity=dict(identity),
        receipt=None,
        receipt_content=None,
        authorization=None,
        host_request=None,
        typed_blocker=blocker,
        error=None,
    )


def _invalid_host_input(detail: str) -> dict[str, Any]:
    return _finalize(
        status="invalid_host_input",
        study_identity=None,
        receipt=None,
        receipt_content=None,
        authorization=None,
        host_request=None,
        typed_blocker=None,
        error={"code": "invalid_host_input", "detail": detail},
    )


def _finalize(
    *,
    status: str,
    study_identity: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
    receipt_content: Mapping[str, Any] | None,
    authorization: Mapping[str, Any] | None,
    host_request: Mapping[str, Any] | None,
    typed_blocker: Mapping[str, Any] | None,
    error: Mapping[str, Any] | None,
) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "study_identity": (
            None if study_identity is None else dict(study_identity)
        ),
        "provisioning_receipt": None if receipt is None else dict(receipt),
        "provisioning_receipt_content_binding": (
            None if receipt_content is None else dict(receipt_content)
        ),
        "mas_qualification_work_item_cas_mutation_authorization": (
            None if authorization is None else dict(authorization)
        ),
        "opl_host_materialization_request": (
            None if host_request is None else dict(host_request)
        ),
        "typed_blocker": (
            None if typed_blocker is None else dict(typed_blocker)
        ),
        "error": None if error is None else dict(error),
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    decision_fingerprint = _fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-qualification-work-item-provisioning-decision:"
            f"{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }
