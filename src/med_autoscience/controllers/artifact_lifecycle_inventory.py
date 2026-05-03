from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
ARTIFACT_ROLES = (
    "canonical_source",
    "runtime_ephemeral",
    "derived_projection",
    "human_handoff_mirror",
    "data_release",
    "cold_archive",
    "audit_log",
)
LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
GENERATED_AUTHORITY_SURFACE_NAMES = frozenset(
    {
        "current_package",
        "current_package.zip",
        "submission_minimal",
    }
)
GENERATED_AUTHORITY_SUFFIXES = (".zip", ".pdf", ".docx")


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
    role = classify_artifact_role(path=resolved_path, study_root=resolved_study_root, quest_root=resolved_quest_root)
    lifecycle = lifecycle_for_role(role)
    edit_source_allowed = role == "canonical_source"
    quality_authority_allowed = role == "canonical_source"
    cleanup_candidate_action = cleanup_action_for_artifact(
        role=role,
        lifecycle=lifecycle,
        runtime_status=runtime_status,
    )
    cleanup_blockers = cleanup_blockers_for_artifact(
        role=role,
        runtime_status=runtime_status,
    )
    return {
        "path": str(resolved_path),
        "role": role,
        "lifecycle": lifecycle,
        "edit_source_allowed": edit_source_allowed,
        "quality_authority_allowed": quality_authority_allowed,
        "cleanup_candidate_action": cleanup_candidate_action,
        "cleanup_blockers": cleanup_blockers,
    }


def classify_artifact_role(
    *,
    path: Path,
    study_root: Path,
    quest_root: Path | None = None,
) -> str:
    resolved_path = _resolve_path(path)
    parts = resolved_path.parts
    if _path_contains(parts, (".ds", "cold_archive")):
        return "cold_archive"
    if quest_root is not None and _is_relative_to(resolved_path, quest_root / ".ds"):
        return "runtime_ephemeral"
    if _path_contains(parts, ("datasets",)):
        return "data_release"
    if _path_contains(parts, ("artifacts", "runtime")) or _path_contains(parts, ("artifacts", "publication_eval")):
        return "audit_log"
    if _path_contains(parts, ("submission_minimal",)):
        return "human_handoff_mirror"
    if _is_generated_projection_path(resolved_path):
        return "derived_projection"
    if _path_contains(parts, ("manuscript",)) and not _path_contains(parts, ("current_package",)):
        return "human_handoff_mirror"
    return "canonical_source" if _is_relative_to(resolved_path, study_root / "paper") else "audit_log"


def lifecycle_for_role(role: str) -> str:
    mapping = {
        "canonical_source": "active_authority",
        "runtime_ephemeral": "runtime_transient",
        "derived_projection": "rebuildable_projection",
        "human_handoff_mirror": "human_handoff",
        "data_release": "retained_release",
        "cold_archive": "archived_restore_candidate",
        "audit_log": "audit_retained",
    }
    if role not in mapping:
        raise ValueError(f"unknown artifact role: {role}")
    return mapping[role]


def build_delivery_authority_sync(*, study_root: Path, paths: Sequence[Path]) -> dict[str, Any]:
    resolved_study_root = _resolve_path(study_root)
    authority_paths = [path for path in paths if _is_generated_authority_surface_path(_resolve_path(path))]
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "delivery_authority_sync",
        "status": "projection_only" if authority_paths else "authority_source_unblocked",
        "study_root": str(resolved_study_root),
        "direct_edit_allowed": not authority_paths,
        "quality_authority_allowed": not authority_paths,
        "authority_source_roles": ["canonical_source"],
        "blocked_authority_paths": [str(_resolve_path(path)) for path in authority_paths],
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
    restore_handle = _first_text(metadata, ("restore_handle", "restore_command", "archive_ref", "archive_uri", "external_archive_uri"))
    checksum = _first_text(metadata, ("sha256", "checksum", "manifest_sha256", "archive_sha256"))
    rehydrate_status = _rehydrate_verification_status(metadata)
    if restore_handle is None:
        blockers.append("missing_restore_handle")
    if checksum is None:
        blockers.append("missing_checksum")
    if rehydrate_status != "verified":
        blockers.append("missing_rehydrate_verification")
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "archive_cleanup_readiness",
        "archive_path": str(_resolve_path(archive_path)),
        "candidate_action": "blocked" if blockers else "cleanup-expanded-copy",
        "blockers": blockers,
        "restore_handle": restore_handle,
        "checksum": checksum,
        "rehydrate_verification_status": rehydrate_status,
    }


def cleanup_action_for_artifact(
    *,
    role: str,
    lifecycle: str,
    runtime_status: Mapping[str, Any] | None = None,
) -> str:
    if role == "runtime_ephemeral" and _runtime_is_live(runtime_status):
        return "audit-only"
    if role in {"canonical_source", "data_release", "audit_log", "human_handoff_mirror"}:
        return "keep-online"
    if lifecycle == "rebuildable_projection":
        return "rebuildable"
    if role == "cold_archive":
        return "restore-gated"
    return "audit-only"


def cleanup_blockers_for_artifact(*, role: str, runtime_status: Mapping[str, Any] | None = None) -> list[str]:
    if role == "runtime_ephemeral" and _runtime_is_live(runtime_status):
        return ["live_runtime_active"]
    return []


def _resolve_path(path: Path | None) -> Path:
    if path is None:
        raise ValueError("path must not be None")
    return Path(path).expanduser().resolve()


def _runtime_is_live(runtime_status: Mapping[str, Any] | None) -> bool:
    if not isinstance(runtime_status, Mapping):
        return False
    status = str(runtime_status.get("status") or "").strip().lower()
    active_run_id = str(runtime_status.get("active_run_id") or "").strip()
    return status in LIVE_RUNTIME_STATUSES and bool(active_run_id)


def _is_generated_projection_path(path: Path) -> bool:
    parts = path.parts
    return (
        _path_contains(parts, ("current_package",))
        or path.name == "current_package.zip"
        or path.suffix.lower() in GENERATED_AUTHORITY_SUFFIXES
    )


def _is_generated_authority_surface_path(path: Path) -> bool:
    parts = path.parts
    return (
        any(part in GENERATED_AUTHORITY_SURFACE_NAMES for part in parts)
        or path.name in GENERATED_AUTHORITY_SURFACE_NAMES
        or path.suffix.lower() in GENERATED_AUTHORITY_SUFFIXES
    )


def _path_contains(parts: tuple[str, ...], expected: tuple[str, ...]) -> bool:
    if not expected:
        return False
    if len(expected) == 1:
        return expected[0] in parts
    limit = len(parts) - len(expected) + 1
    return any(parts[index : index + len(expected)] == expected for index in range(max(0, limit)))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


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
    "build_study_delivery_lifecycle_hook",
    "classify_artifact",
    "classify_artifact_role",
    "cleanup_action_for_artifact",
    "cleanup_blockers_for_artifact",
    "evaluate_archive_cleanup_readiness",
    "lifecycle_for_role",
]
