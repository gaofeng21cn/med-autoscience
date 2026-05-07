from __future__ import annotations

from .workspace_surfaces_parts import cockpit_markdown as _cockpit_markdown
from .workspace_surfaces_parts import cockpit_payload as _cockpit_payload
from .workspace_surfaces_parts import launch_surface as _launch_surface
from .workspace_surfaces_parts import state_and_study_items as _state_and_study_items


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


for _module in (
    _state_and_study_items,
    _cockpit_payload,
    _cockpit_markdown,
    _launch_surface,
):
    _module_reexport(_module)

del _module

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
