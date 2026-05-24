from __future__ import annotations

from .owner_route_handoff_parts.export_projection import export_family_sidecar


def dispatch_family_sidecar_task(*args, **kwargs):
    from .owner_route_handoff_parts.dispatch_orchestration import (
        dispatch_family_sidecar_task as _dispatch_family_sidecar_task,
    )

    return _dispatch_family_sidecar_task(*args, **kwargs)


__all__ = ["dispatch_family_sidecar_task", "export_family_sidecar"]
