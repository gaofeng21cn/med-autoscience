from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.study_progress_cases.provider_admission_projection_cases.current_control_typed_blocker import (
    _current_executable_quality_repair_payload,
    _quality_repair_consumed_typed_blocker_handoff,
    _write_ready_quality_repair_dispatch,
)


def test_provider_admission_projection_honors_handoff_consumed_typed_blocker(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload=_current_executable_quality_repair_payload(study_id=study_id, fingerprint=fingerprint),
        handoff=_quality_repair_consumed_typed_blocker_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
    }


def test_existing_projection_refresh_keeps_current_control_typed_blocker_over_stale_action(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)

    result = module.refresh_existing_projection_current_owner_surfaces(
        payload={
            **_current_executable_quality_repair_payload(study_id=study_id, fingerprint=fingerprint),
            "quest_id": study_id,
            "opl_current_control_state_handoff": _quality_repair_consumed_typed_blocker_handoff(
                study_id=study_id,
                fingerprint=fingerprint,
                source="opl_current_control_state.current_work_unit",
            ),
            "progress_first_monitoring_summary": {
                "owner_action_admission": {
                    "admission_pending": True,
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
        status={
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_liveness_audit": {},
            "runtime_health_snapshot": {},
        },
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
        attach_delivery_inspection_projection_fn=lambda payload, **_: payload,
    )

    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["owner"] == "med-autoscience"
    assert result["current_work_unit"]["work_unit_fingerprint"] == fingerprint
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert result["current_executable_owner_action"] is None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["owner_action_admission"]["admission_pending"] is False
    assert result["paper_recovery_state"]["phase"] == "domain_blocked"
