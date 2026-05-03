from __future__ import annotations

from pathlib import Path
import os
from typing import Any, Mapping, Sequence

from med_autoscience.controllers.artifact_lifecycle_authority_kernel import (
    ARTIFACT_ROLES,
    SCHEMA_VERSION,
    ArtifactLifecycleAuthorityKernel,
    classify_artifact_role,
    cleanup_action_for_artifact,
    cleanup_blockers_for_artifact,
    is_generated_authority_surface_path,
    lifecycle_for_role,
)

def build_artifact_lifecycle_inventory(
    *,
    study_root: Path,
    quest_root: Path | None = None,
    paths: Sequence[Path],
    runtime_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = _resolve_path(study_root)
    resolved_quest_root = _resolve_path(quest_root) if quest_root is not None else None
    artifacts = [
        classify_artifact(
            path=path,
            study_root=resolved_study_root,
            quest_root=resolved_quest_root,
            runtime_status=runtime_status,
        )
        for path in paths
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "artifact_lifecycle_inventory",
        "study_root": str(resolved_study_root),
        "quest_root": str(resolved_quest_root) if resolved_quest_root is not None else None,
        "roles": list(ARTIFACT_ROLES),
        "artifacts": artifacts,
        "summary": {
            "total_files_count": len(artifacts),
            "role_counts": {role: sum(1 for item in artifacts if item["role"] == role) for role in ARTIFACT_ROLES},
        },
    }


def build_study_artifact_lifecycle_registry(
    *,
    study_root: Path,
    workspace_root: Path,
    quest_root: Path | None = None,
    runtime_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = _resolve_path(study_root)
    resolved_workspace_root = _resolve_path(workspace_root)
    resolved_quest_root = _resolve_path(quest_root) if quest_root is not None else None
    paths = _discover_registry_paths(
        study_root=resolved_study_root,
        workspace_root=resolved_workspace_root,
        quest_root=resolved_quest_root,
    )
    inventory = build_artifact_lifecycle_inventory(
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        paths=paths,
        runtime_status=runtime_status,
    )
    return {
        **inventory,
        "surface_kind": "workspace_study_artifact_lifecycle_registry",
        "workspace_root": str(resolved_workspace_root),
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
    return ArtifactLifecycleAuthorityKernel(
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        runtime_status=runtime_status,
    ).classify(resolved_path)


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
            "submission_minimal": "human_handoff_mirror",
            "zip": "derived_projection",
            "pdf": "derived_projection",
            "docx": "derived_projection",
        },
    }


def evaluate_archive_cleanup_readiness(
    *,
    archive_path: Path,
    restore_metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    metadata = restore_metadata if isinstance(restore_metadata, Mapping) else {}
    blockers: list[str] = []
    restore_index = _first_text(metadata, ("restore_index_path", "restore_index", "restore_index_ref"))
    checksum = _first_text(metadata, ("sha256", "checksum", "manifest_sha256", "archive_sha256"))
    rehydrate_status = _rehydrate_verification_status(metadata)
    if restore_index is None:
        blockers.append("missing_restore_index")
    if checksum is None:
        blockers.append("missing_checksum")
    if rehydrate_status != "verified":
        blockers.append("missing_rehydrate_verification")
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "archive_cleanup_readiness",
        "archive_path": str(_resolve_path(archive_path)),
        "candidate_action": "blocked" if blockers else "cleanup-expanded-copy",
        "physical_cleanup_allowed": not blockers,
        "blockers": blockers,
        "restore_index_path": restore_index,
        "checksum": checksum,
        "rehydrate_verification_status": rehydrate_status,
    }


def _discover_registry_paths(
    *,
    study_root: Path,
    workspace_root: Path,
    quest_root: Path | None,
) -> list[Path]:
    roots = [study_root, workspace_root / "datasets"]
    if quest_root is not None:
        roots.append(quest_root / ".ds")
    seen: set[Path] = set()
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in {".git", ".venv", "__pycache__"}]
            for filename in filenames:
                candidate = Path(current_root) / filename
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    paths.append(resolved)
    return sorted(paths)


def _resolve_path(path: Path | None) -> Path:
    if path is None:
        raise ValueError("path must not be None")
    return Path(path).expanduser().resolve()


def _first_text(payload: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _rehydrate_verification_status(payload: Mapping[str, Any]) -> str | None:
    for key in ("rehydrate_verification", "restore_verification"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            status = str(value.get("status") or "").strip().lower()
            if status:
                return status
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    status = str(payload.get("rehydrate_verification_status") or "").strip().lower()
    return status or None


__all__ = [
    "ARTIFACT_ROLES",
    "SCHEMA_VERSION",
    "build_artifact_lifecycle_inventory",
    "build_delivery_authority_sync",
    "build_study_artifact_lifecycle_registry",
    "build_study_delivery_lifecycle_hook",
    "classify_artifact",
    "classify_artifact_role",
    "cleanup_action_for_artifact",
    "cleanup_blockers_for_artifact",
    "evaluate_archive_cleanup_readiness",
    "lifecycle_for_role",
]
