from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.controllers.artifact_lifecycle_authority_kernel import (
    SCHEMA_VERSION,
    ArtifactLifecycleAuthorityKernel,
    classify_artifact_role,
    is_generated_authority_suffix,
    is_generated_authority_surface_path,
)
from med_autoscience.controllers.submission_package_layout import (
    AUDIT_DIRNAME,
    LEGACY_ROOT_AUDIT_RELATIVE_PATHS,
    REPRODUCIBILITY_DIRNAME,
    has_legacy_root_audit_files,
)
OPL_ARTIFACT_LIFECYCLE_INDEX = Path(
    "control/opl/artifact_lifecycle/artifact_lifecycle_index.json"
)
OPL_ARTIFACT_LIFECYCLE_OWNER_REF = (
    "one-person-lab:src/modules/workspace/workspace-artifact-lifecycle.ts"
)


def read_opl_artifact_lifecycle_refs(*, study_root: Path) -> dict[str, Any]:
    """Read the OPL-owned lifecycle projection without rebuilding its inventory."""
    resolved_study_root = _resolve_path(study_root)
    index_path = resolved_study_root / OPL_ARTIFACT_LIFECYCLE_INDEX
    index = _read_json_object(index_path)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_artifact_lifecycle_refs",
        "status": "available" if index else "opl_projection_required",
        "study_root": str(resolved_study_root),
        "opl_artifact_lifecycle_index_ref": str(index_path),
        "opl_owner_surface_ref": OPL_ARTIFACT_LIFECYCLE_OWNER_REF,
        "refs": dict(index.get("refs") or {}) if isinstance(index.get("refs"), Mapping) else {},
        "lifecycle_status": str(index.get("status") or "").strip() or None,
        "authority_boundary": {
            "refs_only": True,
            "mas_rebuilds_generic_inventory": False,
            "mas_scans_workspace_for_lifecycle": False,
            "mas_can_authorize_artifact_mutation_from_projection": False,
            "artifact_mutation_authority_owner": "MedAutoScience",
        },
    }


def classify_artifact(
    *,
    path: Path,
    study_root: Path,
    quest_root: Path | None = None,
    runtime_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    resolved_study_root = _resolve_path(study_root)
    resolved_quest_root = _resolve_path(quest_root) if quest_root is not None else None
    artifact = ArtifactLifecycleAuthorityKernel(
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        runtime_status=runtime_status,
    ).classify(resolved_path)
    delivery_package_layout = classify_delivery_package_layout(resolved_path)
    if delivery_package_layout is None:
        return artifact
    return {
        **artifact,
        "delivery_package_layout_status": delivery_package_layout["status"],
        "delivery_package_layout": delivery_package_layout,
    }


def build_delivery_authority_sync(*, study_root: Path, paths: Sequence[Path]) -> dict[str, Any]:
    resolved_study_root = _resolve_path(study_root)
    authority_paths = [path for path in paths if is_generated_authority_surface_path(_resolve_path(path))]
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
        if not (is_generated_authority_surface_path(resolved_path) or is_generated_authority_suffix(resolved_path)):
            return None
        package_root = resolved_path.parent
        package_surface = "generated_output"

    legacy_root_audit_files_present = has_legacy_root_audit_files(package_root)
    v2_layout_present = (package_root / AUDIT_DIRNAME).exists() or (package_root / REPRODUCIBILITY_DIRNAME).exists()
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


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


__all__ = [
    "SCHEMA_VERSION",
    "build_delivery_authority_sync",
    "build_study_delivery_lifecycle_hook",
    "classify_artifact",
    "classify_artifact_role",
    "classify_delivery_package_layout",
    "read_opl_artifact_lifecycle_refs",
]
