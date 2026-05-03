from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


_AUTHORITY_OWNER_FIELDS = ("authority_owner", "owner", "authority")
_MANIFEST_SUFFIXES = ("manifest.json", "manifest.yaml", "manifest.yml")
_KNOWN_AUTHORITY_OWNERS = {"controller", "mas_controller", "publication_gate", "runtime_controller"}
_SKIPPED_DIR_NAMES = {
    ".codex",
    ".ds",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
}
_TRAVERSABLE_DIR_NAMES = {
    "current_package",
    "manuscript",
    "paper",
    "papers",
    "submission_minimal",
    "studies",
}
_TRAVERSABLE_DIR_PREFIXES = ("0",)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _as_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def _workspace_style(root: Path) -> str:
    name = root.name.lower()
    if "nf-pitnet" in name or (root / "papers").is_dir():
        return "nf_pitnet"
    if "dm-cvd" in name or (root / "studies").is_dir():
        return "dm_cvd"
    return "generic"


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _is_manifest(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in _MANIFEST_SUFFIXES)


def _should_enter_dir(path: Path) -> bool:
    name = path.name
    if name in _SKIPPED_DIR_NAMES:
        return False
    if name in _TRAVERSABLE_DIR_NAMES:
        return True
    return name.startswith(_TRAVERSABLE_DIR_PREFIXES)


def _iter_candidate_paths(root: Path) -> Iterable[Path]:
    for path in root.iterdir():
        if path.is_dir():
            if not _should_enter_dir(path):
                continue
            yield from _iter_candidate_paths(path)
        else:
            yield path


def _iter_candidate_nodes(root: Path) -> Iterable[Path]:
    for path in root.iterdir():
        if path.is_dir():
            if not _should_enter_dir(path):
                continue
            yield path
            yield from _iter_candidate_nodes(path)
        else:
            yield path


def _manifest_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in _iter_candidate_paths(root) if path.is_file() and _is_manifest(path))


def _current_package_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    paths: list[Path] = []
    for path in _iter_candidate_nodes(root):
        if path.name == "current_package" and (path.is_dir() or path.is_file()):
            paths.append(path)
        elif path.name == "current_package.zip" and path.is_file():
            paths.append(path)
    return sorted(paths)


def _submission_minimal_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in _iter_candidate_nodes(root) if path.name == "submission_minimal" and path.is_dir())


def _study_id_from_manifest(path: Path, payload: Mapping[str, Any]) -> str | None:
    return _text(payload.get("study_id")) or _text(payload.get("study")) or _infer_study_id(path)


def _infer_study_id(path: Path) -> str | None:
    for parent in path.parents:
        name = parent.name
        if name[:3].isdigit() and len(name) > 4:
            return name
    return None


def _authority_owner(payload: Mapping[str, Any]) -> str | None:
    for field_name in _AUTHORITY_OWNER_FIELDS:
        direct = _text(payload.get(field_name))
        if direct:
            return direct
    authority_payload = payload.get("authority")
    if isinstance(authority_payload, Mapping):
        return _text(authority_payload.get("owner")) or _text(authority_payload.get("authority_owner"))
    return None


def _authority_status(payload: Mapping[str, Any], manifest_path: Path) -> str:
    owner = _authority_owner(payload)
    if owner in _KNOWN_AUTHORITY_OWNERS:
        return "classified"
    source_signature = _text(payload.get("source_signature"))
    authority_signature = _text(payload.get("authority_source_signature"))
    if source_signature and authority_signature and source_signature == authority_signature:
        return "classified"
    surface = _text(payload.get("surface"))
    if surface in {"product_entry_manifest", "workspace_manifest", "study_manifest", "delivery_manifest"}:
        return "classified"
    if _is_manifest(manifest_path):
        return "classified"
    return "unclassified"


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _study_roots_from_manifests(workspace_root: Path, manifests: list[Path]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for manifest_path in manifests:
        payload = _read_json(manifest_path)
        study_id = _study_id_from_manifest(manifest_path, payload)
        if study_id is None:
            continue
        candidate = manifest_path.parent
        if candidate.name in {"paper", "manuscript", "submission_minimal"}:
            candidate = candidate.parent
        if candidate.name == "submission_minimal":
            candidate = candidate.parent.parent
        roots.setdefault(study_id, candidate if candidate.exists() else workspace_root)
    return roots


def _count_under(paths: Iterable[Path], root: Path) -> int:
    return sum(1 for path in paths if path == root or root in path.parents)


def _study_reports(workspace_root: Path, manifests: list[Path]) -> list[dict[str, Any]]:
    packages = _current_package_paths(workspace_root)
    submission_minimals = _submission_minimal_paths(workspace_root)
    reports: list[dict[str, Any]] = []
    for study_id, study_root in sorted(_study_roots_from_manifests(workspace_root, manifests).items()):
        study_manifests = [path for path in manifests if _study_id_from_manifest(path, _read_json(path)) == study_id]
        reports.append(
            {
                "study_id": study_id,
                "study_root": _rel(study_root, workspace_root),
                "manifest_count": len(study_manifests),
                "current_package_count": _count_under(packages, study_root),
                "submission_minimal_count": _count_under(submission_minimals, study_root),
                "manifest_paths": [_rel(path, workspace_root) for path in study_manifests],
            }
        )
    return reports


def _workspace_report(workspace_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    manifests = _manifest_paths(workspace_root)
    unclassified = 0
    manifest_reports: list[dict[str, Any]] = []
    for manifest_path in manifests:
        payload = _read_json(manifest_path)
        authority_status = _authority_status(payload, manifest_path)
        if authority_status == "unclassified":
            unclassified += 1
        manifest_reports.append(
            {
                "path": _rel(manifest_path, workspace_root),
                "study_id": _study_id_from_manifest(manifest_path, payload),
                "surface": _text(payload.get("surface")) or manifest_path.stem,
                "authority_status": authority_status,
            }
        )

    studies = _study_reports(workspace_root, manifests)
    workspace = {
        "workspace_root": str(workspace_root),
        "workspace_style": _workspace_style(workspace_root),
        "manifest_count": len(manifests),
        "study_count": len(studies),
        "current_package_count": len(_current_package_paths(workspace_root)),
        "submission_minimal_count": len(_submission_minimal_paths(workspace_root)),
        "manifests": manifest_reports,
    }
    return workspace, studies, unclassified


def run_migration_audit(*, workspace_roots: Iterable[str | Path], dry_run: bool = True) -> dict[str, Any]:
    resolved_roots = sorted(_as_path(root) for root in workspace_roots)
    workspaces: list[dict[str, Any]] = []
    studies: list[dict[str, Any]] = []
    unclassified = 0

    for workspace_root in resolved_roots:
        workspace, workspace_studies, workspace_unclassified = _workspace_report(workspace_root)
        workspaces.append(workspace)
        studies.extend(
            {
                "workspace_root": workspace["workspace_root"],
                "workspace_style": workspace["workspace_style"],
                **study,
            }
            for study in workspace_studies
        )
        unclassified += workspace_unclassified

    return {
        "surface": "control_plane_migration_audit",
        "schema_version": 1,
        "dry_run": bool(dry_run),
        "workspace_count": len(workspaces),
        "study_count": len(studies),
        "unclassified_authority_surface": unclassified,
        "apply_actions": [],
        "delete_actions": [],
        "write_actions": [],
        "workspaces": workspaces,
        "studies": studies,
    }
