from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context


SYNC_STAGES = ("draft_handoff", "submission_minimal", "finalize")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def remove_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def clear_directory_contents(path: Path, *, keep_names: tuple[str, ...] = ()) -> list[str]:
    path.mkdir(parents=True, exist_ok=True)
    cleared_paths: list[str] = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        if child.name in keep_names:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        cleared_paths.append(str(child.resolve()))
    return cleared_paths


def can_sync_study_delivery(*, paper_root: Path) -> bool:
    try:
        _resolve_delivery_context(paper_root.resolve())
    except (FileNotFoundError, ValueError):
        return False
    return True


def _resolve_study_owned_paper_context(paper_root: Path) -> tuple[Path, Path, str] | None:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    if resolved_paper_root.name != "paper":
        return None
    study_root = resolved_paper_root.parent
    if study_root.parent.name != "studies":
        return None
    if not (study_root / "study.yaml").exists():
        return None
    return resolved_paper_root, study_root, study_root.name


def _resolve_delivery_context(paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    try:
        context = resolve_paper_root_context(resolved_paper_root)
    except (FileNotFoundError, ValueError):
        direct_context = _resolve_study_owned_paper_context(resolved_paper_root)
        if direct_context is None:
            raise
        resolved_paper_root, study_root, study_id = direct_context
        return {
            "paper_root": resolved_paper_root,
            "worktree_root": study_root,
            "study_id": study_id,
            "study_root": study_root,
        }
    return {
        "paper_root": context.paper_root,
        "worktree_root": context.worktree_root,
        "study_id": context.study_id,
        "study_root": context.study_root,
    }


def copy_file(
    *,
    source: Path,
    target: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> None:
    if not source.exists():
        raise FileNotFoundError(f"missing delivery source: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied_files.append(
        {
            "category": category,
            "source_path": str(source.resolve()),
            "target_path": str(target.resolve()),
        }
    )


def copy_tree(
    *,
    source_root: Path,
    target_root: Path,
    category: str,
    copied_files: list[dict[str, str]],
    ignore_filenames: tuple[str, ...] = (),
) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"missing delivery source directory: {source_root}")
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        if source.name in ignore_filenames:
            continue
        relative = source.relative_to(source_root)
        copy_file(
            source=source,
            target=target_root / relative,
            category=category,
            copied_files=copied_files,
        )


def build_submission_source_root(*, paper_root: Path, publication_profile: str) -> Path:
    normalized_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")
    if normalized_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return paper_root / "submission_minimal"
    return paper_root / "journal_submissions" / normalized_profile


def build_submission_package_readme(*, study_id: str, stage: str, publication_profile: str) -> str:
    normalized_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")
    if normalized_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return (
            f"# Submission Package\n\n"
            f"- Study: `{study_id}`\n"
            f"- Sync stage: `{stage}`\n"
            f"- Contents:\n"
            f"  - `manuscript.docx`\n"
            f"  - `paper.pdf`\n"
            f"  - `submission_manifest.json`\n"
            f"  - `figures/`\n"
            f"  - `tables/`\n\n"
            f"This directory is assembled automatically during study delivery sync so the manuscript and submission assets can be reviewed or handed off as one package.\n"
        )
    return (
        f"# Journal Submission Package\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{stage}`\n"
        f"- Publication profile: `{normalized_profile}`\n"
        f"- Contents:\n"
        f"  - `manuscript.docx`\n"
        f"  - `paper.pdf`\n"
        f"  - `submission_manifest.json`\n"
        f"  - `Supplementary_Material.docx` (when generated)\n"
        f"  - `figures/`\n"
        f"  - `tables/`\n\n"
        f"This journal-specific package is assembled automatically so the target-journal version can coexist with the generic final delivery.\n"
    )


def build_general_delivery_readme(*, study_id: str, stage: str, source_relative_root: str) -> str:
    return (
        f"# Study Final Delivery\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{stage}`\n"
        f"- Canonical authority surface: `paper/`\n"
        f"- Controller-authorized package source: `{source_relative_root}/`\n"
        f"- This directory: `manuscript/` (human-facing delivery root)\n"
        f"- Stable human-facing entry: `manuscript/current_package/`\n"
        f"- Delivery manifest: `manuscript/delivery_manifest.json`\n\n"
        f"This directory is refreshed automatically from the controller-authorized paper package. "
        f"Humans should open `manuscript/current_package/`, not reconstruct stage-specific paths.\n"
    )


def _submission_delivery_stale_reason_label(stale_reason: str | None) -> str:
    normalized = str(stale_reason or "").strip()
    if normalized == "current_submission_source_missing":
        return "the current authority submission package has not been materialized"
    if normalized == "delivery_manifest_sources_missing":
        return "the recorded mirror still references sources that no longer exist"
    if normalized == "delivery_manifest_source_mismatch":
        return "the recorded mirror points at a different authority package root"
    if normalized == "delivery_projection_missing":
        return "the stage-neutral current package projection has not been materialized yet"
    return normalized or "the current authority submission package is unavailable"


def build_unavailable_general_delivery_readme(
    *,
    study_id: str,
    stale_reason: str | None,
    source_relative_root: str,
) -> str:
    return (
        "# Study Final Delivery Unavailable\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: current submission package mirror is unavailable\n"
        f"- Reason: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/`\n"
        f"- Expected package root inside the authority surface: `{source_relative_root}/`\n"
        "- Human-facing delivery root: `manuscript/`\n\n"
        "This directory was cleared because the previous study-level mirror became stale. "
        "Wait for a fresh submission-minimal export before treating anything under `manuscript/` as the current package.\n"
    )


def build_preview_general_delivery_readme(
    *,
    study_id: str,
    stale_reason: str | None,
    source_relative_root: str,
) -> str:
    return (
        "# Study Delivery Audit Preview\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: audit preview only; not submission-ready\n"
        f"- Reason formal delivery is blocked: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/`\n"
        f"- Expected package root inside the authority surface: `{source_relative_root}/`\n"
        "- Human-facing review root: `manuscript/`\n\n"
        "This directory now exposes the latest auditable manuscript-facing materials that are still available from the authority surface. "
        "Treat it as a user review package only, not as a handoff-ready submission package.\n"
    )


def build_manuscript_root_readme() -> str:
    return (
        "# Manuscript Delivery Surface\n\n"
        "- Canonical authority surface: `paper/`\n"
        "- Human-facing delivery root: `manuscript/`\n"
        "- Stable human-facing package entry: `manuscript/current_package/`\n"
        "- Delivery manifest: `manuscript/delivery_manifest.json`\n\n"
        "Use `manuscript/` when a human needs the latest handoff-ready manuscript bundle. "
        "Edit or regenerate from `paper/`, not from this mirror.\n"
    )


def build_artifacts_root_readme() -> str:
    return (
        "# Artifact Auxiliary Surface\n\n"
        "- Canonical authority surface: `paper/`\n"
        "- Human-facing final delivery surface: `manuscript/`\n"
        "- This directory is reserved for machine-generated auxiliary/runtime/finalization evidence.\n"
        "- Figures/tables are no longer mirrored here during normal submission sync.\n\n"
        "Use `manuscript/` for the latest handoff-ready package. `artifacts/` is not part of the human-facing final delivery surface; touch it only when a runtime/finalize contract explicitly asks for auxiliary evidence.\n"
    )


def build_artifacts_finalize_readme(*, study_id: str, stage: str) -> str:
    return (
        f"# Finalization Evidence Surface\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{stage}`\n"
        "- This directory is not part of the human-facing final delivery surface.\n"
        "- Expected contents: finalize/manuscript build evidence such as `paper_bundle_manifest.json` and `compile_report.json`.\n"
        "- Stable human-facing package entry remains `manuscript/current_package/`.\n"
        "- Figures/tables remain in `manuscript/current_package/` for human review, and in `paper/` as authority.\n\n"
        "Use this directory only for machine-generated finalization evidence only, not for human-facing display lookup.\n"
    )


def build_unavailable_submission_package_readme(*, study_id: str, stale_reason: str | None) -> str:
    return (
        "# Submission Package Unavailable\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: current submission package mirror is unavailable\n"
        f"- Reason: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/submission_minimal/`\n"
        "- This directory no longer represents a current handoff-ready package.\n\n"
        "The previous mirror was cleared because the active authority package disappeared or no longer matches. "
        "Wait for a fresh submission-minimal export before using this path for review or handoff.\n"
    )


def build_submission_package_audit_preview_readme(*, study_id: str, stale_reason: str | None) -> str:
    return (
        "# Submission Package Audit Preview\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: audit preview only; not submission-ready\n"
        f"- Reason formal delivery is blocked: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/`\n"
        "- This package mirrors the latest still-available manuscript, figure, table, and audit materials for human review.\n"
        "- Do not treat this directory as the formal submission handoff until a fresh `submission_minimal` export is materialized.\n"
    )


def build_delivery_surface_roles(
    *,
    paper_root: Path,
    source_root: Path,
    manuscript_root: Path | None = None,
    current_package_root: Path | None = None,
    current_package_zip: Path | None = None,
    auxiliary_evidence_root: Path | None = None,
    journal_submission_mirror_root: Path | None = None,
) -> dict[str, str | None]:
    return {
        "controller_authorized_paper_root": str(paper_root),
        "controller_authorized_package_source_root": str(source_root),
        "human_facing_delivery_root": str(manuscript_root) if manuscript_root is not None else None,
        "human_facing_current_package_root": str(current_package_root) if current_package_root is not None else None,
        "human_facing_current_package_zip": str(current_package_zip) if current_package_zip is not None else None,
        "auxiliary_evidence_root": str(auxiliary_evidence_root) if auxiliary_evidence_root is not None else None,
        "journal_submission_mirror_root": (
            str(journal_submission_mirror_root) if journal_submission_mirror_root is not None else None
        ),
    }


def build_promoted_delivery_readme(*, study_id: str, publication_profile: str, source_relative_root: str) -> str:
    return (
        f"# Study Final Delivery\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{publication_profile}_submission`\n"
        f"- Publication profile: `{publication_profile}`\n"
        f"- Controller-authorized package source: `{source_relative_root}/`\n"
        f"- Contents:\n"
        f"  - `manuscript.docx`\n"
        f"  - `paper.pdf`\n"
        f"  - `submission_manifest.json`\n"
        f"  - `Supplementary_Material.docx` (when generated)\n"
        f"  - `current_package/`\n"
        f"  - `current_package.zip`\n"
        f"  - `journal_package_mirrors/{publication_profile}/`\n\n"
        f"This study-level final delivery is assembled automatically from the primary journal package so the canonical shallow handoff stays aligned with the active target-journal surface.\n"
    )


def ensure_manuscript_root_readme(*, manuscript_root: Path) -> None:
    readme_path = manuscript_root / "README.md"
    if readme_path.exists():
        return
    write_text(readme_path, build_manuscript_root_readme())


def resolve_finalize_resume_packet_source(*, paper_root: Path, worktree_root: Path) -> Path:
    candidates = [
        paper_root / "finalize_resume_packet.md",
        worktree_root / "handoffs" / "finalize_resume_packet.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "missing delivery source: no finalize resume packet found in "
        f"{paper_root / 'finalize_resume_packet.md'} or {worktree_root / 'handoffs' / 'finalize_resume_packet.md'}"
    )


def build_zip_from_directory(*, source_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(source_root.rglob("*")):
            if not source.is_file():
                continue
            archive.write(source, source.relative_to(source_root).as_posix())


def build_authority_source_relative_root(*, paper_root: Path, source_root: Path) -> str:
    return source_root.resolve().relative_to(paper_root.resolve().parent).as_posix()


def build_current_package_readme(*, study_id: str, stage: str, source_relative_root: str, status_line: str) -> str:
    return (
        "# Current Human Package\n\n"
        f"- Study: `{study_id}`\n"
        f"- Active sync stage: `{stage}`\n"
        f"- Status: {status_line}\n"
        f"- Controller-authorized source: `{source_relative_root}`\n"
        "- Canonical authority surface: `paper/`\n"
        "- This directory is the stable, stage-agnostic entry point for the latest human-facing package.\n\n"
        "Use this directory when a human wants the latest readable package without first deciding which stage-specific mirror to open. "
        "Regenerate from the controller-authorized source, not from this projection.\n"
    )


def sync_current_package_projection(
    *,
    source_root: Path,
    current_package_root: Path,
    current_package_zip: Path,
    study_id: str,
    stage: str,
    source_relative_root: str,
    status_line: str,
    copied_files: list[dict[str, str]],
    generated_files: list[dict[str, str]],
) -> None:
    reset_directory(current_package_root)
    copy_tree(
        source_root=source_root,
        target_root=current_package_root,
        category="current_package",
        copied_files=copied_files,
    )
    readme_path = current_package_root / "README.md"
    write_text(
        readme_path,
        build_current_package_readme(
            study_id=study_id,
            stage=stage,
            source_relative_root=source_relative_root,
            status_line=status_line,
        ),
    )
    generated_files.append(
        {
            "category": "current_package",
            "path": str(readme_path.resolve()),
        }
    )
    build_zip_from_directory(source_root=current_package_root, output_path=current_package_zip)
    generated_files.append(
        {
            "category": "current_package",
            "path": str(current_package_zip.resolve()),
        }
    )


def _copy_relative_files(
    *,
    source_root: Path,
    relative_paths: tuple[Path, ...],
    target_root: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> None:
    for relative_path in relative_paths:
        source = source_root / relative_path
        copy_file(
            source=source,
            target=target_root / relative_path,
            category=category,
            copied_files=copied_files,
        )


def _copy_optional_file(
    *,
    source: Path,
    target: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> bool:
    if not source.exists():
        return False
    copy_file(
        source=source,
        target=target,
        category=category,
        copied_files=copied_files,
    )
    return True


def _copy_optional_tree(
    *,
    source_root: Path,
    target_root: Path,
    category: str,
    copied_files: list[dict[str, str]],
    ignore_suffixes: tuple[str, ...] = (),
    ignore_filenames: tuple[str, ...] = (),
) -> int:
    if not source_root.exists():
        return 0
    relative_paths = _iter_relative_files(
        source_root,
        ignore_suffixes=ignore_suffixes,
        ignore_filenames=ignore_filenames,
    )
    for relative_path in relative_paths:
        copy_file(
            source=source_root / relative_path,
            target=target_root / relative_path,
            category=category,
            copied_files=copied_files,
        )
    return len(relative_paths)


def _iter_relative_files(
    source_root: Path,
    *,
    ignore_suffixes: tuple[str, ...] = (),
    ignore_filenames: tuple[str, ...] = (),
) -> tuple[Path, ...]:
    relative_paths: list[Path] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in ignore_filenames:
            continue
        if any(path.name.endswith(suffix) for suffix in ignore_suffixes):
            continue
        relative_paths.append(path.relative_to(source_root))
    return tuple(relative_paths)


def _draft_handoff_source_relative_paths(*, paper_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    required_files = (
        Path("draft.md"),
        Path("paper_bundle_manifest.json"),
    )
    missing_required = [str(path) for path in required_files if not (resolved_paper_root / path).exists()]
    if missing_required:
        raise FileNotFoundError(
            "missing draft handoff source files: " + ", ".join(missing_required)
        )

    relative_paths: list[Path] = list(required_files)
    optional_files = (
        Path("paper.pdf"),
        Path("manuscript.docx"),
        Path("references.bib"),
        Path("build/review_manuscript.md"),
        Path("build/compile_report.json"),
        Path("review/review.md"),
        Path("review/revision_log.md"),
        Path("review/submission_checklist.json"),
        Path("proofing/proofing_report.md"),
        Path("proofing/language_issues.md"),
        Path("proofing/page_images_manifest.json"),
        Path("selected_outline.json"),
        Path("claim_evidence_map.json"),
        Path("evidence_ledger.json"),
    )
    relative_paths.extend(path for path in optional_files if (resolved_paper_root / path).exists())
    if (resolved_paper_root / "figures").is_dir():
        relative_paths.extend(
            Path("figures") / path
            for path in _iter_relative_files(
                resolved_paper_root / "figures",
                ignore_suffixes=(".shell.json",),
            )
        )
    if (resolved_paper_root / "tables").is_dir():
        relative_paths.extend(
            Path("tables") / path
            for path in _iter_relative_files(
                resolved_paper_root / "tables",
                ignore_suffixes=(".shell.json",),
            )
        )
    deduped = sorted({path.as_posix(): path for path in relative_paths}.values(), key=lambda item: item.as_posix())
    return tuple(deduped)


def _draft_handoff_source_signature(*, paper_root: Path, relative_paths: tuple[Path, ...]) -> str:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    fingerprint_payload = []
    for relative_path in relative_paths:
        source = resolved_paper_root / relative_path
        stat = source.stat()
        fingerprint_payload.append(
            {
                "path": relative_path.as_posix(),
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
            }
        )
    canonical = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_draft_handoff_readme(*, study_id: str) -> str:
    return (
        "# Draft Handoff Delivery\n\n"
        f"- Study: `{study_id}`\n"
        "- Sync stage: `draft_handoff`\n"
        "- Status: review-only draft surface; not a submission-ready package\n"
        "- Canonical authority surface: `paper/`\n"
        "- Stable human-facing entry: `manuscript/current_package/`\n"
        "- Delivery manifest: `manuscript/delivery_manifest.json`\n\n"
        "This delivery mirrors the latest human-reviewable paper draft into the study shallow path. "
        "It does not relax the publication gate, and it must not be treated as a formal submission package.\n"
    )


def describe_draft_handoff_delivery(*, paper_root: Path) -> dict[str, Any]:
    if not can_sync_study_delivery(paper_root=paper_root):
        return {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        }

    context = _resolve_delivery_context(Path(paper_root).expanduser().resolve())
    resolved_paper_root = context["paper_root"]
    study_root = context["study_root"]
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_zip = study_root / "manuscript" / "current_package.zip"
    delivery_manifest_path = study_root / "manuscript" / "delivery_manifest.json"
    if not delivery_manifest_path.exists():
        return {
            "applicable": True,
            "status": "missing",
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "delivery_manifest_path": None,
        }
    try:
        manifest = json.loads(delivery_manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "applicable": True,
            "status": "invalid",
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "delivery_manifest_path": str(delivery_manifest_path),
        }
    if not isinstance(manifest, dict):
        return {
            "applicable": True,
            "status": "invalid",
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "delivery_manifest_path": str(delivery_manifest_path),
        }

    try:
        relative_paths = _draft_handoff_source_relative_paths(paper_root=resolved_paper_root)
        source_signature = _draft_handoff_source_signature(
            paper_root=resolved_paper_root,
            relative_paths=relative_paths,
        )
    except FileNotFoundError:
        return {
            "applicable": True,
            "status": "stale",
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "delivery_manifest_path": str(delivery_manifest_path),
        }

    recorded_surface_roles = manifest.get("surface_roles") or {}
    recorded_source_signature = str(manifest.get("source_signature") or "").strip()
    recorded_source_root = str((recorded_surface_roles or {}).get("controller_authorized_paper_root") or "").strip()
    projection_ready = current_package_root.exists() and current_package_zip.exists()
    status = (
        "current"
        if (
            recorded_source_signature == source_signature
            and recorded_source_root == str(resolved_paper_root)
            and projection_ready
        )
        else "stale"
    )
    return {
        "applicable": True,
        "status": status,
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
        "delivery_manifest_path": str(delivery_manifest_path),
    }


def describe_submission_delivery(
    *,
    paper_root: Path,
    publication_profile: str = "general_medical_journal",
) -> dict[str, Any]:
    if not can_sync_study_delivery(paper_root=paper_root):
        return {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": None,
            "current_package_zip": None,
            "missing_source_paths": [],
        }

    context = _resolve_delivery_context(Path(paper_root).expanduser().resolve())
    resolved_paper_root = context["paper_root"]
    study_root = context["study_root"]
    manuscript_root = study_root / "manuscript"
    delivery_manifest_path = manuscript_root / "delivery_manifest.json"
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    if not delivery_manifest_path.exists():
        return {
            "applicable": True,
            "status": "missing",
            "stale_reason": None,
            "delivery_manifest_path": None,
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": [],
        }
    try:
        manifest = json.loads(delivery_manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "delivery_manifest_invalid",
            "delivery_manifest_path": str(delivery_manifest_path),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": [],
        }
    if not isinstance(manifest, dict):
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "delivery_manifest_invalid",
            "delivery_manifest_path": str(delivery_manifest_path),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": [],
        }

    expected_source_root = build_submission_source_root(
        paper_root=resolved_paper_root,
        publication_profile=normalized_publication_profile,
    )
    expected_manifest_path = expected_source_root / "submission_manifest.json"
    if not expected_manifest_path.exists():
        missing_source_paths = sorted(
            {
                str(Path(item.get("source_path")).expanduser())
                for item in (manifest.get("copied_files") or [])
                if isinstance(item, dict) and str(item.get("source_path") or "").strip()
            }
        )
        return {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "current_submission_source_missing",
            "delivery_manifest_path": str(delivery_manifest_path),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
            "missing_source_paths": missing_source_paths,
        }

    recorded_surface_roles = manifest.get("surface_roles") or {}
    recorded_source_root = (
        str((recorded_surface_roles or {}).get("controller_authorized_package_source_root") or "").strip()
        or str(((manifest.get("source") or {}) if isinstance(manifest.get("source"), dict) else {}).get("package_source_root") or "").strip()
    )
    missing_source_paths = sorted(
        {
            str(Path(item.get("source_path")).expanduser().resolve())
            for item in (manifest.get("copied_files") or [])
            if isinstance(item, dict)
            and str(item.get("source_path") or "").strip()
            and not Path(str(item.get("source_path"))).expanduser().exists()
        }
    )
    if missing_source_paths:
        status = "stale_source_missing"
        stale_reason = "delivery_manifest_sources_missing"
    elif not current_package_root.exists() or not current_package_zip.exists():
        status = "stale_projection_missing"
        stale_reason = "delivery_projection_missing"
    elif recorded_source_root and recorded_source_root != str(expected_source_root.resolve()):
        status = "stale_source_mismatch"
        stale_reason = "delivery_manifest_source_mismatch"
    else:
        status = "current"
        stale_reason = None
    return {
        "applicable": True,
        "status": status,
        "stale_reason": stale_reason,
        "delivery_manifest_path": str(delivery_manifest_path),
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
        "missing_source_paths": missing_source_paths,
    }


def materialize_submission_delivery_stale_notice(
    *,
    paper_root: Path,
    stale_reason: str,
    missing_source_paths: list[str] | None = None,
    publication_profile: str = "general_medical_journal",
) -> dict[str, Any]:
    if not can_sync_study_delivery(paper_root=paper_root):
        return {
            "applicable": False,
            "status": "not_applicable",
            "stale_reason": None,
            "delivery_status_path": None,
            "current_package_root": None,
            "current_package_zip": None,
            "missing_source_paths": [],
            "cleared_paths": [],
        }

    context = _resolve_delivery_context(Path(paper_root).expanduser().resolve())
    resolved_paper_root = context["paper_root"]
    study_root = context["study_root"]
    study_id = context["study_id"]
    manuscript_root = study_root / "manuscript"
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    delivery_manifest_path = manuscript_root / "delivery_manifest.json"
    delivery_status_path = manuscript_root / "delivery_status.json"
    cleared_paths = clear_directory_contents(manuscript_root, keep_names=("delivery_manifest.json",))
    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []

    expected_source_root = build_submission_source_root(
        paper_root=resolved_paper_root,
        publication_profile=normalized_publication_profile,
    )
    source_relative_root = build_authority_source_relative_root(
        paper_root=resolved_paper_root,
        source_root=expected_source_root,
    )
    manuscript_root.mkdir(parents=True, exist_ok=True)
    current_package_root.mkdir(parents=True, exist_ok=True)
    preview_file_count = 0
    for name in ("manuscript.docx", "paper.pdf", "submission_manifest.json"):
        if _copy_optional_file(
            source=expected_source_root / name,
            target=manuscript_root / name,
            category="preview_delivery_root",
            copied_files=copied_files,
        ):
            preview_file_count += 1
            copy_file(
                source=manuscript_root / name,
                target=current_package_root / name,
                category="preview_current_package",
                copied_files=copied_files,
            )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "build" / "review_manuscript.md",
            target=current_package_root / "review_manuscript.md",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "build" / "compile_report.json",
            target=current_package_root / "compile_report.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "review" / "submission_checklist.json",
            target=current_package_root / "submission_checklist.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "paper_bundle_manifest.json",
            target=current_package_root / "paper_bundle_manifest.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "figures" / "figure_catalog.json",
            target=current_package_root / "figures" / "figure_catalog.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += _copy_optional_tree(
        source_root=resolved_paper_root / "figures" / "generated",
        target_root=current_package_root / "figures",
        category="preview_current_package",
        copied_files=copied_files,
        ignore_suffixes=(".layout.json",),
        ignore_filenames=("README.md",),
    )
    preview_file_count += int(
        _copy_optional_file(
            source=resolved_paper_root / "tables" / "table_catalog.json",
            target=current_package_root / "tables" / "table_catalog.json",
            category="preview_current_package",
            copied_files=copied_files,
        )
    )
    preview_file_count += _copy_optional_tree(
        source_root=resolved_paper_root / "tables" / "generated",
        target_root=current_package_root / "tables",
        category="preview_current_package",
        copied_files=copied_files,
        ignore_filenames=("README.md",),
    )
    write_text(
        manuscript_root / "README.md",
        build_preview_general_delivery_readme(
            study_id=study_id,
            stale_reason=stale_reason,
            source_relative_root=source_relative_root,
        ),
    )
    generated_files.append(
        {
            "category": "preview_delivery_readme",
            "path": str((manuscript_root / "README.md").resolve()),
        }
    )
    current_package_readme_path = current_package_root / "README.md"
    write_text(
        current_package_readme_path,
        build_current_package_readme(
            study_id=study_id,
            stage="submission_preview",
            source_relative_root=source_relative_root,
            status_line="audit preview only; not submission-ready",
        ),
    )
    generated_files.append(
        {
            "category": "preview_current_package",
            "path": str(current_package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(source_root=current_package_root, output_path=current_package_zip)
    generated_files.append(
        {
            "category": "preview_current_package",
            "path": str(current_package_zip.resolve()),
        }
    )
    status_payload = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "study_id": study_id,
        "publication_profile": normalized_publication_profile,
        "status": "stale_source_missing",
        "stale_reason": stale_reason,
        "preview_mode": "authority_audit_preview",
        "submission_ready": False,
        "preview_file_count": preview_file_count,
        "source": {
            "paper_root": str(resolved_paper_root),
            "expected_package_source_root": str(expected_source_root),
        },
        "active_delivery_manifest_path": str(delivery_manifest_path) if delivery_manifest_path.exists() else None,
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
        "missing_source_paths": list(missing_source_paths or []),
        "cleared_paths": cleared_paths,
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    generated_files.append(
        {
            "category": "preview_delivery_status",
            "path": str(delivery_status_path.resolve()),
        }
    )
    dump_json(delivery_status_path, status_payload)
    return {
        "applicable": True,
        **status_payload,
        "delivery_status_path": str(delivery_status_path),
    }


def sync_draft_handoff_delivery(
    *,
    paper_root: Path,
    study_id: str,
    study_root: Path,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    relative_paths = _draft_handoff_source_relative_paths(paper_root=paper_root)
    source_signature = _draft_handoff_source_signature(
        paper_root=paper_root,
        relative_paths=relative_paths,
    )
    source_relative_root = build_authority_source_relative_root(
        paper_root=paper_root,
        source_root=paper_root,
    )

    reset_directory(manuscript_root)
    _copy_relative_files(
        source_root=paper_root,
        relative_paths=relative_paths,
        target_root=current_package_root,
        category="draft_handoff",
        copied_files=copied_files,
    )

    readme_path = manuscript_root / "README.md"
    write_text(readme_path, build_draft_handoff_readme(study_id=study_id))
    generated_files.append(
        {
            "category": "delivery_readme",
            "path": str(readme_path.resolve()),
        }
    )
    current_package_readme_path = current_package_root / "README.md"
    write_text(
        current_package_readme_path,
        build_current_package_readme(
            study_id=study_id,
            stage="draft_handoff",
            source_relative_root=source_relative_root,
            status_line="review-only draft surface; not a submission-ready package",
        ),
    )
    generated_files.append(
        {
            "category": "current_package",
            "path": str(current_package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(source_root=current_package_root, output_path=current_package_zip)
    generated_files.append(
        {
            "category": "current_package",
            "path": str(current_package_zip.resolve()),
        }
    )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": "draft_handoff",
        "study_id": study_id,
        "quest_id": study_id,
        "source_signature": source_signature,
        "source_relative_paths": [path.as_posix() for path in relative_paths],
        "source": {
            "paper_root": str(paper_root),
        },
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=paper_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
        ),
        "targets": {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
        },
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    dump_json(manuscript_root / "delivery_manifest.json", manifest)
    return manifest


def sync_general_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    artifacts_final_root = study_root / "artifacts" / "final"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"

    reset_directory(manuscript_root)
    remove_directory(artifacts_final_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile="general_medical_journal")
    source_relative_root = build_authority_source_relative_root(paper_root=paper_root, source_root=source_root)

    copy_file(
        source=source_root / "manuscript.docx",
        target=manuscript_root / "manuscript.docx",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "paper.pdf",
        target=manuscript_root / "paper.pdf",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "submission_manifest.json",
        target=manuscript_root / "submission_manifest.json",
        category="manifest",
        copied_files=copied_files,
    )
    if normalized_stage == "finalize":
        reset_directory(artifacts_final_root)
        copy_file(
            source=worktree_root / "SUMMARY.md",
            target=manuscript_root / "SUMMARY.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=worktree_root / "status.md",
            target=manuscript_root / "status.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "final_claim_ledger.md",
            target=manuscript_root / "final_claim_ledger.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=resolve_finalize_resume_packet_source(paper_root=paper_root, worktree_root=worktree_root),
            target=manuscript_root / "finalize_resume_packet.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "paper_bundle_manifest.json",
            target=artifacts_final_root / "paper_bundle_manifest.json",
            category="manifest",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "build" / "compile_report.json",
            target=artifacts_final_root / "compile_report.json",
            category="manifest",
            copied_files=copied_files,
        )

    readme_path = manuscript_root / "README.md"
    write_text(
        readme_path,
        build_general_delivery_readme(
            study_id=study_id,
            stage=normalized_stage,
            source_relative_root=source_relative_root,
        ),
    )
    generated_files.append(
        {
            "category": "delivery_readme",
            "path": str(readme_path.resolve()),
        }
    )
    if normalized_stage == "finalize":
        artifacts_readme_path = artifacts_final_root / "README.md"
        write_text(
            artifacts_readme_path,
            build_artifacts_finalize_readme(study_id=study_id, stage=normalized_stage),
        )
        generated_files.append(
            {
                "category": "artifact_readme",
                "path": str(artifacts_readme_path.resolve()),
            }
        )

    sync_current_package_projection(
        source_root=source_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        study_id=study_id,
        stage=normalized_stage,
        source_relative_root=source_relative_root,
        status_line="human-facing manuscript handoff surface",
        copied_files=copied_files,
        generated_files=generated_files,
    )

    targets = {
        "study_root": str(study_root),
        "manuscript_root": str(manuscript_root),
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
    }
    if normalized_stage == "finalize":
        targets["artifacts_final_root"] = str(artifacts_final_root)

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": normalized_stage,
        "study_id": study_id,
        "quest_id": study_id,
        "publication_profile": "general_medical_journal",
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
        },
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            auxiliary_evidence_root=artifacts_final_root if normalized_stage == "finalize" else None,
        ),
        "targets": targets,
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    dump_json(manuscript_root / "delivery_manifest.json", manifest)
    return manifest


def sync_journal_specific_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    publication_profile: str,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    journal_package_root = manuscript_root / "journal_packages" / publication_profile
    journal_package_zip = manuscript_root / f"{publication_profile}_submission_package.zip"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile=publication_profile)
    source_relative_root = build_authority_source_relative_root(paper_root=paper_root, source_root=source_root)

    manuscript_root.mkdir(parents=True, exist_ok=True)
    journal_package_root.parent.mkdir(parents=True, exist_ok=True)
    ensure_manuscript_root_readme(manuscript_root=manuscript_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())
    reset_directory(journal_package_root)

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    copy_file(
        source=source_root / "manuscript.docx",
        target=journal_package_root / "manuscript.docx",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "paper.pdf",
        target=journal_package_root / "paper.pdf",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "submission_manifest.json",
        target=journal_package_root / "submission_manifest.json",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    supplementary_docx = source_root / "Supplementary_Material.docx"
    if supplementary_docx.exists():
        copy_file(
            source=supplementary_docx,
            target=journal_package_root / "Supplementary_Material.docx",
            category="journal_submission_package",
            copied_files=copied_files,
        )
    copy_tree(
        source_root=source_root / "figures",
        target_root=journal_package_root / "figures",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=source_root / "tables",
        target_root=journal_package_root / "tables",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    package_readme_path = journal_package_root / "README.md"
    write_text(
        package_readme_path,
        build_submission_package_readme(
            study_id=study_id,
            stage=normalized_stage,
            publication_profile=publication_profile,
        ),
    )
    generated_files.append(
        {
            "category": "journal_submission_package",
            "path": str(package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(
        source_root=journal_package_root,
        output_path=journal_package_zip,
    )
    generated_files.append(
        {
            "category": "journal_submission_package",
            "path": str(journal_package_zip.resolve()),
        }
    )
    sync_current_package_projection(
        source_root=journal_package_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        study_id=study_id,
        stage=f"{publication_profile}_{normalized_stage}",
        source_relative_root=source_relative_root,
        status_line="journal-specific human-facing manuscript package",
        copied_files=copied_files,
        generated_files=generated_files,
    )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": normalized_stage,
        "study_id": study_id,
        "quest_id": study_id,
        "publication_profile": publication_profile,
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
            "package_source_root": str(source_root),
        },
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            auxiliary_evidence_root=None,
        ),
        "targets": {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "journal_package_root": str(journal_package_root),
            "journal_package_zip": str(journal_package_zip),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
        },
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    dump_json(journal_package_root / "delivery_manifest.json", manifest)
    return manifest


def sync_promoted_journal_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    publication_profile: str,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    artifacts_final_root = study_root / "artifacts" / "final"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    mirror_root = manuscript_root / "journal_package_mirrors" / publication_profile
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile=publication_profile)
    source_relative_root = build_authority_source_relative_root(paper_root=paper_root, source_root=source_root)

    reset_directory(manuscript_root)
    remove_directory(artifacts_final_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    copy_file(
        source=source_root / "manuscript.docx",
        target=manuscript_root / "manuscript.docx",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "paper.pdf",
        target=manuscript_root / "paper.pdf",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "submission_manifest.json",
        target=manuscript_root / "submission_manifest.json",
        category="manifest",
        copied_files=copied_files,
    )
    supplementary_docx = source_root / "Supplementary_Material.docx"
    if supplementary_docx.exists():
        copy_file(
            source=supplementary_docx,
            target=manuscript_root / "Supplementary_Material.docx",
            category="manuscript",
            copied_files=copied_files,
        )
    if normalized_stage == "finalize":
        reset_directory(artifacts_final_root)
        copy_file(
            source=worktree_root / "SUMMARY.md",
            target=manuscript_root / "SUMMARY.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=worktree_root / "status.md",
            target=manuscript_root / "status.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "final_claim_ledger.md",
            target=manuscript_root / "final_claim_ledger.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=resolve_finalize_resume_packet_source(paper_root=paper_root, worktree_root=worktree_root),
            target=manuscript_root / "finalize_resume_packet.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "paper_bundle_manifest.json",
            target=artifacts_final_root / "paper_bundle_manifest.json",
            category="manifest",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "build" / "compile_report.json",
            target=artifacts_final_root / "compile_report.json",
            category="manifest",
            copied_files=copied_files,
        )

    readme_path = manuscript_root / "README.md"
    write_text(
        readme_path,
        build_promoted_delivery_readme(
            study_id=study_id,
            publication_profile=publication_profile,
            source_relative_root=source_relative_root,
        ),
    )
    generated_files.append(
        {
            "category": "delivery_readme",
            "path": str(readme_path.resolve()),
        }
    )
    if normalized_stage == "finalize":
        artifacts_readme_path = artifacts_final_root / "README.md"
        write_text(
            artifacts_readme_path,
            build_artifacts_finalize_readme(study_id=study_id, stage=normalized_stage),
        )
        generated_files.append(
            {
                "category": "artifact_readme",
                "path": str(artifacts_readme_path.resolve()),
            }
        )

    sync_current_package_projection(
        source_root=source_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        study_id=study_id,
        stage=f"{publication_profile}_submission",
        source_relative_root=source_relative_root,
        status_line="promoted human-facing manuscript handoff surface",
        copied_files=copied_files,
        generated_files=generated_files,
    )

    reset_directory(mirror_root)
    copy_tree(
        source_root=source_root,
        target_root=mirror_root,
        category="journal_submission_mirror",
        copied_files=copied_files,
    )
    mirror_readme_path = mirror_root / "README.md"
    write_text(
        mirror_readme_path,
        build_submission_package_readme(
            study_id=study_id,
            stage=f"{publication_profile}_submission_mirror",
            publication_profile=publication_profile,
        ),
    )
    mirror_generated_files = [
        {
            "category": "journal_submission_mirror",
            "path": str(mirror_readme_path.resolve()),
        }
    ]
    mirror_manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": f"{publication_profile}_submission_mirror",
        "study_id": study_id,
        "quest_id": study_id,
        "publication_profile": publication_profile,
        "source": {
            "paper_root": str(paper_root),
            "package_source_root": str(source_root),
        },
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            journal_submission_mirror_root=mirror_root,
        ),
        "targets": {
            "study_root": str(study_root),
            "journal_package_root": str(mirror_root),
        },
        "copied_files": [
            item
            for item in copied_files
            if item["category"] == "journal_submission_mirror"
        ],
        "generated_files": mirror_generated_files,
    }
    dump_json(mirror_root / "delivery_manifest.json", mirror_manifest)

    targets = {
        "study_root": str(study_root),
        "manuscript_root": str(manuscript_root),
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
        "journal_package_mirror_root": str(mirror_root),
    }
    if normalized_stage == "finalize":
        targets["artifacts_final_root"] = str(artifacts_final_root)

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": f"{publication_profile}_submission",
        "study_id": study_id,
        "quest_id": study_id,
        "publication_profile": publication_profile,
        "source": {
            "paper_root": str(paper_root),
            "package_source_root": str(source_root),
        },
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            auxiliary_evidence_root=artifacts_final_root if normalized_stage == "finalize" else None,
            journal_submission_mirror_root=mirror_root,
        ),
        "targets": targets,
        "copied_files": [
            item
            for item in copied_files
            if item["category"] != "journal_submission_mirror"
        ],
        "generated_files": generated_files,
    }
    dump_json(manuscript_root / "delivery_manifest.json", manifest)
    return manifest


def sync_study_delivery(
    *,
    paper_root: Path,
    stage: str,
    publication_profile: str = "general_medical_journal",
    promote_to_final: bool = False,
) -> dict[str, Any]:
    normalized_stage = str(stage or "").strip()
    if normalized_stage not in SYNC_STAGES:
        raise ValueError(f"unsupported sync stage: {stage}")
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_publication_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")

    context = _resolve_delivery_context(paper_root.resolve())
    paper_root = context["paper_root"]
    worktree_root = context["worktree_root"]
    study_id = context["study_id"]
    study_root = context["study_root"]

    if normalized_stage == "draft_handoff":
        if normalized_publication_profile != GENERAL_MEDICAL_JOURNAL_PROFILE:
            raise ValueError("draft_handoff only supports the general_medical_journal profile")
        return sync_draft_handoff_delivery(
            paper_root=paper_root,
            study_id=study_id,
            study_root=study_root,
        )

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return sync_general_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
        )

    if not is_supported_publication_profile(normalized_publication_profile):
        raise ValueError(f"unsupported publication profile: {normalized_publication_profile}")

    if promote_to_final:
        return sync_promoted_journal_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
            publication_profile=normalized_publication_profile,
        )

    return sync_journal_specific_delivery(
        paper_root=paper_root,
        worktree_root=worktree_root,
        study_id=study_id,
        study_root=study_root,
        normalized_stage=normalized_stage,
        publication_profile=normalized_publication_profile,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync finalized paper deliverables into the study shallow path.")
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--stage", choices=SYNC_STAGES, required=True)
    parser.add_argument("--publication-profile", default="general_medical_journal")
    parser.add_argument("--promote-to-final", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sync_study_delivery(
        paper_root=args.paper_root,
        stage=args.stage,
        publication_profile=args.publication_profile,
        promote_to_final=args.promote_to_final,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
