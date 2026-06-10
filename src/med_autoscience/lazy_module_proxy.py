from __future__ import annotations

import sys
from importlib import import_module
from typing import Any, Callable


class LazyModuleProxy:
    def __init__(self, loader: Callable[[], Any], *, module_name: str | None = None) -> None:
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_module", None)

    def _resolve(self) -> Any:
        module = object.__getattribute__(self, "_module")
        module_name = object.__getattribute__(self, "_module_name")
        if module_name is None and module is not None:
            module_name = getattr(module, "__name__", None)
        if module_name:
            current = sys.modules.get(module_name)
            if current is not None:
                if module is not current:
                    object.__setattr__(self, "_module", current)
                return current
            module = None
        if module is None:
            module = object.__getattribute__(self, "_loader")()
            loaded_name = module_name or getattr(module, "__name__", None)
            if loaded_name:
                current = sys.modules.get(loaded_name)
                if current is not None:
                    module = current
                object.__setattr__(self, "_module_name", loaded_name)
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        setattr(self._resolve(), name, value)


def lazy_import_module(module_name: str) -> LazyModuleProxy:
    return LazyModuleProxy(lambda: import_module(module_name), module_name=module_name)


def lazy_controller_module(module_name: str) -> LazyModuleProxy:
    return lazy_import_module(f"med_autoscience.controllers.{module_name}")


__all__ = ["LazyModuleProxy", "lazy_controller_module", "lazy_import_module"]
