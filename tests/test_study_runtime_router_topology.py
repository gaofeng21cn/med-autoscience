from __future__ import annotations

import importlib

import pytest


def test_retired_private_runtime_modules_are_not_importable() -> None:
    for module_name in (
        "med_autoscience.controllers.study_runtime_execution",
        "med_autoscience.controllers.study_runtime_transport",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)


def test_router_does_not_reexport_retired_private_runtime_bindings() -> None:
    router = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    exported_names = set(vars(router))

    assert not [name for name in exported_names if name.startswith("StudyRuntimeExecution")]
    assert not [name for name in exported_names if name.startswith("_managed_runtime_backend")]
    assert not [name for name in exported_names if name.startswith("_execute_runtime_")]
    assert not [
        name
        for name in exported_names
        if name in {"request_opl_stage_attempt", "pause_study_runtime"}
        or name.startswith("_create_quest")
        or name.startswith("_resume_quest")
        or name.startswith("_pause_quest")
    ]


def test_router_topology_does_not_keep_provider_backend_alias() -> None:
    router = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    assert not hasattr(router, "_managed_runtime_backend_for_execution")
    assert "_managed_runtime_backend_for_execution" not in vars(router)
