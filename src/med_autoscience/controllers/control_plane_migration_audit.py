from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
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
_FINGERPRINT_LENGTH = 24


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


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _fingerprint(prefix: str, payload: object) -> str:
    return f"{prefix}::{_canonical_digest(payload)[:_FINGERPRINT_LENGTH]}"


def _content_addressed_recorded_at(digest: str) -> str:
    offset_seconds = int(digest[:8], 16) % 86400
    recorded_at = datetime(2026, 5, 3, tzinfo=UTC) + timedelta(seconds=offset_seconds)
    return recorded_at.isoformat()


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


def _delivery_projection_completion(
    *,
    current_package_count: int,
    submission_minimal_count: int,
    delivery_manifest_summary: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None]:
    missing_delivery_surfaces = _missing_delivery_manifest_surfaces(delivery_manifest_summary)
    if current_package_count > 0 and submission_minimal_count > 0 and not missing_delivery_surfaces:
        return "current_package_and_submission_minimal_present", None

    missing_surfaces: list[str] = []
    regeneration_path = ["refresh_canonical_manuscript_sources"]
    if current_package_count == 0:
        missing_surfaces.append("current_package")
        regeneration_path.append("regenerate_current_package")
    if submission_minimal_count == 0:
        missing_surfaces.append("submission_minimal")
        regeneration_path.append("regenerate_submission_minimal")
    if missing_surfaces:
        regeneration_path.append("rerun_publication_gate")
        missing_surface = "_and_".join(missing_surfaces)
        return (
            f"missing_{missing_surface}",
            {
                "plan_type": "canonical_regeneration",
                "missing_surface": missing_surface,
                "manual_patch_allowed": False,
                "canonical_regeneration_path": regeneration_path,
                "gate_status": "publication_gate_required_before_delivery_complete",
                "mutation_policy": "dry_run_projection_only",
            },
        )

    for surface_name in missing_delivery_surfaces:
        regeneration_path.append(f"backfill_{surface_name}")
    regeneration_path.append("rerun_publication_gate")
    missing_surface = _delivery_manifest_missing_surface_name(missing_delivery_surfaces)
    return (
        f"missing_{missing_surface}",
        {
            "plan_type": "delivery_manifest_lifecycle_backfill",
            "missing_surface": missing_surface,
            "manual_patch_allowed": False,
            "canonical_regeneration_path": regeneration_path,
            "gate_status": "publication_gate_required_before_delivery_complete",
            "mutation_policy": "dry_run_projection_only",
        },
    )


def _delivery_manifest_missing_surface_name(missing_surfaces: Iterable[str]) -> str:
    names = list(missing_surfaces)
    if "delivery_manifest_lifecycle_hook" in names and "delivery_manifest_publication_refs" in names:
        names = [
            "delivery_manifest_lifecycle_hook" if name == "delivery_manifest_lifecycle_hook" else name
            for name in names
            if name != "delivery_manifest_publication_refs"
        ]
        names.append("publication_refs")
    return "_and_".join(names)


def _missing_delivery_manifest_surfaces(summary: Mapping[str, Any]) -> list[str]:
    if int(summary.get("delivery_manifest_count") or 0) == 0:
        return ["delivery_manifest"]
    missing: list[str] = []
    if not bool(summary.get("lifecycle_hook_present")):
        missing.append("delivery_manifest_lifecycle_hook")
    if not bool(summary.get("source_signature_present")):
        missing.append("delivery_manifest_source_signature")
    if not bool(summary.get("publication_refs_present")):
        missing.append("delivery_manifest_publication_refs")
    return missing


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
        candidate = _study_root_from_manifest(workspace_root=workspace_root, manifest_path=manifest_path, study_id=study_id)
        roots.setdefault(study_id, candidate if candidate.exists() else workspace_root)
    return roots


def _study_root_from_manifest(*, workspace_root: Path, manifest_path: Path, study_id: str) -> Path:
    for parent in manifest_path.parents:
        if parent == workspace_root:
            break
        if parent.name == study_id:
            return parent
    candidate = manifest_path.parent
    while candidate.name in {"current_package", "paper", "manuscript", "submission_minimal"}:
        candidate = candidate.parent
    return candidate


def _count_under(paths: Iterable[Path], root: Path) -> int:
    return sum(1 for path in paths if path == root or root in path.parents)


def _is_delivery_manifest(path: Path, payload: Mapping[str, Any]) -> bool:
    return _text(payload.get("surface")) == "delivery_manifest" or path.name == "delivery_manifest.json"


def _delivery_manifest_summary(manifests: Iterable[Path]) -> dict[str, Any]:
    delivery_manifests = [path for path in manifests if _is_delivery_manifest(path, _read_json(path))]
    return {
        "delivery_manifest_count": len(delivery_manifests),
        "lifecycle_hook_present": any(_delivery_manifest_lifecycle_hook_present(_read_json(path)) for path in delivery_manifests),
        "source_signature_present": any(_delivery_manifest_source_signature_present(_read_json(path)) for path in delivery_manifests),
        "publication_refs_present": any(_delivery_manifest_publication_refs_present(_read_json(path)) for path in delivery_manifests),
    }


def _delivery_manifest_lifecycle_hook_present(payload: Mapping[str, Any]) -> bool:
    lifecycle = payload.get("artifact_lifecycle")
    if not isinstance(lifecycle, Mapping):
        return False
    return bool(lifecycle.get("authority_sync")) and bool(lifecycle.get("lifecycle_roles"))


def _delivery_manifest_source_signature_present(payload: Mapping[str, Any]) -> bool:
    return bool(_text(payload.get("source_signature")) or _text(payload.get("delivery_source_signature")))


def _delivery_manifest_publication_refs_present(payload: Mapping[str, Any]) -> bool:
    for field_name in ("publication_refs", "delivery_context_refs", "publication_context_refs"):
        refs = payload.get(field_name)
        if isinstance(refs, Mapping) and any(_text(value) for value in refs.values()):
            return True
    return False


def _study_reports(workspace_root: Path, manifests: list[Path]) -> list[dict[str, Any]]:
    packages = _current_package_paths(workspace_root)
    submission_minimals = _submission_minimal_paths(workspace_root)
    reports: list[dict[str, Any]] = []
    for study_id, study_root in sorted(_study_roots_from_manifests(workspace_root, manifests).items()):
        study_manifests = [path for path in manifests if _study_id_from_manifest(path, _read_json(path)) == study_id]
        unclassified = sum(
            1
            for path in study_manifests
            if _authority_status(_read_json(path), path) == "unclassified"
        )
        current_package_count = _count_under(packages, study_root)
        submission_minimal_count = _count_under(submission_minimals, study_root)
        delivery_manifest_summary = _delivery_manifest_summary(study_manifests)
        completeness_reason, completion_plan = _delivery_projection_completion(
            current_package_count=current_package_count,
            submission_minimal_count=submission_minimal_count,
            delivery_manifest_summary=delivery_manifest_summary,
        )
        reports.append(
            {
                "study_id": study_id,
                "study_root": _rel(study_root, workspace_root),
                "manifest_count": len(study_manifests),
                "current_package_count": current_package_count,
                "submission_minimal_count": submission_minimal_count,
                "authority_classification": "controller_authorized" if unclassified == 0 else "needs_authority_classification",
                "lifecycle_classification": (
                    "package_and_submission_ready"
                    if completion_plan is None
                    else "delivery_projection_incomplete"
                ),
                "delivery_projection_completeness_reason": completeness_reason,
                "delivery_projection_completion_plan": completion_plan,
                "delivery_manifest_summary": delivery_manifest_summary,
                "authority_summary": {
                    "unclassified_authority_surface": unclassified,
                    "manifest_count": len(study_manifests),
                },
                "lifecycle_summary": {
                    "current_package_count": current_package_count,
                    "submission_minimal_count": submission_minimal_count,
                },
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
    if not dry_run:
        raise ValueError("control plane migration audit is dry-run only; cleanup apply requires a separate controller apply contract")
    resolved_roots = sorted(_as_path(root) for root in workspace_roots)
    workspaces: list[dict[str, Any]] = []
    studies: list[dict[str, Any]] = []
    unclassified = 0

    for workspace_root in resolved_roots:
        workspace, workspace_studies, workspace_unclassified = _workspace_report(workspace_root)
        workspace_fingerprint = _fingerprint("workspace-migration-audit", workspace)
        workspace = {
            **workspace,
            "workspace_fingerprint": workspace_fingerprint,
        }
        workspaces.append(workspace)
        for study in workspace_studies:
            full_study = {
                "workspace_root": workspace["workspace_root"],
                "workspace_style": workspace["workspace_style"],
                "workspace_fingerprint": workspace_fingerprint,
                **study,
            }
            studies.append(
                {
                    **full_study,
                    "study_fingerprint": _fingerprint("study-migration-audit", full_study),
                }
            )
        unclassified += workspace_unclassified

    workspace_fingerprint = _fingerprint(
        "workspace-migration-audit",
        [workspace["workspace_fingerprint"] for workspace in workspaces],
    )
    study_fingerprint = _fingerprint(
        "study-migration-audit",
        [study["study_fingerprint"] for study in studies],
    )
    delivery_plan_count = sum(1 for study in studies if study["delivery_projection_completion_plan"] is not None)
    report_payload = {
        "surface": "control_plane_migration_audit",
        "schema_version": 1,
        "dry_run": bool(dry_run),
        "workspace_count": len(workspaces),
        "study_count": len(studies),
        "unclassified_authority_surface": unclassified,
        "workspace_fingerprint": workspace_fingerprint,
        "study_fingerprint": study_fingerprint,
        "delivery_projection_completion_plan_count": delivery_plan_count,
        "workspaces": workspaces,
        "studies": studies,
    }
    report_digest = _canonical_digest(report_payload)
    recorded_at = _content_addressed_recorded_at(report_digest)
    workspaces = [{**workspace, "recorded_at": recorded_at} for workspace in workspaces]
    studies = [{**study, "recorded_at": recorded_at} for study in studies]

    return {
        "surface": "control_plane_migration_audit",
        "schema_version": 1,
        "report_id": f"control-plane-migration-audit::{report_digest[:_FINGERPRINT_LENGTH]}",
        "recorded_at": recorded_at,
        "dry_run": bool(dry_run),
        "workspace_count": len(workspaces),
        "study_count": len(studies),
        "unclassified_authority_surface": unclassified,
        "workspace_fingerprint": workspace_fingerprint,
        "study_fingerprint": study_fingerprint,
        "delivery_projection_completion_plan_count": delivery_plan_count,
        "mutation_policy": {
            "dry_run_read_only": True,
            "cleanup_apply_supported": False,
        },
        "action_counts": {
            "apply": 0,
            "delete": 0,
            "write": 0,
            "mutating": 0,
        },
        "mutating_actions": [],
        "apply_actions": [],
        "delete_actions": [],
        "write_actions": [],
        "workspaces": workspaces,
        "studies": studies,
    }
