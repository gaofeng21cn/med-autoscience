from __future__ import annotations

import importlib


def test_domain_status_projection_keeps_private_runtime_control_plane_retired() -> None:
    router = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    for name in (
        "request_opl_stage_attempt",
        "pause_study_runtime",
        "_managed_runtime_backend_for_execution",
        "_execute_runtime_decision",
        "_create_quest",
        "_resume_quest",
        "_pause_quest",
    ):
        assert not hasattr(router, name)


def test_domain_status_projection_keeps_provider_backend_resolution_retired() -> None:
    router = importlib.import_module("med_autoscience.controllers.domain_status_projection")

    assert "_managed_runtime_backend_for_execution" not in vars(router)
    assert not hasattr(router, "_managed_runtime_backend_for_execution")
