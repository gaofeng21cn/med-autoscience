from __future__ import annotations

import importlib

import pytest


def test_runtime_supervision_module_is_physically_retired() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.controllers.runtime_supervision")


def test_domain_health_diagnostic_is_the_remaining_mas_diagnostic_surface() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")

    assert hasattr(module, "run_domain_health_diagnostic_for_runtime")
    assert not hasattr(module, "materialize_runtime_supervision")
