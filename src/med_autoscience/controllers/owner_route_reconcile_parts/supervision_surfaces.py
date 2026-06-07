from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import domain_route_contract
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile


SUPERVISION_LATEST_RELATIVE_PATH = domain_route_contract.SUPERVISION_LATEST_RELATIVE_PATH
SUPERVISION_HISTORY_RELATIVE_PATH = domain_route_contract.SUPERVISION_HISTORY_RELATIVE_PATH
SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES = domain_route_contract.SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES
SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES = domain_route_contract.SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES
SUPERVISION_FORBIDDEN_ACTIONS = domain_route_contract.SUPERVISION_FORBIDDEN_ACTIONS


def latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_HISTORY_RELATIVE_PATH


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def repair_lifecycle_path(study_root: Path) -> Path:
    return study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"


def clear_resolved_repair_lifecycle(
    *,
    study_root: Path,
    previous_lifecycle: Mapping[str, Any],
    current_lifecycle: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    persist_surfaces: bool,
) -> bool:
    if not persist_surfaces or not developer_mode.safe_actions_enabled:
        return False
    if not previous_lifecycle or current_lifecycle:
        return False
    try:
        repair_lifecycle_path(study_root).unlink()
    except FileNotFoundError:
        return False
    return True


__all__ = [
    "SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES",
    "SUPERVISION_FORBIDDEN_ACTIONS",
    "SUPERVISION_HISTORY_RELATIVE_PATH",
    "SUPERVISION_LATEST_RELATIVE_PATH",
    "SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES",
    "append_json_line",
    "clear_resolved_repair_lifecycle",
    "history_path",
    "latest_path",
    "read_json_object",
    "repair_lifecycle_path",
    "write_json",
]
