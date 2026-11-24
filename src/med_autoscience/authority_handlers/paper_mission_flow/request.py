"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import model_validator

from .._generation_manifest import (
    normalize_generation_manifest,
    require_stage_scope,
)
from .._record_validation import (
    NonEmptyStr,
    NonNegativeInt,
    OptionalSha256Text,
    RequestShapeError,
    Sha256Text,
    StrictRecordModel,
    UniqueNonEmptyStrList,
    canonical_json_bytes,
    enum_field,
    exact_int_field,
    exact_keys,
    exact_ref_field,
    exact_ref_list_field,
    exact_str_field,
    fingerprint,
    mapping,
    optional_exact_ref_field,
    optional_typed_ref_field,
    sequence,
    text,
    typed_ref_field,
    typed_ref_list_field,
    validate_record_dict,
    validate_record_model,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)
from ..candidate_admission import normalize_candidate_admission_receipt
from .constants import (
    _REVISION_CONSUMPTION_AUTHORITY_BOUNDARY,
    REQUEST_KIND,
    SCHEMA_VERSION,
)
from .currentness import (
    _normalize_hard_gate,
    _normalize_repair,
    _normalize_review_currentness_receipt,
    _normalize_selected_build_currentness_authority,
)
from .validation import (
    _exact_ref_identity,
    _validate_review_currentness_receipt_ref,
    _validate_selected_build_currentness_authority,
)


class _PaperMissionRequestEnvelopeModel(StrictRecordModel):
    surface_kind: exact_str_field(
        REQUEST_KIND,
        message=f"surface_kind must be {REQUEST_KIND}",
    )
    schema_version: exact_int_field(
        SCHEMA_VERSION,
        message="schema_version must be integer 2",
    )
    host_context: Any
    mission: Any
    medical_evidence: Any
    generation_manifest: Any
    generation_manifest_ref: Any
    candidate_admissions: Any
    review_authority: Any
    repair_state: Any
    hard_gate: Any
    revision_consumption: Any = None
    selected_build_currentness_authority: Any = None


class _HostContextModel(StrictRecordModel):
    action_id: exact_str_field("paper_mission")
    run_ref: typed_ref_field("opl_stage_run")
    producer_attempt_ref: typed_ref_field("opl_stage_attempt")
    output_ref: exact_ref_field("opl_action_output")
    output_state: enum_field({"consumable", "no_output", "damaged", "failed"})
    build_dependency_currentness_authority_ref: exact_ref_field(
        "mas_build_dependency_currentness_authority"
    ) = None
    build_dependency_currentness_authority_issuer_attempt_ref: typed_ref_field(
        "opl_stage_attempt"
    ) = None

    @model_validator(mode="after")
    def _validate_authority_pair(self) -> _HostContextModel:
        has_ref = "build_dependency_currentness_authority_ref" in self.model_fields_set
        has_issuer = (
            "build_dependency_currentness_authority_issuer_attempt_ref"
            in self.model_fields_set
        )
        if has_ref != has_issuer:
            raise RequestShapeError(
                "host_context build dependency currentness authority refs must be "
                "supplied together"
            )
        return self


class _MissionModel(StrictRecordModel):
    program_id: NonEmptyStr
    study_id: NonEmptyStr
    mission_id: NonEmptyStr
    stage_id: NonEmptyStr
    stage_goal_ref: typed_ref_field("mas_stage_goal")


class _MedicalEvidenceModel(StrictRecordModel):
    source_readiness_status: enum_field({"ready", "not_ready", "unknown"})
    source_readiness_receipt_ref: optional_typed_ref_field(
        "mas_source_readiness_receipt"
    )
    claim_evidence_status: enum_field(
        {"aligned", "revision_required", "unsafe", "unknown"}
    )
    claim_boundary_ref: typed_ref_field("mas_claim_boundary")
    candidate_artifact_refs: typed_ref_list_field("mas_artifact")
    evidence_refs: typed_ref_list_field("mas_evidence")
    negative_result_refs: typed_ref_list_field("mas_negative_result")
    failed_path_refs: typed_ref_list_field("mas_failed_path")
    artifact_lineage_refs: typed_ref_list_field("mas_artifact_lineage")
    reproducibility_refs: typed_ref_list_field("mas_reproducibility")

    @model_validator(mode="after")
    def _validate_source_readiness_ref(self) -> _MedicalEvidenceModel:
        if (
            self.source_readiness_status == "ready"
            and self.source_readiness_receipt_ref is None
        ):
            raise RequestShapeError(
                "ready source status requires source_readiness_receipt_ref"
            )
        return self


class _CandidateAdmissionEntryModel(StrictRecordModel):
    receipt_ref: exact_ref_field("mas_candidate_admission_receipt")
    receipt: Any


class _MissionIdentityModel(StrictRecordModel):
    program_id: NonEmptyStr
    study_id: NonEmptyStr
    mission_id: NonEmptyStr


class _OplFindingLineageModel(StrictRecordModel):
    review_kind: enum_field({"initial_review", "finding_closure_review"})
    finding_ids: UniqueNonEmptyStrList
    findings_sha256: Sha256Text
    repair_map_sha256: OptionalSha256Text
    re_review_result_sha256: OptionalSha256Text

    @model_validator(mode="after")
    def _validate_lineage(self) -> _OplFindingLineageModel:
        if not self.finding_ids:
            raise RequestShapeError("__FIELD__.finding_ids must not be empty")
        self.finding_ids = sorted(self.finding_ids)
        if self.review_kind == "initial_review" and (
            self.repair_map_sha256 is not None
            or self.re_review_result_sha256 is not None
        ):
            raise RequestShapeError(
                "__FIELD__ initial_review must not carry repair or re-review hashes"
            )
        if self.review_kind == "finding_closure_review" and (
            self.repair_map_sha256 is None or self.re_review_result_sha256 is None
        ):
            raise RequestShapeError(
                "__FIELD__ finding_closure_review requires repair_map_sha256 and "
                "re_review_result_sha256"
            )
        return self


class _RevisionFindingClosureModel(StrictRecordModel):
    finding_id: NonEmptyStr
    status: enum_field({"closed", "partially_closed", "still_open"})
    evidence_refs: UniqueNonEmptyStrList

    @model_validator(mode="after")
    def _validate_evidence_refs(self) -> _RevisionFindingClosureModel:
        if not self.evidence_refs:
            raise RequestShapeError("__FIELD__.evidence_refs must not be empty")
        self.evidence_refs = sorted(self.evidence_refs)
        return self


class _RevisionConsumptionBindingModel(StrictRecordModel):
    surface_kind: exact_str_field("mas_revision_consumption_binding")
    schema_version: exact_int_field(1)
    current_accepted_or_active_revision_intake_refs: exact_ref_list_field(
        "opl_revision_intake"
    ) = None
    consumption_receipt_ref: exact_ref_field("mas_revision_consumption_receipt")
    consumption_receipt: Any


class _RevisionConsumptionReceiptModel(StrictRecordModel):
    receipt_kind: exact_str_field("mas_revision_consumption_receipt")
    schema_version: exact_int_field(1)
    owner: exact_str_field("MedAutoScience")
    authority_role: exact_str_field("revision_consumption_owner")
    mission_identity: _MissionIdentityModel
    generation_id: NonEmptyStr
    producer_attempt_ref: typed_ref_field("opl_stage_attempt")
    producer_output_ref: exact_ref_field("opl_action_output")
    applicability: enum_field({"not_applicable", "revision_consumed"})
    revision_intake_refs: exact_ref_list_field("opl_revision_intake")
    opl_review_receipt_ref: optional_exact_ref_field("opl_stage_review_receipt")
    opl_finding_lineage: _OplFindingLineageModel | None
    finding_closures: Any
    consumed_revision_refs: Any
    authority_boundary: Any
    receipt_id: NonEmptyStr
    receipt_size_bytes: NonNegativeInt
    receipt_fingerprint: Sha256Text


class _ReviewAuthorityModel(StrictRecordModel):
    review_request_ref: exact_ref_field("opl_action_output")
    currentness_receipt_ref: exact_ref_field("mas_review_currentness_receipt")
    currentness_receipt: Any


def _is_reviewer_revision(request: Mapping[str, Any]) -> bool:
    receipt = request["revision_consumption"]["consumption_receipt"]
    return receipt is not None and receipt["applicability"] == "revision_consumed"


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    envelope = validate_record_model(
        _PaperMissionRequestEnvelopeModel, request, "request"
    )
    present_fields = envelope.model_fields_set

    mission = _normalize_mission(envelope.mission)
    manifest = normalize_generation_manifest(envelope.generation_manifest)
    require_stage_scope(mission["stage_id"], manifest["manifest_scope"])
    manifest_ref = _exact_ref(
        envelope.generation_manifest_ref,
        "generation_manifest_ref",
        "mas_generation_manifest",
    )
    if (
        manifest_ref["sha256"] != manifest["generation_manifest_sha256"]
        or manifest_ref["size_bytes"] != manifest["generation_manifest_size_bytes"]
    ):
        raise RequestShapeError(
            "generation_manifest_ref size/hash does not match canonical manifest"
        )
    if (
        "revision_consumption" in present_fields
        and envelope.revision_consumption is None
    ):
        raise RequestShapeError("revision_consumption must be an object when supplied")
    selected_build = manifest.get("selected_build_binding")
    if (
        selected_build is not None
        and "selected_build_currentness_authority" not in present_fields
    ):
        raise RequestShapeError(
            "selected_build_currentness_authority is required for selected build binding"
        )
    if (
        selected_build is None
        and "selected_build_currentness_authority" in present_fields
    ):
        raise RequestShapeError(
            "selected_build_currentness_authority requires selected build binding"
        )
    host_context = _normalize_host_context(envelope.host_context)
    review_authority = _normalize_review_authority(envelope.review_authority)
    selected_build_authority = (
        _normalize_selected_build_currentness_authority(
            envelope.selected_build_currentness_authority
        )
        if selected_build is not None
        else None
    )
    normalized = {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "host_context": host_context,
        "mission": mission,
        "medical_evidence": _normalize_medical_evidence(envelope.medical_evidence),
        "generation_manifest": manifest,
        "generation_manifest_ref": manifest_ref,
        "candidate_admissions": _normalize_candidate_admissions(
            envelope.candidate_admissions
        ),
        "review_authority": review_authority,
        "selected_build_currentness_authority": selected_build_authority,
        "revision_consumption": _normalize_revision_consumption(
            envelope.revision_consumption
            if "revision_consumption" in present_fields
            else None
        ),
        "repair_state": _normalize_repair(envelope.repair_state),
        "hard_gate": _normalize_hard_gate(envelope.hard_gate),
    }
    currentness_version = normalized["review_authority"]["currentness_receipt"][
        "schema_version"
    ]
    if manifest["schema_version"] != currentness_version:
        raise RequestShapeError(
            "generation manifest and review currentness schema versions must match"
        )
    _validate_review_currentness_receipt_ref(normalized)
    _validate_selected_build_currentness_authority(normalized)
    return normalized


def _normalize_host_context(value: Any) -> dict[str, Any]:
    return validate_record_dict(_HostContextModel, value, "host_context")


def _normalize_mission(value: Any) -> dict[str, Any]:
    return validate_record_dict(_MissionModel, value, "mission")


def _normalize_medical_evidence(value: Any) -> dict[str, Any]:
    return validate_record_dict(_MedicalEvidenceModel, value, "medical_evidence")


def _normalize_candidate_admissions(value: Any) -> list[dict[str, Any]]:
    field = "candidate_admissions"
    admissions: list[dict[str, Any]] = []
    for index, item in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        entry = validate_record_model(_CandidateAdmissionEntryModel, item, item_field)
        receipt_ref = entry.receipt_ref
        receipt = normalize_candidate_admission_receipt(
            entry.receipt, f"{item_field}.receipt"
        )
        if (
            receipt_ref["ref"] != receipt["receipt_id"]
            or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
            or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
        ):
            raise RequestShapeError(
                f"{item_field}.receipt_ref does not match canonical receipt bytes"
            )
        admissions.append({"receipt_ref": receipt_ref, "receipt": receipt})
    identities = [
        (item["receipt_ref"]["ref"], item["receipt_ref"]["sha256"])
        for item in admissions
    ]
    candidates = [item["receipt"]["candidate_id"] for item in admissions]
    if len(identities) != len(set(identities)) or len(candidates) != len(
        set(candidates)
    ):
        raise RequestShapeError("candidate_admissions contains duplicate receipts")
    return admissions


def _normalize_revision_consumption(value: Any) -> dict[str, Any]:
    field = "revision_consumption"
    if value is None:
        return {
            "binding_status": "legacy_unbound",
            "current_accepted_or_active_revision_intake_refs": None,
            "consumption_receipt_ref": None,
            "consumption_receipt": None,
        }
    binding = validate_record_model(_RevisionConsumptionBindingModel, value, field)
    current_revision_intake_refs = None
    if (
        "current_accepted_or_active_revision_intake_refs"
        in binding.model_fields_set
    ):
        current_revision_intake_refs = sorted(
            binding.current_accepted_or_active_revision_intake_refs,
            key=_exact_ref_identity,
        )
    receipt_ref = binding.consumption_receipt_ref
    receipt = _normalize_revision_consumption_receipt(
        binding.consumption_receipt,
        f"{field}.consumption_receipt",
    )
    if (
        receipt_ref["ref"] != receipt["receipt_id"]
        or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
        or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
    ):
        raise RequestShapeError(
            f"{field}.consumption_receipt_ref does not match canonical receipt bytes"
        )
    return {
        "binding_status": "bound",
        "surface_kind": "mas_revision_consumption_binding",
        "schema_version": 1,
        "current_accepted_or_active_revision_intake_refs": (
            current_revision_intake_refs
        ),
        "consumption_receipt_ref": receipt_ref,
        "consumption_receipt": receipt,
    }


def _normalize_revision_consumption_receipt(
    value: Any,
    field: str,
) -> dict[str, Any]:
    parsed = validate_record_model(_RevisionConsumptionReceiptModel, value, field)
    mission_identity = parsed.mission_identity.model_dump()
    applicability = parsed.applicability
    revision_intake_refs = sorted(
        parsed.revision_intake_refs, key=_exact_ref_identity
    )
    opl_review_receipt_ref = parsed.opl_review_receipt_ref
    finding_lineage = (
        parsed.opl_finding_lineage.model_dump()
        if parsed.opl_finding_lineage is not None
        else None
    )
    finding_closures = _normalize_revision_finding_closures(
        parsed.finding_closures,
        f"{field}.finding_closures",
    )
    consumed_revision_refs = _normalize_consumed_revision_refs(
        parsed.consumed_revision_refs,
        f"{field}.consumed_revision_refs",
    )
    authority_boundary = mapping(
        parsed.authority_boundary, f"{field}.authority_boundary"
    )
    exact_keys(
        authority_boundary,
        set(_REVISION_CONSUMPTION_AUTHORITY_BOUNDARY),
        f"{field}.authority_boundary",
    )
    if authority_boundary != _REVISION_CONSUMPTION_AUTHORITY_BOUNDARY:
        raise RequestShapeError(
            f"{field}.authority_boundary must preserve the non-authoritative receipt boundary"
        )

    if applicability == "not_applicable":
        if any(
            (
                revision_intake_refs,
                opl_review_receipt_ref is not None,
                finding_lineage is not None,
                finding_closures,
                consumed_revision_refs,
            )
        ):
            raise RequestShapeError(
                f"{field} not_applicable receipt cannot carry revision inputs or findings"
            )
    else:
        if not revision_intake_refs:
            raise RequestShapeError(
                f"{field}.revision_intake_refs must not be empty when revision is consumed"
            )
        if opl_review_receipt_ref is None or finding_lineage is None:
            raise RequestShapeError(
                f"{field}.opl_review_receipt_ref and opl_finding_lineage are required "
                "when revision is consumed"
            )
        expected_consumed_refs = list(revision_intake_refs)
        expected_consumed_refs.append(opl_review_receipt_ref)
        expected_consumed_refs.sort(
            key=lambda item: (item["kind"], *_exact_ref_identity(item))
        )
        if consumed_revision_refs != expected_consumed_refs:
            raise RequestShapeError(
                f"{field}.consumed_revision_refs must exactly equal revision intake "
                "and review receipt refs"
            )
        if finding_lineage["review_kind"] != "finding_closure_review":
            raise RequestShapeError(
                f"{field}.opl_finding_lineage must be a finding_closure_review"
            )
        finding_ids = set(finding_lineage["finding_ids"])
        closure_ids = {item["finding_id"] for item in finding_closures}
        if finding_ids != closure_ids:
            raise RequestShapeError(
                f"{field}.finding_closures must cover every OPL finding_lineage id "
                "exactly once"
            )

    core = {
        "receipt_kind": "mas_revision_consumption_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "revision_consumption_owner",
        "mission_identity": mission_identity,
        "generation_id": parsed.generation_id,
        "producer_attempt_ref": parsed.producer_attempt_ref,
        "producer_output_ref": parsed.producer_output_ref,
        "applicability": applicability,
        "revision_intake_refs": revision_intake_refs,
        "opl_review_receipt_ref": opl_review_receipt_ref,
        "opl_finding_lineage": finding_lineage,
        "finding_closures": finding_closures,
        "consumed_revision_refs": consumed_revision_refs,
        "authority_boundary": dict(_REVISION_CONSUMPTION_AUTHORITY_BOUNDARY),
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = (
        f"mas-revision-consumption:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if parsed.receipt_id != expected_id:
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if parsed.receipt_size_bytes != expected_size:
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    if parsed.receipt_fingerprint != expected_fingerprint:
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_opl_finding_lineage(
    value: Any,
    field: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    return validate_record_dict(_OplFindingLineageModel, value, field)


def _normalize_revision_finding_closures(
    value: Any,
    field: str,
) -> list[dict[str, Any]]:
    closures = [
        validate_record_dict(_RevisionFindingClosureModel, item, f"{field}[{index}]")
        for index, item in enumerate(sequence(value, field))
    ]
    finding_ids = [item["finding_id"] for item in closures]
    if len(finding_ids) != len(set(finding_ids)):
        raise RequestShapeError(f"{field} contains duplicate finding_id values")
    closures.sort(key=lambda item: item["finding_id"])
    return closures


def _normalize_consumed_revision_refs(
    value: Any,
    field: str,
) -> list[dict[str, Any]]:
    refs = []
    for index, item in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        payload = mapping(item, item_field)
        kind = text(payload.get("kind"), f"{item_field}.kind")
        if kind not in {"opl_revision_intake", "opl_stage_review_receipt"}:
            raise RequestShapeError(
                f"{item_field}.kind must be opl_revision_intake or opl_stage_review_receipt"
            )
        refs.append(_exact_ref(payload, item_field, kind))
    identities = [(item["kind"], *_exact_ref_identity(item)) for item in refs]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate refs")
    refs.sort(key=lambda item: (item["kind"], *_exact_ref_identity(item)))
    return refs


def _normalize_review_authority(value: Any) -> dict[str, Any]:
    parsed = validate_record_model(_ReviewAuthorityModel, value, "review_authority")
    return {
        "review_request_ref": parsed.review_request_ref,
        "currentness_receipt_ref": parsed.currentness_receipt_ref,
        "currentness_receipt": _normalize_review_currentness_receipt(
            parsed.currentness_receipt
        ),
    }
