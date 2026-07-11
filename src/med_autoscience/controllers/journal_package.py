from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.authority_route_gate import (
    attach_authority_route_gate,
)
from med_autoscience.controllers.authority_write_route import (
    blocked_authority_write_payload,
    resolve_authority_write_route_context,
)
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    normalize_publication_profile,
)
from med_autoscience.controllers.submission_package_layout import (
    build_analysis_results_from_source_contract,
    AUDIT_DIRNAME,
    build_package_layout_block,
    build_analysis_manifest_document,
    build_artifact_lineage_graph_document,
    build_software_environment_document,
    build_source_relative_paths_document,
    build_source_signature_document,
    reproducibility_path,
    resolve_submission_manifest_path,
    submission_manifest_path,
)


_USER_CONFIRMED_DECISION_SOURCES = {
    "human_confirmed",
    "physician_confirmed",
    "user",
    "user_confirmed",
    "user_selected",
}


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


def slugify_journal_name(journal_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(journal_name or "").strip().lower()).strip("-")
    if not normalized:
        raise ValueError("journal_name must resolve to a non-empty journal_slug")
    return normalized


def journal_requirements_root(*, study_root: Path, journal_slug: str) -> Path:
    return Path(study_root).expanduser().resolve() / "paper" / "journal_requirements" / journal_slug


def journal_requirements_json_path(*, study_root: Path, journal_slug: str) -> Path:
    return journal_requirements_root(study_root=study_root, journal_slug=journal_slug) / "requirements.json"


def journal_submission_package_root(*, study_root: Path, journal_slug: str) -> Path:
    return Path(study_root).expanduser().resolve() / "submission_packages" / journal_slug


def journal_requirements_snapshot_path(*, package_root: Path) -> Path:
    root = Path(package_root).expanduser().resolve()
    current = root / AUDIT_DIRNAME / "journal_requirements_snapshot.json"
    return current if current.exists() else root / "journal_requirements_snapshot.json"


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _normalize_string_tuple(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in values if str(item).strip())


def _requirements_from_payload(payload: dict[str, Any]) -> JournalRequirements:
    journal_name = _optional_text(payload.get("journal_name")) or "Journal Target"
    official_guidelines_url = _optional_text(payload.get("official_guidelines_url")) or ""
    if not official_guidelines_url:
        raise ValueError("official_guidelines_url is required")
    return JournalRequirements(
        journal_name=journal_name,
        journal_slug=_optional_text(payload.get("journal_slug")) or slugify_journal_name(journal_name),
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
    for title, items in (
        ("Required Sections", requirements.required_sections),
        ("Declaration Requirements", requirements.declaration_requirements),
        ("Submission Checklist", requirements.submission_checklist_items),
    ):
        if items:
            lines.extend(["", f"## {title}", ""])
            lines.extend(f"- {item}" for item in items)
    return "\n".join(lines) + "\n"


def write_journal_requirements(*, study_root: Path, requirements: JournalRequirements) -> dict[str, str]:
    root = journal_requirements_root(study_root=study_root, journal_slug=requirements.journal_slug)
    root.mkdir(parents=True, exist_ok=True)
    payload = asdict(requirements)
    for key in (
        "required_sections",
        "declaration_requirements",
        "submission_checklist_items",
        "template_assets",
    ):
        payload[key] = list(payload[key])
    payload["generated_at"] = requirements.generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
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
    return _requirements_from_payload(payload) if isinstance(payload, dict) else None


def describe_journal_submission_package(*, study_root: Path, journal_slug: str) -> dict[str, Any]:
    package_root = journal_submission_package_root(study_root=study_root, journal_slug=journal_slug)
    manifest_path = resolve_submission_manifest_path(package_root)
    zip_path = package_root / f"{journal_slug}_submission_package.zip"
    if not package_root.exists() or not manifest_path.exists():
        return {
            "status": "missing",
            "package_root": str(package_root),
            "submission_manifest_path": str(manifest_path),
            "zip_path": str(zip_path),
        }
    snapshot_path = journal_requirements_snapshot_path(package_root=package_root)
    required_paths = (
        package_root / "main_manuscript.docx",
        package_root / "main_manuscript.pdf",
        snapshot_path,
        zip_path,
    )
    missing_files = [str(path) for path in required_paths if not path.exists()]
    return {
        "status": "current" if not missing_files else "incomplete",
        "package_root": str(package_root),
        "submission_manifest_path": str(manifest_path),
        "journal_requirements_snapshot_path": str(snapshot_path),
        "zip_path": str(zip_path),
        "missing_files": missing_files,
    }


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


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _source_signature_payload(source_manifest: Mapping[str, Any]) -> dict[str, Any]:
    source_contract = source_manifest.get("source_contract")
    source_contract_payload = source_contract if isinstance(source_contract, dict) else {}
    source_signature = (
        str(source_manifest.get("source_signature") or source_contract_payload.get("source_signature") or "").strip()
        or None
    )
    source_paths = source_contract_payload.get("source_paths")
    source_files = source_contract_payload.get("source_files")
    return {
        "source_signature": source_signature,
        "source_contract": source_contract_payload,
        "source_paths": source_paths if isinstance(source_paths, list) else [],
        "source_files": source_files if isinstance(source_files, list) else [],
    }


def _write_journal_reproducibility_documents(
    *,
    package_root: Path,
    source_manifest: Mapping[str, Any],
) -> None:
    source_payload = _source_signature_payload(source_manifest)
    analysis_results = build_analysis_results_from_source_contract(source_payload["source_contract"])
    study_delivery_sync.dump_json(
        reproducibility_path(package_root, "source_signature"),
        build_source_signature_document(
            source_signature=source_payload["source_signature"] or "",
            source_contract=source_payload["source_contract"],
            package_role="journal_targeted_projection",
        ),
    )
    study_delivery_sync.dump_json(
        reproducibility_path(package_root, "source_relative_paths"),
        build_source_relative_paths_document(
            source_relative_paths=source_payload["source_paths"],
            source_files=source_payload["source_files"],
            package_role="journal_targeted_projection",
        ),
    )
    study_delivery_sync.dump_json(
        reproducibility_path(package_root, "analysis_manifest"),
        build_analysis_manifest_document(
            analysis_manifest_source=None,
            analysis_manifest_present=bool(analysis_results),
            package_role="journal_targeted_projection",
            analysis_results=analysis_results,
        ),
    )
    study_delivery_sync.dump_json(
        reproducibility_path(package_root, "software_environment"),
        build_software_environment_document(
            package_role="journal_targeted_projection",
        ),
    )
    study_delivery_sync.dump_json(
        reproducibility_path(package_root, "artifact_lineage_graph"),
        build_artifact_lineage_graph_document(
            package_role="journal_targeted_projection",
            source_signature=source_payload["source_signature"] or "",
            source_contract=source_payload["source_contract"],
        ),
    )


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
    authority_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_study_root = _resolve_study_root(paper_root=resolved_paper_root, study_root=study_root)
    resolved_route_context, authority_route_gate = resolve_authority_write_route_context(
        action="bundle_build",
        context=authority_route_context or route_context,
        default_paths=[resolved_study_root / "manuscript" / "journal_packages"],
    )
    if not bool(authority_route_gate.get("authorized")):
        return blocked_authority_write_payload(
            gate=authority_route_gate,
            study_root=str(resolved_study_root),
            paper_root=str(resolved_paper_root),
            journal_slug=journal_slug,
        )
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
    source_manifest_path = resolve_submission_manifest_path(source_root)
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
    requirements_snapshot_path = package_root / AUDIT_DIRNAME / "journal_requirements_snapshot.json"
    requirements_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
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
            "- Do not call it final journal-ready formatting unless `audit/submission_manifest.json` records a confirmed target and current requirements/QC.\n"
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
        "delivery_layout": build_package_layout_block(
            package_root=package_root,
            source_package_root=source_root,
            human_package_root=package_root,
            source_signature=str(source_manifest.get("source_signature") or "").strip() or None,
            package_role="journal_targeted_projection",
            legacy_input_status=(
                "v2_source_manifest_read"
                if source_manifest_path == submission_manifest_path(source_root)
                else "legacy_root_manifest_read"
            ),
            extra_audit_paths={
                "journal_requirements_snapshot": Path(AUDIT_DIRNAME) / "journal_requirements_snapshot.json",
            },
        ),
    }
    package_manifest_path = submission_manifest_path(package_root)
    package_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    package_manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_journal_reproducibility_documents(
        package_root=package_root,
        source_manifest=source_manifest,
    )
    _zip_package_root(package_root=package_root, zip_path=zip_path)
    package_status = describe_journal_submission_package(
        study_root=resolved_study_root,
        journal_slug=journal_slug,
    )
    return attach_authority_route_gate({
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
        "submission_manifest_path": str(package_manifest_path),
        "zip_path": str(zip_path),
        "package_status": package_status["status"],
    }, authority_route_gate)
