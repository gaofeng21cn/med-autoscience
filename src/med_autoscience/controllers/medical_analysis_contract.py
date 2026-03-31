from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers._medical_contract_support import (
    DEFAULT_MANUSCRIPT_FAMILY_BY_ARCHETYPE,
    build_contract_summary,
    managed_study_field_summary,
    resolve_endpoint_type,
    resolve_manuscript_family,
    resolve_primary_submission_target_context,
    resolve_study_archetype,
    normalized_string,
)
from med_autoscience.policies.medical_analysis_contract import (
    SUPPORTED_ENDPOINT_TYPES,
    SUPPORTED_STUDY_ARCHETYPES,
    SUPPORTED_SUBMISSION_TARGET_FAMILIES,
    resolve_medical_analysis_contract,
)
from med_autoscience.profiles import WorkspaceProfile


def resolve_medical_analysis_contract_for_study(
    *,
    study_root: Path,
    study_payload: dict[str, Any],
    profile: WorkspaceProfile,
) -> dict[str, Any]:
    study_archetype, archetype_issue = resolve_study_archetype(study_payload=study_payload, profile=profile)
    endpoint_type, endpoint_issue = resolve_endpoint_type(study_payload=study_payload)
    manuscript_family = normalized_string(study_payload.get("manuscript_family")) or None
    if study_archetype is not None:
        manuscript_family, _ = resolve_manuscript_family(
            study_payload=study_payload,
            study_archetype=study_archetype,
            default_by_archetype=DEFAULT_MANUSCRIPT_FAMILY_BY_ARCHETYPE,
        )
    target_context = resolve_primary_submission_target_context(study_root=study_root, profile=profile)
    supported_inputs = {
        "study_archetypes": list(SUPPORTED_STUDY_ARCHETYPES),
        "endpoint_types": list(SUPPORTED_ENDPOINT_TYPES),
        "submission_target_families": list(SUPPORTED_SUBMISSION_TARGET_FAMILIES),
    }

    if archetype_issue is not None:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            endpoint_type=endpoint_type,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code=archetype_issue,
            supported_inputs=supported_inputs,
            extra=managed_study_field_summary(study_payload=study_payload),
        )
    if study_archetype not in SUPPORTED_STUDY_ARCHETYPES:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            endpoint_type=endpoint_type,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code="unsupported_study_archetype",
            supported_inputs=supported_inputs,
            extra=managed_study_field_summary(study_payload=study_payload),
        )
    if endpoint_issue is not None:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            endpoint_type=endpoint_type,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code=endpoint_issue,
            supported_inputs=supported_inputs,
            extra=managed_study_field_summary(study_payload=study_payload),
        )
    if endpoint_type not in SUPPORTED_ENDPOINT_TYPES:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            endpoint_type=endpoint_type,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code="unsupported_endpoint_type",
            supported_inputs=supported_inputs,
            extra=managed_study_field_summary(study_payload=study_payload),
        )
    if target_context["status"] != "resolved":
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            endpoint_type=endpoint_type,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code=str(target_context["reason_code"]),
            supported_inputs=supported_inputs,
            extra=managed_study_field_summary(study_payload=study_payload),
        )

    contract = resolve_medical_analysis_contract(
        study_archetype=study_archetype,
        endpoint_type=endpoint_type,
        submission_target_family=str(target_context["submission_target_family"]),
    )
    return build_contract_summary(
        study_root=study_root,
        status="resolved",
        study_archetype=contract.study_archetype,
        endpoint_type=contract.endpoint_type,
        manuscript_family=manuscript_family,
        target_context=target_context,
        supported_inputs=supported_inputs,
        extra={
            **managed_study_field_summary(study_payload=study_payload),
            "required_analysis_packages": list(contract.required_analysis_packages),
            "required_reporting_items": list(contract.required_reporting_items),
            "forbidden_default_routes": list(contract.forbidden_default_routes),
        },
    )
