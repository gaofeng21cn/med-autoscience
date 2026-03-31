from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.policies.medical_reporting_contract import resolve_medical_reporting_contract
from med_autoscience.profiles import WorkspaceProfile


MANUSCRIPT_FAMILY_BY_ARCHETYPE: dict[str, str] = {
    "clinical_classifier": "prediction_model",
}


def _normalized_string(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _resolve_study_archetype(*, study_payload: dict[str, Any], profile: WorkspaceProfile) -> str:
    archetype = _normalized_string(study_payload.get("preferred_study_archetype"))
    if archetype:
        return archetype
    if profile.preferred_study_archetypes:
        return str(profile.preferred_study_archetypes[0]).strip()
    raise ValueError("study_archetype is required: preferred_study_archetype or profile.preferred_study_archetypes[0]")


def _resolve_manuscript_family(*, study_payload: dict[str, Any], study_archetype: str) -> str:
    manuscript_family = _normalized_string(study_payload.get("manuscript_family"))
    if manuscript_family:
        return manuscript_family
    mapped = MANUSCRIPT_FAMILY_BY_ARCHETYPE.get(study_archetype)
    if mapped:
        return mapped
    raise ValueError("manuscript_family is required when archetype mapping is unavailable")


def _resolve_submission_target_family(
    *,
    study_payload: dict[str, Any],
    profile: WorkspaceProfile,
) -> str:
    explicit_family = _normalized_string(study_payload.get("submission_target_family"))
    if explicit_family:
        return explicit_family

    raw_targets = study_payload.get("submission_targets")
    if isinstance(raw_targets, list):
        for item in raw_targets:
            if isinstance(item, str):
                candidate = item.strip()
                if candidate:
                    return candidate
            elif isinstance(item, dict):
                candidate = _normalized_string(item.get("publication_profile"))
                if candidate:
                    return candidate

    profile_family = str(profile.default_publication_profile).strip()
    if profile_family:
        return profile_family
    raise ValueError(
        "submission_target_family is required: submission_target_family, submission_targets[*].publication_profile, "
        "or profile.default_publication_profile"
    )


def resolve_medical_reporting_contract_for_study(
    *,
    study_root: Path,
    study_payload: dict[str, Any],
    profile: WorkspaceProfile,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    study_archetype = _resolve_study_archetype(study_payload=study_payload, profile=profile)
    manuscript_family = _resolve_manuscript_family(study_payload=study_payload, study_archetype=study_archetype)
    submission_target_family = _resolve_submission_target_family(study_payload=study_payload, profile=profile)
    contract = resolve_medical_reporting_contract(
        study_archetype=study_archetype,
        manuscript_family=manuscript_family,
        submission_target_family=submission_target_family,
    )
    return {
        "study_root": str(resolved_study_root),
        "study_archetype": study_archetype,
        "manuscript_family": manuscript_family,
        "submission_target_family": submission_target_family,
        "reporting_guideline_family": contract.reporting_guideline_family,
        "cohort_flow_required": contract.cohort_flow_required,
        "baseline_characteristics_required": contract.baseline_characteristics_required,
        "table_shell_requirements": list(contract.table_shell_requirements),
        "figure_shell_requirements": list(contract.figure_shell_requirements),
    }
