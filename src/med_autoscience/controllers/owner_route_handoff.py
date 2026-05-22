from __future__ import annotations

from pathlib import Path
from typing import Any

from .owner_route_handoff_parts.dispatch_orchestration import dispatch_family_sidecar_task
from .owner_route_handoff_parts.export_projection import export_family_sidecar


def dispatch_owner_route_handoff_task(*, task_path: Path) -> dict[str, Any]:
    return dispatch_family_sidecar_task(task_path=task_path)


__all__ = ["dispatch_family_sidecar_task", "dispatch_owner_route_handoff_task", "export_family_sidecar"]
