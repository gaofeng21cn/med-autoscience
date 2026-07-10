from __future__ import annotations

import importlib


def _legacy_action() -> dict[str, object]:
    return {
        "surface_kind": "current_executable_owner_action",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "legacy-repair",
        "work_unit_fingerprint": "legacy-repair::fingerprint",
    }


def test_legacy_current_surfaces_without_canonical_next_action_fail_closed() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.current_control_executable_handoff"
    )
    legacy_action = _legacy_action()

    assert module.current_control_executable_owner_action(
        {
            "current_executable_owner_action": legacy_action,
            "current_work_unit": {"state": {"current_executable_owner_action": legacy_action}},
            "current_execution_envelope": {"state_kind": "executable_owner_action"},
        }
    ) is None
