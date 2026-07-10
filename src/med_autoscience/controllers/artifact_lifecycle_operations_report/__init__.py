from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.artifact_lifecycle_inventory import (
    OPL_ARTIFACT_LIFECYCLE_INDEX,
    OPL_ARTIFACT_LIFECYCLE_OWNER_REF,
    read_opl_artifact_lifecycle_refs,
)


SCHEMA_VERSION = 2
SURFACE_KIND = "artifact_lifecycle_report"
OPL_WORKSPACE_INDEX = Path("workspace_index.json")


def run_lifecycle_operations_report(
    *,
    workspace_roots: Iterable[str | Path],
    deep: bool = False,
    max_files: int | None = None,
    max_seconds: float | None = None,
) -> dict[str, Any]:
    workspaces = [
        _workspace_projection(Path(root).expanduser().resolve())
        for root in sorted(workspace_roots, key=str)
    ]
    projects = [
        project
        for workspace in workspaces
        for project in workspace["projects"]
    ]
    available_count = sum(project["status"] == "available" for project in projects)
    return {
        "surface": SURFACE_KIND,
        "surface_kind": "mas_artifact_lifecycle_refs_report",
        "schema_version": SCHEMA_VERSION,
        "report_kind": "opl_lifecycle_index_domain_projection",
        "status": (
            "available"
            if projects and available_count == len(projects)
            else "partial"
            if available_count
            else "opl_projection_required"
        ),
        "workspace_count": len(workspaces),
        "project_count": len(projects),
        "available_project_count": available_count,
        "workspaces": workspaces,
        "scan_policy": {
            "inventory_owner": "one-person-lab",
            "inventory_source": "opl_workspace_artifact_lifecycle_index",
            "recursive_scan_enabled": False,
            "filesystem_discovery_enabled": False,
            "mas_builds_lifecycle_registry": False,
            "mas_computes_restore_or_cleanup_readiness": False,
        },
        "requested_options": {
            "deep": bool(deep),
            "max_files": max_files,
            "max_seconds": max_seconds,
            "options_affect_inventory": False,
        },
        "retention_and_delivery_authority": {
            "generic_lifecycle_owner": "one-person-lab",
            "domain_artifact_authority_owner": "MedAutoScience",
            "mas_retains_artifact_mutation_authorization": True,
            "mas_retains_canonical_rebuild_and_package_freshness_interpretation": True,
            "mas_can_authorize_cleanup_from_projection": False,
            "opl_projection_can_authorize_artifact_mutation": False,
        },
        "mutation_policy": {
            "read_only": True,
            "writes_workspace": False,
            "physical_cleanup_performed": False,
        },
        "authority_boundary": {
            "opl_owner_surface_ref": OPL_ARTIFACT_LIFECYCLE_OWNER_REF,
            "mas_projection_is_refs_only": True,
            "mas_scans_workspace_for_lifecycle": False,
            "mas_can_claim_artifact_ready": False,
            "mas_can_claim_package_ready": False,
            "mas_can_claim_publication_ready": False,
        },
    }


def _workspace_projection(workspace_root: Path) -> dict[str, Any]:
    workspace_index_path = workspace_root / OPL_WORKSPACE_INDEX
    workspace_index = _read_json_object(workspace_index_path)
    projects, blocker = _declared_projects(
        workspace_root=workspace_root,
        workspace_index=workspace_index,
        workspace_index_exists=workspace_index_path.is_file(),
    )
    project_projections = [
        _project_projection(
            workspace_root=workspace_root,
            project_id=project["project_id"],
            project_root=project["project_root"],
        )
        for project in projects
    ]
    return {
        "workspace_root": str(workspace_root),
        "workspace_index_ref": str(workspace_index_path),
        "workspace_index_status": (
            "loaded"
            if workspace_index
            else "invalid"
            if blocker
            else "direct_project_root"
        ),
        "workspace_index_blocker": blocker,
        "project_count": len(project_projections),
        "projects": project_projections,
    }


def _declared_projects(
    *,
    workspace_root: Path,
    workspace_index: Mapping[str, Any],
    workspace_index_exists: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    if not workspace_index_exists:
        return [
            {
                "project_id": workspace_root.name,
                "project_root": workspace_root,
            }
        ], None
    if (
        workspace_index.get("surface_kind") != "opl_workspace_index"
        or workspace_index.get("version") != "workspace-index.v1"
        or not isinstance(workspace_index.get("projects"), list)
    ):
        return [], "opl_workspace_index_invalid"
    projects: list[dict[str, Any]] = []
    for item in workspace_index["projects"]:
        if not isinstance(item, Mapping):
            continue
        project_root_ref = _text(item.get("project_root"))
        if project_root_ref is None:
            continue
        projects.append(
            {
                "project_id": _text(item.get("project_id")) or project_root_ref,
                "project_root": (workspace_root / project_root_ref).resolve(),
            }
        )
    return projects, None


def _project_projection(
    *,
    workspace_root: Path,
    project_id: str,
    project_root: Path,
) -> dict[str, Any]:
    lifecycle = read_opl_artifact_lifecycle_refs(study_root=project_root)
    return {
        "project_id": project_id,
        "project_root": str(project_root),
        "workspace_relative_project_root": _relative_ref(project_root, workspace_root),
        "status": lifecycle["status"],
        "opl_artifact_lifecycle_index_ref": lifecycle[
            "opl_artifact_lifecycle_index_ref"
        ],
        "opl_owner_surface_ref": lifecycle["opl_owner_surface_ref"],
        "lifecycle_status": lifecycle["lifecycle_status"],
        "refs": dict(lifecycle["refs"]),
        "authority_boundary": dict(lifecycle["authority_boundary"]),
    }


def render_lifecycle_operations_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Artifact Lifecycle Refs",
        "",
        f"- status: `{report.get('status') or 'unknown'}`",
        f"- inventory owner: `{dict(report.get('scan_policy') or {}).get('inventory_owner') or 'one-person-lab'}`",
        f"- project count: `{report.get('project_count') or 0}`",
        f"- available project count: `{report.get('available_project_count') or 0}`",
        "",
    ]
    for workspace in report.get("workspaces") or []:
        if not isinstance(workspace, Mapping):
            continue
        lines.append(f"## `{workspace.get('workspace_root')}`")
        lines.append("")
        for project in workspace.get("projects") or []:
            if not isinstance(project, Mapping):
                continue
            lines.append(
                f"- `{project.get('project_id')}`: `{project.get('status')}`; "
                f"index `{project.get('opl_artifact_lifecycle_index_ref')}`"
            )
        lines.append("")
    return "\n".join(lines)


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _relative_ref(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


__all__ = [
    "OPL_ARTIFACT_LIFECYCLE_INDEX",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "render_lifecycle_operations_report_markdown",
    "run_lifecycle_operations_report",
]
