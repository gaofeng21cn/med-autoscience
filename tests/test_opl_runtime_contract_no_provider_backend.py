from __future__ import annotations

import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_TRANSPORT_ROOT = REPO_ROOT / "src" / "med_autoscience" / "runtime_transport"


def test_mas_runtime_transport_package_is_physically_absent() -> None:
    assert not RUNTIME_TRANSPORT_ROOT.exists()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.runtime_transport")


def test_opl_provider_backed_stage_runtime_callable_module_is_absent() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.runtime_transport.opl_provider_backed_stage_runtime")
