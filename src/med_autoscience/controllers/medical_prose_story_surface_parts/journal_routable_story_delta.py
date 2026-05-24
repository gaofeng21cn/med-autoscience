from __future__ import annotations


def current_writer_story_delta_is_journal_routable(text: str) -> bool:
    lowered = text.lower()
    return (
        _has_required_sections(lowered)
        and _has_medical_reporting_structure(lowered)
        and (
            _has_treatment_gap_manuscript_pattern(lowered)
            or _has_external_validation_manuscript_pattern(lowered)
        )
    )


def _has_required_sections(lowered: str) -> bool:
    required_sections = (
        "## abstract",
        "## introduction",
        "## methods",
        "## results",
        "## discussion",
        "## limitations",
        "## conclusion",
    )
    return all(section in lowered for section in required_sections)


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


__all__ = ["current_writer_story_delta_is_journal_routable"]
