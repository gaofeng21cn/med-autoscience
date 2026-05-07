from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context
from med_autoscience.controllers.control_plane_write_route import (
    blocked_control_plane_write_payload,
    resolve_control_plane_write_route_context,
)
from med_autoscience.controllers.submission_package_layout import (
    audit_path,
    reproducibility_path,
    resolve_submission_manifest_path,
)

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




from .submission_delivery_descriptions import (
    CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS,
    CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS,
    _hash_file_bytes,
    _load_json_file,
    _normalize_projection_json_payload,
    _resolve_submission_source_path,
    _submission_projection_file_matches_source,
    _submission_projection_matches_source,
    _submission_source_relative_paths,
    _submission_source_signature,
    describe_submission_delivery,
    materialize_submission_delivery_stale_notice,
)
