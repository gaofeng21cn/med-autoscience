from __future__ import annotations

import importlib

import pytest


def test_mas_runtime_transport_package_does_not_export_provider_callables() -> None:
    module = importlib.import_module("med_autoscience.runtime_transport")

    assert not hasattr(module, "__all__")
    for name in (
        "create_quest",
        "resume_quest",
        "relaunch_stopped_quest",
        "pause_quest",
        "chat_quest",
        "schedule_turn",
        "complete_turn_and_normalize",
    ):
        assert not hasattr(module, name)


def test_opl_provider_backed_stage_runtime_callable_module_is_absent() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.runtime_transport.opl_provider_backed_stage_runtime")
