from __future__ import annotations

import importlib

import pytest


def test_runtime_supervision_module_is_physically_retired() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.controllers.runtime_supervision")
