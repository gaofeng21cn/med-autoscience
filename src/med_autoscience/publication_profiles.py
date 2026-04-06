from __future__ import annotations


GENERAL_MEDICAL_JOURNAL_PROFILE = "general_medical_journal"
FRONTIERS_FAMILY_HARVARD_PROFILE = "frontiers_family_harvard"

SUPPORTED_PUBLICATION_PROFILES = frozenset(
    {
        GENERAL_MEDICAL_JOURNAL_PROFILE,
        FRONTIERS_FAMILY_HARVARD_PROFILE,
    }
)

EXPORTER_FAMILY_BY_PUBLICATION_PROFILE = {
    GENERAL_MEDICAL_JOURNAL_PROFILE: "generic_medical_journal",
    FRONTIERS_FAMILY_HARVARD_PROFILE: "frontiers_family",
}

GENERIC_EXPORTER_PROFILES = frozenset({GENERAL_MEDICAL_JOURNAL_PROFILE})

DEFAULT_CITATION_STYLE_BY_PUBLICATION_PROFILE = {
    GENERAL_MEDICAL_JOURNAL_PROFILE: "AMA",
    FRONTIERS_FAMILY_HARVARD_PROFILE: "FrontiersHarvard",
}

SUPPORTED_CITATION_STYLES_BY_PUBLICATION_PROFILE = {
    GENERAL_MEDICAL_JOURNAL_PROFILE: frozenset({"AMA"}),
    FRONTIERS_FAMILY_HARVARD_PROFILE: frozenset({"FrontiersHarvard"}),
}


def normalize_publication_profile(publication_profile: str) -> str:
    return str(publication_profile or "").strip()


def is_frontiers_family_harvard_profile(publication_profile: str) -> bool:
    return normalize_publication_profile(publication_profile) == FRONTIERS_FAMILY_HARVARD_PROFILE


def is_supported_publication_profile(publication_profile: str | None) -> bool:
    if publication_profile is None:
        return False
    return normalize_publication_profile(publication_profile) in SUPPORTED_PUBLICATION_PROFILES


def exporter_family_for_publication_profile(publication_profile: str | None) -> str | None:
    if publication_profile is None:
        return None
    return EXPORTER_FAMILY_BY_PUBLICATION_PROFILE.get(normalize_publication_profile(publication_profile))


def is_generic_publication_profile(publication_profile: str | None) -> bool:
    if publication_profile is None:
        return False
    return normalize_publication_profile(publication_profile) in GENERIC_EXPORTER_PROFILES


def default_citation_style_for_publication_profile(publication_profile: str | None) -> str | None:
    if publication_profile is None:
        return None
    return DEFAULT_CITATION_STYLE_BY_PUBLICATION_PROFILE.get(normalize_publication_profile(publication_profile))


def publication_profile_supports_citation_style(
    publication_profile: str | None,
    citation_style: str | None,
) -> bool:
    if publication_profile is None:
        return False
    normalized_profile = normalize_publication_profile(publication_profile)
    if normalized_profile not in SUPPORTED_PUBLICATION_PROFILES:
        return False
    normalized_citation_style = str(citation_style or "auto").strip()
    if normalized_citation_style in {"", "auto"}:
        return True
    return normalized_citation_style in SUPPORTED_CITATION_STYLES_BY_PUBLICATION_PROFILE[normalized_profile]
