from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


def owner_controller_decision_refs(
    *,
    profile: WorkspaceProfile,
    target_study_id: str,
) -> list[dict[str, Any]]:
    return _owner_surface_refs(
        profile=profile,
        target_study_id=target_study_id,
        role="mas_owner_controller_decision",
        relative_path=Path("artifacts/controller_decisions/latest.json"),
    )


def _owner_surface_refs(
    *,
    profile: WorkspaceProfile,
    target_study_id: str,
    role: str,
    relative_path: Path,
) -> list[dict[str, Any]]:
    matched_roots = [
        study_root
        for study_root in _study_roots(profile)
        if _matches_target_study(study_root.name, target_study_id)
    ]
    if not matched_roots:
        path = profile.studies_root / target_study_id / relative_path
        return [_owner_surface_ref(path=path, role=role, workspace_root=profile.workspace_root)]
    return [
        _owner_surface_ref(path=study_root / relative_path, role=role, workspace_root=profile.workspace_root)
        for study_root in matched_roots
    ]


def _owner_surface_ref(*, path: Path, role: str, workspace_root: Path) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "role": role,
        "ref": _workspace_relative(path, workspace_root=workspace_root),
        "exists": path.exists(),
    }
    digest = _file_sha256(path)
    if digest is not None:
        ref["content_sha256"] = digest
    return ref


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path for path in profile.studies_root.iterdir() if path.is_dir())


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _file_sha256(path: Path) -> str | None:
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    return hashlib.sha256(payload).hexdigest()


def _matches_target_study(study_id: str, target_study_id: str) -> bool:
    return _normalize_study_id(study_id) == _normalize_study_id(target_study_id)


def _normalize_study_id(study_id: str) -> str:
    text = str(study_id or "").strip().lower().replace("_", "-")
    aliases = {
        "dm002": "002",
        "dm-002": "002",
        "dm003": "003",
        "dm-003": "003",
        "obesity": "obesity",
    }
    if text in aliases:
        return aliases[text]
    if text.startswith("002-"):
        return "002"
    if text.startswith("003-"):
        return "003"
    if "obesity" in text:
        return "obesity"
    return text


__all__ = ["owner_controller_decision_refs"]
