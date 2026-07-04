from __future__ import annotations


def current_writer_story_delta_is_journal_routable(text: str) -> bool:
    lowered = text.lower()
    return (
        _has_required_sections(lowered)
        and _has_medical_reporting_structure(lowered)
        and (
            _has_treatment_gap_manuscript_pattern(lowered)
            or _has_external_validation_manuscript_pattern(lowered)
            or _has_descriptive_registry_atlas_pattern(lowered)
        )
    )


def _has_required_sections(lowered: str) -> bool:
    required_section_groups = (
        ("## abstract",),
        ("## introduction",),
        ("## methods", "## materials and methods"),
        ("## results",),
        ("## discussion",),
        ("## limitations", "### limitations"),
        ("## conclusion", "## conclusions", "### conclusion", "### conclusions"),
    )
    return all(any(section in lowered for section in group) for group in required_section_groups)


def _has_medical_reporting_structure(lowered: str) -> bool:
    return (
        any(
            phrase in lowered
            for phrase in ("study design", "data source", "data sources", "cohort", "participants", "patients")
        )
        and any(phrase in lowered for phrase in ("statistical analysis", "statistical analyses", "analysis used"))
        and any(phrase in lowered for phrase in ("results", "95% ci", "confidence interval", "denominator"))
    )


def _has_treatment_gap_manuscript_pattern(lowered: str) -> bool:
    return (
        "phenotype derivation" in lowered
        and "data quality" in lowered
        and "statistical analysis" in lowered
        and any(
            phrase in lowered
            for phrase in (
                "recorded medication-coverage gap",
                "recorded medication coverage gap",
                "recorded medication-coverage pattern",
                "recorded treatment-review gap",
                "potential treatment-review gap",
            )
        )
    )


def _has_external_validation_manuscript_pattern(lowered: str) -> bool:
    return (
        any(phrase in lowered for phrase in ("external validation", "validation cohort", "validation analysis"))
        and any(phrase in lowered for phrase in ("c-index", "concordance", "discrimination"))
        and "calibration" in lowered
        and any(phrase in lowered for phrase in ("95% ci", "confidence interval", "bootstrap", "wilson"))
        and any(phrase in lowered for phrase in ("cox", "prediction model", "mortality score", "risk score"))
        and any(phrase in lowered for phrase in ("nhanes", "development cohort", "validation sample"))
    )


def _has_descriptive_registry_atlas_pattern(lowered: str) -> bool:
    return (
        "registry" in lowered
        and any(phrase in lowered for phrase in ("phenotype atlas", "descriptive atlas", "registry atlas"))
        and any(phrase in lowered for phrase in ("source layer", "source-layer", "source-specific"))
        and any(phrase in lowered for phrase in ("denominator", "available-record", "missingness"))
        and any(phrase in lowered for phrase in ("bmi", "waist circumference", "central obesity"))
        and any(phrase in lowered for phrase in ("phq-9", "gad-7", "psychobehavioral"))
        and any(
            phrase in lowered
            for phrase in (
                "not as disease prevalence",
                "not estimate population",
                "not establish population",
                "registry-field summaries",
                "observed registry data",
            )
        )
    )


__all__ = ["current_writer_story_delta_is_journal_routable"]
