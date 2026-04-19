from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_string_tuple(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(str(item).strip() for item in values if str(item).strip())


def slugify_journal_name(journal_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(journal_name or "").strip().lower()).strip("-")
    if not normalized:
        raise ValueError("journal_name must resolve to a non-empty journal_slug")
    return normalized


@dataclass(frozen=True)
class JournalRequirements:
    journal_name: str
    journal_slug: str
    official_guidelines_url: str
    publication_profile: str | None
    abstract_word_cap: int | None
    title_word_cap: int | None
    keyword_limit: int | None
    main_text_word_cap: int | None
    main_display_budget: int | None
    table_budget: int | None
    figure_budget: int | None
    supplementary_allowed: bool
    title_page_required: bool
    blinded_main_document: bool
    reference_style_family: str | None
    required_sections: tuple[str, ...]
    declaration_requirements: tuple[str, ...]
    submission_checklist_items: tuple[str, ...]
    template_assets: tuple[str, ...]
    generated_at: str | None = None


def journal_requirements_root(*, study_root: Path, journal_slug: str) -> Path:
    return Path(study_root).expanduser().resolve() / "paper" / "journal_requirements" / journal_slug


def journal_requirements_json_path(*, study_root: Path, journal_slug: str) -> Path:
    return journal_requirements_root(study_root=study_root, journal_slug=journal_slug) / "requirements.json"


def journal_requirements_markdown_path(*, study_root: Path, journal_slug: str) -> Path:
    return journal_requirements_root(study_root=study_root, journal_slug=journal_slug) / "requirements.md"


def journal_submission_package_root(*, study_root: Path, journal_slug: str) -> Path:
    return Path(study_root).expanduser().resolve() / "submission_packages" / journal_slug


def journal_submission_manifest_path(*, study_root: Path, journal_slug: str) -> Path:
    return journal_submission_package_root(study_root=study_root, journal_slug=journal_slug) / "submission_manifest.json"


def _serialize_requirements(requirements: JournalRequirements) -> dict[str, Any]:
    payload = asdict(requirements)
    payload["required_sections"] = list(requirements.required_sections)
    payload["declaration_requirements"] = list(requirements.declaration_requirements)
    payload["submission_checklist_items"] = list(requirements.submission_checklist_items)
    payload["template_assets"] = list(requirements.template_assets)
    payload["generated_at"] = requirements.generated_at or utc_now()
    return payload


def _requirements_from_payload(payload: dict[str, Any]) -> JournalRequirements:
    journal_name = _optional_text(payload.get("journal_name")) or "Journal Target"
    journal_slug = _optional_text(payload.get("journal_slug")) or slugify_journal_name(journal_name)
    official_guidelines_url = _optional_text(payload.get("official_guidelines_url")) or ""
    if not official_guidelines_url:
        raise ValueError("official_guidelines_url is required")
    return JournalRequirements(
        journal_name=journal_name,
        journal_slug=journal_slug,
        official_guidelines_url=official_guidelines_url,
        publication_profile=_optional_text(payload.get("publication_profile")),
        abstract_word_cap=_optional_int(payload.get("abstract_word_cap")),
        title_word_cap=_optional_int(payload.get("title_word_cap")),
        keyword_limit=_optional_int(payload.get("keyword_limit")),
        main_text_word_cap=_optional_int(payload.get("main_text_word_cap")),
        main_display_budget=_optional_int(payload.get("main_display_budget")),
        table_budget=_optional_int(payload.get("table_budget")),
        figure_budget=_optional_int(payload.get("figure_budget")),
        supplementary_allowed=bool(payload.get("supplementary_allowed")),
        title_page_required=bool(payload.get("title_page_required")),
        blinded_main_document=bool(payload.get("blinded_main_document")),
        reference_style_family=_optional_text(payload.get("reference_style_family")),
        required_sections=_normalize_string_tuple(payload.get("required_sections")),
        declaration_requirements=_normalize_string_tuple(payload.get("declaration_requirements")),
        submission_checklist_items=_normalize_string_tuple(payload.get("submission_checklist_items")),
        template_assets=_normalize_string_tuple(payload.get("template_assets")),
        generated_at=_optional_text(payload.get("generated_at")),
    )


def render_journal_requirements_markdown(requirements: JournalRequirements) -> str:
    lines = [
        "# Journal Requirements",
        "",
        f"- Journal: `{requirements.journal_name}`",
        f"- Journal slug: `{requirements.journal_slug}`",
        f"- Official guidelines: `{requirements.official_guidelines_url}`",
        f"- Publication profile: `{requirements.publication_profile or 'unspecified'}`",
        f"- Abstract word cap: `{requirements.abstract_word_cap}`",
        f"- Title word cap: `{requirements.title_word_cap}`",
        f"- Keyword limit: `{requirements.keyword_limit}`",
        f"- Main text word cap: `{requirements.main_text_word_cap}`",
        f"- Main display budget: `{requirements.main_display_budget}`",
        f"- Table budget: `{requirements.table_budget}`",
        f"- Figure budget: `{requirements.figure_budget}`",
        f"- Supplementary allowed: `{str(requirements.supplementary_allowed).lower()}`",
        f"- Title page required: `{str(requirements.title_page_required).lower()}`",
        f"- Blinded main document: `{str(requirements.blinded_main_document).lower()}`",
        f"- Reference style family: `{requirements.reference_style_family or 'unspecified'}`",
    ]
    if requirements.required_sections:
        lines.extend(["", "## Required Sections", ""])
        lines.extend(f"- {item}" for item in requirements.required_sections)
    if requirements.declaration_requirements:
        lines.extend(["", "## Declaration Requirements", ""])
        lines.extend(f"- {item}" for item in requirements.declaration_requirements)
    if requirements.submission_checklist_items:
        lines.extend(["", "## Submission Checklist", ""])
        lines.extend(f"- {item}" for item in requirements.submission_checklist_items)
    return "\n".join(lines) + "\n"


def write_journal_requirements(
    *,
    study_root: Path,
    requirements: JournalRequirements,
) -> dict[str, str]:
    root = journal_requirements_root(study_root=study_root, journal_slug=requirements.journal_slug)
    root.mkdir(parents=True, exist_ok=True)
    payload = _serialize_requirements(requirements)
    json_path = root / "requirements.json"
    markdown_path = root / "requirements.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_journal_requirements_markdown(requirements), encoding="utf-8")
    return {
        "journal_slug": requirements.journal_slug,
        "requirements_path": str(json_path),
        "requirements_markdown_path": str(markdown_path),
    }


def load_journal_requirements(*, study_root: Path, journal_slug: str) -> JournalRequirements | None:
    path = journal_requirements_json_path(study_root=study_root, journal_slug=journal_slug)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return _requirements_from_payload(payload)


def describe_journal_submission_package(*, study_root: Path, journal_slug: str) -> dict[str, Any]:
    package_root = journal_submission_package_root(study_root=study_root, journal_slug=journal_slug)
    manifest_path = package_root / "submission_manifest.json"
    zip_path = package_root / f"{journal_slug}_submission_package.zip"
    if not package_root.exists() or not manifest_path.exists():
        return {
            "status": "missing",
            "package_root": str(package_root),
            "submission_manifest_path": str(manifest_path),
            "zip_path": str(zip_path),
        }

    required_paths = (
        package_root / "main_manuscript.docx",
        package_root / "main_manuscript.pdf",
        package_root / "journal_requirements_snapshot.json",
        zip_path,
    )
    missing_files = [str(path) for path in required_paths if not path.exists()]
    status = "current" if not missing_files else "incomplete"
    return {
        "status": status,
        "package_root": str(package_root),
        "submission_manifest_path": str(manifest_path),
        "zip_path": str(zip_path),
        "missing_files": missing_files,
    }
