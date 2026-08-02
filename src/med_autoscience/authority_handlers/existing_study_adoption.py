"""Authorize adoption of one existing study without performing I/O."""

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


REQUEST_KIND = "mas_study_work_item_adoption_authority_request"
RESULT_KIND = "mas_study_work_item_adoption_authority_result"
RECEIPT_KIND = "mas_study_work_item_adoption_receipt"
RECEIPT_CONTENT_KIND = "mas_study_work_item_adoption_receipt_content_binding"
SCHEMA_VERSION = 1
ACTION_ID = "study_work_item_adoption_authority_evaluate"
DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "MedAutoScience"
HOST_CAPABILITY_ID = "opl_domain_artifact_cas_materialization.v1"
MAS_INVENTORY_PATH = "runtime/artifacts/mas_workspace_index/latest.json"
WORKSPACE_LIFECYCLE_PATH = (
    "runtime/artifacts/study_lifecycle_control/latest.json"
)

_SAFE_STUDY_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_SHA256 = re.compile(r"^sha256:[a-f0-9]{64}$")
_LIFECYCLE_STATES = {"active", "paused", "delivered_paused", "stopped"}
_AUTHORITY_BOUNDARY = {
    "owner": DOMAIN_OWNER,
    "handler_role": (
        "authorize_one_existing_study_adoption_and_exact_cas_bytes"
    ),
    "opl_role": (
        "journal_and_materialize_exact_authorized_bytes_all_or_rollback"
    ),
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


def evaluate_study_work_item_adoption_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return deterministic exact adoption bytes or a fail-closed result."""

    try:
        normalized = _normalize_request(request)
    except (RequestShapeError, TypeError, ValueError) as error:
        return _invalid_host_input(str(error))

    identity = normalized["study_identity"]
    topology_projects = normalized["current_opl_topology_inventory"]["record"][
        "projects"
    ]
    topology_matches = [
        item for item in topology_projects if item["project_id"] == identity["study_id"]
    ]
    if not topology_matches:
        return _typed_blocker(
            normalized,
            reason_code="existing_study_missing_from_opl_topology",
            resume_condition=(
                "refresh the current OPL topology inventory and provide the exact "
                "project row for the existing study before adoption"
            ),
        )
    if len(topology_matches) != 1:
        return _typed_blocker(
            normalized,
            reason_code="existing_study_topology_identity_collision",
            resume_condition=(
                "repair the OPL-owned topology so the study project_id is unique"
            ),
        )

    current_inventory = normalized["current_mas_workspace_index"]
    inventory_matches = [
        item
        for item in current_inventory["record"]["studies"]
        if item["study_id"] == identity["study_id"]
        or item["canonical_study_root"] == identity["canonical_study_root"]
    ]
    current_workspace_lifecycle = normalized[
        "current_workspace_lifecycle_latest"
    ]
    lifecycle_matches = [
        item
        for item in current_workspace_lifecycle["record"]["studies"]
        if item["study_id"] == identity["study_id"]
    ]
    if inventory_matches or lifecycle_matches:
        return _typed_blocker(
            normalized,
            reason_code="existing_study_already_adopted",
            resume_condition=(
                "use the current MAS lifecycle projection instead of replaying "
                "existing-study adoption"
            ),
        )

    lifecycle = _lifecycle_record(normalized)
    lifecycle_bytes = _canonical_json_bytes(lifecycle)
    lifecycle_sha256 = _bytes_sha256(lifecycle_bytes)

    inventory = _updated_mas_inventory(normalized, lifecycle)
    inventory_bytes = _canonical_json_bytes(inventory)
    inventory_sha256 = _bytes_sha256(inventory_bytes)

    workspace_lifecycle = _updated_workspace_lifecycle(normalized, lifecycle)
    workspace_lifecycle_bytes = _canonical_json_bytes(workspace_lifecycle)
    workspace_lifecycle_sha256 = _bytes_sha256(workspace_lifecycle_bytes)

    submission = _submission_status(normalized)
    submission_bytes = _canonical_json_bytes(submission)
    submission_sha256 = _bytes_sha256(submission_bytes)

    receipt = _adoption_receipt(
        normalized,
        inventory_sha256=inventory_sha256,
        workspace_lifecycle_sha256=workspace_lifecycle_sha256,
        lifecycle_sha256=lifecycle_sha256,
        submission_sha256=submission_sha256,
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
        lifecycle=lifecycle,
        lifecycle_bytes=lifecycle_bytes,
        inventory_bytes=inventory_bytes,
        workspace_lifecycle=workspace_lifecycle,
        workspace_lifecycle_bytes=workspace_lifecycle_bytes,
        submission_bytes=submission_bytes,
        receipt=receipt,
        receipt_bytes=receipt_bytes,
    )
    absent_paths = sorted(
        item["target_relative_path"]
        for item in operations
        if item["precondition"]["kind"] == "absent"
    )
    operations_sha256 = _fingerprint(operations)
    materialization_scope_sha256 = _fingerprint(
        {
            "operations": operations,
            "absent_relative_path_preconditions": absent_paths,
        }
    )
    request_id = (
        "mas-existing-study-adoption-cas-request:"
        f"{materialization_scope_sha256.removeprefix('sha256:')}"
    )
    authorization = _cas_authorization(
        normalized,
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
            "adoption_authority",
            "existing_study_identity",
            "current_mas_workspace_index",
            "current_workspace_lifecycle",
        },
        "request",
    )
    if payload.get("surface_kind") != REQUEST_KIND:
        raise RequestShapeError(f"surface_kind must be {REQUEST_KIND}")
    if type(payload.get("schema_version")) is not int or payload.get(
        "schema_version"
    ) != SCHEMA_VERSION:
        raise RequestShapeError("schema_version must be integer 1")

    context = _normalize_authority_context(payload["authority_context"])
    adoption_authority = mapping(
        payload["adoption_authority"], "adoption_authority"
    )
    exact_keys(
        adoption_authority,
        {"user_authority", "current_opl_topology_inventory"},
        "adoption_authority",
    )
    identity, evidence = _normalize_existing_study_identity(
        payload["existing_study_identity"]
    )
    user_authority = _normalize_user_authority(
        adoption_authority["user_authority"]
    )
    topology = _normalize_topology(
        adoption_authority["current_opl_topology_inventory"],
        workspace_root=identity["canonical_workspace_root"],
    )
    inventory = _normalize_mas_inventory(
        payload["current_mas_workspace_index"],
        workspace_root=identity["canonical_workspace_root"],
    )
    workspace_lifecycle = _normalize_workspace_lifecycle(
        payload["current_workspace_lifecycle"],
        workspace_name=topology["record"]["workspace_id"],
    )

    if user_authority["record"]["study_id"] != identity["study_id"]:
        raise RequestShapeError("user authority study_id does not match identity")
    if evidence["record"]["study_id"] != identity["study_id"]:
        raise RequestShapeError("existing study evidence study_id does not match identity")
    if evidence["record"]["canonical_study_root"] != identity[
        "canonical_study_root"
    ]:
        raise RequestShapeError(
            "existing study evidence canonical_study_root does not match identity"
        )
    if evidence["record"]["display_name"] != identity["display_name"]:
        raise RequestShapeError(
            "existing study evidence display_name does not match identity"
        )
    return {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "authority_context": context,
        "study_identity": identity,
        "user_authority": user_authority,
        "existing_study_evidence": evidence,
        "current_opl_topology_inventory": topology,
        "current_mas_workspace_index": inventory,
        "current_workspace_lifecycle_latest": workspace_lifecycle,
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


def _normalize_existing_study_identity(
    value: Any,
) -> tuple[dict[str, str], dict[str, Any]]:
    field = "existing_study_identity"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "study_id",
            "canonical_workspace_root",
            "canonical_study_root",
            "display_name",
            "evidence_ref",
            "evidence_sha256",
            "evidence_bytes_base64",
            "evidence_byte_size",
            "record",
        },
        field,
    )
    study_id = _study_id(payload.get("study_id"), f"{field}.study_id")
    workspace_root = _canonical_workspace_root(
        payload.get("canonical_workspace_root"),
        f"{field}.canonical_workspace_root",
    )
    study_root = text(
        payload.get("canonical_study_root"), f"{field}.canonical_study_root"
    )
    if study_root != f"studies/{study_id}":
        raise RequestShapeError(
            f"{field}.canonical_study_root must be studies/<study_id>"
        )
    identity = {
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "study_id": study_id,
        "canonical_workspace_root": workspace_root,
        "canonical_study_root": study_root,
        "display_name": text(payload.get("display_name"), f"{field}.display_name"),
        "lifecycle_relative_path": f"{study_root}/control/lifecycle.json",
        "submission_status_relative_path": f"{study_root}/submission/STATUS.json",
        "receipt_relative_path": (
            f"{study_root}/artifacts/controller/adoption/"
            "provisioning-receipt.json"
        ),
    }
    evidence = _normalize_existing_study_evidence(
        {
            "evidence_ref": payload["evidence_ref"],
            "evidence_sha256": payload["evidence_sha256"],
            "evidence_bytes_base64": payload["evidence_bytes_base64"],
            "evidence_byte_size": payload["evidence_byte_size"],
            "record": payload["record"],
        }
    )
    return identity, evidence


def _normalize_user_authority(value: Any) -> dict[str, Any]:
    field = "user_authority"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "authority_ref",
            "authority_sha256",
            "authority_bytes_base64",
            "authority_byte_size",
            "record",
        },
        field,
    )
    sha256 = _digest_text(payload.get("authority_sha256"), f"{field}.authority_sha256")
    encoded, byte_size, record = _normalize_exact_json_object(
        encoded_value=payload.get("authority_bytes_base64"),
        byte_size_value=payload.get("authority_byte_size"),
        expected_sha256=sha256,
        supplied_record=payload.get("record"),
        field=field,
    )
    record_field = f"{field}.record"
    exact_keys(
        record,
        {
            "surface_kind",
            "schema_version",
            "study_id",
            "task_intake_kind",
            "status",
            "explicit_user_wakeup",
            "allow_stopped_relaunch",
            "recorded_at",
            "source_kind",
            "source_ref",
            "instruction_text",
            "instruction_sha256",
            "source_owner",
            "record_owner",
            "owner_receipt",
        },
        record_field,
    )
    constants = {
        "surface_kind": "mas_explicit_user_authority_evidence",
        "schema_version": 1,
        "task_intake_kind": "reviewer_revision",
        "status": "accepted",
        "explicit_user_wakeup": True,
        "source_kind": "explicit_user_instruction",
        "source_owner": "user",
        "record_owner": DOMAIN_OWNER,
        "owner_receipt": False,
    }
    for name, expected in constants.items():
        if type(record.get(name)) is not type(expected) or record.get(name) != expected:
            raise RequestShapeError(
                f"{record_field}.{name} must be {expected!r}"
            )
    if not isinstance(record.get("allow_stopped_relaunch"), bool):
        raise RequestShapeError(
            f"{record_field}.allow_stopped_relaunch must be boolean"
        )
    instruction = text(
        record.get("instruction_text"), f"{record_field}.instruction_text"
    )
    instruction_sha256 = _digest_text(
        record.get("instruction_sha256"),
        f"{record_field}.instruction_sha256",
    )
    if _bytes_sha256(instruction.encode("utf-8")) != instruction_sha256:
        raise RequestShapeError(
            f"{record_field}.instruction_sha256 does not match instruction_text"
        )
    normalized_record = deepcopy(record)
    normalized_record["study_id"] = _study_id(
        record.get("study_id"), f"{record_field}.study_id"
    )
    normalized_record["recorded_at"] = _timestamp(
        record.get("recorded_at"), f"{record_field}.recorded_at"
    )
    normalized_record["source_ref"] = text(
        record.get("source_ref"), f"{record_field}.source_ref"
    )
    normalized_record["instruction_text"] = instruction
    normalized_record["instruction_sha256"] = instruction_sha256
    return {
        "authority_ref": text(
            payload.get("authority_ref"), f"{field}.authority_ref"
        ),
        "authority_sha256": sha256,
        "authority_bytes_base64": encoded,
        "authority_byte_size": byte_size,
        "record": normalized_record,
    }


def _normalize_existing_study_evidence(value: Any) -> dict[str, Any]:
    field = "existing_study_evidence"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "evidence_ref",
            "evidence_sha256",
            "evidence_bytes_base64",
            "evidence_byte_size",
            "record",
        },
        field,
    )
    sha256 = _digest_text(payload.get("evidence_sha256"), f"{field}.evidence_sha256")
    encoded, byte_size, record = _normalize_exact_json_object(
        encoded_value=payload.get("evidence_bytes_base64"),
        byte_size_value=payload.get("evidence_byte_size"),
        expected_sha256=sha256,
        supplied_record=payload.get("record"),
        field=field,
    )
    record_field = f"{field}.record"
    exact_keys(
        record,
        {
            "surface_kind",
            "schema_version",
            "study_id",
            "canonical_study_root",
            "display_name",
            "evidence_kind",
            "observed_at",
            "evidence_refs",
            "qualification_only",
            "authorizes_stage_body",
            "authorizes_publication",
            "authorizes_submission",
        },
        record_field,
    )
    constants = {
        "surface_kind": "mas_existing_study_adoption_evidence",
        "schema_version": 1,
        "evidence_kind": "persisted_existing_study",
        "qualification_only": False,
        "authorizes_stage_body": False,
        "authorizes_publication": False,
        "authorizes_submission": False,
    }
    for name, expected in constants.items():
        if type(record.get(name)) is not type(expected) or record.get(name) != expected:
            raise RequestShapeError(
                f"{record_field}.{name} must be {expected!r}"
            )
    refs = _normalize_evidence_refs(record.get("evidence_refs"), record_field)
    normalized_record = deepcopy(record)
    normalized_record["study_id"] = _study_id(
        record.get("study_id"), f"{record_field}.study_id"
    )
    normalized_record["canonical_study_root"] = _workspace_relative_path(
        record.get("canonical_study_root"),
        f"{record_field}.canonical_study_root",
    )
    normalized_record["display_name"] = text(
        record.get("display_name"), f"{record_field}.display_name"
    )
    normalized_record["observed_at"] = _timestamp(
        record.get("observed_at"), f"{record_field}.observed_at"
    )
    normalized_record["evidence_refs"] = refs
    return {
        "evidence_ref": text(
            payload.get("evidence_ref"), f"{field}.evidence_ref"
        ),
        "evidence_sha256": sha256,
        "evidence_bytes_base64": encoded,
        "evidence_byte_size": byte_size,
        "record": normalized_record,
    }


def _normalize_evidence_refs(value: Any, field: str) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RequestShapeError(f"{field}.evidence_refs must be an array")
    if not value:
        raise RequestShapeError(f"{field}.evidence_refs must not be empty")
    refs: list[dict[str, str]] = []
    for index, item_value in enumerate(value):
        item_field = f"{field}.evidence_refs[{index}]"
        item = mapping(item_value, item_field)
        exact_keys(item, {"kind", "ref", "sha256"}, item_field)
        refs.append(
            {
                "kind": text(item.get("kind"), f"{item_field}.kind"),
                "ref": text(item.get("ref"), f"{item_field}.ref"),
                "sha256": _digest_text(
                    item.get("sha256"), f"{item_field}.sha256"
                ),
            }
        )
    return refs


def _normalize_topology(value: Any, *, workspace_root: str) -> dict[str, Any]:
    field = "current_opl_topology_inventory"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "topology_ref",
            "topology_sha256",
            "topology_bytes_base64",
            "topology_byte_size",
            "record",
        },
        field,
    )
    sha256 = _digest_text(payload.get("topology_sha256"), f"{field}.topology_sha256")
    encoded, byte_size, record = _normalize_exact_json_object(
        encoded_value=payload.get("topology_bytes_base64"),
        byte_size_value=payload.get("topology_byte_size"),
        expected_sha256=sha256,
        supplied_record=payload.get("record"),
        field=field,
    )
    if record.get("surface_kind") != "opl_workspace_index":
        raise RequestShapeError(f"{field}.record.surface_kind is unsupported")
    if record.get("version") != "workspace-index.v1":
        raise RequestShapeError(f"{field}.record.version is unsupported")
    if _canonical_workspace_root(
        record.get("workspace_path"), f"{field}.record.workspace_path"
    ) != workspace_root:
        raise RequestShapeError(
            f"{field}.record.workspace_path does not match study identity"
        )
    workspace_id = text(
        record.get("workspace_id"), f"{field}.record.workspace_id"
    )
    agent = mapping(record.get("agent"), f"{field}.record.agent")
    if agent.get("agent_id") != "mas":
        raise RequestShapeError(f"{field}.record.agent.agent_id must be mas")
    projects_value = record.get("projects")
    if not isinstance(projects_value, Sequence) or isinstance(
        projects_value, (str, bytes, bytearray)
    ):
        raise RequestShapeError(f"{field}.record.projects must be an array")
    projects: list[dict[str, Any]] = []
    for index, item_value in enumerate(projects_value):
        item_field = f"{field}.record.projects[{index}]"
        item = mapping(item_value, item_field)
        project_id = _study_id(item.get("project_id"), f"{item_field}.project_id")
        project_root = _workspace_relative_path(
            item.get("project_root"), f"{item_field}.project_root"
        )
        normalized_item = deepcopy(item)
        normalized_item["project_id"] = project_id
        normalized_item["project_root"] = project_root
        projects.append(normalized_item)
    normalized_record = deepcopy(record)
    normalized_record["workspace_id"] = workspace_id
    normalized_record["workspace_path"] = workspace_root
    normalized_record["projects"] = projects
    return {
        "topology_ref": text(
            payload.get("topology_ref"), f"{field}.topology_ref"
        ),
        "topology_sha256": sha256,
        "topology_bytes_base64": encoded,
        "topology_byte_size": byte_size,
        "record": normalized_record,
    }


def _normalize_mas_inventory(value: Any, *, workspace_root: str) -> dict[str, Any]:
    field = "current_mas_workspace_index"
    normalized = _normalize_optional_exact_projection(
        value,
        field=field,
        ref_field="mas_workspace_index_ref",
        expected_ref=MAS_INVENTORY_PATH,
        value_prefix="mas_workspace_index",
        absent_record={
            "surface_kind": "mas_workspace_index",
            "schema_version": "mas.workspace_index.v1",
            "canonical_workspace_root": workspace_root,
            "recorded_at": None,
            "status_counts": {},
            "studies": [],
        },
    )
    record = normalized["record"]
    if record.get("surface_kind") != "mas_workspace_index":
        raise RequestShapeError(f"{field}.record.surface_kind is unsupported")
    if record.get("schema_version") != "mas.workspace_index.v1":
        raise RequestShapeError(f"{field}.record.schema_version is unsupported")
    indexed_root = record.get("canonical_workspace_root")
    if indexed_root is not None and _canonical_workspace_root(
        indexed_root, f"{field}.record.canonical_workspace_root"
    ) != workspace_root:
        raise RequestShapeError(
            f"{field}.record canonical_workspace_root does not match identity"
        )
    studies = _normalize_inventory_rows(record.get("studies"), field)
    _validate_status_counts(record.get("status_counts"), studies, field)
    if normalized["exists"]:
        _timestamp(record.get("recorded_at"), f"{field}.record.recorded_at")
    normalized["record"] = deepcopy(record)
    normalized["record"]["canonical_workspace_root"] = workspace_root
    normalized["record"]["studies"] = studies
    return normalized


def _normalize_workspace_lifecycle(
    value: Any, *, workspace_name: str
) -> dict[str, Any]:
    field = "current_workspace_lifecycle_latest"
    normalized = _normalize_optional_exact_projection(
        value,
        field=field,
        ref_field="workspace_lifecycle_ref",
        expected_ref=WORKSPACE_LIFECYCLE_PATH,
        value_prefix="workspace_lifecycle",
        absent_record={
            "surface_kind": "workspace_study_lifecycle_control",
            "schema_version": "mas.workspace_study_lifecycle_control.v1",
            "workspace_name": workspace_name,
            "recorded_at": None,
            "status_counts": {},
            "changed_study_id": None,
            "changed_generation": None,
            "studies": [],
        },
    )
    record = normalized["record"]
    if record.get("surface_kind") != "workspace_study_lifecycle_control":
        raise RequestShapeError(f"{field}.record.surface_kind is unsupported")
    if record.get("schema_version") != (
        "mas.workspace_study_lifecycle_control.v1"
    ):
        raise RequestShapeError(f"{field}.record.schema_version is unsupported")
    if record.get("workspace_name") != workspace_name:
        raise RequestShapeError(
            f"{field}.record.workspace_name does not match topology"
        )
    studies_value = record.get("studies")
    if not isinstance(studies_value, Sequence) or isinstance(
        studies_value, (str, bytes, bytearray)
    ):
        raise RequestShapeError(f"{field}.record.studies must be an array")
    studies: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item_value in enumerate(studies_value):
        item_field = f"{field}.record.studies[{index}]"
        item = mapping(item_value, item_field)
        study_id = _study_id(item.get("study_id"), f"{item_field}.study_id")
        state = item.get("lifecycle_state")
        if state not in _LIFECYCLE_STATES:
            raise RequestShapeError(
                f"{item_field}.lifecycle_state is unsupported"
            )
        if study_id in seen:
            raise RequestShapeError(f"{field}.record contains duplicate study_id")
        seen.add(study_id)
        normalized_item = deepcopy(item)
        normalized_item["study_id"] = study_id
        normalized_item["lifecycle_state"] = state
        studies.append(normalized_item)
    _validate_status_counts(record.get("status_counts"), studies, field)
    if normalized["exists"]:
        _timestamp(record.get("recorded_at"), f"{field}.record.recorded_at")
        _study_id(
            record.get("changed_study_id"),
            f"{field}.record.changed_study_id",
        )
        if (
            type(record.get("changed_generation")) is not int
            or record["changed_generation"] < 1
        ):
            raise RequestShapeError(
                f"{field}.record.changed_generation must be positive integer"
            )
    normalized["record"] = deepcopy(record)
    normalized["record"]["studies"] = studies
    return normalized


def _normalize_optional_exact_projection(
    value: Any,
    *,
    field: str,
    ref_field: str,
    expected_ref: str,
    value_prefix: str,
    absent_record: dict[str, Any],
) -> dict[str, Any]:
    payload = mapping(value, field)
    sha_field = f"{value_prefix}_sha256"
    bytes_field = f"{value_prefix}_bytes_base64"
    size_field = f"{value_prefix}_byte_size"
    exact_keys(
        payload,
        {"exists", ref_field, sha_field, bytes_field, size_field, "record"},
        field,
    )
    if payload.get(ref_field) != expected_ref:
        raise RequestShapeError(f"{field}.{ref_field} must be {expected_ref}")
    exists = payload.get("exists")
    if not isinstance(exists, bool):
        raise RequestShapeError(f"{field}.exists must be boolean")
    if not exists:
        if any(
            payload.get(name) is not None
            for name in (sha_field, bytes_field, size_field, "record")
        ):
            raise RequestShapeError(
                f"{field} absent state must carry null exact-byte fields"
            )
        return {
            "exists": False,
            ref_field: expected_ref,
            sha_field: None,
            bytes_field: None,
            size_field: None,
            "record": absent_record,
        }
    sha256 = _digest_text(payload.get(sha_field), f"{field}.{sha_field}")
    encoded, byte_size, record = _normalize_exact_json_object(
        encoded_value=payload.get(bytes_field),
        byte_size_value=payload.get(size_field),
        expected_sha256=sha256,
        supplied_record=payload.get("record"),
        field=field,
    )
    return {
        "exists": True,
        ref_field: expected_ref,
        sha_field: sha256,
        bytes_field: encoded,
        size_field: byte_size,
        "record": record,
    }


def _normalize_inventory_rows(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RequestShapeError(f"{field}.record.studies must be an array")
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_roots: set[str] = set()
    for index, item_value in enumerate(value):
        item_field = f"{field}.record.studies[{index}]"
        item = mapping(item_value, item_field)
        study_id = _study_id(item.get("study_id"), f"{item_field}.study_id")
        root = _workspace_relative_path(
            item.get("canonical_study_root"),
            f"{item_field}.canonical_study_root",
        )
        if root != f"studies/{study_id}":
            raise RequestShapeError(
                f"{item_field}.canonical_study_root must match study_id"
            )
        state = item.get("lifecycle_state", item.get("status"))
        if state not in _LIFECYCLE_STATES and state != "qualification_only":
            raise RequestShapeError(f"{item_field} status is unsupported")
        if study_id in seen_ids or root in seen_roots:
            raise RequestShapeError(f"{field}.record contains duplicate identity")
        seen_ids.add(study_id)
        seen_roots.add(root)
        row = deepcopy(item)
        row["study_id"] = study_id
        row["canonical_study_root"] = root
        rows.append(row)
    return rows


def _validate_status_counts(
    value: Any, studies: Sequence[Mapping[str, Any]], field: str
) -> None:
    counts = mapping(value, f"{field}.record.status_counts")
    normalized_counts: dict[str, int] = {}
    for name, count in counts.items():
        if (
            not isinstance(name, str)
            or not name
            or type(count) is not int
            or count < 0
        ):
            raise RequestShapeError(
                f"{field}.record.status_counts must contain nonnegative integers"
            )
        normalized_counts[name] = count
    expected: dict[str, int] = {}
    for item in studies:
        state = item.get("lifecycle_state", item.get("status"))
        expected[state] = expected.get(state, 0) + 1
    if normalized_counts != expected:
        raise RequestShapeError(
            f"{field}.record.status_counts does not match study rows"
        )


def _lifecycle_record(normalized: Mapping[str, Any]) -> dict[str, Any]:
    identity = normalized["study_identity"]
    authority = normalized["user_authority"]
    evidence = normalized["existing_study_evidence"]
    recorded_at = authority["record"]["recorded_at"]
    return {
        "surface_kind": "study_lifecycle_control",
        "schema_version": "mas.study_lifecycle_control.v1",
        "study_id": identity["study_id"],
        "lifecycle_ref": "control/lifecycle.json",
        "lifecycle_state": "delivered_paused",
        "business_status": "delivered_paused",
        "generation": 1,
        "recorded_at": recorded_at,
        "materialized_at": recorded_at,
        "reason_code": "existing_study_adopted_delivered_paused",
        "reason_summary": (
            "Existing study adopted into MAS lifecycle; explicit user wakeup "
            "is required before any Stage body runs."
        ),
        "source_kind": "existing_study_adoption",
        "source_ref": evidence["evidence_ref"],
        "evidence_refs": [
            evidence["evidence_ref"],
            authority["authority_ref"],
        ],
        "current_stage_id": None,
        "current_stage_status": None,
        "current_stage_policy": "no_current_stage_while_inactive",
        "milestone_package_delivered": True,
        "submission_ready": False,
        "package_status": "milestone_delivered",
        "next_action": {
            "surface_kind": "mas_lifecycle_action",
            "action_id": "wait_for_explicit_user_wakeup",
            "action_type": "user_action",
            "owner": "user",
            "status": "delivered_paused",
            "summary": (
                "Wait for the exact reviewer-revision intake and explicit "
                "reactivation materialization."
            ),
        },
        "resume_policy": {
            "policy_id": "explicit_user_wakeup",
            "auto_resume_allowed": False,
            "explicit_user_wakeup_required": True,
            "allow_stopped_relaunch_required": False,
        },
        "authority_boundary": {
            "truth_owner": DOMAIN_OWNER,
            "domain_truth": True,
            "opl_consumption": "read_only_projection",
            "paper_body_mutated": False,
            "publication_eval_mutated": False,
            "runtime_or_telemetry_can_override": False,
            "submission_package_promoted": False,
        },
    }


def _inventory_row(
    normalized: Mapping[str, Any], lifecycle: Mapping[str, Any]
) -> dict[str, Any]:
    identity = normalized["study_identity"]
    return {
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "display_name": identity["display_name"],
        "status": lifecycle["lifecycle_state"],
        "business_status": lifecycle["business_status"],
        "lifecycle_state": lifecycle["lifecycle_state"],
        "current_stage_id": None,
        "current_stage_status": None,
        "package_status": lifecycle["package_status"],
        "lifecycle_ref": "control/lifecycle.json",
        "submission_ready": False,
        "qualification_only": False,
        "auto_resume_allowed": False,
        "lifecycle_reason_code": lifecycle["reason_code"],
        "lifecycle_reason_summary": lifecycle["reason_summary"],
        "next_action": deepcopy(lifecycle["next_action"]),
        "resume_policy": deepcopy(lifecycle["resume_policy"]),
    }


def _updated_mas_inventory(
    normalized: Mapping[str, Any], lifecycle: Mapping[str, Any]
) -> dict[str, Any]:
    current = normalized["current_mas_workspace_index"]["record"]
    payload = deepcopy(current)
    payload["surface_kind"] = "mas_workspace_index"
    payload["schema_version"] = "mas.workspace_index.v1"
    payload["canonical_workspace_root"] = normalized["study_identity"][
        "canonical_workspace_root"
    ]
    payload["recorded_at"] = lifecycle["recorded_at"]
    payload["studies"] = [*payload["studies"], _inventory_row(normalized, lifecycle)]
    payload["status_counts"] = _status_counts(payload["studies"])
    return payload


def _updated_workspace_lifecycle(
    normalized: Mapping[str, Any], lifecycle: Mapping[str, Any]
) -> dict[str, Any]:
    current = normalized["current_workspace_lifecycle_latest"]["record"]
    payload = deepcopy(current)
    payload["surface_kind"] = "workspace_study_lifecycle_control"
    payload["schema_version"] = "mas.workspace_study_lifecycle_control.v1"
    payload["workspace_name"] = normalized["current_opl_topology_inventory"][
        "record"
    ]["workspace_id"]
    payload["recorded_at"] = lifecycle["recorded_at"]
    payload["changed_study_id"] = lifecycle["study_id"]
    payload["changed_generation"] = lifecycle["generation"]
    payload["studies"] = [*payload["studies"], deepcopy(lifecycle)]
    payload["status_counts"] = _status_counts(payload["studies"])
    return payload


def _status_counts(studies: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in studies:
        state = item.get("lifecycle_state", item.get("status"))
        counts[state] = counts.get(state, 0) + 1
    return counts


def _submission_status(normalized: Mapping[str, Any]) -> dict[str, Any]:
    recorded_at = normalized["user_authority"]["record"]["recorded_at"]
    return {
        "surface_kind": "study_current_package_status",
        "schema_version": 1,
        "lifecycle_state": "delivered_paused",
        "status": "not_ready",
        "submission_ready": False,
        "promotion_allowed": False,
        "publication_verdict": "not_ready",
        "reason": (
            "Existing study adoption does not authorize publication, submission, "
            "or package promotion."
        ),
        "recorded_at": recorded_at,
    }


def _adoption_receipt(
    normalized: Mapping[str, Any],
    *,
    inventory_sha256: str,
    workspace_lifecycle_sha256: str,
    lifecycle_sha256: str,
    submission_sha256: str,
) -> dict[str, Any]:
    identity = normalized["study_identity"]
    authority = normalized["user_authority"]
    evidence = normalized["existing_study_evidence"]
    topology = normalized["current_opl_topology_inventory"]
    inventory = normalized["current_mas_workspace_index"]
    workspace_lifecycle = normalized["current_workspace_lifecycle_latest"]
    context = normalized["authority_context"]
    core = {
        "surface_kind": RECEIPT_KIND,
        "schema_version": SCHEMA_VERSION,
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "canonical_workspace_root": identity["canonical_workspace_root"],
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "lifecycle_state": "delivered_paused",
        "lifecycle_generation": 1,
        "user_authority_ref": authority["authority_ref"],
        "user_authority_sha256": authority["authority_sha256"],
        "user_authority_byte_size": authority["authority_byte_size"],
        "existing_study_evidence_ref": evidence["evidence_ref"],
        "existing_study_evidence_sha256": evidence["evidence_sha256"],
        "existing_study_evidence_byte_size": evidence["evidence_byte_size"],
        "opl_topology_ref": topology["topology_ref"],
        "opl_topology_sha256": topology["topology_sha256"],
        "handler_call_ref": context["handler_call_ref"],
        "owner_ledger_ref": context["owner_ledger_ref"],
        "mas_workspace_index_ref": MAS_INVENTORY_PATH,
        "mas_workspace_index_before_sha256": inventory[
            "mas_workspace_index_sha256"
        ],
        "mas_workspace_index_after_sha256": inventory_sha256,
        "workspace_lifecycle_ref": WORKSPACE_LIFECYCLE_PATH,
        "workspace_lifecycle_before_sha256": workspace_lifecycle[
            "workspace_lifecycle_sha256"
        ],
        "workspace_lifecycle_after_sha256": workspace_lifecycle_sha256,
        "lifecycle_relative_path": identity["lifecycle_relative_path"],
        "lifecycle_sha256": lifecycle_sha256,
        "submission_status_relative_path": identity[
            "submission_status_relative_path"
        ],
        "submission_status_sha256": submission_sha256,
        "receipt_relative_path": identity["receipt_relative_path"],
        "issued_at": authority["record"]["recorded_at"],
        "single_use": True,
        "qualification_only": False,
        "authorizes_lifecycle_initialization": True,
        "authorizes_stage_body": False,
        "authorizes_business_action": False,
        "authorizes_publication": False,
        "authorizes_submission": False,
        "requires_opl_cas_materialization_receipt": True,
        "materialization_semantics": "journaled_all_or_rollback",
        "provider_completion_is_domain_completion": False,
    }
    fingerprint = _fingerprint(core)
    return {
        **core,
        "receipt_ref": (
            "mas-study-work-item-adoption:"
            f"{fingerprint.removeprefix('sha256:')}"
        ),
        "receipt_fingerprint": fingerprint,
    }


def _materialization_operations(
    normalized: Mapping[str, Any],
    *,
    lifecycle: Mapping[str, Any],
    lifecycle_bytes: bytes,
    inventory_bytes: bytes,
    workspace_lifecycle: Mapping[str, Any],
    workspace_lifecycle_bytes: bytes,
    submission_bytes: bytes,
    receipt: Mapping[str, Any],
    receipt_bytes: bytes,
) -> list[dict[str, Any]]:
    identity = normalized["study_identity"]
    current_inventory = normalized["current_mas_workspace_index"]
    current_workspace_lifecycle = normalized[
        "current_workspace_lifecycle_latest"
    ]
    event_stamp = _history_stamp(lifecycle["recorded_at"])
    study_id = identity["study_id"]
    generation = lifecycle["generation"]
    inventory_precondition = _projection_precondition(
        current_inventory,
        sha_field="mas_workspace_index_sha256",
        size_field="mas_workspace_index_byte_size",
    )
    workspace_lifecycle_precondition = _projection_precondition(
        current_workspace_lifecycle,
        sha_field="workspace_lifecycle_sha256",
        size_field="workspace_lifecycle_byte_size",
    )
    return [
        _operation(
            MAS_INVENTORY_PATH,
            inventory_bytes,
            precondition=inventory_precondition,
        ),
        _operation(
            WORKSPACE_LIFECYCLE_PATH,
            workspace_lifecycle_bytes,
            precondition=workspace_lifecycle_precondition,
        ),
        _operation(
            identity["lifecycle_relative_path"],
            lifecycle_bytes,
            precondition={"kind": "absent"},
        ),
        _operation(
            identity["submission_status_relative_path"],
            submission_bytes,
            precondition={"kind": "absent"},
        ),
        _operation(
            identity["receipt_relative_path"],
            receipt_bytes,
            precondition={"kind": "absent"},
        ),
        _operation(
            (
                f"studies/{study_id}/artifacts/controller/lifecycle_control/"
                f"history/{event_stamp}-g{generation:04d}.json"
            ),
            lifecycle_bytes,
            precondition={"kind": "absent"},
        ),
        _operation(
            (
                f"studies/{study_id}/artifacts/controller/lifecycle_control/"
                f"history/{event_stamp}-g{generation:04d}-adoption-receipt.json"
            ),
            receipt_bytes,
            precondition={"kind": "absent"},
        ),
        _operation(
            (
                "runtime/artifacts/study_lifecycle_control/history/"
                f"{event_stamp}-{study_id}-g{generation:04d}.json"
            ),
            _canonical_json_bytes(workspace_lifecycle),
            precondition={"kind": "absent"},
        ),
    ]


def _projection_precondition(
    projection: Mapping[str, Any], *, sha_field: str, size_field: str
) -> dict[str, Any]:
    if not projection["exists"]:
        return {"kind": "absent"}
    return {
        "kind": "existing_exact",
        "sha256": projection[sha_field],
        "byte_size": projection[size_field],
    }


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
    *,
    request_id: str,
    operations_sha256: str,
    materialization_scope_sha256: str,
    absent_paths: list[str],
    receipt: Mapping[str, Any],
    receipt_content: Mapping[str, Any],
) -> dict[str, Any]:
    identity = normalized["study_identity"]
    authority = normalized["user_authority"]
    evidence = normalized["existing_study_evidence"]
    core = {
        "surface_kind": (
            "mas_study_work_item_adoption_cas_mutation_authorization"
        ),
        "version": (
            "mas-study-work-item-adoption-cas-mutation-authorization.v1"
        ),
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "user_authority_ref": authority["authority_ref"],
        "user_authority_sha256": authority["authority_sha256"],
        "existing_study_evidence_ref": evidence["evidence_ref"],
        "existing_study_evidence_sha256": evidence["evidence_sha256"],
        "authority_receipt_ref": receipt["receipt_ref"],
        "authority_receipt_content_sha256": receipt_content["sha256"],
        "operations_sha256": operations_sha256,
        "materialization_scope_sha256": materialization_scope_sha256,
        "absent_relative_path_preconditions": absent_paths,
        "authorized": True,
        "single_use": True,
        "qualification_only": False,
        "authorizes_lifecycle_initialization": True,
        "authorizes_stage_body": False,
        "authorizes_business_action": False,
        "authorizes_publication": False,
        "authorizes_submission": False,
    }
    fingerprint = _fingerprint(core)
    return {
        **core,
        "authorization_ref": (
            "mas-study-work-item-adoption-cas-authorization:"
            f"{fingerprint.removeprefix('sha256:')}"
        ),
        "authorization_fingerprint": fingerprint,
    }


def _typed_blocker(
    normalized: Mapping[str, Any],
    *,
    reason_code: str,
    resume_condition: str,
) -> dict[str, Any]:
    identity = normalized["study_identity"]
    authority = normalized["user_authority"]
    blocker = {
        "surface_kind": "mas_study_work_item_adoption_typed_blocker",
        "schema_version": SCHEMA_VERSION,
        "reason_code": reason_code,
        "resume_condition": resume_condition,
        "domain_owner": DOMAIN_OWNER,
        "domain_id": DOMAIN_ID,
        "study_id": identity["study_id"],
        "canonical_study_root": identity["canonical_study_root"],
        "user_authority_ref": authority["authority_ref"],
        "user_authority_sha256": authority["authority_sha256"],
    }
    return _finalize(
        status="typed_blocker",
        study_identity=identity,
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
        "adoption_receipt": None if receipt is None else dict(receipt),
        "adoption_receipt_content_binding": (
            None if receipt_content is None else dict(receipt_content)
        ),
        "mas_study_work_item_adoption_cas_mutation_authorization": (
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
    fingerprint = _fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-study-work-item-adoption-decision:"
            f"{fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": fingerprint,
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
    if _bytes_sha256(raw_bytes) != expected_sha256:
        raise RequestShapeError(f"{field} sha256 does not match exact bytes")
    try:
        parsed = json.loads(
            raw_bytes.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RequestShapeError(
            f"{field} exact bytes must be one UTF-8 JSON object"
        ) from error
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


def _study_id(value: Any, field: str) -> str:
    study_id = text(value, field)
    if not _SAFE_STUDY_ID.fullmatch(study_id) or len(study_id) > 128:
        raise RequestShapeError(f"{field} is not a canonical study_id")
    return study_id


def _digest_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise RequestShapeError(f"{field} must be sha256:<64 lowercase hex>")
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


def _history_stamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.strftime("%Y%m%dT%H%M%SZ")


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


__all__ = ["evaluate_study_work_item_adoption_authority"]
