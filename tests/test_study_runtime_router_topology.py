from __future__ import annotations

import importlib


def test_study_runtime_router_reexports_split_startup_and_completion_helpers() -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    startup = importlib.import_module("med_autoscience.controllers.study_runtime_startup")
    completion = importlib.import_module("med_autoscience.controllers.study_runtime_completion")

    assert router._prepare_runtime_overlay is startup._prepare_runtime_overlay
    assert router._audit_runtime_overlay is startup._audit_runtime_overlay
    assert router._build_startup_contract is startup._build_startup_contract
    assert router._build_create_payload is startup._build_create_payload
    assert router._runtime_reentry_requires_startup_hydration is startup._runtime_reentry_requires_startup_hydration
    assert router._runtime_reentry_requires_managed_skill_audit is startup._runtime_reentry_requires_managed_skill_audit
    assert router._run_startup_hydration is startup._run_startup_hydration
    assert router._sync_existing_quest_startup_context is startup._sync_existing_quest_startup_context
    assert router._study_completion_state is completion._study_completion_state
    assert router._build_study_completion_request_message is completion._build_study_completion_request_message
    assert router._sync_study_completion is completion._sync_study_completion
