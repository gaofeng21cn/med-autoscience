from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_profiles import (
    FRONTIERS_FAMILY_HARVARD_PROFILE,
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    normalize_publication_profile,
)
from med_autoscience.submission_targets import resolve_submission_target_contract


MEDICAL_SUBMISSION_TARGET_FAMILY_BY_PUBLICATION_PROFILE: dict[str, str] = {
    GENERAL_MEDICAL_JOURNAL_PROFILE: "general_medical_journal",
    FRONTIERS_FAMILY_HARVARD_PROFILE: "general_medical_journal",
}
RECOMMENDED_MANAGED_STUDY_FIELDS = (
    "study_archetype",
    "endpoint_type",
    "manuscript_family",
)
DEFAULT_MANUSCRIPT_FAMILY_BY_ARCHETYPE: dict[str, str] = {
    "clinical_classifier": "prediction_model",
    "survey_trend_analysis": "clinical_observation",
}


def normalized_string(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def managed_study_field_summary(*, study_payload: dict[str, Any]) -> dict[str, list[str]]:
    declared_fields = [
        field_name
        for field_name in RECOMMENDED_MANAGED_STUDY_FIELDS
        if normalized_string(study_payload.get(field_name))
    ]
    return {
        "recommended_study_fields": list(RECOMMENDED_MANAGED_STUDY_FIELDS),
        "declared_study_fields": declared_fields,
    }


def resolve_study_archetype(*, study_payload: dict[str, Any], profile: WorkspaceProfile) -> tuple[str | None, str | None]:
    explicit_study_archetype = normalized_string(study_payload.get("study_archetype"))
    if explicit_study_archetype:
        return explicit_study_archetype, None

    explicit_study_archetype = normalized_string(study_payload.get("preferred_study_archetype"))
    if explicit_study_archetype:
        return explicit_study_archetype, None

    profile_archetypes = [str(item).strip() for item in profile.preferred_study_archetypes if str(item).strip()]
    if len(profile_archetypes) == 1:
        return profile_archetypes[0], None
    if len(profile_archetypes) > 1:
        return None, "ambiguous_study_archetype"
    return None, "missing_study_archetype"


def resolve_endpoint_type(*, study_payload: dict[str, Any]) -> tuple[str | None, str | None]:
    endpoint_type = normalized_string(study_payload.get("endpoint_type"))
    if endpoint_type:
        return endpoint_type, None
    return None, "missing_endpoint_type"


def resolve_manuscript_family(
    *,
    study_payload: dict[str, Any],
    study_archetype: str,
    default_by_archetype: dict[str, str],
) -> tuple[str | None, str | None]:
    explicit_manuscript_family = normalized_string(study_payload.get("manuscript_family"))
    if explicit_manuscript_family:
        return explicit_manuscript_family, None
    mapped_family = default_by_archetype.get(study_archetype)
    if mapped_family:
        return mapped_family, None
    return None, "missing_manuscript_family_mapping"


def resolve_primary_submission_target_context(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    contract = resolve_submission_target_contract(profile=profile, study_root=study_root)
    primary_target = contract.primary_target
    publication_profile = normalize_publication_profile(primary_target.publication_profile or "") or None
    target_context: dict[str, Any] = {
        "primary_target_key": primary_target.target_key,
        "primary_target_source": primary_target.source,
        "primary_target_resolution_status": primary_target.resolution_status,
        "publication_profile": publication_profile,
        "journal_name": primary_target.journal_name,
        "official_guidelines_url": primary_target.official_guidelines_url,
    }
    if primary_target.resolution_status != "resolved_profile" or publication_profile is None:
        target_context["status"] = "unsupported"
        target_context["reason_code"] = "primary_submission_target_not_resolved_to_publication_profile"
        return target_context

    submission_target_family = MEDICAL_SUBMISSION_TARGET_FAMILY_BY_PUBLICATION_PROFILE.get(publication_profile)
    if submission_target_family is None:
        target_context["status"] = "unsupported"
        target_context["reason_code"] = "unsupported_publication_profile"
        return target_context

    target_context["status"] = "resolved"
    target_context["submission_target_family"] = submission_target_family
    return target_context


def build_contract_summary(
    *,
    study_root: Path,
    status: str,
    study_archetype: str | None,
    endpoint_type: str | None = None,
    manuscript_family: str | None = None,
    target_context: dict[str, Any] | None = None,
    reason_code: str | None = None,
    supported_inputs: dict[str, list[str]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "status": status,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "study_archetype": study_archetype,
    }
    if endpoint_type is not None:
        summary["endpoint_type"] = endpoint_type
    if manuscript_family is not None:
        summary["manuscript_family"] = manuscript_family
    if target_context is not None:
        for key in (
            "primary_target_key",
            "primary_target_source",
            "primary_target_resolution_status",
            "publication_profile",
            "journal_name",
            "official_guidelines_url",
            "submission_target_family",
        ):
            if key in target_context:
                summary[key] = target_context[key]
    if reason_code is not None:
        summary["reason_code"] = reason_code
    if supported_inputs is not None:
        summary["supported_inputs"] = supported_inputs
    if extra is not None:
        summary.update(extra)
    return summary
