from __future__ import annotations

from importlib import import_module
from types import ModuleType

_PART_MODULES = (
    "asset_scans",
    "catalog_checks",
    "manuscript_checks",
    "reporting",
    "shared",
)


def _reexport(module: ModuleType) -> None:
    names = getattr(module, "__all__", None)
    if names is None:
        names = tuple(name for name in vars(module) if not name.startswith("_"))
    for name in names:
        globals()[name] = getattr(module, name)


for _module_name in _PART_MODULES:
    _reexport(import_module(f"{__package__}.medical_publication_surface_parts.{_module_name}"))

del import_module, ModuleType

__all__ = tuple(name for name in globals() if not name.startswith("_"))

del _PART_MODULES, _module_name, _reexport
