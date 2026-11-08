"""Validate qualification authority and the exact current workspace inventory."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any
from .._record_validation import (
    RequestShapeError,
    exact_json_object,
    exact_keys,
    mapping,
    text,
)
from .values import (
    ACTION_ID,
    DOMAIN_ID,
    DOMAIN_OWNER,
    QUALIFICATION_SCOPE,
    REQUEST_KIND,
    SCHEMA_VERSION,
    _SAFE_STUDY_ID,
    _canonical_workspace_root,
    _raw_digest,
    _timestamp,
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
    encoded, byte_size, record = exact_json_object(
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
    encoded, byte_size, record = exact_json_object(
        encoded_value=payload.get("workspace_index_bytes_base64"),
        byte_size_value=payload.get("workspace_index_byte_size"),
        expected_sha256=sha256,
        supplied_record=payload.get("record"),
        field=field,
    )
    if not _supported_workspace_index_envelope(record):
        raise RequestShapeError(
            f"{field}.record workspace index envelope is unsupported"
        )
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


def _supported_workspace_index_envelope(record: Mapping[str, Any]) -> bool:
    return (
        record.get("surface_kind") == "workspace_index"
        and record.get("schema_version") == "mas.workspace_index.v1"
        and "version" not in record
    ) or (
        record.get("surface_kind") == "opl_workspace_index"
        and record.get("version") == "workspace-index.v1"
        and "schema_version" not in record
    )


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
