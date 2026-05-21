from __future__ import annotations

from pathlib import Path
from typing import Any

from .sidecar_family_adapter_parts.dispatch_orchestration import (
    dispatch_family_sidecar_task as _dispatch_family_sidecar_task,
)
from .sidecar_family_adapter_parts.export_projection import export_family_sidecar


def dispatch_family_sidecar_task(*, task_path: Path) -> dict[str, Any]:
    return _dispatch_family_sidecar_task(task_path=task_path)


__all__ = ["dispatch_family_sidecar_task", "export_family_sidecar"]
