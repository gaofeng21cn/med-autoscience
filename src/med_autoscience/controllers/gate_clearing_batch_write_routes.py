from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers.control_plane_route_context_call import call_with_control_plane_route_context
from med_autoscience.profiles import WorkspaceProfile


def route_bound_call(*, function, control_plane_route_context: dict[str, Any] | None):
    return lambda *, paper_root, profile: call_with_control_plane_route_context(
        function,
        paper_root=paper_root,
        profile=profile,
        control_plane_route_context=control_plane_route_context,
    )


def create_submission_minimal_package_with_route(
    *,
    submission_minimal,
    paper_root: Path,
    profile: WorkspaceProfile,
    control_plane_route_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return call_with_control_plane_route_context(
        submission_minimal.create_submission_minimal_package,
        paper_root=paper_root,
        publication_profile=profile.default_publication_profile,
        citation_style=profile.default_citation_style,
        control_plane_route_context=control_plane_route_context,
    )


def sync_submission_minimal_delivery_with_route(
    *,
    study_delivery_sync,
    paper_root: Path,
    profile: WorkspaceProfile,
    control_plane_route_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return call_with_control_plane_route_context(
        study_delivery_sync.sync_study_delivery,
        paper_root=paper_root,
        stage="submission_minimal",
        publication_profile=profile.default_publication_profile,
        control_plane_route_context=control_plane_route_context,
    )


__all__ = [
    "create_submission_minimal_package_with_route",
    "route_bound_call",
    "sync_submission_minimal_delivery_with_route",
]
