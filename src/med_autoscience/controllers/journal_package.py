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
    slugify_journal_name,
)
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    normalize_publication_profile,
)
from med_autoscience.controllers import study_delivery_sync


_USER_CONFIRMED_DECISION_SOURCES = {
    "human_confirmed",
    "physician_confirmed",
    "user",
    "user_confirmed",
    "user_selected",
}


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


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _paper_authority_summary(*, paper_root: Path, study_root: Path, source_root: Path) -> dict[str, Any]:
    canonical_paper_root = (study_root / "paper").expanduser().resolve()
    is_study_canonical = paper_root == canonical_paper_root
    return {
        "authority_kind": "study_canonical_paper" if is_study_canonical else "runtime_worktree_paper",
        "paper_root": str(paper_root),
        "study_canonical_paper_root": str(canonical_paper_root),
        "is_study_canonical_paper_root": is_study_canonical,
        "source_submission_root": str(source_root),
    }


def _journal_target_authority(
    *,
    paper_root: Path,
    journal_slug: str,
    confirmed_target: bool,
) -> dict[str, Any]:
    resolved_targets_path = paper_root / "submission_targets.resolved.json"
    payload = _load_json_object(resolved_targets_path)
    primary_target = payload.get("primary_target")
    primary_target_payload = primary_target if isinstance(primary_target, dict) else {}
    target_slug = str(primary_target_payload.get("journal_slug") or "").strip()
    target_name = str(primary_target_payload.get("journal_name") or "").strip()
    if not target_slug and target_name:
        target_slug = slugify_journal_name(target_name)
    target_matches = not target_slug or target_slug == journal_slug
    decision_source = str(
        primary_target_payload.get("decision_source")
        or payload.get("decision_source")
        or ""
    ).strip()
    decision_kind = str(
        primary_target_payload.get("decision_kind")
        or payload.get("decision_kind")
        or ""
    ).strip()
    target_user_confirmed = (
        confirmed_target
        or bool(primary_target_payload.get("user_confirmed"))
        or bool(payload.get("user_confirmed"))
        or str(primary_target_payload.get("target_confirmation_status") or "").strip().lower() == "confirmed"
        or str(payload.get("target_confirmation_status") or "").strip().lower() == "confirmed"
        or decision_source.strip().lower() in _USER_CONFIRMED_DECISION_SOURCES
    )
    confirmation_status = "confirmed" if target_user_confirmed else "unconfirmed"
    confirmation_basis = "explicit_controller_argument" if confirmed_target else None
    if confirmation_basis is None and target_user_confirmed:
        confirmation_basis = "target_payload"
    if confirmation_basis is None:
        confirmation_basis = "no_user_confirmation_recorded"
    return {
        "source_path": str(resolved_targets_path) if resolved_targets_path.exists() else None,
        "target_matches_requested_slug": target_matches,
        "journal_name": target_name or None,
        "journal_slug": target_slug or journal_slug,
        "decision_kind": decision_kind or None,
        "decision_source": decision_source or None,
        "resolution_status": primary_target_payload.get("resolution_status"),
        "user_confirmed": target_user_confirmed,
        "confirmation_status": confirmation_status,
        "confirmation_basis": confirmation_basis,
    }


def _formatting_boundary(
    *,
    publication_profile: str,
    target_authority: dict[str, Any],
    requirements_path: Path,
) -> dict[str, Any]:
    user_confirmed = bool(target_authority.get("user_confirmed"))
    return {
        "package_role": "journal_targeted_projection",
        "publication_profile": publication_profile,
        "requirements_snapshot_present": requirements_path.exists(),
        "journal_submission_ready_claim_allowed": user_confirmed,
        "boundary_reason": "target_user_confirmed" if user_confirmed else "target_not_user_confirmed",
    }


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
    confirmed_target: bool = False,
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
    source_authority = _paper_authority_summary(
        paper_root=resolved_paper_root,
        study_root=resolved_study_root,
        source_root=source_root,
    )
    target_authority = _journal_target_authority(
        paper_root=resolved_paper_root,
        journal_slug=requirements.journal_slug,
        confirmed_target=confirmed_target,
    )
    formatting_boundary = _formatting_boundary(
        publication_profile=resolved_profile,
        target_authority=target_authority,
        requirements_path=requirements_path,
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
            "- Package role: `journal_targeted_projection`\n"
            f"- Target confirmation: `{target_authority['confirmation_status']}`\n"
            f"- Source authority: `{source_authority['authority_kind']}`\n"
            "- Default human-facing package: `manuscript/current_package/`\n"
            "- This directory is a derived target-journal projection, not the default manuscript review entry.\n"
            "- Do not call it final journal-ready formatting unless `submission_manifest.json` records a confirmed target and current requirements/QC.\n"
        ),
    )

    zip_path = package_root / f"{journal_slug}_submission_package.zip"
    manifest = {
        "schema_version": 1,
        "generated_at": study_delivery_sync.utc_now(),
        "status": "materialized",
        "package_role": "journal_targeted_projection",
        "default_human_facing_package_root": str(resolved_study_root / "manuscript" / "current_package"),
        "journal_name": requirements.journal_name,
        "journal_slug": requirements.journal_slug,
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "publication_profile": resolved_profile,
        "requirements_path": str(requirements_path),
        "source_authority": source_authority,
        "journal_target_authority": target_authority,
        "formatting_boundary": formatting_boundary,
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
        "package_role": "journal_targeted_projection",
        "target_confirmation_status": target_authority["confirmation_status"],
        "source_authority_kind": source_authority["authority_kind"],
        "is_study_canonical_paper_root": source_authority["is_study_canonical_paper_root"],
        "package_root": str(package_root),
        "submission_manifest_path": str(package_root / "submission_manifest.json"),
        "zip_path": str(zip_path),
        "package_status": package_status["status"],
    }
