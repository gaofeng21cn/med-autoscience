from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.artifact_lifecycle_inventory import ARTIFACT_ROLES, lifecycle_for_role
from med_autoscience.controllers.control_plane_migration_audit import (
    build_delivery_manifest_historical_backfill_plan,
    summarize_delivery_manifests,
)


PROJECTION_SURFACES = ("current_package", "submission_minimal", "docx", "pdf", "zip")


def build_study_projection_reports(
    *,
    workspace_root: Path,
    study_roots: Iterable[Path],
    artifacts: Iterable[Mapping[str, Any]],
    as_path: Callable[[str | Path], Path],
    is_relative_to: Callable[[Path, Path], bool],
    rel: Callable[[Path, Path], str],
) -> list[dict[str, Any]]:
    artifact_list = [dict(item) for item in artifacts]
    reports: list[dict[str, Any]] = []
    for study_root in sorted({as_path(root) for root in study_roots}):
        study_artifacts = [
            item
            for item in artifact_list
            if is_relative_to(Path(str(item.get("path"))), study_root)
        ]
        surfaces = _projection_surfaces(study_artifacts)
        manifest_paths = [
            Path(str(item.get("path")))
            for item in study_artifacts
            if str(item.get("path") or "").endswith(("manifest.json", "manifest.yaml", "manifest.yml"))
        ]
        delivery_manifest_summary = summarize_delivery_manifests(manifest_paths)
        historical_backfill_plan = build_delivery_manifest_historical_backfill_plan(delivery_manifest_summary)
        reports.append(
            {
                "study_id": _study_id_for_root(study_root, workspace_root),
                "study_root": str(study_root),
                "workspace_relative_study_root": rel(study_root, workspace_root),
                "artifact_count": len(study_artifacts),
                "role_counts": _role_counts(study_artifacts),
                "lifecycle_counts": _lifecycle_counts(study_artifacts),
                "authority_blocker_counts": _blocker_counts(study_artifacts, "authority_blockers"),
                "cleanup_blocker_counts": _blocker_counts(study_artifacts, "cleanup_blockers"),
                "projection_surfaces": surfaces,
                "projection_completeness": projection_completeness(surfaces),
                "delivery_manifest_summary": delivery_manifest_summary,
                "historical_backfill_plan": historical_backfill_plan,
            }
        )
    return reports


def projection_role_catalog() -> dict[str, dict[str, str]]:
    return {
        "current_package": {
            "role": "derived_projection",
            "lifecycle": lifecycle_for_role("derived_projection"),
        },
        "submission_minimal": {
            "role": "derived_projection",
            "lifecycle": lifecycle_for_role("derived_projection"),
            "delivery_package_role": "controller_authorized_package_source",
        },
        "docx": {
            "role": "derived_projection",
            "lifecycle": lifecycle_for_role("derived_projection"),
        },
        "pdf": {
            "role": "derived_projection",
            "lifecycle": lifecycle_for_role("derived_projection"),
        },
        "zip": {
            "role": "derived_projection",
            "lifecycle": lifecycle_for_role("derived_projection"),
        },
    }


def projection_completeness(surfaces: Mapping[str, Any]) -> dict[str, Any]:
    blockers = [
        f"missing_{surface_name}"
        for surface_name in PROJECTION_SURFACES
        if not bool(dict(surfaces.get(surface_name) or {}).get("present"))
    ]
    return {
        "status": "complete" if not blockers else "incomplete",
        "required_surfaces": list(PROJECTION_SURFACES),
        "blockers": blockers,
    }


def workspace_projection_completeness(studies: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    study_list = [dict(item) for item in studies]
    missing_surface_counts = {f"missing_{name}": 0 for name in PROJECTION_SURFACES}
    complete = 0
    incomplete = 0
    for study in study_list:
        completeness = dict(study.get("projection_completeness") or {})
        if completeness.get("status") == "complete":
            complete += 1
        else:
            incomplete += 1
        for blocker in completeness.get("blockers") or []:
            if blocker in missing_surface_counts:
                missing_surface_counts[blocker] += 1
    return {
        "study_count": len(study_list),
        "complete_study_count": complete,
        "incomplete_study_count": incomplete,
        "missing_surface_counts": missing_surface_counts,
    }


def historical_backfill_plan_count(studies: Iterable[Mapping[str, Any]]) -> int:
    return sum(1 for study in studies if study.get("historical_backfill_plan") is not None)


def aggregate_historical_backfill_plan_count(workspaces: Iterable[Mapping[str, Any]]) -> int:
    return sum(int(workspace.get("historical_backfill_plan_count") or 0) for workspace in workspaces)


def aggregate_projection_completeness(workspaces: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    result = {
        "study_count": 0,
        "complete_study_count": 0,
        "incomplete_study_count": 0,
        "missing_surface_counts": {f"missing_{name}": 0 for name in PROJECTION_SURFACES},
    }
    for workspace in workspaces:
        projection = dict(workspace.get("projection_completeness") or {})
        result["study_count"] += int(projection.get("study_count") or 0)
        result["complete_study_count"] += int(projection.get("complete_study_count") or 0)
        result["incomplete_study_count"] += int(projection.get("incomplete_study_count") or 0)
        for key, value in dict(projection.get("missing_surface_counts") or {}).items():
            result["missing_surface_counts"][key] = result["missing_surface_counts"].get(key, 0) + int(value or 0)
    return result


def _projection_surfaces(artifacts: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    artifact_list = [dict(item) for item in artifacts]
    return {
        "current_package": _surface_report(
            name="current_package",
            role="derived_projection",
            artifacts=[
                item
                for item in artifact_list
                if _path_has_part(item, "current_package") or _path_name(item) == "current_package.zip"
            ],
        ),
        "submission_minimal": _surface_report(
            name="submission_minimal",
            role="derived_projection",
            artifacts=[item for item in artifact_list if _path_has_part(item, "submission_minimal")],
            delivery_package_role="controller_authorized_package_source",
        ),
        "docx": _surface_report(
            name="docx",
            role="derived_projection",
            artifacts=[item for item in artifact_list if _path_suffix(item) == ".docx"],
        ),
        "pdf": _surface_report(
            name="pdf",
            role="derived_projection",
            artifacts=[item for item in artifact_list if _path_suffix(item) == ".pdf"],
        ),
        "zip": _surface_report(
            name="zip",
            role="derived_projection",
            artifacts=[item for item in artifact_list if _path_suffix(item) == ".zip"],
        ),
    }


def _surface_report(
    *,
    name: str,
    role: str,
    artifacts: Iterable[Mapping[str, Any]],
    delivery_package_role: str | None = None,
) -> dict[str, Any]:
    artifact_list = [dict(item) for item in artifacts]
    lifecycle = lifecycle_for_role(role)
    report = {
        "surface": name,
        "role": role,
        "lifecycle": lifecycle,
        "present": bool(artifact_list),
        "artifact_count": len(artifact_list),
        "size_bytes": sum(int(item.get("size_bytes") or 0) for item in artifact_list),
        "paths": [str(item.get("workspace_relative_path") or item.get("path") or "") for item in artifact_list],
        "authority_blockers": _artifact_blocker_values(artifact_list, "authority_blockers"),
        "cleanup_blockers": _artifact_blocker_values(artifact_list, "cleanup_blockers"),
    }
    if delivery_package_role is not None:
        report["delivery_package_role"] = delivery_package_role
    return report


def _artifact_blocker_values(artifacts: Iterable[Mapping[str, Any]], key: str) -> list[str]:
    blockers: set[str] = set()
    for item in artifacts:
        blockers.update(str(blocker) for blocker in list(item.get(key) or []))
    return sorted(blockers)


def _role_counts(artifacts: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {role: 0 for role in ARTIFACT_ROLES}
    for item in artifacts:
        role = str(item.get("role") or "")
        if role in counts:
            counts[role] += int(item.get("file_count") or 1)
    return counts


def _lifecycle_counts(artifacts: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in artifacts:
        lifecycle = str(item.get("lifecycle") or "")
        if not lifecycle:
            continue
        counts[lifecycle] = counts.get(lifecycle, 0) + int(item.get("file_count") or 1)
    return counts


def _blocker_counts(items: Iterable[Mapping[str, Any]], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for blocker in item.get(field_name) or []:
            key = str(blocker)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _path_has_part(item: Mapping[str, Any], part: str) -> bool:
    return part in Path(str(item.get("path") or "")).parts


def _path_name(item: Mapping[str, Any]) -> str:
    return Path(str(item.get("path") or "")).name


def _path_suffix(item: Mapping[str, Any]) -> str:
    return Path(str(item.get("path") or "")).suffix.lower()


def _study_id_for_root(study_root: Path, workspace_root: Path) -> str:
    if study_root == workspace_root:
        return workspace_root.name
    return study_root.name
