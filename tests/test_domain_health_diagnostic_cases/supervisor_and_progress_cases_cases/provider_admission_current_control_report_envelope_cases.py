from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_runtime_report_prefers_fresh_progress_envelope_over_stale_user_waiting_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"

    result = report_aggregation._current_execution_envelopes(
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "continue_supervising_runtime",
                },
            }
        ],
        suppressions=[],
        progress_currentness={
            study_id: {
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source_refs": [
                        "/workspace/studies/003/artifacts/controller/repair_execution_evidence/latest.json"
                    ],
                    "conflict_suppression_refs": [
                        "runtime_health:continue_supervising_runtime"
                    ],
                },
            }
        },
    )

    envelope = result[study_id]
    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == work_unit_id
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None


def test_runtime_report_managed_action_uses_running_current_work_unit_over_stale_handoff_blocker() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    active_stage_attempt_id = "sat_984679e67f111f547bea943e"
    active_workflow_id = "wf_5224528fda81acd998d7073c"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "runtime_health_snapshot": {
                    "attempt_state": "live",
                    "worker_liveness_state": {
                        "state": "live",
                        "active_run_id": f"opl-stage-attempt://{active_stage_attempt_id}",
                    },
                },
                "authority_snapshot": {
                    "blocking_reasons": ["opl_current_control_state.handoff_required"],
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[
            {
                "surface_kind": "mas_opl_runtime_owner_handoff",
                "study_id": study_id,
                "status": "handoff_required",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "typed_blocker": {"blocker_type": "opl_runtime_owner_handoff_required"},
            }
        ],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "running_provider_attempt",
                    "owner": "one-person-lab",
                    "state": {
                        "state_kind": "running_provider_attempt",
                        "provider_attempt_proof": {
                            "running_provider_attempt": True,
                            "active_stage_attempt_id": active_stage_attempt_id,
                            "active_run_id": f"opl-stage-attempt://{active_stage_attempt_id}",
                            "active_workflow_id": active_workflow_id,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "running_provider_attempt",
                    "owner": "one-person-lab",
                    "next_work_unit": active_stage_attempt_id,
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["decision"] == "noop"
    assert action["reason"] == "running_provider_attempt_observed"
    assert action["running_provider_attempt"] is True
    assert action["active_stage_attempt_id"] == active_stage_attempt_id
    assert action["active_workflow_id"] == active_workflow_id
    assert result["current_execution_envelopes"][study_id]["state_kind"] == "running_provider_attempt"
    handoff = result["managed_study_opl_runtime_owner_handoffs"][0]
    assert handoff["status"] == "superseded_by_current_work_unit"
    assert handoff["previous_status"] == "handoff_required"
    assert handoff["reason"] == "running_provider_attempt"
    assert handoff["refs_only_handoff_superseded"] is True
