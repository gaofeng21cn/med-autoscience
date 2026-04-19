from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from med_autoscience.journal_requirements import (
    describe_journal_submission_package,
    journal_requirements_json_path,
    journal_submission_package_root,
    load_journal_requirements,
)
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    normalize_publication_profile,
)
from med_autoscience.controllers import study_delivery_sync


def _resolve_study_root(*, paper_root: Path, study_root: Path | None) -> Path:
    if study_root is not None:
        return Path(study_root).expanduser().resolve()
    context = study_delivery_sync._resolve_delivery_context(Path(paper_root).expanduser().resolve())
    return Path(context["study_root"]).expanduser().resolve()


def _copy_if_exists(*, source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def _zip_package_root(*, package_root: Path, zip_path: Path) -> None:
    temporary_zip = package_root.parent / f".{zip_path.name}.tmp"
    if temporary_zip.exists():
        temporary_zip.unlink()
    with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(package_root.rglob("*")):
            if not source.is_file():
                continue
            archive.write(source, source.relative_to(package_root).as_posix())
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(temporary_zip), str(zip_path))


def _render_title_page_markdown(*, journal_name: str, placeholders: dict[str, Any]) -> str:
    lines = [
        "# Title Page",
        "",
        f"- Target journal: `{journal_name}`",
        f"- Authors: `{placeholders.get('authors') or 'pending'}`",
        f"- Affiliations: `{placeholders.get('affiliations') or 'pending'}`",
        f"- Corresponding author: `{placeholders.get('corresponding_author') or 'pending'}`",
        f"- Funding: `{placeholders.get('funding') or 'pending'}`",
        f"- Ethics: `{placeholders.get('ethics') or 'pending'}`",
        f"- Data availability: `{placeholders.get('data_availability') or 'pending'}`",
    ]
    return "\n".join(lines) + "\n"


def _render_declarations_markdown(*, declaration_requirements: tuple[str, ...], placeholders: dict[str, Any]) -> str:
    lines = ["# Declarations", ""]
    if not declaration_requirements:
        lines.append("- No journal-specific declaration sections were recorded.")
        return "\n".join(lines) + "\n"
    for item in declaration_requirements:
        key = item.strip().lower().replace(" ", "_")
        lines.append(f"## {item}")
        lines.append("")
        lines.append(str(placeholders.get(key) or "pending"))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def materialize_journal_package(
    *,
    paper_root: Path,
    study_root: Path,
    journal_slug: str,
    publication_profile: str | None = None,
) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_study_root = _resolve_study_root(paper_root=resolved_paper_root, study_root=study_root)
    requirements = load_journal_requirements(
        study_root=resolved_study_root,
        journal_slug=journal_slug,
    )
    if requirements is None:
        raise FileNotFoundError(f"missing journal requirements for {journal_slug}")

    resolved_profile = normalize_publication_profile(
        publication_profile or requirements.publication_profile or GENERAL_MEDICAL_JOURNAL_PROFILE
    )
    source_root = study_delivery_sync.build_submission_source_root(
        paper_root=resolved_paper_root,
        publication_profile=resolved_profile,
    )
    source_manifest_path = source_root / "submission_manifest.json"
    if not source_manifest_path.exists():
        raise FileNotFoundError(f"missing submission manifest: {source_manifest_path}")

    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    placeholders = source_manifest.get("front_matter_placeholders") or {}
    package_root = journal_submission_package_root(
        study_root=resolved_study_root,
        journal_slug=journal_slug,
    )
    study_delivery_sync.reset_directory(package_root)

    _copy_if_exists(source=source_root / "manuscript.docx", target=package_root / "main_manuscript.docx")
    _copy_if_exists(source=source_root / "paper.pdf", target=package_root / "main_manuscript.pdf")
    _copy_if_exists(
        source=source_root / "Supplementary_Material.docx",
        target=package_root / "supplementary" / "Supplementary_Material.docx",
    )
    if (source_root / "figures").exists():
        shutil.copytree(source_root / "figures", package_root / "figures", dirs_exist_ok=True)
    if (source_root / "tables").exists():
        shutil.copytree(source_root / "tables", package_root / "tables", dirs_exist_ok=True)

    requirements_path = journal_requirements_json_path(
        study_root=resolved_study_root,
        journal_slug=journal_slug,
    )
    requirements_snapshot_path = package_root / "journal_requirements_snapshot.json"
    requirements_snapshot_path.write_text(
        requirements_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    if requirements.title_page_required:
        study_delivery_sync.write_text(
            package_root / "title_page.md",
            _render_title_page_markdown(
                journal_name=requirements.journal_name,
                placeholders=placeholders,
            ),
        )
    study_delivery_sync.write_text(
        package_root / "declarations.md",
        _render_declarations_markdown(
            declaration_requirements=requirements.declaration_requirements,
            placeholders=placeholders,
        ),
    )
    submission_todo = study_delivery_sync.build_submission_todo_from_manifest(
        manifest_path=source_manifest_path,
    )
    if submission_todo is not None:
        study_delivery_sync.write_text(package_root / "SUBMISSION_TODO.md", submission_todo)
    study_delivery_sync.write_text(
        package_root / "README.md",
        (
            "# Journal Submission Package\n\n"
            f"- Journal: `{requirements.journal_name}`\n"
            f"- Journal slug: `{requirements.journal_slug}`\n"
            f"- Publication profile: `{resolved_profile}`\n"
            "- Stable shallow handoff for journal-specific submission review.\n"
        ),
    )

    zip_path = package_root / f"{journal_slug}_submission_package.zip"
    manifest = {
        "schema_version": 1,
        "generated_at": study_delivery_sync.utc_now(),
        "status": "materialized",
        "journal_name": requirements.journal_name,
        "journal_slug": requirements.journal_slug,
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "publication_profile": resolved_profile,
        "requirements_path": str(requirements_path),
        "source_submission_root": str(source_root),
        "source_submission_manifest_path": str(source_manifest_path),
        "front_matter_placeholders": placeholders,
        "title_page_required": requirements.title_page_required,
        "declaration_requirements": list(requirements.declaration_requirements),
        "paths": {
            "package_root": str(package_root),
            "zip_path": str(zip_path),
            "main_manuscript_docx": str(package_root / "main_manuscript.docx"),
            "main_manuscript_pdf": str(package_root / "main_manuscript.pdf"),
            "requirements_snapshot": str(requirements_snapshot_path),
            "title_page_markdown": str(package_root / "title_page.md") if requirements.title_page_required else None,
            "declarations_markdown": str(package_root / "declarations.md"),
        },
    }
    (package_root / "submission_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _zip_package_root(package_root=package_root, zip_path=zip_path)
    package_status = describe_journal_submission_package(
        study_root=resolved_study_root,
        journal_slug=journal_slug,
    )
    return {
        "status": "materialized",
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "journal_slug": journal_slug,
        "journal_name": requirements.journal_name,
        "publication_profile": resolved_profile,
        "package_root": str(package_root),
        "submission_manifest_path": str(package_root / "submission_manifest.json"),
        "zip_path": str(zip_path),
        "package_status": package_status["status"],
    }
