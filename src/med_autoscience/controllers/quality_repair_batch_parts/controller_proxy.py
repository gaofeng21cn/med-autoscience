from __future__ import annotations

from importlib import import_module
from typing import Any, Callable


class LazyModuleProxy:
    def __init__(self, loader: Callable[[], Any]) -> None:
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_module", None)

    def _resolve(self) -> Any:
        module = object.__getattribute__(self, "_module")
        if module is None:
            module = object.__getattribute__(self, "_loader")()
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        setattr(self._resolve(), name, value)


def lazy_controller_module(module_name: str) -> LazyModuleProxy:
    return LazyModuleProxy(lambda: import_module(f"med_autoscience.controllers.{module_name}"))


__all__ = ["LazyModuleProxy", "lazy_controller_module"]
