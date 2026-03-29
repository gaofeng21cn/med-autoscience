from __future__ import annotations


GENERAL_MEDICAL_JOURNAL_PROFILE = "general_medical_journal"
FRONTIERS_FAMILY_HARVARD_PROFILE = "frontiers_family_harvard"

SUPPORTED_PUBLICATION_PROFILES = frozenset(
    {
        GENERAL_MEDICAL_JOURNAL_PROFILE,
        FRONTIERS_FAMILY_HARVARD_PROFILE,
    }
)


def normalize_publication_profile(publication_profile: str) -> str:
    return str(publication_profile or "").strip()


def is_frontiers_family_harvard_profile(publication_profile: str) -> bool:
    return normalize_publication_profile(publication_profile) == FRONTIERS_FAMILY_HARVARD_PROFILE


def is_supported_publication_profile(publication_profile: str | None) -> bool:
    if publication_profile is None:
        return False
    return normalize_publication_profile(publication_profile) in SUPPORTED_PUBLICATION_PROFILES
