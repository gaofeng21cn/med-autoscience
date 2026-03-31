from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.policies.medical_analysis_contract import resolve_medical_analysis_contract
from med_autoscience.profiles import WorkspaceProfile


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


def _resolve_endpoint_type(*, study_payload: dict[str, Any]) -> str:
    endpoint_type = _normalized_string(study_payload.get("endpoint_type"))
    return endpoint_type or "binary"


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


def resolve_medical_analysis_contract_for_study(
    *,
    study_root: Path,
    study_payload: dict[str, Any],
    profile: WorkspaceProfile,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    study_archetype = _resolve_study_archetype(study_payload=study_payload, profile=profile)
    endpoint_type = _resolve_endpoint_type(study_payload=study_payload)
    submission_target_family = _resolve_submission_target_family(study_payload=study_payload, profile=profile)
    contract = resolve_medical_analysis_contract(
        study_archetype=study_archetype,
        endpoint_type=endpoint_type,
        submission_target_family=submission_target_family,
    )
    return {
        "study_root": str(resolved_study_root),
        "study_archetype": contract.study_archetype,
        "endpoint_type": contract.endpoint_type,
        "submission_target_family": contract.submission_target_family,
        "required_analysis_packages": list(contract.required_analysis_packages),
        "required_reporting_items": list(contract.required_reporting_items),
        "forbidden_default_routes": list(contract.forbidden_default_routes),
    }
