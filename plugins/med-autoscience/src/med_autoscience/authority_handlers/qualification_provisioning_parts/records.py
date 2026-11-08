"""Construct exact qualification lifecycle, receipt and CAS authorization records."""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
from typing import Any
from .values import (
    DOMAIN_ID,
    DOMAIN_OWNER,
    HOST_CAPABILITY_ID,
    QUALIFICATION_SCOPE,
    RECEIPT_KIND,
    SCHEMA_VERSION,
    _bytes_sha256,
    _fingerprint,
    _workspace_relative_path,
)


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
        "satisfied_gate_ids": [],
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
