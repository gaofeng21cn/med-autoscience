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

    retired_bindings = {
        "StudyRuntimeExecutionContext",
        "StudyRuntimeExecutionOutcome",
        "ensure_study_runtime",
        "pause_study_runtime",
        "_managed_runtime_backend_for_execution",
        "_execute_runtime_decision",
        "_create_quest",
        "_resume_quest",
        "_pause_quest",
    }

    assert retired_bindings.isdisjoint(vars(router))


def test_router_topology_does_not_keep_provider_backend_alias() -> None:
    router = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    assert not hasattr(router, "_managed_runtime_backend_for_execution")
    assert "_managed_runtime_backend_for_execution" not in vars(router)
