from __future__ import annotations

import sys
from types import ModuleType

from med_autoscience.lazy_module_proxy import LazyModuleProxy


def test_lazy_module_proxy_tracks_sys_modules_replacement(monkeypatch) -> None:
    module_name = "med_autoscience.tests.fake_lazy_proxy_target"
    first = ModuleType(module_name)
    first.marker = "first"
    second = ModuleType(module_name)
    second.marker = "second"
    monkeypatch.setitem(sys.modules, module_name, first)
    proxy = LazyModuleProxy(lambda: sys.modules[module_name], module_name=module_name)

    assert proxy.marker == "first"

    monkeypatch.setitem(sys.modules, module_name, second)
    assert proxy.marker == "second"

    proxy.marker = "patched"
    assert second.marker == "patched"
    assert first.marker == "first"
