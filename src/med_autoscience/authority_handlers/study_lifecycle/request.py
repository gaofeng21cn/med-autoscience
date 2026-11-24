"""Normalize exact study lifecycle reactivation inputs."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from copy import deepcopy
from typing import Annotated, Any

from pydantic import PlainValidator, StrictBool, model_validator

from .._record_validation import (
    NonEmptyStr,
    NonNegativeInt,
    PositiveInt,
    RequestShapeError,
    StrictRecordModel,
    UniqueNonEmptyStrList,
    enum_field,
    exact_int_field,
    exact_json_object,
    exact_str_field,
    mapping,
    text,
    validate_record_dict,
    validate_record_model,
)
from .constants import (
    _INACTIVE_STATES,
    _LIFECYCLE_STATES,
    _PUBLIC_STAGE_ACTION_IDS,
    _SAFE_SEGMENT,
    REQUEST_KIND,
    SCHEMA_VERSION,
)
from .primitives import (
    _digest_text,
    _file_ref,
    _json_deep_equal,
    _normalized_instruction_text,
    _required_false,
    _timestamp,
    _timestamp_instant,
)
from .projection import (
    _normalize_projection_inventory,
    _normalize_projection_target,  # noqa: F401 - preserve the request facade
    _projection_target_path,  # noqa: F401 - preserve the request facade
    _validate_target_paths,
)


def _validate_safe_segment(value: Any) -> str:
    segment = text(value, "__FIELD__")
    if not _SAFE_SEGMENT.fullmatch(segment):
        raise RequestShapeError("__FIELD__ must be one safe path segment")
    return segment


def _validate_file_ref(value: Any) -> str:
    return _file_ref(value, "__FIELD__")


def _validate_digest_text(value: Any) -> str:
    return _digest_text(value, "__FIELD__")


def _validate_timestamp(value: Any) -> str:
    return _timestamp(value, "__FIELD__")


def _validate_required_false(value: Any) -> bool:
    return _required_false(value, "__FIELD__")


def _validate_required_true(value: Any) -> bool:
    if value is not True:
        raise RequestShapeError("__FIELD__ must be true")
    return True


def _validate_instruction_text(value: Any) -> str:
    return _normalized_instruction_text(value, "__FIELD__")


_SafeSegmentStr = Annotated[str, PlainValidator(_validate_safe_segment)]
_FileRefStr = Annotated[str, PlainValidator(_validate_file_ref)]
_DigestStr = Annotated[str, PlainValidator(_validate_digest_text)]
_TimestampStr = Annotated[str, PlainValidator(_validate_timestamp)]
_RequiredFalseBool = Annotated[bool, PlainValidator(_validate_required_false)]
_RequiredTrueBool = Annotated[bool, PlainValidator(_validate_required_true)]
_InstructionTextStr = Annotated[str, PlainValidator(_validate_instruction_text)]


class _StudyLifecycleReactivationEnvelopeModel(StrictRecordModel):
    study_id: _SafeSegmentStr
    reactivation_request: Any
    authority_context: Any
    study_identity: Any
    current_lifecycle: Any
    user_authority: Any
    reviewer_revision_intake: Any
    profile: Any
    projection_inventory: Any


class _ReactivationRequestModel(StrictRecordModel):
    user_authority_ref: _FileRefStr
    user_authority_sha256: _DigestStr
    reviewer_revision_intake_ref: _FileRefStr
    reviewer_revision_intake_sha256: _DigestStr
    current_lifecycle_ref: _FileRefStr
    current_lifecycle_sha256: _DigestStr
    profile_ref: _FileRefStr
    profile_sha256: _DigestStr
    observed_lifecycle_state: enum_field(_INACTIVE_STATES)
    observed_lifecycle_generation: NonNegativeInt
    explicit_user_wakeup: StrictBool
    allow_stopped_relaunch: StrictBool
    requested_at: _TimestampStr
    reason_code: exact_str_field("reviewer_revision_reactivation")
    reason_summary: NonEmptyStr


class _AuthorityContextModel(StrictRecordModel):
    handler_call_ref: NonEmptyStr
    owner_ledger_ref: NonEmptyStr
    original_admission_request_ref: NonEmptyStr
    original_admission_request_sha256: _DigestStr
    admission_scope_id: NonEmptyStr
    requested_action_id: enum_field(_PUBLIC_STAGE_ACTION_IDS)
    requested_run_id: NonEmptyStr
    original_invocation_sha256: _DigestStr


class _AdmissionScopeModel(StrictRecordModel):
    scope_id: NonEmptyStr
    requested_action_id: enum_field(_PUBLIC_STAGE_ACTION_IDS)
    single_use: _RequiredTrueBool


class _StudyIdentityModel(StrictRecordModel):
    study_id: _SafeSegmentStr
    work_item_root_ref: _FileRefStr
    lifecycle_ref: _FileRefStr
    descriptor_domain_id: enum_field({"medautoscience"})


class _CurrentLifecycleEnvelopeModel(StrictRecordModel):
    lifecycle_ref: _FileRefStr
    lifecycle_sha256: _DigestStr
    lifecycle_bytes_base64: Any
    lifecycle_byte_size: Any
    record: Any


class _LifecycleRecordModel(StrictRecordModel):
    authority_boundary: Any
    business_status: NonEmptyStr
    current_stage_id: Any
    current_stage_policy: NonEmptyStr
    current_stage_status: Any
    evidence_refs: UniqueNonEmptyStrList
    generation: PositiveInt
    lifecycle_ref: exact_str_field("control/lifecycle.json")
    lifecycle_state: enum_field(_LIFECYCLE_STATES)
    materialized_at: _TimestampStr
    milestone_package_delivered: StrictBool
    next_action: Any
    package_status: NonEmptyStr
    reason_code: NonEmptyStr
    reason_summary: NonEmptyStr
    recorded_at: _TimestampStr
    resume_policy: Any
    schema_version: exact_str_field(
        "mas.study_lifecycle_control.v1",
        message="__FIELD__ is unsupported",
    )
    source_kind: NonEmptyStr
    source_ref: NonEmptyStr
    study_id: NonEmptyStr
    submission_ready: _RequiredFalseBool
    surface_kind: exact_str_field(
        "study_lifecycle_control",
        message="__FIELD__ is unsupported",
    )

    @model_validator(mode="after")
    def _validate_lifecycle_invariants(self) -> _LifecycleRecordModel:
        if self.business_status != self.lifecycle_state:
            raise RequestShapeError(
                "__FIELD__.business_status must match lifecycle_state"
            )
        if self.lifecycle_state in _INACTIVE_STATES and (
            self.current_stage_id is not None or self.current_stage_status is not None
        ):
            raise RequestShapeError(
                "__FIELD__ inactive state cannot carry a current stage"
            )
        mapping(self.next_action, "__FIELD__.next_action")
        mapping(self.resume_policy, "__FIELD__.resume_policy")
        boundary = mapping(self.authority_boundary, "__FIELD__.authority_boundary")
        if (
            boundary.get("truth_owner") != "MedAutoScience"
            or boundary.get("domain_truth") is not True
        ):
            raise RequestShapeError(
                "__FIELD__.authority_boundary must retain MAS domain truth"
            )
        return self


class _RevisionIntakeEnvelopeModel(StrictRecordModel):
    intake_ref: _FileRefStr
    intake_sha256: _DigestStr
    intake_bytes_base64: Any
    intake_byte_size: Any
    record: Any


class _RevisionIntakeRecordModel(StrictRecordModel):
    surface_kind: exact_str_field(
        "mas_reviewer_revision_task_intake",
        message="__FIELD__ is unsupported",
    )
    schema_version: exact_int_field(1)
    task_intake_kind: exact_str_field("reviewer_revision")
    study_id: NonEmptyStr
    status: enum_field({"draft", "accepted", "active", "consumed", "superseded"})
    user_authority_ref: _FileRefStr
    user_authority_sha256: _DigestStr
    recorded_at: _TimestampStr
    request_summary: NonEmptyStr
    revision_checklist_ref: _FileRefStr
    revision_checklist_sha256: _DigestStr
    independent_review_packet_ref: _FileRefStr
    independent_review_packet_sha256: _DigestStr
    first_owning_stage_id: enum_field(_PUBLIC_STAGE_ACTION_IDS)
    allowed_revision_scope: UniqueNonEmptyStrList
    record_owner: enum_field({"MedAutoScience"})
    source_owner: enum_field({"user"})
    owner_receipt: _RequiredFalseBool


class _UserAuthorityEnvelopeModel(StrictRecordModel):
    authority_ref: _FileRefStr
    authority_sha256: _DigestStr
    authority_bytes_base64: Any
    authority_byte_size: Any
    record: Any


class _UserAuthorityRecordModel(StrictRecordModel):
    surface_kind: exact_str_field(
        "mas_explicit_user_authority_evidence",
        message="__FIELD__ is unsupported",
    )
    schema_version: exact_int_field(1)
    study_id: NonEmptyStr
    task_intake_kind: exact_str_field("reviewer_revision")
    status: exact_str_field("accepted")
    explicit_user_wakeup: StrictBool
    allow_stopped_relaunch: StrictBool
    recorded_at: _TimestampStr
    source_kind: exact_str_field("explicit_user_instruction")
    source_ref: NonEmptyStr
    instruction_text: _InstructionTextStr
    instruction_sha256: _DigestStr
    source_owner: enum_field({"user"})
    record_owner: enum_field({"MedAutoScience"})
    owner_receipt: _RequiredFalseBool

    @model_validator(mode="after")
    def _validate_instruction_digest(self) -> _UserAuthorityRecordModel:
        if (
            hashlib.sha256(self.instruction_text.encode("utf-8")).hexdigest()
            != self.instruction_sha256
        ):
            raise RequestShapeError(
                "__FIELD__.instruction_sha256 does not match normalized instruction_text"
            )
        return self


class _ProfileModel(StrictRecordModel):
    profile_ref: _FileRefStr
    profile_sha256: _DigestStr
    profile_byte_size: PositiveInt
    profile_body_utf8: Any

    @model_validator(mode="after")
    def _validate_profile_bytes(self) -> _ProfileModel:
        if not isinstance(self.profile_body_utf8, str) or not self.profile_body_utf8:
            raise RequestShapeError(
                "__FIELD__.profile_body_utf8 must be non-empty text"
            )
        profile_bytes = self.profile_body_utf8.encode("utf-8")
        if len(profile_bytes) != self.profile_byte_size:
            raise RequestShapeError(
                "__FIELD__.profile_byte_size does not match profile_body_utf8"
            )
        if hashlib.sha256(profile_bytes).hexdigest() != self.profile_sha256:
            raise RequestShapeError(
                "__FIELD__.profile_sha256 does not match profile_body_utf8"
            )
        return self


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    envelope = validate_record_model(
        _StudyLifecycleReactivationEnvelopeModel, request, "request"
    )
    study_id = envelope.study_id
    reactivation = _normalize_reactivation_request(envelope.reactivation_request)
    authority_context = _normalize_authority_context(envelope.authority_context)
    identity = _normalize_study_identity(envelope.study_identity)
    current_lifecycle = _normalize_current_lifecycle(envelope.current_lifecycle)
    user_authority = _normalize_user_authority(envelope.user_authority)
    intake = _normalize_revision_intake(envelope.reviewer_revision_intake)
    profile = _normalize_profile(envelope.profile)
    inventory = _normalize_projection_inventory(
        envelope.projection_inventory, study_id=study_id
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
        raise RequestShapeError(
            "current lifecycle study_id does not match study_identity"
        )
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
    for (
        name,
        requested_ref,
        requested_sha256,
        injected_ref,
        injected_sha256,
    ) in exact_bindings:
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
    return validate_record_dict(
        _ReactivationRequestModel, value, "reactivation_request"
    )


def _normalize_authority_context(value: Any) -> dict[str, Any]:
    return validate_record_dict(_AuthorityContextModel, value, "authority_context")


def _normalize_admission_scope(value: Any, field: str) -> dict[str, Any]:
    return validate_record_dict(_AdmissionScopeModel, value, field)


def _normalize_study_identity(value: Any) -> dict[str, str]:
    return validate_record_dict(_StudyIdentityModel, value, "study_identity")


def _normalize_current_lifecycle(value: Any) -> dict[str, Any]:
    field = "current_lifecycle"
    envelope = validate_record_model(_CurrentLifecycleEnvelopeModel, value, field)
    lifecycle_bytes_base64, lifecycle_byte_size, raw_record = exact_json_object(
        encoded_value=envelope.lifecycle_bytes_base64,
        byte_size_value=envelope.lifecycle_byte_size,
        expected_sha256=envelope.lifecycle_sha256,
        supplied_record=envelope.record,
        field=field,
    )
    return {
        "lifecycle_ref": envelope.lifecycle_ref,
        "lifecycle_sha256": envelope.lifecycle_sha256,
        "lifecycle_bytes_base64": lifecycle_bytes_base64,
        "lifecycle_byte_size": lifecycle_byte_size,
        "record": _normalize_lifecycle_record(raw_record),
    }


def _normalize_lifecycle_record(value: Any) -> dict[str, Any]:
    field = "current_lifecycle.record"
    payload = mapping(value, field)
    validated = validate_record_model(_LifecycleRecordModel, payload, field)
    normalized = deepcopy(payload)
    normalized["study_id"] = validated.study_id
    normalized["current_stage_policy"] = validated.current_stage_policy
    normalized["evidence_refs"] = validated.evidence_refs
    normalized["package_status"] = validated.package_status
    normalized["reason_code"] = validated.reason_code
    normalized["reason_summary"] = validated.reason_summary
    normalized["source_kind"] = validated.source_kind
    normalized["source_ref"] = validated.source_ref
    normalized["generation"] = validated.generation
    normalized["lifecycle_state"] = validated.lifecycle_state
    return normalized


def _normalize_revision_intake(value: Any) -> dict[str, Any]:
    field = "reviewer_revision_intake"
    envelope = validate_record_model(_RevisionIntakeEnvelopeModel, value, field)
    intake_bytes_base64, intake_byte_size, raw_record = exact_json_object(
        encoded_value=envelope.intake_bytes_base64,
        byte_size_value=envelope.intake_byte_size,
        expected_sha256=envelope.intake_sha256,
        supplied_record=envelope.record,
        field=field,
    )
    record = validate_record_dict(
        _RevisionIntakeRecordModel, raw_record, f"{field}.record"
    )
    return {
        "intake_ref": envelope.intake_ref,
        "intake_sha256": envelope.intake_sha256,
        "intake_bytes_base64": intake_bytes_base64,
        "intake_byte_size": intake_byte_size,
        "record": record,
    }


def _normalize_user_authority(value: Any) -> dict[str, Any]:
    field = "user_authority"
    envelope = validate_record_model(_UserAuthorityEnvelopeModel, value, field)
    authority_bytes_base64, authority_byte_size, raw_record = exact_json_object(
        encoded_value=envelope.authority_bytes_base64,
        byte_size_value=envelope.authority_byte_size,
        expected_sha256=envelope.authority_sha256,
        supplied_record=envelope.record,
        field=field,
    )
    record = validate_record_dict(
        _UserAuthorityRecordModel, raw_record, f"{field}.record"
    )
    return {
        "authority_ref": envelope.authority_ref,
        "authority_sha256": envelope.authority_sha256,
        "authority_bytes_base64": authority_bytes_base64,
        "authority_byte_size": authority_byte_size,
        "record": record,
    }


def _normalize_profile(value: Any) -> dict[str, Any]:
    return validate_record_dict(_ProfileModel, value, "profile")
