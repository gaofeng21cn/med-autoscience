from __future__ import annotations

from pathlib import Path
from typing import Any


KERNEL_OWNER = "artifact_lifecycle_authority_kernel"
LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
GENERATED_AUTHORITY_SURFACE_NAMES = frozenset(
    {
        "current_package",
        "current_package.zip",
        "submission_minimal",
    }
)
GENERATED_AUTHORITY_SUFFIXES = frozenset({".zip", ".pdf", ".docx"})


def artifact_authority_record(
    *,
    path: Path,
    study_root: Path,
    quest_root: Path | None = None,
    runtime_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    role = classify_artifact_role(path=path, study_root=study_root, quest_root=quest_root)
    lifecycle = lifecycle_for_artifact(role=role, path=path)
    authority_allowed = authority_allowed_for_artifact(role=role)
    return {
        "role": role,
        "lifecycle": lifecycle,
        "owner": KERNEL_OWNER,
        "authority_allowed": authority_allowed,
        "cleanup_candidate": cleanup_action_for_artifact(
            role=role,
            lifecycle=lifecycle,
            runtime_status=runtime_status,
        ),
        "projection_currentness": projection_currentness_for_artifact(role=role),
    }


def classify_artifact_role(
    *,
    path: Path,
    study_root: Path,
    quest_root: Path | None = None,
) -> str:
    resolved_path = _resolve_path(path)
    resolved_study_root = _resolve_path(study_root)
    resolved_quest_root = _resolve_path(quest_root) if quest_root is not None else None
    parts = resolved_path.parts
    if _path_contains(parts, (".ds", "cold_archive")):
        return "cold_archive"
    if resolved_quest_root is not None and _is_relative_to(resolved_path, resolved_quest_root / ".ds"):
        return "runtime_ephemeral"
    if is_raw_intake_path(resolved_path) or _path_contains(parts, ("datasets",)):
        return "data_release"
    if _path_contains(parts, ("artifacts", "runtime")) or _path_contains(parts, ("artifacts", "publication_eval")):
        return "audit_log"
    if is_generated_authority_surface_path(resolved_path) or is_generated_authority_suffix(resolved_path):
        return "derived_projection"
    if _path_contains(parts, ("manuscript",)):
        return "human_handoff_mirror"
    return "canonical_source" if _is_relative_to(resolved_path, resolved_study_root / "paper") else "audit_log"


def lifecycle_for_artifact(*, role: str, path: Path) -> str:
    if role == "data_release" and is_raw_intake_path(path):
        return "raw_intake"
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


def authority_allowed_for_artifact(*, role: str) -> dict[str, bool]:
    allowed = role == "canonical_source"
    return {"edit": allowed, "quality": allowed, "dispatch": allowed}


def cleanup_action_for_artifact(
    *,
    role: str,
    lifecycle: str,
    runtime_status: dict[str, Any] | None = None,
) -> str:
    if role == "runtime_ephemeral" and _runtime_is_live(runtime_status):
        return "audit-only"
    if role == "runtime_ephemeral":
        return "archive-compress"
    if role in {"canonical_source", "data_release", "audit_log", "human_handoff_mirror"}:
        return "keep-online"
    if lifecycle == "rebuildable_projection":
        return "rebuildable"
    if role == "cold_archive":
        return "restore-gated"
    return "audit-only"


def projection_currentness_for_artifact(*, role: str) -> str:
    if role == "derived_projection":
        return "projection_only"
    if role == "canonical_source":
        return "authority_source"
    return "not_projection"


def is_raw_intake_path(path: Path) -> bool:
    resolved_path = Path(path)
    parts = resolved_path.parts
    return (
        _path_contains(parts, ("inbox",))
        or (_path_contains(parts, ("datasets",)) and resolved_path.suffix.lower() == ".zip")
        or _path_contains(parts, ("raw", "restricted"))
    )


def is_generated_authority_surface_path(path: Path) -> bool:
    resolved_path = Path(path)
    parts = resolved_path.parts
    return (
        any(part in GENERATED_AUTHORITY_SURFACE_NAMES for part in parts)
        or resolved_path.name in GENERATED_AUTHORITY_SURFACE_NAMES
    )


def is_generated_authority_suffix(path: Path) -> bool:
    return Path(path).suffix.lower() in GENERATED_AUTHORITY_SUFFIXES


def _runtime_is_live(runtime_status: dict[str, Any] | None) -> bool:
    if not isinstance(runtime_status, dict):
        return False
    status = str(runtime_status.get("status") or "").strip().lower()
    active_run_id = str(runtime_status.get("active_run_id") or "").strip()
    return status in LIVE_RUNTIME_STATUSES and bool(active_run_id)


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve()


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


__all__ = [
    "KERNEL_OWNER",
    "artifact_authority_record",
    "authority_allowed_for_artifact",
    "classify_artifact_role",
    "cleanup_action_for_artifact",
    "is_generated_authority_suffix",
    "is_generated_authority_surface_path",
    "is_raw_intake_path",
    "lifecycle_for_artifact",
    "projection_currentness_for_artifact",
]
