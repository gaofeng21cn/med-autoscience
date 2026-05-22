from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import submission_milestone_parking
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile


def refresh_if_platform_repair_required(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_payload: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    enabled: bool,
    runtime_platform_repair_required: bool,
) -> dict[str, Any] | None:
    if not runtime_platform_repair_required:
        return None
    return submission_milestone_parking.refresh_submission_milestone_parking(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status=status_payload,
        developer_mode=developer_mode,
        enabled=enabled,
    )


def reconcile_stopped_parking(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_payload: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    enabled: bool,
) -> dict[str, Any] | None:
    return submission_milestone_parking.reconcile_stopped_submission_milestone_parking(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status=status_payload,
        developer_mode=developer_mode,
        enabled=enabled,
    )


def applied(refresh: Mapping[str, Any] | None) -> bool:
    return _text(_mapping(refresh).get("dispatch_status")) == "applied"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
