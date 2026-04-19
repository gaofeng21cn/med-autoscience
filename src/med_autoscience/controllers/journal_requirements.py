from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.journal_requirements import (
    JournalRequirements,
    slugify_journal_name,
    write_journal_requirements,
)


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def resolve_journal_requirements(
    *,
    study_root: Path,
    journal_name: str | None = None,
    journal_slug: str | None = None,
    official_guidelines_url: str | None = None,
    publication_profile: str | None = None,
    requirements_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_journal_name = _optional_text(journal_name) or _optional_text(journal_slug) or "Journal Target"
    resolved_journal_slug = _optional_text(journal_slug) or slugify_journal_name(resolved_journal_name)
    resolved_guidelines_url = _optional_text(official_guidelines_url)
    if resolved_guidelines_url is None:
        raise ValueError("official_guidelines_url is required")
    payload = dict(requirements_payload or {})
    payload.setdefault("journal_name", resolved_journal_name)
    payload.setdefault("journal_slug", resolved_journal_slug)
    payload.setdefault("official_guidelines_url", resolved_guidelines_url)
    payload.setdefault("publication_profile", _optional_text(publication_profile))
    requirements = JournalRequirements(
        journal_name=str(payload["journal_name"]),
        journal_slug=str(payload["journal_slug"]),
        official_guidelines_url=str(payload["official_guidelines_url"]),
        publication_profile=_optional_text(payload.get("publication_profile")),
        abstract_word_cap=payload.get("abstract_word_cap"),
        title_word_cap=payload.get("title_word_cap"),
        keyword_limit=payload.get("keyword_limit"),
        main_text_word_cap=payload.get("main_text_word_cap"),
        main_display_budget=payload.get("main_display_budget"),
        table_budget=payload.get("table_budget"),
        figure_budget=payload.get("figure_budget"),
        supplementary_allowed=bool(payload.get("supplementary_allowed")),
        title_page_required=bool(payload.get("title_page_required")),
        blinded_main_document=bool(payload.get("blinded_main_document")),
        reference_style_family=_optional_text(payload.get("reference_style_family")),
        required_sections=tuple(str(item) for item in payload.get("required_sections") or []),
        declaration_requirements=tuple(str(item) for item in payload.get("declaration_requirements") or []),
        submission_checklist_items=tuple(str(item) for item in payload.get("submission_checklist_items") or []),
        template_assets=tuple(str(item) for item in payload.get("template_assets") or []),
    )
    write_result = write_journal_requirements(study_root=resolved_study_root, requirements=requirements)
    return {
        "status": "resolved",
        "study_root": str(resolved_study_root),
        "journal_name": resolved_journal_name,
        "journal_slug": resolved_journal_slug,
        **write_result,
    }
