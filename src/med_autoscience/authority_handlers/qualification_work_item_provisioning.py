"""Authorize one qualification-only MAS work item without performing I/O."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
import posixpath
import re
from typing import Any

from ._record_validation import RequestShapeError, exact_keys, mapping, text


REQUEST_KIND = "mas_qualification_work_item_provisioning_authority_request"
RESULT_KIND = "mas_qualification_work_item_provisioning_authority_result"
RECEIPT_KIND = "mas_qualification_work_item_provisioning_receipt"
RECEIPT_CONTENT_KIND = (
    "mas_qualification_work_item_provisioning_receipt_content_binding"
)
SCHEMA_VERSION = 1
ACTION_ID = "qualification_work_item_provisioning_authority_evaluate"
DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "MedAutoScience"
QUALIFICATION_SCOPE = "standard_agent_full_vm_qualification"
HOST_CAPABILITY_ID = "opl_domain_artifact_cas_materialization.v1"

_SAFE_STUDY_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_AUTHORITY_BOUNDARY = {
    "owner": DOMAIN_OWNER,
    "handler_role": "authorize_one_qualification_only_work_item_and_exact_cas_bytes",
    "opl_role": "journal_and_materialize_exact_authorized_bytes_all_or_rollback",
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "owns_runtime_or_attempt_lifecycle": False,
    "persists_artifact_or_receipt": False,
    "selects_scientific_stage": False,
    "authorizes_stage_body": False,
    "authorizes_business_action": False,
    "authorizes_publication": False,
    "authorizes_submission": False,
    "provider_completion_is_domain_completion": False,
    "public_action": False,
}


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


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = mapping(request, "request")
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "authority_context",
            "qualification_authority",
            "current_workspace_index",
        },
        "request",
    )
    if payload.get("surface_kind") != REQUEST_KIND:
        raise RequestShapeError(f"surface_kind must be {REQUEST_KIND}")
    if payload.get("schema_version") != SCHEMA_VERSION or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("schema_version must be integer 1")
    authority_context = _normalize_authority_context(payload["authority_context"])
    authority = _normalize_qualification_authority(
        payload["qualification_authority"]
    )
    workspace_root = authority["record"]["canonical_workspace_root"]
    current_workspace_index = _normalize_workspace_index(
        payload["current_workspace_index"], workspace_root=workspace_root
    )
    return {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "authority_context": authority_context,
        "qualification_authority": authority,
        "current_workspace_index": current_workspace_index,
    }


def _normalize_authority_context(value: Any) -> dict[str, str]:
    field = "authority_context"
    payload = mapping(value, field)
    exact_keys(payload, {"action_id", "handler_call_ref", "owner_ledger_ref"}, field)
    if payload.get("action_id") != ACTION_ID:
        raise RequestShapeError(f"{field}.action_id must be {ACTION_ID}")
    return {
        "action_id": ACTION_ID,
        "handler_call_ref": text(
            payload.get("handler_call_ref"), f"{field}.handler_call_ref"
        ),
        "owner_ledger_ref": text(
            payload.get("owner_ledger_ref"), f"{field}.owner_ledger_ref"
        ),
    }


def _normalize_qualification_authority(value: Any) -> dict[str, Any]:
    field = "qualification_authority"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "authority_sha256",
            "authority_bytes_base64",
            "authority_byte_size",
            "record",
        },
        field,
    )
    authority_sha256 = _raw_digest(
        payload.get("authority_sha256"), f"{field}.authority_sha256"
    )
    encoded, byte_size, record = _normalize_exact_json_object(
        encoded_value=payload.get("authority_bytes_base64"),
        byte_size_value=payload.get("authority_byte_size"),
        expected_sha256=authority_sha256,
        supplied_record=payload.get("record"),
        field=field,
    )
    record_field = f"{field}.record"
    exact_keys(
        record,
        {
            "surface_kind",
            "schema_version",
            "authority_ref",
            "domain_owner",
            "domain_id",
            "canonical_workspace_root",
            "qualification_scope",
            "issued_at",
            "single_use",
            "qualification_only",
            "provisions_work_item",
            "authorizes_stage_body",
            "authorizes_business_action",
            "authorizes_publication",
            "authorizes_submission",
            "provider_completion_is_domain_completion",
        },
        record_field,
    )
    expected_constants = {
        "surface_kind": "mas_qualification_work_item_provisioning_authority",
        "schema_version": SCHEMA_VERSION,
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "qualification_scope": QUALIFICATION_SCOPE,
        "single_use": True,
        "qualification_only": True,
        "provisions_work_item": True,
        "authorizes_stage_body": False,
        "authorizes_business_action": False,
        "authorizes_publication": False,
        "authorizes_submission": False,
        "provider_completion_is_domain_completion": False,
    }
    for name, expected in expected_constants.items():
        if type(record.get(name)) is not type(expected) or record.get(name) != expected:
            raise RequestShapeError(
                f"{record_field}.{name} must be {expected!r}"
            )
    normalized_record = dict(record)
    normalized_record["authority_ref"] = text(
        record.get("authority_ref"), f"{record_field}.authority_ref"
    )
    normalized_record["canonical_workspace_root"] = _canonical_workspace_root(
        record.get("canonical_workspace_root"),
        f"{record_field}.canonical_workspace_root",
    )
    normalized_record["issued_at"] = _timestamp(
        record.get("issued_at"), f"{record_field}.issued_at"
    )
    return {
        "authority_sha256": authority_sha256,
        "authority_bytes_base64": encoded,
        "authority_byte_size": byte_size,
        "record": normalized_record,
    }


def _normalize_workspace_index(value: Any, *, workspace_root: str) -> dict[str, Any]:
    field = "current_workspace_index"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "exists",
            "workspace_index_ref",
            "workspace_index_sha256",
            "workspace_index_bytes_base64",
            "workspace_index_byte_size",
            "record",
        },
        field,
    )
    if payload.get("workspace_index_ref") != "workspace_index.json":
        raise RequestShapeError(
            f"{field}.workspace_index_ref must be workspace_index.json"
        )
    exists = payload.get("exists")
    if not isinstance(exists, bool):
        raise RequestShapeError(f"{field}.exists must be boolean")
    nullable_fields = (
        "workspace_index_sha256",
        "workspace_index_bytes_base64",
        "workspace_index_byte_size",
        "record",
    )
    if not exists:
        if any(payload.get(name) is not None for name in nullable_fields):
            raise RequestShapeError(
                f"{field} absent state must carry null exact-byte fields"
            )
        return {
            "exists": False,
            "workspace_index_ref": "workspace_index.json",
            "workspace_index_sha256": None,
            "workspace_index_bytes_base64": None,
            "workspace_index_byte_size": None,
            "record": {
                "surface_kind": "workspace_index",
                "schema_version": "mas.workspace_index.v1",
                "studies": [],
            },
        }

    sha256 = _raw_digest(
        payload.get("workspace_index_sha256"),
        f"{field}.workspace_index_sha256",
    )
    encoded, byte_size, record = _normalize_exact_json_object(
        encoded_value=payload.get("workspace_index_bytes_base64"),
        byte_size_value=payload.get("workspace_index_byte_size"),
        expected_sha256=sha256,
        supplied_record=payload.get("record"),
        field=field,
    )
    if record.get("surface_kind") != "workspace_index":
        raise RequestShapeError(f"{field}.record.surface_kind is unsupported")
    if record.get("schema_version") != "mas.workspace_index.v1":
        raise RequestShapeError(f"{field}.record.schema_version is unsupported")
    if "studies" not in record:
        raise RequestShapeError(f"{field}.record missing fields: studies")
    if "canonical_workspace_root" in record:
        indexed_root = _canonical_workspace_root(
            record["canonical_workspace_root"],
            f"{field}.record.canonical_workspace_root",
        )
        if indexed_root != workspace_root:
            raise RequestShapeError(
                f"{field}.record canonical_workspace_root does not match authority"
            )
    studies = _normalize_existing_studies(record.get("studies"), field)
    normalized_record = deepcopy(record)
    normalized_record["studies"] = studies
    return {
        "exists": True,
        "workspace_index_ref": "workspace_index.json",
        "workspace_index_sha256": sha256,
        "workspace_index_bytes_base64": encoded,
        "workspace_index_byte_size": byte_size,
        "record": normalized_record,
    }


def _normalize_existing_studies(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RequestShapeError(f"{field}.record.studies must be an array")
    studies: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_roots: set[str] = set()
    for index, raw_item in enumerate(value):
        item_field = f"{field}.record.studies[{index}]"
        item = mapping(raw_item, item_field)
        if "study_id" not in item or "canonical_study_root" not in item:
            raise RequestShapeError(
                f"{item_field} requires study_id and canonical_study_root"
            )
        study_id = text(item["study_id"], f"{item_field}.study_id")
        if not _SAFE_STUDY_ID.fullmatch(study_id) or len(study_id) > 128:
            raise RequestShapeError(f"{item_field}.study_id is not canonical")
        study_root = text(
            item["canonical_study_root"], f"{item_field}.canonical_study_root"
        )
        if study_root != f"studies/{study_id}":
            raise RequestShapeError(
                f"{item_field}.canonical_study_root must match study_id"
            )
        if study_id in seen_ids or study_root in seen_roots:
            raise RequestShapeError(
                f"{field}.record.studies contains duplicate identity"
            )
        seen_ids.add(study_id)
        seen_roots.add(study_root)
        normalized_item = deepcopy(item)
        normalized_item["study_id"] = study_id
        normalized_item["canonical_study_root"] = study_root
        studies.append(normalized_item)
    return studies


def _study_identity(
    workspace_root: str, study_id: str, canonical_study_root: str
) -> dict[str, str]:
    return {
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "canonical_workspace_root": workspace_root,
        "study_id": study_id,
        "canonical_study_root": canonical_study_root,
        "lifecycle_relative_path": f"{canonical_study_root}/control/lifecycle.json",
        "receipt_relative_path": (
            f"{canonical_study_root}/artifacts/controller/qualification/"
            "provisioning-receipt.json"
        ),
    }


def _workspace_index_row(identity: Mapping[str, str]) -> dict[str, Any]:
    return {
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "display_name": "Qualification work item",
        "status": "qualification_only",
        "current_stage_id": None,
        "current_stage_status": None,
        "package_status": "not_started",
        "lifecycle_ref": "control/lifecycle.json",
        "qualification_only": True,
        "stage_body_authorized": False,
        "business_action_authorized": False,
        "publication_authorized": False,
        "submission_authorized": False,
    }


def _lifecycle_record(
    normalized: Mapping[str, Any], identity: Mapping[str, str]
) -> dict[str, Any]:
    authority = normalized["qualification_authority"]
    record = authority["record"]
    return {
        "surface_kind": "study_lifecycle_control",
        "schema_version": "mas.study_lifecycle_control.v1",
        "study_id": identity["study_id"],
        "lifecycle_ref": "control/lifecycle.json",
        "lifecycle_state": "active",
        "generation": 1,
        "business_status": "qualification_only",
        "current_stage_id": None,
        "current_stage_status": None,
        "current_stage_policy": "qualification_only_no_stage_body",
        "package_status": "not_started",
        "submission_ready": False,
        "milestone_package_delivered": False,
        "reason_code": "qualification_work_item_provisioned",
        "reason_summary": "Qualification-only work item; no research Stage body is authorized.",
        "source_kind": "qualification_authority",
        "source_ref": record["authority_ref"],
        "evidence_refs": [record["authority_ref"]],
        "next_action": {"kind": "none", "reason": "qualification_only"},
        "resume_policy": {"allowed": False, "reason": "single_use_qualification_only"},
        "recorded_at": record["issued_at"],
        "materialized_at": record["issued_at"],
        "qualification_scope": QUALIFICATION_SCOPE,
        "qualification_authority_sha256": authority["authority_sha256"],
        "single_use": True,
        "qualification_only": True,
        "stage_body_authorized": False,
        "business_action_authorized": False,
        "publication_authorized": False,
        "submission_authorized": False,
        "authority_boundary": {
            "truth_owner": DOMAIN_OWNER,
            "domain_truth": True,
            "qualification_only": True,
            "stage_body_authorized": False,
            "business_action_authorized": False,
            "publication_authorized": False,
            "submission_authorized": False,
        },
    }


def _provisioning_receipt(
    normalized: Mapping[str, Any],
    identity: Mapping[str, str],
    *,
    workspace_index_after_sha256: str,
    lifecycle_sha256: str,
) -> dict[str, Any]:
    authority = normalized["qualification_authority"]
    authority_record = authority["record"]
    current_index = normalized["current_workspace_index"]
    context = normalized["authority_context"]
    core = {
        "surface_kind": RECEIPT_KIND,
        "schema_version": SCHEMA_VERSION,
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "canonical_workspace_root": identity["canonical_workspace_root"],
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "lifecycle_state": "active",
        "lifecycle_generation": 1,
        "qualification_scope": QUALIFICATION_SCOPE,
        "qualification_authority_ref": authority_record["authority_ref"],
        "qualification_authority_sha256": authority["authority_sha256"],
        "qualification_authority_byte_size": authority["authority_byte_size"],
        "handler_call_ref": context["handler_call_ref"],
        "owner_ledger_ref": context["owner_ledger_ref"],
        "workspace_index_ref": "workspace_index.json",
        "workspace_index_before_sha256": current_index[
            "workspace_index_sha256"
        ],
        "workspace_index_after_sha256": workspace_index_after_sha256,
        "lifecycle_relative_path": identity["lifecycle_relative_path"],
        "lifecycle_sha256": lifecycle_sha256,
        "receipt_relative_path": identity["receipt_relative_path"],
        "issued_at": authority_record["issued_at"],
        "single_use": True,
        "qualification_only": True,
        "stage_body_authorized": False,
        "business_action_authorized": False,
        "publication_authorized": False,
        "submission_authorized": False,
        "requires_opl_cas_materialization_receipt": True,
        "materialization_semantics": "journaled_all_or_rollback",
        "provider_completion_is_domain_completion": False,
    }
    receipt_fingerprint = _fingerprint(core)
    return {
        **core,
        "receipt_ref": (
            "mas-qualification-work-item-provisioning:"
            f"{receipt_fingerprint.removeprefix('sha256:')}"
        ),
        "receipt_fingerprint": receipt_fingerprint,
    }


def _materialization_operations(
    normalized: Mapping[str, Any],
    identity: Mapping[str, str],
    *,
    workspace_index_bytes: bytes,
    lifecycle_bytes: bytes,
    receipt_bytes: bytes,
) -> list[dict[str, Any]]:
    current_index = normalized["current_workspace_index"]
    if current_index["exists"]:
        index_precondition = {
            "kind": "existing_exact",
            "sha256": current_index["workspace_index_sha256"],
            "byte_size": current_index["workspace_index_byte_size"],
        }
    else:
        index_precondition = {"kind": "absent"}
    return [
        _operation(
            "workspace_index.json",
            workspace_index_bytes,
            precondition=index_precondition,
        ),
        _operation(
            identity["lifecycle_relative_path"],
            lifecycle_bytes,
            precondition={"kind": "absent"},
        ),
        _operation(
            identity["receipt_relative_path"],
            receipt_bytes,
            precondition={"kind": "absent"},
        ),
    ]


def _operation(
    relative_path: str,
    replacement_bytes: bytes,
    *,
    precondition: Mapping[str, Any],
) -> dict[str, Any]:
    _workspace_relative_path(relative_path, "target_relative_path")
    return {
        "target_relative_path": relative_path,
        "precondition": dict(precondition),
        "replacement_bytes_base64": base64.b64encode(replacement_bytes).decode(
            "ascii"
        ),
        "replacement_sha256": _bytes_sha256(replacement_bytes),
        "replacement_byte_size": len(replacement_bytes),
    }


def _cas_authorization(
    normalized: Mapping[str, Any],
    identity: Mapping[str, str],
    *,
    request_id: str,
    operations_sha256: str,
    materialization_scope_sha256: str,
    absent_paths: list[str],
    receipt: Mapping[str, Any],
    receipt_content: Mapping[str, Any],
) -> dict[str, Any]:
    authority = normalized["qualification_authority"]
    core = {
        "surface_kind": "mas_qualification_work_item_cas_mutation_authorization",
        "version": "mas-qualification-work-item-cas-mutation-authorization.v1",
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "qualification_authority_ref": authority["record"]["authority_ref"],
        "qualification_authority_sha256": authority["authority_sha256"],
        "authority_receipt_ref": receipt["receipt_ref"],
        "authority_receipt_content_sha256": receipt_content["sha256"],
        "operations_sha256": operations_sha256,
        "materialization_scope_sha256": materialization_scope_sha256,
        "absent_relative_path_preconditions": absent_paths,
        "authorized": True,
        "single_use": True,
        "qualification_only": True,
        "stage_body_authorized": False,
        "business_action_authorized": False,
        "publication_authorized": False,
        "submission_authorized": False,
    }
    fingerprint = _fingerprint(core)
    return {
        **core,
        "authorization_ref": (
            "mas-qualification-work-item-cas-authorization:"
            f"{fingerprint.removeprefix('sha256:')}"
        ),
        "authorization_fingerprint": fingerprint,
    }


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


def _normalize_exact_json_object(
    *,
    encoded_value: Any,
    byte_size_value: Any,
    expected_sha256: str,
    supplied_record: Any,
    field: str,
) -> tuple[str, int, dict[str, Any]]:
    if not isinstance(encoded_value, str) or not encoded_value:
        raise RequestShapeError(f"{field} bytes_base64 must be a non-empty string")
    try:
        raw_bytes = base64.b64decode(encoded_value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise RequestShapeError(f"{field} bytes_base64 is malformed") from error
    if base64.b64encode(raw_bytes).decode("ascii") != encoded_value:
        raise RequestShapeError(f"{field} bytes_base64 must be canonical base64")
    if not isinstance(byte_size_value, int) or isinstance(byte_size_value, bool):
        raise RequestShapeError(f"{field} byte_size must be an integer")
    if byte_size_value < 1 or len(raw_bytes) != byte_size_value:
        raise RequestShapeError(f"{field} byte_size does not match exact bytes")
    if hashlib.sha256(raw_bytes).hexdigest() != expected_sha256:
        raise RequestShapeError(f"{field} sha256 does not match exact bytes")
    try:
        parsed = json.loads(
            raw_bytes.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RequestShapeError(f"{field} exact bytes must be one UTF-8 JSON object") from error
    record = mapping(parsed, f"{field}.exact_bytes")
    _reject_non_finite(record, field)
    supplied = mapping(supplied_record, f"{field}.record")
    if not _json_deep_equal(record, supplied):
        raise RequestShapeError(f"{field}.record must deep-equal exact JSON bytes")
    return encoded_value, byte_size_value, record


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RequestShapeError(f"exact JSON contains duplicate key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value: Any, field: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise RequestShapeError(f"{field} contains a non-finite JSON number")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_non_finite(item, field)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for item in value:
            _reject_non_finite(item, field)


def _json_deep_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_deep_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_deep_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _raw_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise RequestShapeError(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _canonical_workspace_root(value: Any, field: str) -> str:
    root = text(value, field)
    if (
        not root.startswith("/")
        or root == "/"
        or "\\" in root
        or "//" in root
        or posixpath.normpath(root) != root
    ):
        raise RequestShapeError(f"{field} must be a canonical absolute POSIX path")
    return root


def _workspace_relative_path(value: Any, field: str) -> str:
    path = text(value, field)
    if (
        path.startswith("/")
        or "\\" in path
        or "//" in path
        or posixpath.normpath(path) != path
        or path in {".", ".."}
        or path.startswith("../")
    ):
        raise RequestShapeError(f"{field} must stay within the workspace")
    return path


def _timestamp(value: Any, field: str) -> str:
    raw = text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise RequestShapeError(f"{field} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise RequestShapeError(f"{field} must include a timezone")
    return raw


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RequestShapeError(
            "authority JSON contains an unsupported or non-finite value"
        ) from error


def _bytes_sha256(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _fingerprint(value: Any) -> str:
    return _bytes_sha256(_canonical_json_bytes(value))


__all__ = ["evaluate_qualification_work_item_provisioning_authority"]
