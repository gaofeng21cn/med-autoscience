"""Authorize one qualification-only MAS work item without performing I/O."""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import posixpath
import re
from typing import Any

from ._record_validation import (
    RequestShapeError,
    exact_json_object,
    exact_keys,
    mapping,
    text,
)


from .qualification_provisioning_parts.values import (
    REQUEST_KIND,
    RESULT_KIND,
    RECEIPT_KIND,
    RECEIPT_CONTENT_KIND,
    SCHEMA_VERSION,
    ACTION_ID,
    DOMAIN_ID,
    DOMAIN_OWNER,
    QUALIFICATION_SCOPE,
    HOST_CAPABILITY_ID,
    _SAFE_STUDY_ID,
    _SHA256,
    _AUTHORITY_BOUNDARY,
    _raw_digest,
    _canonical_workspace_root,
    _workspace_relative_path,
    _timestamp,
    _canonical_json_bytes,
    _bytes_sha256,
    _fingerprint,
)
from .qualification_provisioning_parts.request import (
    _normalize_request,
    _normalize_authority_context,
    _normalize_qualification_authority,
    _normalize_workspace_index,
    _supported_workspace_index_envelope,
    _normalize_existing_studies,
)
from .qualification_provisioning_parts.records import (
    _study_identity,
    _workspace_index_row,
    _lifecycle_record,
    _provisioning_receipt,
    _materialization_operations,
    _operation,
    _cas_authorization,
)
from .qualification_provisioning_parts.result import (
    _typed_blocker,
    _invalid_host_input,
    _finalize,
)

def evaluate_qualification_work_item_provisioning_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return deterministic exact bytes or a fail-closed result."""

    try:
        normalized = _normalize_request(request)
    except (RequestShapeError, TypeError, ValueError) as error:
        return _invalid_host_input(str(error))

    authority = normalized["qualification_authority"]
    authority_record = authority["record"]
    authority_digest = authority["authority_sha256"]
    study_id = f"qualification-{authority_digest}"
    canonical_study_root = f"studies/{study_id}"
    identity = _study_identity(
        authority_record["canonical_workspace_root"],
        study_id,
        canonical_study_root,
    )

    studies = normalized["current_workspace_index"]["record"]["studies"]
    id_collision = next(
        (item for item in studies if item["study_id"] == study_id), None
    )
    root_collision = next(
        (
            item
            for item in studies
            if item["canonical_study_root"] == canonical_study_root
        ),
        None,
    )
    if id_collision is not None or root_collision is not None:
        reason_code = (
            "qualification_authority_already_consumed"
            if id_collision is not None
            and id_collision["canonical_study_root"] == canonical_study_root
            else "derived_work_item_identity_collision"
        )
        return _typed_blocker(
            normalized,
            identity,
            reason_code=reason_code,
            resume_condition=(
                "do not reuse qualification authority bytes; obtain a fresh exact "
                "MAS qualification authority after reading the current inventory"
            ),
        )

    lifecycle = _lifecycle_record(normalized, identity)
    lifecycle_bytes = _canonical_json_bytes(lifecycle)
    lifecycle_sha256 = _bytes_sha256(lifecycle_bytes)

    workspace_index_after = deepcopy(
        normalized["current_workspace_index"]["record"]
    )
    workspace_index_after["studies"].append(_workspace_index_row(identity))
    workspace_index_bytes = _canonical_json_bytes(workspace_index_after)
    workspace_index_after_sha256 = _bytes_sha256(workspace_index_bytes)

    receipt = _provisioning_receipt(
        normalized,
        identity,
        workspace_index_after_sha256=workspace_index_after_sha256,
        lifecycle_sha256=lifecycle_sha256,
    )
    receipt_bytes = _canonical_json_bytes(receipt)
    receipt_content = {
        "surface_kind": RECEIPT_CONTENT_KIND,
        "schema_version": SCHEMA_VERSION,
        "receipt_ref": receipt["receipt_ref"],
        "target_relative_path": identity["receipt_relative_path"],
        "sha256": _bytes_sha256(receipt_bytes),
        "byte_size": len(receipt_bytes),
    }

    operations = _materialization_operations(
        normalized,
        identity,
        workspace_index_bytes=workspace_index_bytes,
        lifecycle_bytes=lifecycle_bytes,
        receipt_bytes=receipt_bytes,
    )
    absent_paths = sorted(
        operation["target_relative_path"]
        for operation in operations
        if operation["precondition"]["kind"] == "absent"
    )
    operations_sha256 = _fingerprint(operations)
    materialization_scope_sha256 = _fingerprint(
        {
            "operations": operations,
            "absent_relative_path_preconditions": absent_paths,
        }
    )
    request_id = (
        "mas-qualification-provisioning-cas-request:"
        f"{materialization_scope_sha256.removeprefix('sha256:')}"
    )
    authorization = _cas_authorization(
        normalized,
        identity,
        request_id=request_id,
        operations_sha256=operations_sha256,
        materialization_scope_sha256=materialization_scope_sha256,
        absent_paths=absent_paths,
        receipt=receipt,
        receipt_content=receipt_content,
    )
    host_request = {
        "surface_kind": "opl_domain_artifact_cas_materialization_request",
        "version": "opl-domain-artifact-cas-materialization.v1",
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_id": DOMAIN_ID,
        "authorization_ref": authorization["authorization_ref"],
        "operations_sha256": operations_sha256,
        "materialization_scope_sha256": materialization_scope_sha256,
        "absent_relative_path_preconditions": absent_paths,
        "operations": operations,
    }
    return _finalize(
        status="authorized",
        study_identity=identity,
        receipt=receipt,
        receipt_content=receipt_content,
        authorization=authorization,
        host_request=host_request,
        typed_blocker=None,
        error=None,
    )


__all__ = ["evaluate_qualification_work_item_provisioning_authority"]
