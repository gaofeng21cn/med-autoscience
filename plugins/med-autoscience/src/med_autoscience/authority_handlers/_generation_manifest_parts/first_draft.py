"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)

from .constants import (
    FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES,
    FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    FIRST_DRAFT_VALIDATION_DESIGNS,
    LEGACY_FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL,
)

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
    keys = {
        "surface_kind",
        "schema_version",
        "paper_type",
        "validation_design",
        "triggers",
        "candidate_refs",
    }
    if schema_version == 2:
        keys.add("candidate_dispositions")
        if require_scholar_v2_semantics:
            keys.add("scholar_v2_semantic_policy_bindings")
    exact_keys(
        payload,
        keys,
        field,
    )
    if payload.get("surface_kind") != "mas_first_draft_quality_application_candidate":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    paper_type = enum_text(
        payload.get("paper_type"),
        f"{field}.paper_type",
        {"prediction_model", "other"},
    )
    validation_design = enum_text(
        payload.get("validation_design"),
        f"{field}.validation_design",
        set(FIRST_DRAFT_VALIDATION_DESIGNS),
    )
    if paper_type == "prediction_model" and validation_design == "not_applicable":
        raise RequestShapeError(
            f"{field}.validation_design must classify prediction-model validation"
        )
    if paper_type == "other" and validation_design != "not_applicable":
        raise RequestShapeError(
            f"{field}.validation_design must be not_applicable for other paper types"
        )

    triggers_field = f"{field}.triggers"
    trigger_payload = mapping(payload.get("triggers"), triggers_field)
    trigger_keys = {
        "reports_fixed_horizon_risk",
        "competing_risk_relevant",
        "reports_decision_curve_analysis",
        "includes_table_one",
        "requires_reader_pdf",
    }
    if schema_version == 2:
        trigger_keys.add("uses_clinical_or_registry_data")
    exact_keys(trigger_payload, trigger_keys, triggers_field)
    triggers: dict[str, bool] = {}
    for key in sorted(trigger_keys):
        trigger = trigger_payload.get(key)
        if not isinstance(trigger, bool):
            raise RequestShapeError(f"{triggers_field}.{key} must be boolean")
        triggers[key] = trigger
    if schema_version == 2 and paper_type == "prediction_model" and not triggers[
        "uses_clinical_or_registry_data"
    ]:
        raise RequestShapeError(
            f"{triggers_field}.uses_clinical_or_registry_data must be true for "
            "prediction-model manuscripts"
        )

    refs_field = f"{field}.candidate_refs"
    refs_payload = mapping(payload.get("candidate_refs"), refs_field)
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
    if validation_design != "external_validation" and candidate_refs[
        "external_transportability_ref"
    ] is not None:
        raise RequestShapeError(
            f"{refs_field}.external_transportability_ref is external-validation-only"
        )

    normalized = {
        "surface_kind": "mas_first_draft_quality_application_candidate",
        "schema_version": schema_version,
        "paper_type": paper_type,
        "validation_design": validation_design,
        "triggers": triggers,
        "candidate_refs": candidate_refs,
    }
    if schema_version == 2:
        dispositions_field = f"{field}.candidate_dispositions"
        dispositions_payload = mapping(
            payload.get("candidate_dispositions"), dispositions_field
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
            normalized["scholar_v2_semantic_policy_bindings"] = (
                _normalize_scholar_v2_semantic_policy_bindings(
                    payload.get("scholar_v2_semantic_policy_bindings"),
                    f"{field}.scholar_v2_semantic_policy_bindings",
                    required_skill_ids={
                        skill_id
                        for skill_id, policy in SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL.items()
                        if candidate_refs[policy["candidate_ref_field"]] is not None
                    },
                )
            )
            for binding in normalized["scholar_v2_semantic_policy_bindings"]:
                if candidate_refs[binding["candidate_ref_field"]] != binding[
                    "candidate_ref"
                ]:
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
    bindings: list[dict[str, Any]] = []
    for index, raw in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        payload = mapping(raw, item_field)
        exact_keys(
            payload,
            {
                "skill_id",
                "semantic_policy_id",
                "validator_id",
                "semantic_policy_ref",
                "candidate_ref_field",
                "candidate_surface_kind",
                "candidate_ref",
                "invocation_ref",
                "receipt_ref",
            },
            item_field,
        )
        skill_id = enum_text(
            payload.get("skill_id"),
            f"{item_field}.skill_id",
            set(SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL),
        )
        policy = SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL[skill_id]
        if payload.get("semantic_policy_id") != policy["policy_id"]:
            raise RequestShapeError(
                f"{item_field}.semantic_policy_id must bind the current Scholar policy"
            )
        if payload.get("validator_id") != policy["validator_id"]:
            raise RequestShapeError(
                f"{item_field}.validator_id must bind the current Scholar validator"
            )
        if payload.get("candidate_ref_field") != policy["candidate_ref_field"]:
            raise RequestShapeError(
                f"{item_field}.candidate_ref_field is not the current first-draft gate"
            )
        if payload.get("candidate_surface_kind") != policy["candidate_surface_kind"]:
            raise RequestShapeError(
                f"{item_field}.candidate_surface_kind is not the Scholar candidate family"
            )
        bindings.append(
            {
                "skill_id": skill_id,
                "semantic_policy_id": policy["policy_id"],
                "validator_id": policy["validator_id"],
                "candidate_ref_field": policy["candidate_ref_field"],
                "candidate_surface_kind": policy["candidate_surface_kind"],
                "semantic_policy_ref": _exact_ref(
                    payload.get("semantic_policy_ref"),
                    f"{item_field}.semantic_policy_ref",
                    "scholarskills_semantic_policy",
                ),
                "candidate_ref": _exact_ref(
                    payload.get("candidate_ref"),
                    f"{item_field}.candidate_ref",
                    "mas_artifact",
                ),
                "invocation_ref": _exact_ref(
                    payload.get("invocation_ref"),
                    f"{item_field}.invocation_ref",
                    "mas_professional_skill_invocation",
                ),
                "receipt_ref": _exact_ref(
                    payload.get("receipt_ref"),
                    f"{item_field}.receipt_ref",
                    "scholarskills_professional_skill_receipt",
                ),
            }
        )
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
            or invocation.get("semantic_policy_id")
            != binding["semantic_policy_id"]
            or invocation.get("semantic_validator_id") != binding["validator_id"]
            or invocation.get("semantic_policy_ref")
            != binding["semantic_policy_ref"]
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
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "status",
            "earliest_route_back_owner",
            "reason_codes",
            "unresolved_items",
            "not_applicable_reason",
        },
        field,
    )
    status = enum_text(
        payload.get("status"),
        f"{field}.status",
        set(FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES),
    )
    owner = optional_text(
        payload.get("earliest_route_back_owner"),
        f"{field}.earliest_route_back_owner",
    )
    if owner is not None and owner not in FIRST_DRAFT_QUALITY_ROUTE_PRIORITY:
        raise RequestShapeError(
            f"{field}.earliest_route_back_owner must be a canonical first-draft Stage"
        )
    reason_codes = text_list(payload.get("reason_codes"), f"{field}.reason_codes")
    unresolved_items = text_list(
        payload.get("unresolved_items"), f"{field}.unresolved_items"
    )
    not_applicable_reason = optional_text(
        payload.get("not_applicable_reason"),
        f"{field}.not_applicable_reason",
    )

    if status == "satisfied":
        if candidate_ref is None:
            raise RequestShapeError(f"{field} satisfied status requires its exact candidate ref")
        if owner is not None or reason_codes or unresolved_items or not_applicable_reason:
            raise RequestShapeError(f"{field} satisfied status is contradictory")
    elif status == "route_back_required":
        if candidate_ref is None:
            raise RequestShapeError(
                f"{field} route_back_required status requires its exact candidate ref"
            )
        if owner is None or not reason_codes or not unresolved_items:
            raise RequestShapeError(
                f"{field} route_back_required status requires owner, reason codes, "
                "and unresolved items"
            )
        if not_applicable_reason is not None:
            raise RequestShapeError(
                f"{field} route_back_required status cannot carry a not-applicable reason"
            )
    else:
        if candidate_ref is not None:
            raise RequestShapeError(
                f"{field} not_applicable_with_reason status cannot carry a candidate ref"
            )
        if owner is not None or reason_codes or unresolved_items:
            raise RequestShapeError(
                f"{field} not_applicable_with_reason status is contradictory"
            )
        if not_applicable_reason is None:
            raise RequestShapeError(
                f"{field} not_applicable_with_reason status requires a reason"
            )

    return {
        "status": status,
        "earliest_route_back_owner": owner,
        "reason_codes": reason_codes,
        "unresolved_items": unresolved_items,
        "not_applicable_reason": not_applicable_reason,
    }
