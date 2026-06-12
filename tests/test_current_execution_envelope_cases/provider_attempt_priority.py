from __future__ import annotations

import importlib


def test_envelope_prefers_running_provider_attempt_over_stale_action_queue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        blocked_reason=None,
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": "complete_medical_paper_readiness_surface",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "runtime_health": {
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
            "work_unit_id": "complete_medical_paper_readiness_surface",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert envelope["typed_blocker"] is None


def test_envelope_prefers_running_provider_attempt_over_readiness_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": "complete_medical_paper_readiness_surface",
            "work_unit_id": "complete_medical_paper_readiness_surface",
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
            "work_unit_id": "complete_medical_paper_readiness_surface",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert envelope["typed_blocker"] is None
