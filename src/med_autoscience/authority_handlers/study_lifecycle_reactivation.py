"""Authorize an inactive-study reactivation without writing workspace files."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import base64
import hashlib
import json
import re
from typing import Any

from ._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_keys,
    exact_ref,
    fingerprint,
    integer,
    mapping,
    sequence,
    text,
    text_list,
    typed_ref,
)


REQUEST_KIND = "mas_study_lifecycle_reactivation_authority_request"
RESULT_KIND = "mas_study_lifecycle_reactivation_authority_result"
SCHEMA_VERSION = 1
HOST_CAPABILITY_ID = "opl_domain_artifact_cas_materialization.v1"

_LIFECYCLE_STATES = {"active", "paused", "delivered_paused", "stopped"}
_INACTIVE_STATES = {"paused", "delivered_paused", "stopped"}
_REQUIRED_TARGET_ROLES = {
    "study_lifecycle_current",
    "workspace_lifecycle_latest",
    "workspace_index",
    "submission_status",
}
_OPTIONAL_TARGET_ROLES = {
    "publication_current_package_status",
    "stage_index",
    "workspace_latest_status",
    "workspace_studies_index",
}
_PUBLIC_STAGE_ACTION_IDS = {
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
}
_TARGET_ROLE_ORDER = (
    "study_lifecycle_current",
    "workspace_lifecycle_latest",
    "workspace_index",
    "workspace_studies_index",
    "workspace_latest_status",
    "submission_status",
    "publication_current_package_status",
    "stage_index",
)
_AUTHORITY_BOUNDARY = {
    "owner": "MedAutoScience",
    "handler_role": "authorize_exact_inactive_study_reactivation_and_cas_materialization",
    "opl_role": "persist_exact_handler_result_and_journal_all_or_rollback_authorized_json_bytes",
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "owns_runtime_or_attempt_lifecycle": False,
    "selects_scientific_stage": False,
    "authorizes_publication_or_submission": False,
    "provider_completion_is_domain_completion": False,
    "public_action": False,
}
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ProjectionCurrentnessError(ValueError):
    """Raised when a structurally valid projection is stale or incomplete."""


def evaluate_study_lifecycle_reactivation_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic MAS receipt and an OPL-hosted CAS request."""

    try:
        normalized = _normalize_request(request)
    except RequestShapeError as error:
        return _invalid_host_input(str(error))

    lifecycle = normalized["current_lifecycle"]["record"]
    state = lifecycle["lifecycle_state"]
    if state not in _INACTIVE_STATES:
        return _typed_blocker(
            normalized,
            reason_code="study_lifecycle_is_not_inactive",
            resume_condition=(
                "read the current lifecycle and do not request inactive-study "
                "reactivation for an active study"
            ),
        )
    if not normalized["explicit_user_wakeup"]["explicit_user_wakeup"]:
        return _typed_blocker(
            normalized,
            reason_code="explicit_user_wakeup_required",
            resume_condition="provide a current structured explicit user wakeup",
        )
    if state == "stopped" and not normalized["explicit_user_wakeup"][
        "allow_stopped_relaunch"
    ]:
        return _typed_blocker(
            normalized,
            reason_code="stopped_study_relaunch_authority_required",
            resume_condition=(
                "provide allow_stopped_relaunch=true bound to the same user authority"
            ),
        )
    if normalized["reviewer_revision_intake"]["record"]["status"] not in {
        "accepted",
        "active",
    }:
        return _typed_blocker(
            normalized,
            reason_code="reviewer_revision_intake_not_current",
            resume_condition="provide a current accepted or active reviewer_revision intake",
        )

    after_lifecycle = _active_lifecycle_record(normalized)
    receipt = _reactivation_receipt(normalized, after_lifecycle)
    try:
        operations = _materialization_operations(
            normalized,
            after_lifecycle=after_lifecycle,
            receipt=receipt,
        )
    except ProjectionCurrentnessError as error:
        return _typed_blocker(
            normalized,
            reason_code="lifecycle_projection_currentness_mismatch",
            resume_condition=str(error),
        )

    operations_sha256 = _json_fingerprint(operations)
    request_id = (
        "mas-lifecycle-cas-request:"
        f"{operations_sha256.removeprefix('sha256:')}"
    )
    authorization = _cas_authorization(
        request_id=request_id,
        operations_sha256=operations_sha256,
        authority_receipt_ref=receipt["receipt_ref"],
        satisfied_gate_ids=receipt["satisfied_gate_ids"],
    )
    host_request = {
        "surface_kind": "opl_domain_artifact_cas_materialization_request",
        "version": "opl-domain-artifact-cas-materialization.v1",
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_id": "medautoscience",
        "authorization_ref": authorization["authorization_ref"],
        "operations_sha256": operations_sha256,
        "operations": operations,
    }
    return _finalize(
        normalized,
        status="authorized",
        reactivation_receipt=receipt,
        cas_authorization=authorization,
        host_request=host_request,
    )


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = mapping(request, "request")
    exact_keys(
        payload,
        {
            "study_id",
            "reactivation_request",
            "authority_context",
            "study_identity",
            "current_lifecycle",
            "user_authority",
            "reviewer_revision_intake",
            "profile",
            "projection_inventory",
        },
        "request",
    )

    study_id = text(payload["study_id"], "study_id")
    if not _SAFE_SEGMENT.fullmatch(study_id):
        raise RequestShapeError("study_id must be one safe path segment")
    reactivation = _normalize_reactivation_request(payload["reactivation_request"])
    authority_context = _normalize_authority_context(payload["authority_context"])
    identity = _normalize_study_identity(payload["study_identity"])
    current_lifecycle = _normalize_current_lifecycle(payload["current_lifecycle"])
    user_authority = _normalize_user_authority(payload["user_authority"])
    intake = _normalize_revision_intake(payload["reviewer_revision_intake"])
    profile = _normalize_profile(payload["profile"])
    inventory = _normalize_projection_inventory(
        payload["projection_inventory"], study_id=study_id
    )
    wakeup = {
        "explicit_user_wakeup": reactivation["explicit_user_wakeup"],
        "allow_stopped_relaunch": reactivation["allow_stopped_relaunch"],
        "user_authority_ref": reactivation["user_authority_ref"],
        "user_authority_sha256": reactivation["user_authority_sha256"],
        "requested_at": reactivation["requested_at"],
        "reason_code": reactivation["reason_code"],
        "reason_summary": reactivation["reason_summary"],
    }

    if identity["study_id"] != study_id:
        raise RequestShapeError("study_identity study_id does not match study_id")
    if identity["lifecycle_ref"] != current_lifecycle["lifecycle_ref"]:
        raise RequestShapeError(
            "study_identity lifecycle_ref does not match current_lifecycle"
        )
    if current_lifecycle["record"]["study_id"] != study_id:
        raise RequestShapeError("current lifecycle study_id does not match study_identity")
    if intake["record"]["study_id"] != study_id:
        raise RequestShapeError("reviewer_revision intake study_id does not match")
    if user_authority["record"]["study_id"] != study_id:
        raise RequestShapeError("user authority evidence study_id does not match")
    intake_authority = intake["record"]["user_authority_ref"]
    authority_ref = user_authority["authority_ref"]
    if wakeup["user_authority_ref"] != intake_authority or authority_ref != intake_authority:
        raise RequestShapeError(
            "user_authority.authority_ref, explicit_user_wakeup.user_authority_ref, "
            "and reviewer_revision_intake.record.user_authority_ref must match"
        )
    if intake["record"]["user_authority_sha256"] != user_authority["authority_sha256"]:
        raise RequestShapeError(
            "reviewer_revision_intake user authority hash must match injected evidence"
        )
    authority_record = user_authority["record"]
    if authority_record["explicit_user_wakeup"] != wakeup["explicit_user_wakeup"]:
        raise RequestShapeError(
            "user authority evidence explicit_user_wakeup must match wakeup request"
        )
    if authority_record["allow_stopped_relaunch"] != wakeup["allow_stopped_relaunch"]:
        raise RequestShapeError(
            "user authority evidence allow_stopped_relaunch must match wakeup request"
        )
    if authority_record["recorded_at"] != wakeup["requested_at"]:
        raise RequestShapeError(
            "user authority evidence recorded_at must match wakeup requested_at"
        )
    exact_bindings = (
        (
            "user_authority",
            reactivation["user_authority_ref"],
            reactivation["user_authority_sha256"],
            user_authority["authority_ref"],
            user_authority["authority_sha256"],
        ),
        (
            "reviewer_revision_intake",
            reactivation["reviewer_revision_intake_ref"],
            reactivation["reviewer_revision_intake_sha256"],
            intake["intake_ref"],
            intake["intake_sha256"],
        ),
        (
            "current_lifecycle",
            reactivation["current_lifecycle_ref"],
            reactivation["current_lifecycle_sha256"],
            current_lifecycle["lifecycle_ref"],
            current_lifecycle["lifecycle_sha256"],
        ),
        (
            "profile",
            reactivation["profile_ref"],
            reactivation["profile_sha256"],
            profile["profile_ref"],
            profile["profile_sha256"],
        ),
    )
    for name, requested_ref, requested_sha256, injected_ref, injected_sha256 in exact_bindings:
        if requested_ref != injected_ref or requested_sha256 != injected_sha256:
            raise RequestShapeError(
                f"reactivation_request {name} ref/hash does not match injected exact bytes"
            )
    lifecycle = current_lifecycle["record"]
    if (
        reactivation["observed_lifecycle_state"] != lifecycle["lifecycle_state"]
        or reactivation["observed_lifecycle_generation"] != lifecycle["generation"]
    ):
        raise RequestShapeError(
            "reactivation_request lifecycle state/generation does not match current lifecycle"
        )

    targets_by_role = {item["role"]: item for item in inventory["targets"]}
    lifecycle_target = targets_by_role["study_lifecycle_current"]
    if (
        lifecycle_target["current_ref"] != current_lifecycle["lifecycle_ref"]
        or lifecycle_target["current_sha256"] != current_lifecycle["lifecycle_sha256"]
    ):
        raise RequestShapeError(
            "study lifecycle projection ref/hash must match current_lifecycle"
        )
    if lifecycle_target["current_payload"] != current_lifecycle["record"]:
        raise RequestShapeError(
            "study lifecycle projection payload must match current_lifecycle.record"
        )
    expected_lifecycle_path = f"studies/{study_id}/control/lifecycle.json"
    if lifecycle_target["relative_path"] != expected_lifecycle_path:
        raise RequestShapeError(
            "study lifecycle target path does not match the study identity"
        )
    _validate_target_paths(study_id, targets_by_role)

    return {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "reactivation_request": reactivation,
        "authority_context": authority_context,
        "study_identity": identity,
        "current_lifecycle": current_lifecycle,
        "user_authority": user_authority,
        "reviewer_revision_intake": intake,
        "explicit_user_wakeup": wakeup,
        "profile": profile,
        "projection_inventory": inventory,
    }


def _normalize_reactivation_request(value: Any) -> dict[str, Any]:
    field = "reactivation_request"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "user_authority_ref",
            "user_authority_sha256",
            "reviewer_revision_intake_ref",
            "reviewer_revision_intake_sha256",
            "current_lifecycle_ref",
            "current_lifecycle_sha256",
            "profile_ref",
            "profile_sha256",
            "observed_lifecycle_state",
            "observed_lifecycle_generation",
            "explicit_user_wakeup",
            "allow_stopped_relaunch",
            "requested_at",
            "reason_code",
            "reason_summary",
        },
        field,
    )
    for name in ("explicit_user_wakeup", "allow_stopped_relaunch"):
        if not isinstance(payload.get(name), bool):
            raise RequestShapeError(f"{field}.{name} must be boolean")
    if payload.get("reason_code") != "reviewer_revision_reactivation":
        raise RequestShapeError(
            f"{field}.reason_code must be reviewer_revision_reactivation"
        )
    return {
        "user_authority_ref": _file_ref(
            payload["user_authority_ref"], f"{field}.user_authority_ref"
        ),
        "user_authority_sha256": _digest_text(
            payload["user_authority_sha256"], f"{field}.user_authority_sha256"
        ),
        "reviewer_revision_intake_ref": _file_ref(
            payload["reviewer_revision_intake_ref"],
            f"{field}.reviewer_revision_intake_ref",
        ),
        "reviewer_revision_intake_sha256": _digest_text(
            payload["reviewer_revision_intake_sha256"],
            f"{field}.reviewer_revision_intake_sha256",
        ),
        "current_lifecycle_ref": _file_ref(
            payload["current_lifecycle_ref"], f"{field}.current_lifecycle_ref"
        ),
        "current_lifecycle_sha256": _digest_text(
            payload["current_lifecycle_sha256"],
            f"{field}.current_lifecycle_sha256",
        ),
        "profile_ref": _file_ref(payload["profile_ref"], f"{field}.profile_ref"),
        "profile_sha256": _digest_text(
            payload["profile_sha256"], f"{field}.profile_sha256"
        ),
        "observed_lifecycle_state": enum_text(
            payload["observed_lifecycle_state"],
            f"{field}.observed_lifecycle_state",
            _INACTIVE_STATES,
        ),
        "observed_lifecycle_generation": integer(
            payload["observed_lifecycle_generation"],
            f"{field}.observed_lifecycle_generation",
        ),
        "explicit_user_wakeup": payload["explicit_user_wakeup"],
        "allow_stopped_relaunch": payload["allow_stopped_relaunch"],
        "requested_at": _timestamp(payload["requested_at"], f"{field}.requested_at"),
        "reason_code": "reviewer_revision_reactivation",
        "reason_summary": text(payload["reason_summary"], f"{field}.reason_summary"),
    }


def _normalize_authority_context(value: Any) -> dict[str, Any]:
    field = "authority_context"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "handler_call_ref",
            "owner_ledger_ref",
            "original_admission_request_ref",
            "original_admission_request_sha256",
            "admission_scope_id",
            "requested_action_id",
            "requested_run_id",
            "original_invocation_sha256",
        },
        field,
    )
    return {
        "handler_call_ref": text(payload["handler_call_ref"], f"{field}.handler_call_ref"),
        "owner_ledger_ref": text(payload["owner_ledger_ref"], f"{field}.owner_ledger_ref"),
        "original_admission_request_ref": text(
            payload["original_admission_request_ref"],
            f"{field}.original_admission_request_ref",
        ),
        "original_admission_request_sha256": _digest_text(
            payload["original_admission_request_sha256"],
            f"{field}.original_admission_request_sha256",
        ),
        "admission_scope_id": text(
            payload["admission_scope_id"], f"{field}.admission_scope_id"
        ),
        "requested_action_id": enum_text(
            payload["requested_action_id"],
            f"{field}.requested_action_id",
            _PUBLIC_STAGE_ACTION_IDS,
        ),
        "requested_run_id": text(
            payload["requested_run_id"], f"{field}.requested_run_id"
        ),
        "original_invocation_sha256": _digest_text(
            payload["original_invocation_sha256"],
            f"{field}.original_invocation_sha256",
        ),
    }


def _normalize_admission_scope(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"scope_id", "requested_action_id", "single_use"}, field)
    if payload.get("single_use") is not True:
        raise RequestShapeError(f"{field}.single_use must be true")
    return {
        "scope_id": text(payload.get("scope_id"), f"{field}.scope_id"),
        "requested_action_id": enum_text(
            payload.get("requested_action_id"),
            f"{field}.requested_action_id",
            {
                "direction_and_route_selection",
                "baseline_and_evidence_setup",
                "bounded_analysis_campaign",
                "manuscript_authoring",
                "review_and_quality_gate",
                "finalize_and_publication_handoff",
            },
        ),
        "single_use": True,
    }


def _normalize_study_identity(value: Any) -> dict[str, str]:
    field = "study_identity"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"study_id", "work_item_root_ref", "lifecycle_ref", "descriptor_domain_id"},
        field,
    )
    study_id = text(payload["study_id"], f"{field}.study_id")
    if not _SAFE_SEGMENT.fullmatch(study_id):
        raise RequestShapeError(f"{field}.study_id must be one safe path segment")
    return {
        "study_id": study_id,
        "work_item_root_ref": _file_ref(
            payload["work_item_root_ref"], f"{field}.work_item_root_ref"
        ),
        "lifecycle_ref": _file_ref(
            payload["lifecycle_ref"], f"{field}.lifecycle_ref"
        ),
        "descriptor_domain_id": enum_text(
            payload["descriptor_domain_id"],
            f"{field}.descriptor_domain_id",
            {"medautoscience"},
        ),
    }


def _normalize_current_lifecycle(value: Any) -> dict[str, Any]:
    field = "current_lifecycle"
    payload = mapping(value, field)
    exact_keys(payload, {"lifecycle_ref", "lifecycle_sha256", "record"}, field)
    return {
        "lifecycle_ref": _file_ref(
            payload["lifecycle_ref"], f"{field}.lifecycle_ref"
        ),
        "lifecycle_sha256": _digest_text(
            payload["lifecycle_sha256"], f"{field}.lifecycle_sha256"
        ),
        "record": _normalize_lifecycle_record(payload["record"]),
    }


def _normalize_lifecycle_record(value: Any) -> dict[str, Any]:
    field = "current_lifecycle.record"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "authority_boundary",
            "business_status",
            "current_stage_id",
            "current_stage_policy",
            "current_stage_status",
            "evidence_refs",
            "generation",
            "lifecycle_ref",
            "lifecycle_state",
            "materialized_at",
            "milestone_package_delivered",
            "next_action",
            "package_status",
            "reason_code",
            "reason_summary",
            "recorded_at",
            "resume_policy",
            "schema_version",
            "source_kind",
            "source_ref",
            "study_id",
            "submission_ready",
            "surface_kind",
        },
        field,
    )
    if payload.get("schema_version") != "mas.study_lifecycle_control.v1":
        raise RequestShapeError(f"{field}.schema_version is unsupported")
    if payload.get("surface_kind") != "study_lifecycle_control":
        raise RequestShapeError(f"{field}.surface_kind is unsupported")
    state = enum_text(payload.get("lifecycle_state"), f"{field}.lifecycle_state", _LIFECYCLE_STATES)
    if payload.get("business_status") != state:
        raise RequestShapeError(f"{field}.business_status must match lifecycle_state")
    generation = integer(payload.get("generation"), f"{field}.generation")
    if generation < 1:
        raise RequestShapeError(f"{field}.generation must be positive")
    if payload.get("submission_ready") is not False:
        raise RequestShapeError(f"{field}.submission_ready must be false")
    if not isinstance(payload.get("milestone_package_delivered"), bool):
        raise RequestShapeError(f"{field}.milestone_package_delivered must be boolean")
    if state in _INACTIVE_STATES and (
        payload.get("current_stage_id") is not None
        or payload.get("current_stage_status") is not None
    ):
        raise RequestShapeError(f"{field} inactive state cannot carry a current stage")
    if payload.get("lifecycle_ref") != "control/lifecycle.json":
        raise RequestShapeError(f"{field}.lifecycle_ref must be control/lifecycle.json")
    _timestamp(payload.get("recorded_at"), f"{field}.recorded_at")
    _timestamp(payload.get("materialized_at"), f"{field}.materialized_at")
    mapping(payload.get("next_action"), f"{field}.next_action")
    mapping(payload.get("resume_policy"), f"{field}.resume_policy")
    boundary = mapping(payload.get("authority_boundary"), f"{field}.authority_boundary")
    if boundary.get("truth_owner") != "MedAutoScience" or boundary.get("domain_truth") is not True:
        raise RequestShapeError(f"{field}.authority_boundary must retain MAS domain truth")
    normalized = deepcopy(payload)
    normalized["study_id"] = text(payload.get("study_id"), f"{field}.study_id")
    normalized["current_stage_policy"] = text(
        payload.get("current_stage_policy"), f"{field}.current_stage_policy"
    )
    normalized["evidence_refs"] = text_list(
        payload.get("evidence_refs"), f"{field}.evidence_refs"
    )
    for name in ("package_status", "reason_code", "reason_summary", "source_kind", "source_ref"):
        normalized[name] = text(payload.get(name), f"{field}.{name}")
    normalized["generation"] = generation
    normalized["lifecycle_state"] = state
    return normalized


def _normalize_revision_intake(value: Any) -> dict[str, Any]:
    field = "reviewer_revision_intake"
    payload = mapping(value, field)
    exact_keys(payload, {"intake_ref", "intake_sha256", "record"}, field)
    record_field = f"{field}.record"
    record = mapping(payload["record"], record_field)
    exact_keys(
        record,
        {
            "surface_kind",
            "schema_version",
            "task_intake_kind",
            "study_id",
            "status",
            "user_authority_ref",
            "user_authority_sha256",
            "recorded_at",
            "request_summary",
            "revision_checklist_ref",
            "revision_checklist_sha256",
            "independent_review_packet_ref",
            "independent_review_packet_sha256",
            "first_owning_stage_id",
            "allowed_revision_scope",
            "record_owner",
            "source_owner",
            "owner_receipt",
        },
        record_field,
    )
    if record.get("surface_kind") != "mas_reviewer_revision_task_intake":
        raise RequestShapeError(f"{record_field}.surface_kind is unsupported")
    if record.get("schema_version") != 1:
        raise RequestShapeError(f"{record_field}.schema_version must be integer 1")
    if record.get("task_intake_kind") != "reviewer_revision":
        raise RequestShapeError(f"{record_field}.task_intake_kind must be reviewer_revision")
    status = enum_text(
        record.get("status"),
        f"{record_field}.status",
        {"draft", "accepted", "active", "consumed", "superseded"},
    )
    return {
        "intake_ref": _file_ref(payload["intake_ref"], f"{field}.intake_ref"),
        "intake_sha256": _digest_text(
            payload["intake_sha256"], f"{field}.intake_sha256"
        ),
        "record": {
            "surface_kind": "mas_reviewer_revision_task_intake",
            "schema_version": 1,
            "task_intake_kind": "reviewer_revision",
            "study_id": text(record.get("study_id"), f"{record_field}.study_id"),
            "status": status,
            "user_authority_ref": _file_ref(
                record.get("user_authority_ref"), f"{record_field}.user_authority_ref"
            ),
            "user_authority_sha256": _digest_text(
                record.get("user_authority_sha256"),
                f"{record_field}.user_authority_sha256",
            ),
            "recorded_at": _timestamp(record.get("recorded_at"), f"{record_field}.recorded_at"),
            "request_summary": text(
                record.get("request_summary"), f"{record_field}.request_summary"
            ),
            "revision_checklist_ref": _file_ref(
                record.get("revision_checklist_ref"),
                f"{record_field}.revision_checklist_ref",
            ),
            "revision_checklist_sha256": _digest_text(
                record.get("revision_checklist_sha256"),
                f"{record_field}.revision_checklist_sha256",
            ),
            "independent_review_packet_ref": _file_ref(
                record.get("independent_review_packet_ref"),
                f"{record_field}.independent_review_packet_ref",
            ),
            "independent_review_packet_sha256": _digest_text(
                record.get("independent_review_packet_sha256"),
                f"{record_field}.independent_review_packet_sha256",
            ),
            "first_owning_stage_id": enum_text(
                record.get("first_owning_stage_id"),
                f"{record_field}.first_owning_stage_id",
                _PUBLIC_STAGE_ACTION_IDS,
            ),
            "allowed_revision_scope": text_list(
                record.get("allowed_revision_scope"),
                f"{record_field}.allowed_revision_scope",
            ),
            "record_owner": enum_text(
                record.get("record_owner"),
                f"{record_field}.record_owner",
                {"MedAutoScience"},
            ),
            "source_owner": enum_text(
                record.get("source_owner"),
                f"{record_field}.source_owner",
                {"user"},
            ),
            "owner_receipt": _required_false(
                record.get("owner_receipt"), f"{record_field}.owner_receipt"
            ),
        },
    }


def _normalize_user_authority(value: Any) -> dict[str, Any]:
    field = "user_authority"
    payload = mapping(value, field)
    exact_keys(payload, {"authority_ref", "authority_sha256", "record"}, field)
    record_field = f"{field}.record"
    record = mapping(payload["record"], record_field)
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
    if record.get("surface_kind") != "mas_explicit_user_authority_evidence":
        raise RequestShapeError(f"{record_field}.surface_kind is unsupported")
    if record.get("schema_version") != 1:
        raise RequestShapeError(f"{record_field}.schema_version must be integer 1")
    if record.get("task_intake_kind") != "reviewer_revision":
        raise RequestShapeError(f"{record_field}.task_intake_kind must be reviewer_revision")
    if record.get("status") != "accepted":
        raise RequestShapeError(f"{record_field}.status must be accepted")
    for name in ("explicit_user_wakeup", "allow_stopped_relaunch"):
        if not isinstance(record.get(name), bool):
            raise RequestShapeError(f"{record_field}.{name} must be boolean")
    if record.get("source_kind") != "explicit_user_instruction":
        raise RequestShapeError(
            f"{record_field}.source_kind must be explicit_user_instruction"
        )
    instruction_text = _normalized_instruction_text(
        record.get("instruction_text"), f"{record_field}.instruction_text"
    )
    instruction_sha256 = _digest_text(
        record.get("instruction_sha256"), f"{record_field}.instruction_sha256"
    )
    if hashlib.sha256(instruction_text.encode("utf-8")).hexdigest() != instruction_sha256:
        raise RequestShapeError(
            f"{record_field}.instruction_sha256 does not match normalized instruction_text"
        )
    return {
        "authority_ref": _file_ref(
            payload["authority_ref"], f"{field}.authority_ref"
        ),
        "authority_sha256": _digest_text(
            payload["authority_sha256"], f"{field}.authority_sha256"
        ),
        "record": {
            "surface_kind": "mas_explicit_user_authority_evidence",
            "schema_version": 1,
            "study_id": text(record.get("study_id"), f"{record_field}.study_id"),
            "task_intake_kind": "reviewer_revision",
            "status": "accepted",
            "explicit_user_wakeup": record["explicit_user_wakeup"],
            "allow_stopped_relaunch": record["allow_stopped_relaunch"],
            "recorded_at": _timestamp(
                record.get("recorded_at"), f"{record_field}.recorded_at"
            ),
            "source_kind": "explicit_user_instruction",
            "source_ref": text(record.get("source_ref"), f"{record_field}.source_ref"),
            "instruction_text": instruction_text,
            "instruction_sha256": instruction_sha256,
            "source_owner": enum_text(
                record.get("source_owner"),
                f"{record_field}.source_owner",
                {"user"},
            ),
            "record_owner": enum_text(
                record.get("record_owner"),
                f"{record_field}.record_owner",
                {"MedAutoScience"},
            ),
            "owner_receipt": _required_false(
                record.get("owner_receipt"), f"{record_field}.owner_receipt"
            ),
        },
    }


def _normalize_profile(value: Any) -> dict[str, Any]:
    field = "profile"
    payload = mapping(value, field)
    exact_keys(payload, {"profile_ref", "profile_sha256", "profile_byte_size", "profile_body_utf8"}, field)
    byte_size = integer(payload["profile_byte_size"], f"{field}.profile_byte_size")
    if byte_size < 1:
        raise RequestShapeError(f"{field}.profile_byte_size must be positive")
    profile_body = payload["profile_body_utf8"]
    if not isinstance(profile_body, str) or not profile_body:
        raise RequestShapeError(f"{field}.profile_body_utf8 must be non-empty text")
    profile_bytes = profile_body.encode("utf-8")
    if len(profile_bytes) != byte_size:
        raise RequestShapeError(f"{field}.profile_byte_size does not match profile_body_utf8")
    profile_sha256 = _digest_text(payload["profile_sha256"], f"{field}.profile_sha256")
    if hashlib.sha256(profile_bytes).hexdigest() != profile_sha256:
        raise RequestShapeError(f"{field}.profile_sha256 does not match profile_body_utf8")
    return {
        "profile_ref": _file_ref(payload["profile_ref"], f"{field}.profile_ref"),
        "profile_sha256": profile_sha256,
        "profile_byte_size": byte_size,
        "profile_body_utf8": profile_body,
    }


def _normalize_projection_inventory(value: Any, *, study_id: str) -> dict[str, Any]:
    field = "projection_inventory"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"discovery_complete", "targets", "absent_optional_projection_ids"},
        field,
    )
    if payload.get("discovery_complete") is not True:
        raise RequestShapeError(f"{field}.discovery_complete must be true")
    targets = [
        _normalize_projection_target(item, f"{field}.targets[{index}]", study_id=study_id)
        for index, item in enumerate(sequence(payload.get("targets"), f"{field}.targets"))
    ]
    roles = [item["role"] for item in targets]
    if len(roles) != len(set(roles)):
        raise RequestShapeError(f"{field}.targets contains duplicate roles")
    expected_order = [role for role in _TARGET_ROLE_ORDER if role in set(roles)]
    if roles != expected_order:
        raise RequestShapeError(f"{field}.targets must follow declared projection order")
    missing = sorted(_REQUIRED_TARGET_ROLES - set(roles))
    if missing:
        raise RequestShapeError(f"{field}.targets missing required roles: {', '.join(missing)}")
    absent = text_list(
        payload.get("absent_optional_projection_ids"),
        f"{field}.absent_optional_projection_ids",
    )
    unknown_absent = sorted(set(absent) - _OPTIONAL_TARGET_ROLES)
    if unknown_absent:
        raise RequestShapeError(
            f"{field}.absent_optional_projection_ids contains unsupported roles: {', '.join(unknown_absent)}"
        )
    present_optional = set(roles) & _OPTIONAL_TARGET_ROLES
    if present_optional & set(absent):
        raise RequestShapeError(f"{field} optional role cannot be both present and absent")
    if present_optional | set(absent) != _OPTIONAL_TARGET_ROLES:
        raise RequestShapeError(f"{field} must account for every optional role")
    return {
        "discovery_complete": True,
        "targets": targets,
        "absent_optional_projection_ids": sorted(absent),
        "inventory_fingerprint": _json_fingerprint(
            {"targets": targets, "absent_optional_projection_ids": sorted(absent)}
        ),
    }


def _normalize_projection_target(value: Any, field: str, *, study_id: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"projection_id", "root", "relative_path", "ref", "sha256", "byte_size", "record"}, field)
    role = enum_text(
        payload.get("projection_id"),
        f"{field}.projection_id",
        _REQUIRED_TARGET_ROLES | _OPTIONAL_TARGET_ROLES,
    )
    root = enum_text(payload.get("root"), f"{field}.root", {"workspace", "work_item"})
    source_relative_path = _relative_path(
        payload.get("relative_path"), f"{field}.relative_path"
    )
    target_relative_path = (
        source_relative_path
        if root == "workspace"
        else f"studies/{study_id}/{source_relative_path}"
    )
    current_byte_size = integer(payload.get("byte_size"), f"{field}.byte_size")
    if current_byte_size < 1:
        raise RequestShapeError(f"{field}.byte_size must be positive")
    return {
        "role": role,
        "root": root,
        "source_relative_path": source_relative_path,
        "relative_path": target_relative_path,
        "current_ref": _file_ref(payload.get("ref"), f"{field}.ref"),
        "current_sha256": _digest_text(payload.get("sha256"), f"{field}.sha256"),
        "current_byte_size": current_byte_size,
        "current_payload": mapping(payload.get("record"), f"{field}.record"),
    }


def _validate_target_paths(study_id: str, targets: Mapping[str, Mapping[str, Any]]) -> None:
    expected = {
        "study_lifecycle_current": f"studies/{study_id}/control/lifecycle.json",
        "workspace_lifecycle_latest": "runtime/artifacts/study_lifecycle_control/latest.json",
        "workspace_index": "workspace_index.json",
        "submission_status": f"studies/{study_id}/submission/STATUS.json",
        "publication_current_package_status": (
            f"studies/{study_id}/publication/current_package/STATUS.json"
        ),
        "stage_index": f"studies/{study_id}/control/stage_index.json",
        "workspace_latest_status": "reports/latest_status.json",
        "workspace_studies_index": "reports/studies_index.json",
    }
    for role, target in targets.items():
        if target["relative_path"] != expected[role]:
            raise RequestShapeError(f"projection target path does not match role {role}")


def _active_lifecycle_record(request: Mapping[str, Any]) -> dict[str, Any]:
    current = request["current_lifecycle"]["record"]
    wakeup = request["explicit_user_wakeup"]
    intake = request["reviewer_revision_intake"]
    evidence_refs = list(current["evidence_refs"])
    for ref in (intake["intake_ref"], wakeup["user_authority_ref"]):
        if ref not in evidence_refs:
            evidence_refs.append(ref)
    return {
        "schema_version": "mas.study_lifecycle_control.v1",
        "surface_kind": "study_lifecycle_control",
        "study_id": current["study_id"],
        "lifecycle_state": "active",
        "business_status": "active",
        "generation": current["generation"] + 1,
        "recorded_at": wakeup["requested_at"],
        "materialized_at": wakeup["requested_at"],
        "reason_code": wakeup["reason_code"],
        "reason_summary": wakeup["reason_summary"],
        "source_kind": "explicit_user_reviewer_revision_wakeup",
        "source_ref": wakeup["user_authority_ref"],
        "evidence_refs": evidence_refs,
        "lifecycle_ref": "control/lifecycle.json",
        "current_stage_id": None,
        "current_stage_status": None,
        "current_stage_policy": "project_current_runtime_stage",
        "milestone_package_delivered": current["milestone_package_delivered"],
        "submission_ready": False,
        "package_status": current["package_status"],
        "next_action": {
            "surface_kind": "mas_lifecycle_action",
            "action_id": "continue_current_study_line",
            "action_type": "agent_action",
            "owner": "MedAutoScience",
            "status": "active",
            "summary": "Continue the current study line through the canonical MAS route.",
        },
        "resume_policy": {
            "policy_id": "automatic_allowed",
            "auto_resume_allowed": True,
            "explicit_user_wakeup_required": False,
            "allow_stopped_relaunch_required": False,
        },
        "authority_boundary": deepcopy(current["authority_boundary"]),
    }


def _reactivation_receipt(
    request: Mapping[str, Any], after_lifecycle: Mapping[str, Any]
) -> dict[str, Any]:
    current = request["current_lifecycle"]
    wakeup = request["explicit_user_wakeup"]
    intake = request["reviewer_revision_intake"]
    authority_context = request["authority_context"]
    gates = ["explicit_user_wakeup"]
    if current["record"]["lifecycle_state"] == "stopped":
        gates.append("allow_stopped_relaunch")
    core = {
        "receipt_kind": "mas_study_lifecycle_reactivation_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "study_id": request["study_identity"]["study_id"],
        "handler_call_ref": authority_context["handler_call_ref"],
        "owner_ledger_ref": authority_context["owner_ledger_ref"],
        "original_admission_request_ref": authority_context[
            "original_admission_request_ref"
        ],
        "original_admission_request_sha256": authority_context[
            "original_admission_request_sha256"
        ],
        "admission_scope_id": authority_context["admission_scope_id"],
        "requested_action_id": authority_context["requested_action_id"],
        "requested_run_id": authority_context["requested_run_id"],
        "original_invocation_sha256": authority_context[
            "original_invocation_sha256"
        ],
        "profile_ref": request["profile"]["profile_ref"],
        "profile_sha256": request["profile"]["profile_sha256"],
        "reviewer_revision_intake_ref": intake["intake_ref"],
        "reviewer_revision_intake_sha256": intake["intake_sha256"],
        "user_authority_ref": wakeup["user_authority_ref"],
        "user_authority_sha256": wakeup["user_authority_sha256"],
        "revision_checklist_ref": intake["record"]["revision_checklist_ref"],
        "revision_checklist_sha256": intake["record"]["revision_checklist_sha256"],
        "independent_review_packet_ref": intake["record"][
            "independent_review_packet_ref"
        ],
        "independent_review_packet_sha256": intake["record"][
            "independent_review_packet_sha256"
        ],
        "first_owning_stage_id": intake["record"]["first_owning_stage_id"],
        "allowed_revision_scope": deepcopy(
            intake["record"]["allowed_revision_scope"]
        ),
        "projection_inventory_fingerprint": request["projection_inventory"][
            "inventory_fingerprint"
        ],
        "from_state": current["record"]["lifecycle_state"],
        "from_generation": current["record"]["generation"],
        "from_sha256": current["lifecycle_sha256"],
        "to_state": "active",
        "to_generation": after_lifecycle["generation"],
        "after_sha256": _raw_bytes_sha256(canonical_json_bytes(after_lifecycle)),
        "recorded_at": after_lifecycle["recorded_at"],
        "explicit_user_wakeup": True,
        "allow_stopped_relaunch": wakeup["allow_stopped_relaunch"],
        "satisfied_gate_ids": gates,
        "authorizes_lifecycle_transition": True,
        "authorizes_stage_selection": False,
        "authorizes_publication_or_submission": False,
        "authorizes_attempt_admission_without_materialization": False,
        "requires_opl_cas_materialization_receipt": True,
        "requires_no_in_progress_materialization_journal": True,
        "materialization_semantics": "journaled_all_or_rollback",
        "provider_completion_is_domain_completion": False,
    }
    receipt_fingerprint = fingerprint(core)
    receipt_ref = (
        "mas-study-lifecycle-reactivation:"
        f"{receipt_fingerprint.removeprefix('sha256:')}"
    )
    return {
        **core,
        "receipt_ref": receipt_ref,
        "receipt_fingerprint": receipt_fingerprint,
    }


def _materialization_operations(
    request: Mapping[str, Any],
    *,
    after_lifecycle: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> list[dict[str, Any]]:
    targets = {
        item["role"]: item for item in request["projection_inventory"]["targets"]
    }
    current = request["current_lifecycle"]["record"]
    old_state = current["lifecycle_state"]
    study_id = request["study_identity"]["study_id"]
    event_time = after_lifecycle["recorded_at"]
    generation = after_lifecycle["generation"]

    updated_by_role: dict[str, dict[str, Any]] = {
        "study_lifecycle_current": deepcopy(after_lifecycle),
        "workspace_lifecycle_latest": _update_workspace_lifecycle(
            targets["workspace_lifecycle_latest"]["current_payload"],
            current=current,
            after=after_lifecycle,
        ),
        "workspace_index": _update_workspace_index(
            targets["workspace_index"]["current_payload"],
            current=current,
            after=after_lifecycle,
        ),
        "submission_status": _update_status_projection(
            targets["submission_status"]["current_payload"],
            old_state=old_state,
            role="submission_status",
            after=after_lifecycle,
        ),
    }
    if "workspace_studies_index" in targets:
        updated_by_role["workspace_studies_index"] = _update_workspace_index(
            targets["workspace_studies_index"]["current_payload"],
            current=current,
            after=after_lifecycle,
        )
    if "workspace_latest_status" in targets:
        updated_by_role["workspace_latest_status"] = _update_workspace_latest_status(
            targets["workspace_latest_status"]["current_payload"],
            updated_workspace_index=updated_by_role["workspace_index"],
            event_time=event_time,
        )
    if "publication_current_package_status" in targets:
        updated_by_role["publication_current_package_status"] = _update_status_projection(
            targets["publication_current_package_status"]["current_payload"],
            old_state=old_state,
            role="publication_current_package_status",
            after=after_lifecycle,
        )
    if "stage_index" in targets:
        updated_by_role["stage_index"] = _update_stage_index(
            targets["stage_index"]["current_payload"],
            old_state=old_state,
            study_id=study_id,
        )

    operations = []
    for role in _TARGET_ROLE_ORDER:
        target = targets.get(role)
        if target is None:
            continue
        operations.append(
            _replace_operation(target, updated_by_role[role])
        )

    stamp = _history_stamp(event_time)
    history_targets = (
        (
            f"studies/{study_id}/artifacts/controller/lifecycle_control/history/"
            f"{stamp}-g{generation:04d}.json",
            after_lifecycle,
        ),
        (
            f"studies/{study_id}/artifacts/controller/lifecycle_control/"
            f"reactivation_receipts/{stamp}-g{generation:04d}.json",
            receipt,
        ),
        (
            "runtime/artifacts/study_lifecycle_control/history/"
            f"{stamp}-{study_id}-g{generation:04d}.json",
            updated_by_role["workspace_lifecycle_latest"],
        ),
    )
    operations.extend(_create_operation(path, payload) for path, payload in history_targets)
    paths = [operation["target_relative_path"] for operation in operations]
    if len(paths) != len(set(paths)):
        raise ProjectionCurrentnessError("materialization target paths are not unique")
    return operations


def _update_workspace_lifecycle(
    value: Mapping[str, Any],
    *,
    current: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, "workspace_lifecycle_latest.current_payload"))
    if payload.get("schema_version") != "mas.workspace_study_lifecycle_control.v1":
        raise ProjectionCurrentnessError("workspace lifecycle schema is unsupported")
    studies = sequence(payload.get("studies"), "workspace lifecycle studies")
    matches = [
        index
        for index, item in enumerate(studies)
        if isinstance(item, Mapping) and item.get("study_id") == current["study_id"]
    ]
    if len(matches) != 1:
        raise ProjectionCurrentnessError(
            "workspace lifecycle must contain exactly one current study record"
        )
    if dict(studies[matches[0]]) != dict(current):
        raise ProjectionCurrentnessError(
            "workspace lifecycle study record does not match exact current lifecycle"
        )
    studies[matches[0]] = deepcopy(after)
    payload["studies"] = studies
    payload["status_counts"] = _updated_status_counts(
        payload.get("status_counts"), current["lifecycle_state"]
    )
    payload["changed_study_id"] = current["study_id"]
    payload["changed_generation"] = after["generation"]
    payload["recorded_at"] = after["recorded_at"]
    return payload


def _update_workspace_index(
    value: Mapping[str, Any],
    *,
    current: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, "workspace_index.current_payload"))
    studies = sequence(payload.get("studies"), "workspace index studies")
    matches = [
        index
        for index, item in enumerate(studies)
        if isinstance(item, Mapping) and item.get("study_id") == current["study_id"]
    ]
    if len(matches) != 1:
        raise ProjectionCurrentnessError(
            "workspace index must contain exactly one current study entry"
        )
    study = dict(studies[matches[0]])
    for field in ("status", "business_status", "lifecycle_state"):
        if study.get(field) != current["lifecycle_state"]:
            raise ProjectionCurrentnessError(
                f"workspace index {field} does not match current lifecycle"
            )
    study.update(
        {
            "status": "active",
            "business_status": "active",
            "lifecycle_state": "active",
            "auto_resume_allowed": True,
            "lifecycle_reason_code": after["reason_code"],
            "lifecycle_reason_summary": after["reason_summary"],
            "next_action": deepcopy(after["next_action"]),
            "resume_policy": deepcopy(after["resume_policy"]),
        }
    )
    studies[matches[0]] = study
    payload["studies"] = studies
    payload["status_counts"] = _updated_status_counts(
        payload.get("status_counts"), current["lifecycle_state"]
    )
    payload["recorded_at"] = after["recorded_at"]
    return payload


def _update_workspace_latest_status(
    value: Mapping[str, Any],
    *,
    updated_workspace_index: Mapping[str, Any],
    event_time: str,
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, "workspace_latest_status.current_payload"))
    payload["status_counts"] = deepcopy(updated_workspace_index["status_counts"])
    payload["next_required_actions"] = list(
        dict.fromkeys(
            item["next_action"]["action_id"]
            for item in updated_workspace_index["studies"]
            if isinstance(item, Mapping)
            and isinstance(item.get("next_action"), Mapping)
            and isinstance(item["next_action"].get("action_id"), str)
        )
    )
    payload["recorded_at"] = event_time
    return payload


def _update_status_projection(
    value: Mapping[str, Any], *, old_state: str, role: str, after: Mapping[str, Any]
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, f"{role}.current_payload"))
    if payload.get("lifecycle_state") != old_state:
        raise ProjectionCurrentnessError(
            f"{role} lifecycle_state does not match current lifecycle"
        )
    if payload.get("submission_ready") is not False:
        raise ProjectionCurrentnessError(f"{role} unexpectedly claims submission ready")
    if "promotion_allowed" in payload and payload.get("promotion_allowed") is not False:
        raise ProjectionCurrentnessError(f"{role} unexpectedly permits promotion")
    payload["lifecycle_state"] = "active"
    if "reason" in payload:
        payload["reason"] = after["reason_summary"]
    if "reason_code" in payload:
        payload["reason_code"] = after["reason_code"]
    if "reason_summary" in payload:
        payload["reason_summary"] = after["reason_summary"]
    if "recorded_at" in payload:
        payload["recorded_at"] = after["recorded_at"]
    return payload


def _update_stage_index(
    value: Mapping[str, Any], *, old_state: str, study_id: str
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, "stage_index.current_payload"))
    if payload.get("study_id") != study_id:
        raise ProjectionCurrentnessError("stage index study_id does not match")
    if payload.get("lifecycle_state") != old_state:
        raise ProjectionCurrentnessError(
            "stage index lifecycle_state does not match current lifecycle"
        )
    payload["lifecycle_state"] = "active"
    return payload


def _updated_status_counts(value: Any, old_state: str) -> dict[str, int]:
    counts = mapping(value, "status_counts")
    normalized: dict[str, int] = {}
    for key, count in counts.items():
        state = text(key, "status_counts key")
        normalized[state] = integer(count, f"status_counts.{state}")
    if normalized.get(old_state, 0) < 1:
        raise ProjectionCurrentnessError(
            f"status_counts does not contain the current {old_state} study"
        )
    normalized[old_state] -= 1
    if normalized[old_state] == 0:
        normalized.pop(old_state)
    normalized["active"] = normalized.get("active", 0) + 1
    return normalized


def _replace_operation(
    target: Mapping[str, Any], after_json: Mapping[str, Any]
) -> dict[str, Any]:
    after_bytes = canonical_json_bytes(after_json)
    return {
        "target_relative_path": target["relative_path"],
        "precondition": {
            "kind": "existing_exact",
            "sha256": target["current_sha256"],
            "byte_size": target["current_byte_size"],
        },
        "replacement_bytes_base64": base64.b64encode(after_bytes).decode("ascii"),
        "replacement_sha256": _raw_bytes_sha256(after_bytes),
        "replacement_byte_size": len(after_bytes),
    }


def _create_operation(path: str, after_json: Mapping[str, Any]) -> dict[str, Any]:
    normalized_path = _relative_path(path, "history target path")
    after_bytes = canonical_json_bytes(after_json)
    return {
        "target_relative_path": normalized_path,
        "precondition": {"kind": "absent"},
        "replacement_bytes_base64": base64.b64encode(after_bytes).decode("ascii"),
        "replacement_sha256": _raw_bytes_sha256(after_bytes),
        "replacement_byte_size": len(after_bytes),
    }


def _cas_authorization(
    *,
    request_id: str,
    operations_sha256: str,
    authority_receipt_ref: str,
    satisfied_gate_ids: list[str],
) -> dict[str, Any]:
    core = {
        "surface_kind": "mas_lifecycle_cas_mutation_authorization",
        "version": "mas-lifecycle-cas-mutation-authorization.v1",
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_id": "medautoscience",
        "operations_sha256": operations_sha256,
        "authorized": True,
        "authority_receipt_ref": authority_receipt_ref,
        "satisfied_gate_ids": list(satisfied_gate_ids),
    }
    authorization_fingerprint = fingerprint(core)
    return {
        **core,
        "authorization_ref": (
            "mas-lifecycle-cas-authorization:"
            f"{authorization_fingerprint.removeprefix('sha256:')}"
        ),
        "authorization_fingerprint": authorization_fingerprint,
    }


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
    decision_fingerprint = fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-study-lifecycle-reactivation-decision:"
            f"{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }


def _timestamp(value: Any, field: str) -> str:
    raw = text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise RequestShapeError(f"{field} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise RequestShapeError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _relative_path(value: Any, field: str) -> str:
    path = text(value, field)
    parts = path.split("/")
    if path.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise RequestShapeError(f"{field} must be a safe workspace-relative path")
    return path


def _file_ref(value: Any, field: str) -> str:
    ref = text(value, field)
    if not ref.startswith("file:///"):
        raise RequestShapeError(f"{field} must be an exact file URL")
    return ref


def _digest_text(value: Any, field: str) -> str:
    digest = text(value, field).lower().removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise RequestShapeError(f"{field} must be a SHA-256 digest")
    return digest


def _required_false(value: Any, field: str) -> bool:
    if value is not False:
        raise RequestShapeError(f"{field} must be false")
    return False


def _normalized_instruction_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestShapeError(f"{field} must be non-empty normalized text")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value != normalized:
        raise RequestShapeError(
            f"{field} must use LF newlines and have no surrounding whitespace"
        )
    return normalized


def _history_stamp(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("+", "").replace(".", "")


def _json_fingerprint(value: Any) -> str:
    body = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _bytes_sha256(body)


def _bytes_sha256(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _raw_bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


__all__ = ["evaluate_study_lifecycle_reactivation_authority"]
