from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context

from .staging_and_sources import (
    SYNC_STAGES,
    FORMAL_PAPER_DELIVERY_RELATIVE_PATHS,
    utc_now,
    dump_json,
    _normalized_path,
    _build_ledger_contract_linkage,
    build_charter_contract_linkage,
    write_text,
    reset_directory,
    remove_directory,
    create_staging_root,
    remap_staging_path_string,
)
from .staging_and_sources import (
    remap_staging_file_records,
    replace_directory_atomically,
    clear_directory_contents,
    can_sync_study_delivery,
    _resolve_study_owned_paper_context,
    _resolve_delivery_context,
    copy_file,
    copy_tree,
    build_submission_source_root,
    build_submission_package_readme,
    build_general_delivery_readme,
    _submission_delivery_stale_reason_label,
)
from .staging_and_sources import (
    build_unavailable_general_delivery_readme,
    build_preview_general_delivery_readme,
    build_manuscript_root_readme,
    build_artifacts_root_readme,
    build_artifacts_finalize_readme,
    build_unavailable_submission_package_readme,
    build_submission_package_audit_preview_readme,
    build_delivery_surface_roles,
    build_promoted_delivery_readme,
    ensure_manuscript_root_readme,
    resolve_finalize_resume_packet_source,
    build_zip_from_directory,
)
from .staging_and_sources import (
    build_authority_source_relative_root,
    FRONT_MATTER_LABELS,
    METADATA_CLOSEOUT_LABELS,
    _humanize_submission_field,
    _humanize_metadata_closeout_item,
    _is_pending_submission_item,
    build_submission_todo_from_manifest,
    build_current_package_readme,
    sync_current_package_projection,
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


def copy_review_ledger_to_delivery_root(
    *,
    paper_root: Path,
    target_root: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> None:
    review_ledger_source = paper_root / "review" / "review_ledger.json"
    if not review_ledger_source.exists():
        return
    copy_file(
        source=review_ledger_source,
        target=target_root / "review" / review_ledger_source.name,
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
        Path("review/review_ledger.json"),
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


def _resolve_submission_source_path(*, paper_root: Path, source_root: Path, relative_path: Path) -> Path:
    if relative_path in FORMAL_PAPER_DELIVERY_RELATIVE_PATHS:
        return paper_root / relative_path
    return source_root / relative_path


def _hash_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS = frozenset(
    {
        Path("README.md"),
    }
)

CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS: dict[Path, frozenset[str]] = {
    Path("evidence_ledger.json"): frozenset({"updated_at"}),
}


def _submission_source_relative_paths(*, paper_root: Path, source_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_source_root = Path(source_root).expanduser().resolve()
    relative_paths = list(_iter_relative_files(resolved_source_root))
    relative_paths.extend(
        relative_path
        for relative_path in FORMAL_PAPER_DELIVERY_RELATIVE_PATHS
        if (resolved_paper_root / relative_path).exists()
    )
    deduped = {path.as_posix(): path for path in relative_paths}
    return tuple(sorted(deduped.values(), key=lambda item: item.as_posix()))


def _submission_source_signature(*, paper_root: Path, source_root: Path, relative_paths: tuple[Path, ...]) -> str:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_source_root = Path(source_root).expanduser().resolve()
    fingerprint_payload = []
    for relative_path in relative_paths:
        source = _resolve_submission_source_path(
            paper_root=resolved_paper_root,
            source_root=resolved_source_root,
            relative_path=relative_path,
        )
        stat = source.stat()
        fingerprint_payload.append(
            {
                "path": relative_path.as_posix(),
                "size": stat.st_size,
                "sha256": _hash_file_bytes(source),
            }
        )
    canonical = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_json_file(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _normalize_projection_json_payload(*, relative_path: Path, payload: Any) -> Any:
    volatile_keys = CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS.get(relative_path)
    if not volatile_keys or not isinstance(payload, dict):
        return payload
    return {key: value for key, value in payload.items() if key not in volatile_keys}


def _submission_projection_file_matches_source(
    *,
    relative_path: Path,
    source: Path,
    target: Path,
) -> bool:
    if not target.exists():
        return False
    if relative_path in CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS:
        return True
    if _hash_file_bytes(source) == _hash_file_bytes(target):
        return True
    if relative_path not in CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS:
        return False
    source_payload = _load_json_file(source)
    target_payload = _load_json_file(target)
    if source_payload is None or target_payload is None:
        return False
    return _normalize_projection_json_payload(
        relative_path=relative_path,
        payload=source_payload,
    ) == _normalize_projection_json_payload(
        relative_path=relative_path,
        payload=target_payload,
    )


def _submission_projection_matches_source(
    *,
    paper_root: Path,
    source_root: Path,
    current_package_root: Path,
    relative_paths: tuple[Path, ...],
) -> bool:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_source_root = Path(source_root).expanduser().resolve()
    resolved_current_package_root = Path(current_package_root).expanduser().resolve()
    for relative_path in relative_paths:
        source = _resolve_submission_source_path(
            paper_root=resolved_paper_root,
            source_root=resolved_source_root,
            relative_path=relative_path,
        )
        target = resolved_current_package_root / relative_path
        if not _submission_projection_file_matches_source(
            relative_path=relative_path,
            source=source,
            target=target,
        ):
            return False
    return True


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
    source_relative_paths = _submission_source_relative_paths(
        paper_root=resolved_paper_root,
        source_root=expected_source_root,
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
    elif not _submission_projection_matches_source(
        paper_root=resolved_paper_root,
        source_root=expected_source_root,
        current_package_root=current_package_root,
        relative_paths=source_relative_paths,
    ):
        status = "stale_source_changed"
        stale_reason = "delivery_manifest_source_changed"
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
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=resolved_paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        review_ledger_path=resolved_paper_root / "review" / "review_ledger.json",
    )
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
            charter_contract_linkage=charter_contract_linkage,
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
        "charter_contract_linkage": charter_contract_linkage,
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
