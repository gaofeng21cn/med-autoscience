from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from med_autoscience.controllers.submission_package_layout import (
    AUDIT_DIRNAME,
    LEGACY_ROOT_AUDIT_RELATIVE_PATHS,
    REPRODUCIBILITY_DIRNAME,
    has_legacy_root_audit_files,
)


SCHEMA_VERSION = 1
GENERATED_DELIVERY_SURFACE_NAMES = frozenset(
    {
        "current_package",
        "current_package.zip",
        "submission_minimal",
    }
)
GENERATED_DELIVERY_SURFACE_SUFFIXES = frozenset({".zip", ".pdf", ".docx"})


def build_delivery_authority_sync(*, study_root: Path, paths: Sequence[Path]) -> dict[str, Any]:
    resolved_study_root = _resolve_path(study_root)
    authority_paths = [
        path for path in paths if is_generated_delivery_authority_path(_resolve_path(path))
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "delivery_authority_sync",
        "status": "projection_only" if authority_paths else "authority_source_unblocked",
        "study_root": str(resolved_study_root),
        "direct_edit_allowed": not authority_paths,
        "quality_authority_allowed": not authority_paths,
        "dispatch_authority_allowed": not authority_paths,
        "authority_source_roles": ["canonical_source"],
        "blocked_authority_paths": [str(_resolve_path(path)) for path in authority_paths],
        "blocked_dispatch_paths": [str(_resolve_path(path)) for path in authority_paths],
        "blocked_authority_reasons": [
            "generated_delivery_surface_cannot_be_edit_source_or_quality_authority"
            for _ in authority_paths
        ],
    }


def build_study_delivery_lifecycle_hook(
    *,
    study_root: Path,
    current_package_root: Path | None = None,
    current_package_zip: Path | None = None,
    generated_files: Sequence[Mapping[str, Any]] = (),
    copied_files: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    paths: list[Path] = []
    for candidate in (current_package_root, current_package_zip):
        if candidate is not None:
            paths.append(candidate)
    for record in (*generated_files, *copied_files):
        raw_path = str(record.get("path") or "").strip()
        if raw_path:
            paths.append(Path(raw_path))
    authority_sync = build_delivery_authority_sync(study_root=study_root, paths=paths)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "study_delivery_sync_lifecycle",
        "authority_sync": authority_sync,
        "lifecycle_roles": {
            "current_package": "derived_projection",
            "submission_minimal": "controller_authorized_package_source",
            "zip": "derived_projection",
            "pdf": "derived_projection",
            "docx": "derived_projection",
        },
        "delivery_package_roles": {
            "submission_minimal": "controller_authorized_package_source",
            "current_package": "human_facing_mirror",
        },
    }


def classify_delivery_package_layout(path: Path) -> dict[str, Any] | None:
    resolved_path = _resolve_path(path)
    package_root, package_surface = _delivery_package_root_for_path(resolved_path)
    if package_root is None:
        if not is_generated_delivery_surface_path(resolved_path):
            return None
        package_root = resolved_path.parent
        package_surface = "generated_output"

    legacy_root_audit_files_present = has_legacy_root_audit_files(package_root)
    v2_layout_present = (
        (package_root / AUDIT_DIRNAME).exists()
        or (package_root / REPRODUCIBILITY_DIRNAME).exists()
    )
    status = "v2" if v2_layout_present else "legacy" if legacy_root_audit_files_present else "unknown"
    audit_root = package_root / AUDIT_DIRNAME
    reproducibility_root = package_root / REPRODUCIBILITY_DIRNAME
    return {
        "status": status,
        "package_root": str(package_root),
        "package_surface": package_surface,
        "section": _delivery_package_section(
            path=resolved_path,
            package_root=package_root,
            status=status,
        ),
        "audit_root": str(audit_root) if audit_root.exists() else None,
        "reproducibility_root": str(reproducibility_root) if reproducibility_root.exists() else None,
        "legacy_root_audit_files_present": legacy_root_audit_files_present,
        "open_guidance": _delivery_package_open_guidance(status),
        "audit_guidance": _delivery_package_audit_guidance(status),
        "edit_source_allowed": False,
    }


def summarize_delivery_manifests(manifests: Iterable[Path]) -> dict[str, Any]:
    delivery_manifests = [
        path for path in manifests if _is_delivery_manifest(path, _read_json_object(path))
    ]
    return {
        "delivery_manifest_count": len(delivery_manifests),
        "lifecycle_hook_present": any(
            _delivery_manifest_lifecycle_hook_present(_read_json_object(path))
            for path in delivery_manifests
        ),
        "source_signature_present": any(
            _delivery_manifest_source_signature_present(_read_json_object(path))
            for path in delivery_manifests
        ),
        "publication_refs_present": any(
            _delivery_manifest_publication_refs_present(_read_json_object(path))
            for path in delivery_manifests
        ),
    }


def build_delivery_manifest_historical_backfill_plan(
    delivery_manifest_summary: Mapping[str, Any],
) -> dict[str, Any] | None:
    if int(delivery_manifest_summary.get("delivery_manifest_count") or 0) == 0:
        return None
    missing_lifecycle_hook = not bool(delivery_manifest_summary.get("lifecycle_hook_present"))
    missing_source_signature = not bool(delivery_manifest_summary.get("source_signature_present"))
    missing_publication_refs = not bool(delivery_manifest_summary.get("publication_refs_present"))
    missing_surfaces: list[str] = []
    canonical_regeneration_path = ["refresh_canonical_manuscript_sources"]
    if missing_lifecycle_hook:
        missing_surfaces.append("delivery_manifest_lifecycle_hook")
        canonical_regeneration_path.append("regenerate_delivery_manifest_lifecycle_hook")
    if missing_source_signature:
        missing_surfaces.append("source_signature")
        canonical_regeneration_path.append("recompute_delivery_manifest_source_signature")
    if missing_publication_refs:
        missing_surfaces.append("publication_refs")
        canonical_regeneration_path.append("relink_delivery_manifest_publication_refs")
    if not missing_surfaces:
        return None
    canonical_regeneration_path.append("rerun_publication_gate")
    return {
        "plan_type": "delivery_manifest_historical_backfill",
        "read_only": True,
        "missing_surfaces": missing_surfaces,
        "missing_lifecycle_hook": missing_lifecycle_hook,
        "missing_source_signature": missing_source_signature,
        "missing_publication_refs": missing_publication_refs,
        "canonical_regeneration_path": canonical_regeneration_path,
        "mutation_policy": {
            "read_only": True,
            "writes_workspace": False,
            "manual_patch_allowed": False,
            "allowed_mutating_actions": [],
        },
    }


def is_generated_delivery_surface_path(path: Path) -> bool:
    resolved_path = Path(path)
    return (
        is_generated_delivery_authority_path(resolved_path)
        or resolved_path.suffix.lower() in GENERATED_DELIVERY_SURFACE_SUFFIXES
    )


def is_generated_delivery_authority_path(path: Path) -> bool:
    resolved_path = Path(path)
    return (
        any(part in GENERATED_DELIVERY_SURFACE_NAMES for part in resolved_path.parts)
        or resolved_path.name in GENERATED_DELIVERY_SURFACE_NAMES
    )


def _resolve_path(path: Path | None) -> Path:
    if path is None:
        raise ValueError("path must not be None")
    return Path(path).expanduser().resolve()


def _delivery_package_root_for_path(path: Path) -> tuple[Path | None, str | None]:
    if path.name == "current_package.zip":
        return path.with_suffix(""), "current_package_zip"
    for candidate in (path, *path.parents):
        if candidate.name == "current_package":
            return candidate, "current_package"
        if candidate.name == "submission_minimal":
            return candidate, "submission_minimal"
    return None, None


def _delivery_package_section(*, path: Path, package_root: Path, status: str) -> str:
    try:
        relative_path = path.relative_to(package_root)
    except ValueError:
        relative_path = Path("")
    first_part = relative_path.parts[0] if relative_path.parts else ""
    if status == "v2":
        if first_part == AUDIT_DIRNAME:
            return "audit"
        if first_part == REPRODUCIBILITY_DIRNAME:
            return "reproducibility"
        return "human_submission_files"
    if status == "legacy":
        if relative_path in LEGACY_ROOT_AUDIT_RELATIVE_PATHS:
            return "legacy_root_audit"
        return "human_submission_files"
    return "unknown_generated_output"


def _delivery_package_open_guidance(status: str) -> str:
    if status in {"v2", "legacy"}:
        return "open_root_submission_files"
    return "layout_unknown_inspect_file_directly"


def _delivery_package_audit_guidance(status: str) -> str:
    if status == "v2":
        return "inspect_audit_and_reproducibility_directories"
    if status == "legacy":
        return "inspect_legacy_root_audit_files"
    return "audit_and_reproducibility_locations_unknown"


def _is_delivery_manifest(path: Path, payload: Mapping[str, Any]) -> bool:
    return _text(payload.get("surface")) == "delivery_manifest" or path.name == "delivery_manifest.json"


def _delivery_manifest_lifecycle_hook_present(payload: Mapping[str, Any]) -> bool:
    lifecycle = payload.get("artifact_lifecycle")
    return (
        isinstance(lifecycle, Mapping)
        and bool(lifecycle.get("authority_sync"))
        and bool(lifecycle.get("lifecycle_roles"))
    )


def _delivery_manifest_source_signature_present(payload: Mapping[str, Any]) -> bool:
    return bool(
        _text(payload.get("source_signature"))
        or _text(payload.get("delivery_source_signature"))
    )


def _delivery_manifest_publication_refs_present(payload: Mapping[str, Any]) -> bool:
    for field_name in ("publication_refs", "delivery_context_refs", "publication_context_refs"):
        refs = payload.get(field_name)
        if isinstance(refs, Mapping) and any(_text(value) for value in refs.values()):
            return True
    return False


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "build_delivery_authority_sync",
    "build_delivery_manifest_historical_backfill_plan",
    "build_study_delivery_lifecycle_hook",
    "classify_delivery_package_layout",
    "is_generated_delivery_authority_path",
    "is_generated_delivery_surface_path",
    "summarize_delivery_manifests",
]
