from __future__ import annotations

from importlib import import_module
from types import ModuleType

_PART_MODULES = (
    "shared",
    "program_surfaces",
    "workspace_surfaces",
    "manifest_surfaces",
    "entry_runtime",
)


def _reexport(module: ModuleType) -> None:
    names = getattr(module, "__all__", None)
    if names is None:
        names = tuple(name for name in vars(module) if not name.startswith("_"))
    for name in names:
        globals()[name] = getattr(module, name)


for _module_name in _PART_MODULES:
    _reexport(import_module(f"{__package__}.product_entry_parts.{_module_name}"))

del import_module, ModuleType

__all__ = tuple(name for name in globals() if not name.startswith("_"))

del _PART_MODULES, _module_name, _reexport
from .medical_paper_operator_actions import dispatch_guarded_medical_paper_operator_action
