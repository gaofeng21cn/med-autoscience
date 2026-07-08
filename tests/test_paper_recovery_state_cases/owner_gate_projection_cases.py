from __future__ import annotations

import importlib
from tests.test_paper_recovery_state_cases.shared import _module, _typed_blocker_work_unit



def test_owner_gate_route_back_suppresses_residual_provider_admission_projection() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly.paper_recovery_visibility"
    )
    fingerprint = "publication-blockers::497d1260db522f01"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="002-dm-china-us-mortality-attribution",
                action_type="run_quality_repair_batch",
                work_unit_id="analysis_claim_evidence_repair",
                blocker_type="stage_packet_not_current_selected_dispatch",
            )
            | {
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "study_intervention_events": [
                {
                    "surface": "study_intervention_event",
                    "intent": "owner_gate_decision",
                    "payload": {
                        "decision": "route_back_to_mas_packet_materialization_bug",
                        "current_owner_identity": {
                            "study_id": "002-dm-china-us-mortality-attribution",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "analysis_claim_evidence_repair",
                            "work_unit_fingerprint": fingerprint,
                            "blocker_type": "stage_packet_not_current_selected_dispatch",
                        },
                        "human_gate_ref": "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
                        "owner_gate_decision_ref": "owner-gate-decision:c7027de42ca336cfe0782428",
                        "route_back_evidence_ref": "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
                        "provider_admission_allowed": False,
                    },
                }
            ],
        }
    )

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "queued",
            "current_blockers": [],
            "paper_recovery_state": state,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": fingerprint,
                }
            ],
            "owner_action_admission": {
                "admission_pending": True,
                "provider_attempt_start_requested": True,
            },
            "progress_first_monitoring_summary": {
                "owner_action_admission": {
                    "admission_pending": True,
                    "provider_attempt_start_requested": True,
                }
            },
        }
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["paper_recovery_provider_admission_blocked_count"] == 1
    assert len(result["blocked_provider_admission_candidates"]) == 1
    assert result["owner_action_admission"]["admission_pending"] is False
    assert result["owner_action_admission"]["blocked_by"] == "paper_autonomy_supervisor_decision"
    monitoring = result["progress_first_monitoring_summary"]["owner_action_admission"]
    assert monitoring["admission_pending"] is False
    assert monitoring["blocked_by"] == "paper_autonomy_supervisor_decision"


def test_user_visible_projection_blocks_provider_admission_by_supervisor_decision() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly.paper_recovery_visibility"
    )
    fingerprint = "publication-blockers::497d1260db522f01"
    state = {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "current_authority": {
            "owner": "write",
            "obligation": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": fingerprint,
            },
        },
        "next_safe_action": {
            "kind": "admit_provider_attempt",
            "provider_admission_allowed": True,
        },
        "supervisor_decision": {
            "surface_kind": "paper_autonomy_supervisor_decision",
            "decision": "materialize_recovery_action",
            "next_safe_action": {
                "kind": "materialize_recovery_work_unit_or_receipt",
                "recovery_kind": "opl_runtime_repair",
            },
        },
    }

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "queued",
            "paper_recovery_state": state,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": fingerprint,
                }
            ],
            "owner_action_admission": {
                "admission_pending": True,
                "provider_attempt_start_requested": True,
            },
            "progress_first_monitoring_summary": {
                "owner_action_admission": {
                    "admission_pending": True,
                    "provider_attempt_start_requested": True,
                }
            },
        }
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["owner_action_admission"]["admission_pending"] is False
    assert result["owner_action_admission"]["blocked_by"] == "paper_autonomy_supervisor_decision"
    monitoring = result["progress_first_monitoring_summary"]["owner_action_admission"]
    assert monitoring["admission_pending"] is False
    assert monitoring["blocked_by"] == "paper_autonomy_supervisor_decision"


def test_successor_recovery_visibility_keeps_provider_admission_projection() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly.paper_recovery_visibility"
    )
    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "provider_admission_allowed": True,
                    "owner": "write",
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "next_safe_action": {
                        "kind": "materialize_recovery_work_unit_or_receipt",
                        "source_next_safe_action": {
                            "kind": "materialize_successor_owner_action",
                            "provider_admission_allowed": True,
                        },
                    },
                },
            },
        }
    )

    assert result["provider_admission_pending_count"] == 1
    assert result["provider_admission_candidates"][0]["work_unit_id"] == "medical_prose_write_repair"
    assert "blocked_provider_admission_candidates" not in result
    assert "paper_recovery_provider_admission_blocked_count" not in result


def test_successor_recovery_visibility_keeps_opl_live_readback_with_owner_receipt_current_work_unit() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly.paper_recovery_visibility"
    )
    fingerprint = "publication-blockers::0915410f804b3697"
    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "owner_receipt_recorded",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "status": "provider_admission_pending",
                    "provider_admission_pending": True,
                    "opl_transition_readback_source": (
                        "opl_domain_progress_transition_runtime_live_readback"
                    ),
                }
            ],
            "owner_action_admission": {
                "admission_pending": True,
                "provider_attempt_start_requested": True,
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "provider_admission_allowed": True,
                    "owner": "write",
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "next_safe_action": {
                        "kind": "materialize_recovery_work_unit_or_receipt",
                        "source_next_safe_action": {
                            "kind": "materialize_successor_owner_action",
                            "provider_admission_allowed": True,
                        },
                    },
                },
            },
        }
    )

    assert result["provider_admission_pending_count"] == 1
    assert result["provider_admission_candidates"][0]["work_unit_fingerprint"] == fingerprint
    assert result["owner_action_admission"]["admission_pending"] is True
    assert "blocked_provider_admission_candidates" not in result
    assert "paper_recovery_provider_admission_blocked_count" not in result
