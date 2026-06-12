from __future__ import annotations

from . import shared_base as _shared_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared_base)


def _runtime_state_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json"


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
