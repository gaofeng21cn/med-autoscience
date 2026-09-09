"""Normalize exact study lifecycle reactivation inputs."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
from typing import Any

from .._record_validation import (
    RequestShapeError,
    enum_text,
    exact_json_object,
    exact_keys,
    exact_ref,
    integer,
    mapping,
    sequence,
    text,
    text_list,
    typed_ref,
)
from .constants import (
    REQUEST_KIND,
    SCHEMA_VERSION,
    _INACTIVE_STATES,
    _LIFECYCLE_STATES,
    _OPTIONAL_TARGET_ROLES,
    _PUBLIC_STAGE_ACTION_IDS,
    _REQUIRED_TARGET_ROLES,
    _SAFE_SEGMENT,
    _TARGET_ROLE_ORDER,
)
from .primitives import (
    _digest_text,
    _file_ref,
    _json_deep_equal,
    _json_fingerprint,
    _normalized_instruction_text,
    _relative_path,
    _required_false,
    _timestamp,
    _timestamp_instant,
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
    if intake["record"]["recorded_at"] != wakeup["requested_at"]:
        raise RequestShapeError(
            "reviewer_revision intake recorded_at must match wakeup requested_at"
        )
    lifecycle = current_lifecycle["record"]
    requested_at = _timestamp_instant(wakeup["requested_at"])
    if requested_at <= _timestamp_instant(lifecycle["recorded_at"]):
        raise RequestShapeError(
            "wakeup requested_at must be strictly later than current lifecycle recorded_at"
        )
    if requested_at <= _timestamp_instant(lifecycle["materialized_at"]):
        raise RequestShapeError(
            "wakeup requested_at must be strictly later than current lifecycle materialized_at"
        )
    if (
        authority_context["requested_action_id"]
        != intake["record"]["first_owning_stage_id"]
    ):
        raise RequestShapeError(
            "authority_context requested_action_id must match reviewer_revision "
            "intake first_owning_stage_id"
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
    if not _json_deep_equal(
        lifecycle_target["current_payload"], current_lifecycle["record"]
    ):
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
    exact_keys(
        payload,
        {
            "lifecycle_ref",
            "lifecycle_sha256",
            "lifecycle_bytes_base64",
            "lifecycle_byte_size",
            "record",
        },
        field,
    )
    lifecycle_sha256 = _digest_text(
        payload["lifecycle_sha256"], f"{field}.lifecycle_sha256"
    )
    lifecycle_bytes_base64, lifecycle_byte_size, raw_record = (
        exact_json_object(
            encoded_value=payload["lifecycle_bytes_base64"],
            byte_size_value=payload["lifecycle_byte_size"],
            expected_sha256=lifecycle_sha256,
            supplied_record=payload["record"],
            field=field,
        )
    )
    return {
        "lifecycle_ref": _file_ref(
            payload["lifecycle_ref"], f"{field}.lifecycle_ref"
        ),
        "lifecycle_sha256": lifecycle_sha256,
        "lifecycle_bytes_base64": lifecycle_bytes_base64,
        "lifecycle_byte_size": lifecycle_byte_size,
        "record": _normalize_lifecycle_record(raw_record),
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
    exact_keys(
        payload,
        {
            "intake_ref",
            "intake_sha256",
            "intake_bytes_base64",
            "intake_byte_size",
            "record",
        },
        field,
    )
    intake_sha256 = _digest_text(
        payload["intake_sha256"], f"{field}.intake_sha256"
    )
    intake_bytes_base64, intake_byte_size, raw_record = (
        exact_json_object(
            encoded_value=payload["intake_bytes_base64"],
            byte_size_value=payload["intake_byte_size"],
            expected_sha256=intake_sha256,
            supplied_record=payload["record"],
            field=field,
        )
    )
    record_field = f"{field}.record"
    record = raw_record
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
        "intake_sha256": intake_sha256,
        "intake_bytes_base64": intake_bytes_base64,
        "intake_byte_size": intake_byte_size,
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
    authority_sha256 = _digest_text(
        payload["authority_sha256"], f"{field}.authority_sha256"
    )
    authority_bytes_base64, authority_byte_size, raw_record = (
        exact_json_object(
            encoded_value=payload["authority_bytes_base64"],
            byte_size_value=payload["authority_byte_size"],
            expected_sha256=authority_sha256,
            supplied_record=payload["record"],
            field=field,
        )
    )
    record_field = f"{field}.record"
    record = raw_record
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
        "authority_sha256": authority_sha256,
        "authority_bytes_base64": authority_bytes_base64,
        "authority_byte_size": authority_byte_size,
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
    exact_keys(
        payload,
        {
            "projection_id",
            "root",
            "relative_path",
            "ref",
            "sha256",
            "bytes_base64",
            "byte_size",
            "record",
        },
        field,
    )
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
    current_sha256 = _digest_text(payload.get("sha256"), f"{field}.sha256")
    current_bytes_base64, current_byte_size, current_payload = (
        exact_json_object(
            encoded_value=payload.get("bytes_base64"),
            byte_size_value=payload.get("byte_size"),
            expected_sha256=current_sha256,
            supplied_record=payload.get("record"),
            field=field,
        )
    )
    return {
        "role": role,
        "root": root,
        "source_relative_path": source_relative_path,
        "relative_path": target_relative_path,
        "current_ref": _file_ref(payload.get("ref"), f"{field}.ref"),
        "current_sha256": current_sha256,
        "current_bytes_base64": current_bytes_base64,
        "current_byte_size": current_byte_size,
        "current_payload": current_payload,
    }


def _validate_target_paths(study_id: str, targets: Mapping[str, Mapping[str, Any]]) -> None:
    for role, target in targets.items():
        if target["relative_path"] != _projection_target_path(role, study_id):
            raise RequestShapeError(f"projection target path does not match role {role}")


def _projection_target_path(role: str, study_id: str) -> str:
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
    return expected[role]
