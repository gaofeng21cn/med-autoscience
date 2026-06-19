from __future__ import annotations

import importlib

from tests.provider_admission_current_control_helpers import opl_transition_readback


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"


def _live_readback(*, work_unit_id: str, fingerprint: str, stage_run_id: str = "sat-live") -> dict[str, object]:
    route_key = f"provider-admission::{STUDY_ID}::{fingerprint}"
    return opl_transition_readback(
        STUDY_ID,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=stage_run_id,
    )


def test_envelope_prefers_running_provider_attempt_over_stale_action_queue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")
    work_unit_id = "complete_medical_paper_readiness_surface"
    fingerprint = "sha256:complete-medical-paper-readiness-running"

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": work_unit_id,
                "owner": "MedAutoScience",
                "next_work_unit": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            }
        ],
        blocked_reason=None,
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "study_id": STUDY_ID,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": work_unit_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "opl_domain_progress_transition_runtime_live_readback": _live_readback(
                work_unit_id=work_unit_id,
                fingerprint=fingerprint,
            ),
            "runtime_health": {
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == work_unit_id
    assert envelope["typed_blocker"] is None


def test_envelope_prefers_running_provider_attempt_over_readiness_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")
    work_unit_id = "complete_medical_paper_readiness_surface"
    fingerprint = "sha256:readiness-blocker-running"

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": work_unit_id,
                "owner": "MedAutoScience",
                "next_work_unit": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "study_id": STUDY_ID,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": work_unit_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "opl_domain_progress_transition_runtime_live_readback": _live_readback(
                work_unit_id=work_unit_id,
                fingerprint=fingerprint,
            ),
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == work_unit_id
    assert envelope["typed_blocker"] is None
