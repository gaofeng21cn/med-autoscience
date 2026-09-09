"""Authorize first-use study lifecycle bytes without performing I/O."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import PurePosixPath
import re
from typing import Any
from urllib.parse import unquote, urlsplit

from ._record_validation import (
    RequestShapeError,
    exact_json_object,
    exact_keys,
    integer,
    mapping,
    text,
)
from .study_lifecycle_reactivation_parts.constants import (
    HOST_CAPABILITY_ID,
    _PUBLIC_STAGE_ACTION_IDS,
)
from .study_lifecycle_reactivation_parts.materialization import (
    _cas_authorization,
    _create_operation,
    _replace_operation,
)
from .study_lifecycle_reactivation_parts.primitives import (
    _digest_text,
    _file_ref,
    _relative_path,
    _strict_fingerprint,
    _timestamp,
)


ACTION_ID = "study_initialization_authority_evaluate"
_AUTHORITY_BOUNDARY = {
    "domain_truth_owner": "MedAutoScience",
    "host_materialization_owner": "one-person-lab",
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "persists_artifact_or_receipt": False,
    "quality_verdict_created": False,
    "publication_authorized": False,
    "submission_authorized": False,
    "handler_result_alone_is_launch_clearance": False,
}


def evaluate_study_initialization_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Initialize an identity-only inventory row through one hosted CAS."""
    try:
        normalized = _normalize_request(request)
    except RequestShapeError as error:
        return _result("invalid_host_input", error={
            "code": "invalid_host_input", "detail": str(error), "retryable": False,
        })

    identity = normalized["work_item_identity"]
    inventory = normalized["current_inventory"]
    selected = inventory["record"]["studies"][inventory["selected_item_index"]]
    # First-use authority must not relaunch or promote pre-existing domain truth.
    existing_lifecycle_fields = {
        "lifecycle_ref", "lifecycle_state", "generation", "business_status",
        "status", "current_stage_id", "current_stage_status", "package_status",
        "submission_ready", "stage_body_authorized",
        "business_action_authorized",
        "publication_authorized", "submission_authorized", "initialization_receipt_ref",
    }
    if (
        selected.get("qualification_only") is True
        or existing_lifecycle_fields.intersection(selected)
    ):
        return _result("typed_blocker", typed_blocker={
            "reason_code": "study_is_not_uninitialized",
            "next_owner": "MedAutoScience",
            "resume_condition": "Use the current MAS lifecycle authority; first-use initialization cannot replace existing business or qualification truth.",
            "authorizes_lifecycle_transition": False,
        })

    context = normalized["authority_context"]
    study_root = identity["canonical_work_item_root"]
    lifecycle_path = f"{study_root}/control/lifecycle.json"
    lifecycle = _lifecycle(identity["work_item_id"], context)
    receipt_core = {
        "receipt_kind": "mas_study_initialization_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "study_id": identity["work_item_id"],
        **{key: value for key, value in context.items() if key != "action_id"},
        "inventory_ref": inventory["inventory_ref"],
        "inventory_sha256": inventory["inventory_sha256"],
        "from_state": "uninitialized",
        "from_generation": 0,
        "to_state": "active",
        "to_generation": 1,
        "lifecycle_ref": lifecycle_path,
        "lifecycle_sha256": _strict_fingerprint(lifecycle),
        "stage_body_authorized": True,
        "publication_authorized": False,
        "submission_authorized": False,
        "quality_verdict_created": False,
        "requires_opl_cas_materialization_receipt": True,
        "materialization_semantics": "journaled_all_or_rollback",
    }
    receipt_fingerprint = _strict_fingerprint(receipt_core)
    receipt = {
        **receipt_core,
        "receipt_ref": f"mas-study-initialization:{receipt_fingerprint.removeprefix('sha256:')}",
        "receipt_fingerprint": receipt_fingerprint,
    }
    receipt_path = f"{study_root}/artifacts/controller/lifecycle_control/initialization-receipt.json"
    after_inventory = deepcopy(inventory["record"])
    after_inventory["studies"][inventory["selected_item_index"]] = {
        **selected,
        "lifecycle_ref": "control/lifecycle.json",
        "lifecycle_state": "active",
        "generation": 1,
        "business_status": "active",
        "status": "active",
        "current_stage_id": None,
        "current_stage_status": None,
        "package_status": "not_ready",
        "submission_ready": False,
        "initialization_receipt_ref": receipt_path,
    }
    operations = [
        _replace_operation({
            "relative_path": inventory["inventory_ref"],
            "current_sha256": inventory["inventory_sha256"],
            "current_byte_size": inventory["inventory_byte_size"],
        }, after_inventory),
        _create_operation(lifecycle_path, lifecycle),
        _create_operation(receipt_path, receipt),
    ]
    operations_sha256 = _strict_fingerprint(operations)
    materialization_scope_sha256 = _strict_fingerprint({
        "operations": operations, "absent_relative_path_preconditions": [],
    })
    request_id = f"mas-study-initialization-cas:{materialization_scope_sha256.removeprefix('sha256:')}"
    authorization = _cas_authorization(
        request_id=request_id,
        operations_sha256=operations_sha256,
        materialization_scope_sha256=materialization_scope_sha256,
        absent_relative_path_preconditions=[],
        authority_receipt_ref=receipt["receipt_ref"],
        satisfied_gate_ids=[],
    )
    host_request = {
        "surface_kind": "opl_domain_artifact_cas_materialization_request",
        "version": "opl-domain-artifact-cas-materialization.v1",
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_id": "medautoscience",
        "authorization_ref": authorization["authorization_ref"],
        "operations_sha256": operations_sha256,
        "materialization_scope_sha256": materialization_scope_sha256,
        "absent_relative_path_preconditions": [],
        "operations": operations,
    }
    return _result(
        "authorized", initialization_receipt=receipt,
        mas_lifecycle_cas_mutation_authorization=authorization,
        opl_host_materialization_request=host_request,
    )


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = mapping(request, "request")
    exact_keys(payload, {"authority_context", "work_item_identity", "current_inventory"}, "request")
    context = mapping(payload["authority_context"], "authority_context")
    exact_keys(context, {
        "action_id", "handler_call_ref", "owner_ledger_ref",
        "original_admission_request_ref", "original_admission_request_sha256",
        "admission_scope_id", "requested_action_id", "requested_run_id",
        "original_invocation_sha256", "requested_at",
    }, "authority_context")
    for key in context:
        context[key] = text(context[key], f"authority_context.{key}")
    if context["action_id"] != ACTION_ID:
        raise RequestShapeError("authority_context.action_id is not the initialization action")
    if context["requested_action_id"] not in _PUBLIC_STAGE_ACTION_IDS:
        raise RequestShapeError("requested_action_id must be a public MAS Stage action")
    for key in ("original_admission_request_sha256", "original_invocation_sha256"):
        context[key] = _digest_text(context[key], f"authority_context.{key}")
    for key in ("owner_ledger_ref", "original_admission_request_ref"):
        _file_ref(context[key], f"authority_context.{key}")
    context["requested_at"] = _timestamp(context["requested_at"], "authority_context.requested_at")

    identity = mapping(payload["work_item_identity"], "work_item_identity")
    exact_keys(identity, {
        "work_item_id", "canonical_workspace_root", "canonical_work_item_root",
        "work_item_root_ref", "descriptor_domain_id",
    }, "work_item_identity")
    study_id = text(identity["work_item_id"], "work_item_identity.work_item_id")
    if study_id != identity["work_item_id"] or len(study_id) > 128 or not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)*", study_id):
        raise RequestShapeError("work_item_id must be a canonical MAS study_id")
    workspace_root = text(identity["canonical_workspace_root"], "canonical_workspace_root")
    workspace_path = PurePosixPath(workspace_root)
    if workspace_root != identity["canonical_workspace_root"] or not workspace_path.is_absolute() or str(workspace_path) != workspace_root or ".." in workspace_path.parts:
        raise RequestShapeError("canonical_workspace_root must be a normalized absolute path")
    expected_root = f"studies/{study_id}"
    if identity["canonical_work_item_root"] != expected_root:
        raise RequestShapeError("canonical_work_item_root does not match study_id")
    root_ref = urlsplit(_file_ref(identity["work_item_root_ref"], "work_item_root_ref"))
    if root_ref.netloc or root_ref.query or root_ref.fragment or unquote(root_ref.path) != str(workspace_path / expected_root):
        raise RequestShapeError("work_item_root_ref does not match the canonical study root")
    if identity["descriptor_domain_id"] != "medautoscience":
        raise RequestShapeError("descriptor_domain_id must be medautoscience")

    inventory = mapping(payload["current_inventory"], "current_inventory")
    exact_keys(inventory, {
        "inventory_ref", "inventory_sha256", "inventory_bytes_base64",
        "inventory_byte_size", "record", "selected_item_index",
    }, "current_inventory")
    inventory_ref = _relative_path(inventory["inventory_ref"], "current_inventory.inventory_ref")
    if inventory_ref != "workspace_index.json":
        raise RequestShapeError("inventory_ref must be the MAS workspace_index.json")
    inventory_sha256 = _digest_text(inventory["inventory_sha256"], "current_inventory.inventory_sha256")
    _, byte_size, record = exact_json_object(
        encoded_value=inventory["inventory_bytes_base64"],
        byte_size_value=inventory["inventory_byte_size"],
        expected_sha256=inventory_sha256,
        supplied_record=inventory["record"],
        field="current_inventory",
    )
    envelope = (record.get("surface_kind"), record.get("schema_version"), record.get("version"))
    if envelope not in {
        ("workspace_index", "mas.workspace_index.v1", None),
        ("opl_workspace_index", None, "workspace-index.v1"),
    }:
        raise RequestShapeError("current_inventory has an unsupported workspace envelope")
    studies = record.get("studies")
    if not isinstance(studies, list):
        raise RequestShapeError("current_inventory.record.studies must be an array")
    index = integer(inventory["selected_item_index"], "current_inventory.selected_item_index")
    if index >= len(studies):
        raise RequestShapeError("selected_item_index is outside the current inventory")
    selected = mapping(studies[index], "selected inventory item")
    if selected.get("study_id") != study_id or selected.get("canonical_study_root") != expected_root:
        raise RequestShapeError("selected inventory item does not match the exact study identity")
    matches = [item for item in studies if isinstance(item, dict) and (
        item.get("study_id") == study_id or item.get("canonical_study_root") == expected_root
    )]
    if len(matches) != 1:
        raise RequestShapeError("current inventory contains a duplicate study identity or root")
    return {
        "authority_context": context,
        "work_item_identity": identity,
        "current_inventory": {
            **inventory, "inventory_ref": inventory_ref, "inventory_sha256": inventory_sha256,
            "inventory_byte_size": byte_size, "record": record,
        },
    }


def _lifecycle(study_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "mas.study_lifecycle_control.v1",
        "surface_kind": "study_lifecycle_control",
        "study_id": study_id,
        "lifecycle_state": "active",
        "business_status": "active",
        "generation": 1,
        "recorded_at": context["requested_at"],
        "materialized_at": context["requested_at"],
        "reason_code": "study_initialized_for_stage",
        "reason_summary": "Continue the requested research Stage; initialization does not determine research quality.",
        "source_kind": "host_bound_stage_invocation",
        "source_ref": context["original_admission_request_ref"],
        "evidence_refs": [context["original_admission_request_ref"]],
        "lifecycle_ref": "control/lifecycle.json",
        "current_stage_id": None,
        "current_stage_status": None,
        "current_stage_policy": "project_current_runtime_stage",
        "milestone_package_delivered": False,
        "submission_ready": False,
        "package_status": "not_ready",
        "next_action": {
            "surface_kind": "mas_lifecycle_action",
            "action_id": "continue_current_study_line",
            "action_type": "agent_action",
            "owner": "MedAutoScience",
            "status": "active",
            "summary": "Continue the requested research Stage through the canonical MAS route.",
        },
        "resume_policy": {
            "policy_id": "automatic_allowed",
            "auto_resume_allowed": True,
            "explicit_user_wakeup_required": False,
            "allow_stopped_relaunch_required": False,
        },
        "authority_boundary": {
            "domain_truth": True,
            "opl_consumption": "read_only_projection",
            "paper_body_mutated": False,
            "publication_eval_mutated": False,
            "runtime_or_telemetry_can_override": False,
            "submission_package_promoted": False,
            "truth_owner": "MedAutoScience",
        },
    }


def _result(status: str, **fields: Any) -> dict[str, Any]:
    core = {
        "surface_kind": "mas_study_initialization_authority_result",
        "schema_version": 1,
        "status": status,
        "initialization_receipt": None,
        "mas_lifecycle_cas_mutation_authorization": None,
        "opl_host_materialization_request": None,
        "typed_blocker": None,
        "error": None,
        "authority_boundary": deepcopy(_AUTHORITY_BOUNDARY),
        **fields,
    }
    decision_fingerprint = _strict_fingerprint(core)
    return {
        **core,
        "decision_id": f"mas-study-initialization-decision:{decision_fingerprint.removeprefix('sha256:')}",
        "decision_fingerprint": decision_fingerprint,
    }


__all__ = ["evaluate_study_initialization_authority"]
