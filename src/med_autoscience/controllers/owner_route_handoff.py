from __future__ import annotations

from .owner_route_handoff_parts.domain_handler_export import export_family_domain_handler


def dispatch_family_domain_handler_task(*args, **kwargs):
    from .owner_route_handoff_parts.dispatch_orchestration import (
        dispatch_family_domain_handler_task as _dispatch_family_domain_handler_task,
    )

    return _dispatch_family_domain_handler_task(*args, **kwargs)


__all__ = ["dispatch_family_domain_handler_task", "export_family_domain_handler"]
