from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.study_task_intake import (
    build_task_intake_progress_override,
    read_latest_task_intake,
    task_intake_requests_manuscript_fast_lane,
)

from . import existing_projection_refresh as _existing_projection_refresh
from .delivery_inspection import attach_delivery_inspection_projection as _attach_delivery_inspection_projection
from .shared_base import _mapping_copy, _non_empty_text


_TASK_INTAKE_OVERRIDE_FIELDS = (
    "quality_closure_truth",
    "quality_execution_lane",
    "same_line_route_truth",
    "same_line_route_surface",
)


def refresh_existing_projection_current_owner_surfaces(
    *,
    payload: dict[str, Any],
    status: dict[str, Any],
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
    attach_delivery_inspection_projection_fn=_attach_delivery_inspection_projection,
) -> dict[str, Any]:
    return _existing_projection_refresh.refresh_existing_projection_current_owner_surfaces(
        payload=payload,
        status=status,
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        attach_delivery_inspection_projection_fn=attach_delivery_inspection_projection_fn,
    )


def refresh_existing_projection_task_intake_override(
    *,
    payload: dict[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    latest_task_intake_payload = read_latest_task_intake(study_root=study_root)
    if not task_intake_requests_manuscript_fast_lane(latest_task_intake_payload):
        return payload
    if build_task_intake_progress_override(latest_task_intake_payload, study_root=study_root) is not None:
        return payload

    quality_closure_truth = _mapping_copy(payload.get("quality_closure_truth"))
    same_line_route_surface = _mapping_copy(payload.get("same_line_route_surface"))
    stale_fast_lane_override = (
        _non_empty_text(quality_closure_truth.get("state")) == "manuscript_fast_lane_requested"
        or _non_empty_text(same_line_route_surface.get("closure_state")) == "manuscript_fast_lane_requested"
    )
    if not stale_fast_lane_override:
        return payload

    refreshed = dict(payload)
    for key in _TASK_INTAKE_OVERRIDE_FIELDS:
        refreshed.pop(key, None)
    refreshed["manuscript_fast_lane_closeout"] = {
        "surface_kind": "manuscript_fast_lane_closeout_projection",
        "status": "task_intake_override_retired",
        "task_id": _non_empty_text(latest_task_intake_payload.get("task_id")),
        "authority_boundary": {
            "authorizes_submission_ready": False,
            "authorizes_publication_ready": False,
        },
    }
    return refreshed
