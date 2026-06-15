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


def test_runtime_report_preserves_user_gate_when_provider_admission_is_pending() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    gate = {
        "gate_kind": "developer_supervisor",
        "blocked": True,
        "reason": "developer_apply_safe_required",
        "requested_mode": "external_observe",
        "effective_mode": "external_observe",
        "required_mode": "developer_apply_safe",
        "safe_actions_enabled": False,
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "execution_gate": gate,
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[
            {
                "study_id": study_id,
                "status": "provider_admission_pending",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            }
        ],
        managed_study_progress_currentness={
            study_id: {
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert result["provider_admission_pending_count"] == 1
    assert result["will_start_llm"] is False
    assert action["decision"] == "blocked"
    assert action["reason"] == "quest_waiting_for_user"
    assert action["running_provider_attempt"] is False
    assert action["execution_gate"] == gate
    assert action["provider_admission_state"] == {
        "status": "pending_but_execution_gate_blocked",
        "candidate_count": 1,
        "running_provider_attempt": False,
        "execution_gate_reason": "developer_apply_safe_required",
    }


def test_runtime_report_uses_managed_action_runtime_health_for_recovery_state() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-event-current",
                    },
                    "state": {
                        "state_kind": "executable_owner_action",
                        "provider_admission_pending": True,
                    },
                },
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "next_owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["paper_recovery_provider_admission_blocked_count"] == 1
    recovery = result["paper_recovery_states"][study_id]
    assert recovery["phase"] == "admission_blocked"
    assert recovery["conditions"] == [
        {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "runtime_recovery_retry_budget_exhausted",
        }
    ]
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "admission_blocked"
    assert action["paper_recovery_state"]["next_safe_action"]["provider_admission_allowed"] is False


def test_runtime_report_prefers_owner_receipt_currentness_over_stale_user_waiting_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    owner_receipt_ref = (
        "/workspace/studies/003/artifacts/controller/quality_repair_batch/latest.json"
    )
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_receipt_recorded",
        "current_authority": {
            "obligation": {
                "study_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            }
        },
        "next_safe_action": {
            "kind": "consume_owner_receipt",
            "owner": "write",
            "provider_admission_allowed": False,
            "owner_receipt_ref": owner_receipt_ref,
        },
        "owner_receipt_ref": owner_receipt_ref,
        "evidence_refs": [owner_receipt_ref],
        "supervisor_decision": {"decision": "stop_with_owner_receipt"},
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": owner_receipt_ref,
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "owner_receipt_recorded",
                    "owner": "write",
                    "next_work_unit": None,
                    "typed_blocker": None,
                    "parked_state": None,
                },
                "paper_recovery_state": recovery_state,
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["decision"] == "owner_receipt_recorded"
    assert action["reason"] == "current_owner_receipt_recorded"
    assert action["running_provider_attempt"] is False
    assert action["current_work_unit"]["status"] == "owner_receipt_recorded"
    assert action["paper_recovery_state"]["phase"] == "owner_receipt_recorded"
    assert action["paper_recovery_state"]["next_safe_action"]["kind"] == "consume_owner_receipt"
