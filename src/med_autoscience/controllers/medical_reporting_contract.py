from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers._medical_contract_support import (
    build_contract_summary,
    resolve_manuscript_family,
    resolve_primary_submission_target_context,
    resolve_study_archetype,
)
from med_autoscience.policies.medical_reporting_contract import (
    SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES,
    SUPPORTED_STUDY_ARCHETYPES,
    SUPPORTED_SUBMISSION_TARGET_FAMILIES,
    resolve_medical_reporting_contract,
)
from med_autoscience.profiles import WorkspaceProfile


MANUSCRIPT_FAMILY_BY_ARCHETYPE: dict[str, str] = {
    "clinical_classifier": "prediction_model",
}


def resolve_medical_reporting_contract_for_study(
    *,
    study_root: Path,
    study_payload: dict[str, Any],
    profile: WorkspaceProfile,
) -> dict[str, Any]:
    study_archetype, archetype_issue = resolve_study_archetype(study_payload=study_payload, profile=profile)
    target_context = resolve_primary_submission_target_context(study_root=study_root, profile=profile)
    supported_inputs = {
        "study_archetypes": list(SUPPORTED_STUDY_ARCHETYPES),
        "manuscript_families": list(sorted(SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES)),
        "submission_target_families": list(SUPPORTED_SUBMISSION_TARGET_FAMILIES),
    }

    manuscript_family: str | None = None
    manuscript_issue: str | None = None
    if archetype_issue is None and study_archetype is not None:
        manuscript_family, manuscript_issue = resolve_manuscript_family(
            study_payload=study_payload,
            study_archetype=study_archetype,
            default_by_archetype=MANUSCRIPT_FAMILY_BY_ARCHETYPE,
        )

    if archetype_issue is not None:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code=archetype_issue,
            supported_inputs=supported_inputs,
        )
    if study_archetype not in SUPPORTED_STUDY_ARCHETYPES:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code="unsupported_study_archetype",
            supported_inputs=supported_inputs,
        )
    if manuscript_issue is not None:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code=manuscript_issue,
            supported_inputs=supported_inputs,
        )
    if manuscript_family not in SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES:
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code="unsupported_manuscript_family",
            supported_inputs=supported_inputs,
        )
    if target_context["status"] != "resolved":
        return build_contract_summary(
            study_root=study_root,
            status="unsupported",
            study_archetype=study_archetype,
            manuscript_family=manuscript_family,
            target_context=target_context,
            reason_code=str(target_context["reason_code"]),
            supported_inputs=supported_inputs,
        )

    contract = resolve_medical_reporting_contract(
        study_archetype=study_archetype,
        manuscript_family=manuscript_family,
        submission_target_family=str(target_context["submission_target_family"]),
    )
    return build_contract_summary(
        study_root=study_root,
        status="resolved",
        study_archetype=study_archetype,
        manuscript_family=manuscript_family,
        target_context=target_context,
        supported_inputs=supported_inputs,
        extra={
            "reporting_guideline_family": contract.reporting_guideline_family,
            "cohort_flow_required": contract.cohort_flow_required,
            "baseline_characteristics_required": contract.baseline_characteristics_required,
            "table_shell_requirements": list(contract.table_shell_requirements),
            "figure_shell_requirements": list(contract.figure_shell_requirements),
        },
    )
