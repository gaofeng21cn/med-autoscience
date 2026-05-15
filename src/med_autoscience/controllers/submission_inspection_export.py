from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import delivery_inspector
from med_autoscience.controllers.study_delivery_sync_parts.delivery_io import (
    build_zip_from_directory,
    dump_json,
    replace_directory_atomically,
    reset_directory,
    remap_staging_file_records,
    utc_now,
    write_text,
)
from med_autoscience.profiles import WorkspaceProfile


INSPECTION_PACKAGE_DIRNAME = "inspection_package"
INSPECTION_PACKAGE_ZIPNAME = "inspection_package.zip"
INSPECTION_PACKAGE_MANIFEST = "inspection_package_manifest.json"
INSPECTION_ARTIFACT_DIRNAME = "inspection_package"
INSPECTION_ARTIFACT_MANIFEST = "manifest.json"
INSPECTION_EXPORT_RECEIPT = "export_receipt.json"
INSPECTION_RECEIPT_RELATIVE_PATH = Path("artifacts/inspection_package/latest.json")

_PRIMARY_SOURCE_FILES = (
    "draft.md",
    "manuscript_submission.md",
    "paper.md",
    "paper_bundle_manifest.json",
    "paper_line_state.json",
    "claim_evidence_map.json",
    "evidence_ledger.json",
    "results_narrative_map.json",
    "numeric_trace.json",
    "derived_analysis_manifest.json",
    "methods_implementation_manifest.json",
    "manuscript_safe_reproducibility_supplement.json",
    "medical_manuscript_blueprint.json",
    "medical_prose_review.json",
    "publication_style_profile.json",
    "medical_journal_style_corpus.json",
    "figure_semantics_manifest.json",
    "display_registry.json",
    "display_overrides.json",
    "endpoint_provenance_note.md",
    "README.md",
)
_PRIMARY_SOURCE_DIRS = (
    "build",
    "review",
    "figures",
    "tables",
)
_SKIP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
_SKIP_SUFFIXES = (
    ".pyc",
    ".tmp",
    ".bak",
)


def export_inspection_package(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    publication_profile: str | None = None,
    source: str = "med_autoscience",
    force_materialize: bool = False,
) -> dict[str, Any]:
    resolved_study_root = _resolve_study_root(profile=profile, study_id=study_id, study_root=study_root)
    resolved_publication_profile = publication_profile or profile.default_publication_profile
    inspection = delivery_inspector.inspect_study_delivery(
        profile=profile,
        profile_ref=profile_ref,
        study_root=resolved_study_root,
        publication_profile=resolved_publication_profile,
    )
    current_zip = _mapping(inspection.get("zip"))
    current_zip_path = Path(str(current_zip.get("path") or "")).expanduser()
    current_zip_ready = (
        inspection.get("freshness", {}).get("verdict") == "current"
        and bool(current_zip.get("exists"))
        and current_zip_path.exists()
    )
    manifest_path = _inspection_manifest_path(resolved_study_root)
    receipt_path = _inspection_receipt_path(resolved_study_root)
    if current_zip_ready and not force_materialize:
        manifest = _current_package_reuse_manifest(
            study_root=resolved_study_root,
            profile=profile,
            profile_ref=profile_ref,
            inspection=inspection,
            current_zip_path=current_zip_path.resolve(),
            source=source,
        )
        dump_json(manifest_path, manifest)
        _write_inspection_artifacts(study_root=resolved_study_root, manifest=manifest)
        return manifest

    paper_root = _inspection_paper_root(study_root=resolved_study_root, inspection=inspection)
    package_root = resolved_study_root / "manuscript" / INSPECTION_PACKAGE_DIRNAME
    package_zip = resolved_study_root / "manuscript" / INSPECTION_PACKAGE_ZIPNAME
    staging_root = package_root.parent / f".{package_root.name}.tmp-export"
    if staging_root.exists():
        shutil.rmtree(staging_root)
    reset_directory(staging_root)
    copied_files: list[dict[str, str]] = []
    try:
        _write_inspection_readme(staging_root)
        _copy_inspection_sources(
            paper_root=paper_root,
            target_root=staging_root,
            copied_files=copied_files,
        )
        staged_package_manifest = _package_manifest_payload(
            study_root=resolved_study_root,
            paper_root=paper_root,
            package_root=package_root,
            package_zip=package_zip,
            profile=profile,
            profile_ref=profile_ref,
            inspection=inspection,
            copied_files=copied_files,
            source=source,
        )
        dump_json(staging_root / INSPECTION_PACKAGE_MANIFEST, staged_package_manifest)
        replace_directory_atomically(staging_root=staging_root, target_root=package_root)
    except Exception:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise

    remapped_copied_files = remap_staging_file_records(
        records=copied_files,
        staging_root=staging_root,
        target_root=package_root,
    )
    package_manifest = {
        **staged_package_manifest,
        "copied_files": remapped_copied_files,
    }
    materialized_manifest = {
        **package_manifest,
        "status": "inspection_package_materialized",
        "targets": {
            **dict(package_manifest.get("targets") or {}),
            "inspection_package_root": str(package_root.resolve()),
            "inspection_package_zip": str(package_zip.resolve()),
            "inspection_manifest_path": str(manifest_path.resolve()),
        },
    }
    dump_json(package_root / INSPECTION_PACKAGE_MANIFEST, materialized_manifest)
    build_zip_from_directory(source_root=package_root, output_path=package_zip)
    manifest = {
        **materialized_manifest,
        "inspection_package_zip_sha256": _sha256(package_zip),
        "inspection_package_zip_size_bytes": package_zip.stat().st_size,
    }
    dump_json(package_root / INSPECTION_PACKAGE_MANIFEST, manifest)
    dump_json(manifest_path, manifest)
    _write_inspection_artifacts(study_root=resolved_study_root, manifest=manifest)
    return manifest


def inspect_inspection_package(*, study_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    package_root = resolved_study_root / "manuscript" / INSPECTION_PACKAGE_DIRNAME
    package_zip = resolved_study_root / "manuscript" / INSPECTION_PACKAGE_ZIPNAME
    manifest_path = _inspection_manifest_path(resolved_study_root)
    receipt_path = _inspection_receipt_path(resolved_study_root)
    manifest = _load_json_object(manifest_path)
    receipt = _load_json_object(receipt_path)
    return {
        "role": "human_inspection_only",
        "root": str(package_root),
        "zip_path": str(package_zip),
        "manifest_path": str(manifest_path),
        "receipt_path": str(receipt_path),
        "exists": package_root.exists(),
        "zip_exists": package_zip.exists(),
        "receipt_exists": receipt_path.exists(),
        "zip_size_bytes": package_zip.stat().st_size if package_zip.exists() else None,
        "zip_sha256": _sha256(package_zip) if package_zip.exists() else None,
        "status": _inspection_status(package_root=package_root, package_zip=package_zip, manifest=manifest),
        "manifest_status": "present" if manifest else "missing",
        "receipt_status": receipt.get("receipt_status") if receipt else None,
        "inspection_only": True,
        "can_submit": False,
        "can_authorize_publication_quality": False,
        "source_package_status": manifest.get("source_package_status") if manifest else None,
        "generated_at": manifest.get("generated_at") if manifest else None,
    }


def _resolve_study_root(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
) -> Path:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")
    if study_root is not None:
        return Path(study_root).expanduser().resolve()
    assert study_id is not None
    return (profile.studies_root / study_id).expanduser().resolve()


def _inspection_manifest_path(study_root: Path) -> Path:
    return study_root / "manuscript" / INSPECTION_PACKAGE_MANIFEST


def _inspection_receipt_path(study_root: Path) -> Path:
    return study_root / INSPECTION_RECEIPT_RELATIVE_PATH


def _inspection_artifact_root(study_root: Path) -> Path:
    return study_root / "artifacts" / INSPECTION_ARTIFACT_DIRNAME


def _inspection_export_receipt_path(study_root: Path) -> Path:
    return _inspection_artifact_root(study_root) / INSPECTION_EXPORT_RECEIPT


def _inspection_paper_root(*, study_root: Path, inspection: Mapping[str, Any]) -> Path:
    study_owned = (study_root / "paper").resolve()
    if study_owned.exists():
        return study_owned
    paper_root = str(inspection.get("paper_root") or "").strip()
    if paper_root:
        return Path(paper_root).expanduser().resolve()
    return study_owned


def _current_package_reuse_manifest(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
    profile_ref: Path | None,
    inspection: Mapping[str, Any],
    current_zip_path: Path,
    source: str,
) -> dict[str, Any]:
    generated_at = utc_now()
    return {
        "surface": "inspection_package",
        "surface_kind": "inspection_package",
        "schema_version": 1,
        "status": "authorized_current_package_available",
        "generated_at": generated_at,
        "source": source,
        "study_id": study_root.name,
        "study_root": str(study_root.resolve()),
        "workspace_root": str(profile.workspace_root.resolve()),
        "profile_ref": str(profile_ref.expanduser().resolve()) if profile_ref is not None else None,
        "source_package_status": "authorized_current_package",
        "recommended_human_review_path": str(current_zip_path),
        "not_for_submission": True,
        "gate_blocked_snapshot": False,
        "source_inventory_present": True,
        "targets": {
            "authorized_current_package_zip": str(current_zip_path),
            "inspection_manifest_path": str(_inspection_manifest_path(study_root).resolve()),
            "inspection_artifact_manifest": str(
                (_inspection_artifact_root(study_root) / INSPECTION_ARTIFACT_MANIFEST).resolve()
            ),
            "inspection_export_receipt": str(_inspection_export_receipt_path(study_root).resolve()),
        },
        "authority": _authority_contract(),
        "delivery_inspection": _compact_delivery_inspection(inspection),
        "inspection_only": True,
        "can_submit": False,
        "can_authorize_publication_quality": False,
    }


def _package_manifest_payload(
    *,
    study_root: Path,
    paper_root: Path,
    package_root: Path,
    package_zip: Path,
    profile: WorkspaceProfile,
    profile_ref: Path | None,
    inspection: Mapping[str, Any],
    copied_files: list[dict[str, str]],
    source: str,
) -> dict[str, Any]:
    return {
        "surface": "inspection_package",
        "surface_kind": "inspection_package",
        "schema_version": 1,
        "status": "inspection_package_staged",
        "generated_at": utc_now(),
        "source": source,
        "study_id": study_root.name,
        "study_root": str(study_root.resolve()),
        "workspace_root": str(profile.workspace_root.resolve()),
        "profile_ref": str(profile_ref.expanduser().resolve()) if profile_ref is not None else None,
        "paper_root": str(paper_root.resolve()),
        "source_package_status": "inspection_only_current_paper_snapshot",
        "recommended_human_review_path": str(package_zip.resolve()),
        "not_for_submission": True,
        "gate_blocked_snapshot": True,
        "source_inventory_present": True,
        "targets": {
            "inspection_package_root": str(package_root.resolve()),
            "inspection_package_zip": str(package_zip.resolve()),
            "inspection_manifest_path": str(_inspection_manifest_path(study_root).resolve()),
            "inspection_artifact_manifest": str(
                (_inspection_artifact_root(study_root) / INSPECTION_ARTIFACT_MANIFEST).resolve()
            ),
            "inspection_export_receipt": str(_inspection_export_receipt_path(study_root).resolve()),
        },
        "authority": _authority_contract(),
        "source_policy": {
            "reads_canonical_paper_surfaces": True,
            "reads_current_package_when_available": False,
            "reads_submission_minimal_as_export_source": False,
            "writes_current_package": False,
            "writes_submission_minimal": False,
            "writes_publication_eval": False,
            "writes_controller_decisions": False,
        },
        "copied_files": copied_files,
        "copied_file_count": len(copied_files),
        "delivery_inspection": _compact_delivery_inspection(inspection),
        "inspection_only": True,
        "can_submit": False,
        "can_authorize_publication_quality": False,
    }


def _authority_contract() -> dict[str, Any]:
    return {
        "role": "human_inspection_only",
        "authority": "human_inspection_only",
        "can_submit": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission": False,
        "can_authorize_submission_dispatch": False,
        "can_clear_publishability_gate": False,
        "can_dispatch_delivery_sync": False,
        "can_mutate_delivery_authority": False,
        "generated_delivery_surfaces_can_be_edit_source": False,
        "generated_delivery_surfaces_can_be_quality_authority": False,
        "generated_delivery_surfaces_can_be_dispatch_authority": False,
        "forbidden_writes": [
            "paper/submission_minimal/",
            "manuscript/current_package/",
            "manuscript/current_package.zip",
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
        ],
    }


def _receipt_from_manifest(*, manifest: Mapping[str, Any], receipt_path: Path) -> dict[str, Any]:
    authority = _mapping(manifest.get("authority"))
    targets = _mapping(manifest.get("targets"))
    return {
        "surface_kind": "inspection_package_export_receipt",
        "schema_version": 1,
        "receipt_status": manifest.get("status"),
        "generated_at": manifest.get("generated_at"),
        "study_id": manifest.get("study_id"),
        "study_root": manifest.get("study_root"),
        "workspace_root": manifest.get("workspace_root"),
        "profile_ref": manifest.get("profile_ref"),
        "authority": authority,
        "source_package_status": manifest.get("source_package_status"),
        "recommended_human_review_path": manifest.get("recommended_human_review_path"),
        "targets": targets,
        "receipt_path": str(receipt_path.resolve()),
        "human_inspection_only": True,
        "can_submit": False,
        "can_authorize_submission": False,
        "can_authorize_publication_quality": False,
        "can_clear_publishability_gate": False,
        "can_dispatch_delivery_sync": False,
        "writes": {
            "inspection_package": bool(targets.get("inspection_package_root") or targets.get("inspection_package_zip")),
            "current_package": False,
            "submission_minimal": False,
            "publication_eval": False,
            "controller_decisions": False,
        },
    }


def _write_inspection_artifacts(*, study_root: Path, manifest: Mapping[str, Any]) -> None:
    artifact_root = _inspection_artifact_root(study_root)
    receipt_path = _inspection_receipt_path(study_root)
    export_receipt_path = _inspection_export_receipt_path(study_root)
    receipt = _receipt_from_manifest(manifest=manifest, receipt_path=receipt_path)
    copied_files = list(manifest.get("copied_files") or [])
    zip_path = str(_mapping(manifest.get("targets")).get("inspection_package_zip") or "").strip()
    checksum_items = [
        item
        for item in copied_files
        if isinstance(item, Mapping) and isinstance(item.get("sha256"), str) and item.get("sha256")
    ]
    if zip_path:
        resolved_zip_path = Path(zip_path).expanduser()
        if resolved_zip_path.exists():
            checksum_items.append(
                {
                    "category": "inspection_package_zip",
                    "path": str(resolved_zip_path.resolve()),
                    "sha256": _sha256(resolved_zip_path),
                    "size_bytes": resolved_zip_path.stat().st_size,
                }
            )
    dump_json(artifact_root / INSPECTION_ARTIFACT_MANIFEST, dict(manifest))
    dump_json(
        artifact_root / "source_inventory.json",
        {
            "surface_kind": "inspection_package_source_inventory",
            "schema_version": 1,
            "study_id": manifest.get("study_id"),
            "source_package_status": manifest.get("source_package_status"),
            "source_inventory_present": True,
            "copied_file_count": len(copied_files),
            "copied_files": copied_files,
            "source_policy": manifest.get("source_policy"),
        },
    )
    dump_json(
        artifact_root / "checksums.json",
        {
            "surface_kind": "inspection_package_checksums",
            "schema_version": 1,
            "study_id": manifest.get("study_id"),
            "items": checksum_items,
            "item_count": len(checksum_items),
        },
    )
    dump_json(
        artifact_root / "blocked_context.json",
        {
            "surface_kind": "inspection_package_blocked_context",
            "schema_version": 1,
            "study_id": manifest.get("study_id"),
            "gate_blocked_snapshot": bool(manifest.get("gate_blocked_snapshot")),
            "delivery_inspection": manifest.get("delivery_inspection"),
        },
    )
    dump_json(export_receipt_path, receipt)
    dump_json(receipt_path, receipt)


def _compact_delivery_inspection(inspection: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": inspection.get("surface"),
        "study_id": inspection.get("study_id"),
        "paper_root": inspection.get("paper_root"),
        "freshness": inspection.get("freshness"),
        "source_package": _compact_package(inspection.get("source_package")),
        "human_package": _compact_package(inspection.get("human_package")),
        "zip": inspection.get("zip"),
    }


def _compact_package(value: object) -> dict[str, Any]:
    package = _mapping(value)
    return {
        "root": package.get("root"),
        "exists": package.get("exists"),
        "layout_status": package.get("layout_status"),
        "source_signature": package.get("source_signature"),
        "role": package.get("role"),
    }


def _write_inspection_readme(target_root: Path) -> None:
    write_text(
        target_root / "README.md",
        "\n".join(
            [
                "# Inspection Package",
                "",
                "This package is for human manuscript inspection only.",
                "It is not a submission package and does not authorize publication quality, submission dispatch,",
                "or current_package freshness.",
                "",
                "Use the included source snapshot to review writing style, claim framing, and visible draft state.",
                "",
            ]
        ),
    )


def _copy_inspection_sources(
    *,
    paper_root: Path,
    target_root: Path,
    copied_files: list[dict[str, str]],
) -> None:
    resolved_paper_root = paper_root.expanduser().resolve()
    if not resolved_paper_root.exists():
        raise FileNotFoundError(f"missing paper root for inspection export: {resolved_paper_root}")
    for relative_text in _PRIMARY_SOURCE_FILES:
        _copy_optional_file(
            source=resolved_paper_root / relative_text,
            target=target_root / "paper_snapshot" / relative_text,
            copied_files=copied_files,
        )
    for relative_text in _PRIMARY_SOURCE_DIRS:
        _copy_optional_tree(
            source_root=resolved_paper_root / relative_text,
            target_root=target_root / "paper_snapshot" / relative_text,
            copied_files=copied_files,
        )

def _copy_optional_file(*, source: Path, target: Path, copied_files: list[dict[str, str]]) -> None:
    if not source.exists() or not source.is_file():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied_files.append(
        {
            "category": "inspection_source_snapshot",
            "source_path": str(source.resolve()),
            "target_path": str(target.resolve()),
            "sha256": _sha256(source),
            "size_bytes": source.stat().st_size,
        }
    )


def _copy_optional_tree(*, source_root: Path, target_root: Path, copied_files: list[dict[str, str]]) -> None:
    if not source_root.exists() or not source_root.is_dir():
        return
    for source in _iter_source_files(source_root):
        relative = source.relative_to(source_root)
        _copy_optional_file(source=source, target=target_root / relative, copied_files=copied_files)


def _iter_source_files(source_root: Path) -> Iterable[Path]:
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        if any(part in _SKIP_DIR_NAMES for part in source.relative_to(source_root).parts):
            continue
        if source.name in {INSPECTION_PACKAGE_ZIPNAME, INSPECTION_PACKAGE_MANIFEST}:
            continue
        if source.name.endswith(_SKIP_SUFFIXES):
            continue
        yield source


def _inspection_status(*, package_root: Path, package_zip: Path, manifest: Mapping[str, Any]) -> str:
    if manifest.get("status") == "authorized_current_package_available":
        return "authorized_current_package_available"
    if package_root.exists() and package_zip.exists() and manifest:
        return "current"
    if package_root.exists() or package_zip.exists() or manifest:
        return "partial"
    return "missing"


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "INSPECTION_PACKAGE_DIRNAME",
    "INSPECTION_PACKAGE_MANIFEST",
    "INSPECTION_PACKAGE_ZIPNAME",
    "INSPECTION_ARTIFACT_DIRNAME",
    "INSPECTION_RECEIPT_RELATIVE_PATH",
    "export_inspection_package",
    "inspect_inspection_package",
]
