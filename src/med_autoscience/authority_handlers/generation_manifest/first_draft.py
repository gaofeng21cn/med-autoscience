"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import StrictBool, ValidationInfo, model_validator

from .._record_validation import (
    NonEmptyStr,
    OptionalNonEmptyStr,
    RequestShapeError,
    StrictRecordModel,
    UniqueNonEmptyStrList,
    enum_field,
    exact_int_field,
    exact_keys,
    exact_ref_field,
    exact_str_field,
    integer,
    mapping,
    sequence,
    validate_record_dict,
    validate_record_model,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)
from .constants import (
    FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES,
    FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    FIRST_DRAFT_VALIDATION_DESIGNS,
    LEGACY_FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL,
)


class _FirstDraftTriggersV1Model(StrictRecordModel):
    reports_fixed_horizon_risk: StrictBool
    competing_risk_relevant: StrictBool
    reports_decision_curve_analysis: StrictBool
    includes_table_one: StrictBool
    requires_reader_pdf: StrictBool


class _FirstDraftTriggersV2Model(_FirstDraftTriggersV1Model):
    uses_clinical_or_registry_data: StrictBool


class _FirstDraftApplicationBaseModel(StrictRecordModel):
    surface_kind: exact_str_field(
        "mas_first_draft_quality_application_candidate",
        message="__FIELD__ is invalid",
    )
    paper_type: enum_field({"prediction_model", "other"})
    validation_design: enum_field(FIRST_DRAFT_VALIDATION_DESIGNS)
    candidate_refs: Any

    @model_validator(mode="after")
    def _validate_design_pairing(self, info: ValidationInfo) -> _FirstDraftApplicationBaseModel:
        root_field = (info.context or {}).get("root_field", "first_draft_quality_application")
        if self.paper_type == "prediction_model" and self.validation_design == "not_applicable":
            raise RequestShapeError(
                f"{root_field}.validation_design must classify prediction-model validation"
            )
        if self.paper_type == "other" and self.validation_design != "not_applicable":
            raise RequestShapeError(
                f"{root_field}.validation_design must be not_applicable for other paper types"
            )
        return self


class _FirstDraftApplicationV1Model(_FirstDraftApplicationBaseModel):
    schema_version: exact_int_field(1)
    triggers: _FirstDraftTriggersV1Model


class _FirstDraftApplicationV2Model(_FirstDraftApplicationBaseModel):
    schema_version: exact_int_field(2)
    triggers: _FirstDraftTriggersV2Model
    candidate_dispositions: Any

    @model_validator(mode="after")
    def _validate_prediction_model_clinical_data(
        self, info: ValidationInfo
    ) -> _FirstDraftApplicationV2Model:
        root_field = (info.context or {}).get("root_field", "first_draft_quality_application")
        if self.paper_type == "prediction_model" and not self.triggers.uses_clinical_or_registry_data:
            raise RequestShapeError(
                f"{root_field}.triggers.uses_clinical_or_registry_data must be true for "
                "prediction-model manuscripts"
            )
        return self


class _FirstDraftApplicationV2ScholarModel(_FirstDraftApplicationV2Model):
    scholar_v2_semantic_policy_bindings: Any


class _ScholarV2SemanticPolicyBindingModel(StrictRecordModel):
    skill_id: enum_field(SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL)
    semantic_policy_id: NonEmptyStr
    validator_id: NonEmptyStr
    semantic_policy_ref: exact_ref_field("scholarskills_semantic_policy")
    candidate_ref_field: NonEmptyStr
    candidate_surface_kind: NonEmptyStr
    candidate_ref: exact_ref_field("mas_artifact")
    invocation_ref: exact_ref_field("mas_professional_skill_invocation")
    receipt_ref: exact_ref_field("scholarskills_professional_skill_receipt")

    @model_validator(mode="after")
    def _validate_policy_binding(
        self, info: ValidationInfo
    ) -> _ScholarV2SemanticPolicyBindingModel:
        item_field = (info.context or {}).get("root_field", "binding")
        policy = SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL[self.skill_id]
        if self.semantic_policy_id != policy["policy_id"]:
            raise RequestShapeError(
                f"{item_field}.semantic_policy_id must bind the current Scholar policy"
            )
        if self.validator_id != policy["validator_id"]:
            raise RequestShapeError(
                f"{item_field}.validator_id must bind the current Scholar validator"
            )
        if self.candidate_ref_field != policy["candidate_ref_field"]:
            raise RequestShapeError(
                f"{item_field}.candidate_ref_field is not the current first-draft gate"
            )
        if self.candidate_surface_kind != policy["candidate_surface_kind"]:
            raise RequestShapeError(
                f"{item_field}.candidate_surface_kind is not the Scholar candidate family"
            )
        return self


class _FirstDraftCandidateDispositionModel(StrictRecordModel):
    status: enum_field(FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES)
    earliest_route_back_owner: OptionalNonEmptyStr
    reason_codes: UniqueNonEmptyStrList
    unresolved_items: UniqueNonEmptyStrList
    not_applicable_reason: OptionalNonEmptyStr

    @model_validator(mode="after")
    def _validate_disposition(
        self, info: ValidationInfo
    ) -> _FirstDraftCandidateDispositionModel:
        ctx = info.context or {}
        field = ctx.get("root_field", "disposition")
        candidate_ref = ctx.get("candidate_ref")
        if (
            self.earliest_route_back_owner is not None
            and self.earliest_route_back_owner not in FIRST_DRAFT_QUALITY_ROUTE_PRIORITY
        ):
            raise RequestShapeError(
                f"{field}.earliest_route_back_owner must be a canonical first-draft Stage"
            )
        if self.status == "satisfied":
            if candidate_ref is None:
                raise RequestShapeError(
                    f"{field} satisfied status requires its exact candidate ref"
                )
            if (
                self.earliest_route_back_owner is not None
                or self.reason_codes
                or self.unresolved_items
                or self.not_applicable_reason
            ):
                raise RequestShapeError(f"{field} satisfied status is contradictory")
        elif self.status == "route_back_required":
            if candidate_ref is None:
                raise RequestShapeError(
                    f"{field} route_back_required status requires its exact candidate ref"
                )
            if (
                self.earliest_route_back_owner is None
                or not self.reason_codes
                or not self.unresolved_items
            ):
                raise RequestShapeError(
                    f"{field} route_back_required status requires owner, reason codes, "
                    "and unresolved items"
                )
            if self.not_applicable_reason is not None:
                raise RequestShapeError(
                    f"{field} route_back_required status cannot carry a not-applicable reason"
                )
        else:
            if candidate_ref is not None:
                raise RequestShapeError(
                    f"{field} not_applicable_with_reason status cannot carry a candidate ref"
                )
            if (
                self.earliest_route_back_owner is not None
                or self.reason_codes
                or self.unresolved_items
            ):
                raise RequestShapeError(
                    f"{field} not_applicable_with_reason status is contradictory"
                )
            if self.not_applicable_reason is None:
                raise RequestShapeError(
                    f"{field} not_applicable_with_reason status requires a reason"
                )
        return self


def _normalize_first_draft_quality_application(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
    require_scholar_v2_semantics: bool = False,
) -> dict[str, Any]:
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    require_scholar_v2_semantics = (
        require_scholar_v2_semantics and schema_version == 2
    )
    if schema_version == 1:
        model_cls: type[StrictRecordModel] = _FirstDraftApplicationV1Model
    elif require_scholar_v2_semantics:
        model_cls = _FirstDraftApplicationV2ScholarModel
    else:
        model_cls = _FirstDraftApplicationV2Model

    envelope = validate_record_model(model_cls, payload, field)
    assert isinstance(envelope, _FirstDraftApplicationBaseModel)
    triggers = dict(sorted(envelope.triggers.model_dump().items()))

    refs_field = f"{field}.candidate_refs"
    refs_payload = mapping(envelope.candidate_refs, refs_field)
    role_by_ref_field = (
        FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD
        if require_scholar_v2_semantics
        else LEGACY_FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD
    )
    exact_keys(refs_payload, set(role_by_ref_field), refs_field)
    candidate_refs: dict[str, dict[str, Any] | None] = {}
    for ref_field, role in role_by_ref_field.items():
        raw_ref = refs_payload.get(ref_field)
        if raw_ref is None:
            candidate_refs[ref_field] = None
            continue
        candidate_ref = _exact_ref(raw_ref, f"{refs_field}.{ref_field}", "mas_artifact")
        if schema_version == 2 and candidate_ref["size_bytes"] == 0:
            raise RequestShapeError(
                f"{refs_field}.{ref_field}.size_bytes must be greater than zero "
                "for a current first-draft candidate"
            )
        matching_artifacts = [
            artifact
            for artifact in artifacts
            if artifact["role"] == role
            and all(
                candidate_ref[key] == artifact[key]
                for key in ("ref", "size_bytes", "sha256")
            )
        ]
        if len(matching_artifacts) != 1:
            raise RequestShapeError(
                f"{refs_field}.{ref_field} must bind the exact {role} artifact"
            )
        candidate_refs[ref_field] = candidate_ref
    if (
        envelope.validation_design != "external_validation"
        and candidate_refs["external_transportability_ref"] is not None
    ):
        raise RequestShapeError(
            f"{refs_field}.external_transportability_ref is external-validation-only"
        )

    normalized: dict[str, Any] = {
        "surface_kind": "mas_first_draft_quality_application_candidate",
        "schema_version": schema_version,
        "paper_type": envelope.paper_type,
        "validation_design": envelope.validation_design,
        "triggers": triggers,
        "candidate_refs": candidate_refs,
    }
    if schema_version == 2:
        assert isinstance(envelope, _FirstDraftApplicationV2Model)
        dispositions_field = f"{field}.candidate_dispositions"
        dispositions_payload = mapping(
            envelope.candidate_dispositions, dispositions_field
        )
        exact_keys(
            dispositions_payload,
            set(role_by_ref_field),
            dispositions_field,
        )
        applicable_fields = first_draft_applicable_ref_fields(
            normalized,
            include_scholar_v2_semantics=require_scholar_v2_semantics,
        )
        dispositions = {}
        for ref_field in role_by_ref_field:
            disposition = _normalize_first_draft_candidate_disposition(
                dispositions_payload.get(ref_field),
                f"{dispositions_field}.{ref_field}",
                candidate_ref=candidate_refs[ref_field],
            )
            if ref_field in applicable_fields:
                if disposition["status"] == "not_applicable_with_reason":
                    raise RequestShapeError(
                        f"{dispositions_field}.{ref_field} is required by the "
                        "declared paper type and triggers"
                    )
            elif disposition["status"] != "not_applicable_with_reason":
                raise RequestShapeError(
                    f"{dispositions_field}.{ref_field} must be "
                    "not_applicable_with_reason for the declared paper type and triggers"
                )
            dispositions[ref_field] = disposition
        normalized["candidate_dispositions"] = dispositions
        if require_scholar_v2_semantics:
            assert isinstance(envelope, _FirstDraftApplicationV2ScholarModel)
            normalized["scholar_v2_semantic_policy_bindings"] = (
                _normalize_scholar_v2_semantic_policy_bindings(
                    envelope.scholar_v2_semantic_policy_bindings,
                    f"{field}.scholar_v2_semantic_policy_bindings",
                    required_skill_ids={
                        skill_id
                        for skill_id, policy in SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL.items()
                        if candidate_refs[policy["candidate_ref_field"]] is not None
                    },
                )
            )
            for binding in normalized["scholar_v2_semantic_policy_bindings"]:
                if (
                    candidate_refs[binding["candidate_ref_field"]]
                    != binding["candidate_ref"]
                ):
                    raise RequestShapeError(
                        f"{field}.scholar_v2_semantic_policy_bindings must bind the "
                        "current first-draft candidate artifact bytes"
                    )
    return normalized


def _normalize_scholar_v2_semantic_policy_bindings(
    value: Any,
    field: str,
    *,
    required_skill_ids: set[str],
) -> list[dict[str, Any]]:
    bindings = [
        validate_record_dict(
            _ScholarV2SemanticPolicyBindingModel,
            raw,
            f"{field}[{index}]",
        )
        for index, raw in enumerate(sequence(value, field))
    ]
    skills = [item["skill_id"] for item in bindings]
    if set(skills) != required_skill_ids or len(skills) != len(set(skills)):
        raise RequestShapeError(
            f"{field} must contain exactly one current binding for each applicable Scholar v2 policy"
        )
    return sorted(bindings, key=lambda item: item["skill_id"])


def _validate_scholar_v2_semantic_policy_invocations(
    manifest_core: Mapping[str, Any],
    field: str,
) -> None:
    application = manifest_core.get("first_draft_quality_application")
    if application is None or application["schema_version"] != 2:
        return
    invocations = {
        item["skill_id"]: item
        for item in manifest_core.get("professional_skill_invocations", [])
        if item["surface_kind"]
        == "mas_professional_manuscript_skill_invocation_candidate"
    }
    for binding in application["scholar_v2_semantic_policy_bindings"]:
        invocation = invocations.get(binding["skill_id"])
        if invocation is None:
            raise RequestShapeError(
                f"{field} Scholar v2 policy binding requires one exact professional invocation"
            )
        if invocation["schema_version"] != 2:
            raise RequestShapeError(
                f"{field} current Scholar v2 semantic policy requires a v2 professional invocation"
            )
        if (
            invocation.get("invocation_ref") != binding["invocation_ref"]
            or invocation.get("receipt_ref") != binding["receipt_ref"]
            or invocation.get("semantic_policy_id") != binding["semantic_policy_id"]
            or invocation.get("semantic_validator_id") != binding["validator_id"]
            or invocation.get("semantic_policy_ref") != binding["semantic_policy_ref"]
            or invocation.get("semantic_candidate_ref") != binding["candidate_ref"]
        ):
            raise RequestShapeError(
                f"{field} Scholar v2 policy binding does not match exact invocation and receipt refs"
            )


def first_draft_applicable_ref_fields(
    application: Mapping[str, Any],
    *,
    include_scholar_v2_semantics: bool | None = None,
) -> frozenset[str]:
    fields = {
        "medical_initial_draft_preflight_candidate_ref",
        "citation_source_coverage_ref",
        "claim_guardrail_ref",
    }
    uses_scholar_v2_semantics = (
        "scholar_v2_semantic_policy_bindings" in application
        if include_scholar_v2_semantics is None
        else include_scholar_v2_semantics
    )
    if uses_scholar_v2_semantics:
        fields.update(
            {
                "active_reference_currentness_ref",
                "author_stance_integrity_ref",
            }
        )
    if application["triggers"]["uses_clinical_or_registry_data"]:
        fields.add("clinical_analysis_input_identity_ref")
    if application["paper_type"] == "prediction_model":
        fields.update(
            {
                "validation_partition_integrity_ref",
                "endpoint_analysis_set_reconciliation_ref",
                "model_complexity_sparse_event_ref",
            }
        )
        if uses_scholar_v2_semantics:
            fields.add("linked_prediction_performance_ref")
    triggers = application["triggers"]
    if triggers["reports_fixed_horizon_risk"]:
        fields.add("fixed_horizon_risk_semantics_ref")
    if triggers["competing_risk_relevant"]:
        fields.add("competing_risk_ref")
    if triggers["reports_decision_curve_analysis"]:
        fields.add("decision_curve_validity_ref")
    if triggers["includes_table_one"]:
        fields.add("baseline_table_traceability_ref")
    if triggers["requires_reader_pdf"]:
        fields.add("document_display_scope_coverage_ref")
        if uses_scholar_v2_semantics:
            fields.add("display_render_integrity_ref")
    if application["validation_design"] == "external_validation":
        fields.add("external_transportability_ref")
    return frozenset(fields)


def _normalize_first_draft_candidate_disposition(
    value: Any,
    field: str,
    *,
    candidate_ref: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return validate_record_dict(
        _FirstDraftCandidateDispositionModel,
        value,
        field,
        context={"candidate_ref": candidate_ref},
    )
