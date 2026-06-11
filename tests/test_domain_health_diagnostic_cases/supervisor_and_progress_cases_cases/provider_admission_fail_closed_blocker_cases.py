from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_provider_admission_candidate_fail_closes_owner_route_no_selected_dispatch_blocker() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "write",
                    "required_output_surface": "canonical manuscript story-surface delta",
                    "dispatch_path": "/workspace/current-quality-repair.json",
                    "action_fingerprint": fingerprint,
                    "owner_route": {
                        "next_owner": "write",
                        "work_unit_fingerprint": fingerprint,
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            },
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "write",
                "typed_blocker": {
                    "blocker_type": "owner_route_no_selected_dispatch_for_requested_action",
                    "owner": "write",
                },
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "allowed_actions": ["run_quality_repair_batch"],
            },
        },
    )

    assert result == []
