from __future__ import annotations

from importlib import import_module
from types import ModuleType

_PART_MODULES = (
    "publication_and_submission",
    "publication_owner_currentness",
    "manual_finish_dominance",
    "runtime_events",
    "supervisor_state_overrides",
    "runtime_health_dominance",
    "domain_status_authority",
)


def _reexport(module: ModuleType) -> None:
    names = getattr(module, "__all__", None)
    if names is None:
        names = tuple(name for name in vars(module) if not name.startswith("_"))
    for name in names:
        globals()[name] = getattr(module, name)


for _module_name in _PART_MODULES:
    _reexport(import_module(f"{__package__}.study_runtime_decision_parts.{_module_name}"))

del ModuleType

__all__ = tuple(name for name in globals() if not name.startswith("_"))

del _PART_MODULES, _module_name, _reexport
