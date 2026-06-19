from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_paper_recovery_state_cases.shared import _module, _typed_blocker_work_unit


def test_runtime_report_owner_gate_event_supersedes_managed_action_typed_blocker() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    fingerprint = "publication-blockers::497d1260db522f01"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "stage_packet_not_current_selected_dispatch",
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
                "current_work_unit": _typed_blocker_work_unit(
                    study_id=study_id,
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
                        "event_id": "intervention-event-000001-13263a6ca77a1066",
                        "recorded_at": "2026-06-14T02:27:19+00:00",
                        "payload": {
                            "decision": "route_back_to_mas_packet_materialization_bug",
                            "current_owner_identity": {
                                "study_id": study_id,
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
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    recovery = result["paper_recovery_states"][study_id]
    assert recovery["phase"] == "owner_action_ready"
    assert recovery["conditions"][0]["condition"] == "accepted_owner_gate_decision"
    accepted_decision = recovery["next_safe_action"]["accepted_owner_gate_decision"]
    assert accepted_decision["human_gate_ref"] == (
        "human_gate:owner-gate-decision:c7027de42ca336cfe0782428"
    )
    assert accepted_decision["owner_gate_decision_ref"] == (
        "owner-gate-decision:c7027de42ca336cfe0782428"
    )
    assert accepted_decision["route_back_evidence_ref"] == (
        "route_back:owner-gate-decision:c7027de42ca336cfe0782428"
    )
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "owner_action_ready"
    assert action["decision"] == "blocked"
    assert action["reason"] == "stage_packet_not_current_selected_dispatch"
    assert action["running_provider_attempt"] is False


def test_runtime_report_preserves_human_gate_authority_payload() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::human-gate"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[],
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
                "current_work_unit": _typed_blocker_work_unit(
                    study_id=study_id,
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
                        "event_id": "intervention-event-000001-human",
                        "recorded_at": "2026-06-14T02:27:19+00:00",
                        "payload": {
                            "decision": "wait_for_owner_with_resume_token",
                            "current_owner_identity": {
                                "study_id": study_id,
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "analysis_claim_evidence_repair",
                                "work_unit_fingerprint": fingerprint,
                                "blocker_type": "stage_packet_not_current_selected_dispatch",
                            },
                            "human_gate_ref": "human_gate:owner-gate-decision:003",
                            "owner_gate_decision_ref": "owner-gate-decision:003",
                            "provider_admission_allowed": False,
                        },
                    }
                ],
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    recovery = result["paper_recovery_states"][study_id]
    assert recovery["phase"] == "human_gate"
    assert recovery["next_safe_action"]["kind"] == "resolve_owner_gate_decision"
    accepted_decision = recovery["next_safe_action"]["accepted_owner_gate_decision"]
    assert accepted_decision["human_gate_ref"] == "human_gate:owner-gate-decision:003"
    assert accepted_decision["owner_gate_decision_ref"] == "owner-gate-decision:003"


def test_runtime_report_preserves_gate_followthrough_successor_owner_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    repair_fingerprint = "publication-blockers::0915410f804b3697"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "domain_blocked",
                "reason": "current_work_unit_typed_blocker",
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
                "current_work_unit": _typed_blocker_work_unit(
                    study_id=study_id,
                    action_type="run_gate_clearing_batch",
                    work_unit_id="publication_gate_replay",
                    blocker_type="publication_gate_replay_blocked",
                )
                | {
                    "owner": "publication_gate",
                    "work_unit_fingerprint": gate_fingerprint,
                    "action_fingerprint": gate_fingerprint,
                    "currentness_basis": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-event-current",
                    },
                },
                "gate_clearing_batch_followthrough": {
                    "surface_kind": "gate_clearing_batch_followthrough",
                    "status": "executed",
                    "gate_replay_status": "blocked",
                    "latest_record_path": "/workspace/studies/003/artifacts/controller/gate_clearing_batch/latest.json",
                    "work_unit_currentness": {
                        "current_actionability_status": "actionable",
                        "explicit_publication_work_unit_id": "medical_prose_write_repair",
                        "explicit_work_unit_fingerprint": repair_fingerprint,
                        "lacks_specific_blocker_object": False,
                    },
                    "explicit_publication_work_unit": {
                        "unit_id": "medical_prose_write_repair",
                        "lane": "write",
                    },
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    recovery = result["paper_recovery_states"][study_id]
    assert recovery["phase"] == "owner_action_ready"
    assert recovery["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert recovery["next_safe_action"]["successor_owner_action"] == {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "source_ref": "/workspace/studies/003/artifacts/controller/gate_clearing_batch/latest.json",
    }
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "owner_action_ready"
    assert action["decision"] == "blocked"
    assert action["reason"] == "publication_gate_replay_blocked"


def test_runtime_report_uses_fresh_canonical_paper_recovery_state() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    canonical_recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
        "current_authority": {"owner": "write"},
        "next_safe_action": {
            "kind": "materialize_successor_owner_action",
            "provider_admission_allowed": True,
            "owner": "write",
            "successor_owner_action": {
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
            },
        },
        "supervisor_decision": {
            "decision": "materialize_recovery_action",
        },
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "domain_blocked",
                "reason": "current_work_unit_typed_blocker",
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
                "current_work_unit": _typed_blocker_work_unit(
                    study_id=study_id,
                    owner="gate_clearing_batch",
                    action_type="run_gate_clearing_batch",
                    work_unit_id="publication_gate_replay",
                    blocker_type="current_owner_route_missing",
                ),
                "paper_recovery_state": canonical_recovery,
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["paper_recovery_states"][study_id] == canonical_recovery
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"] == canonical_recovery
    assert action["supervisor_decision"] == canonical_recovery["supervisor_decision"]
    assert action["decision"] == "blocked"
    assert action["reason"] == "current_owner_route_missing"


def test_runtime_report_preserves_opl_stage_attempt_admission_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "resume_postcondition": {
                    "status": "opl_stage_attempt_admission_required",
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
                "current_work_unit": _typed_blocker_work_unit(
                    study_id=study_id,
                    owner="gate_clearing_batch",
                    action_type="run_gate_clearing_batch",
                    work_unit_id="publication_gate_replay",
                    blocker_type="opl_execution_authorization_required",
                ),
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "domain_blocked"
    assert action["decision"] == "blocked"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["resume_postcondition"] == {
        "status": "opl_stage_attempt_admission_required",
    }


def test_owner_gate_route_back_suppresses_residual_provider_admission_projection() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
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
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
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
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
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
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
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


def test_runtime_scan_fresh_currentness_carries_owner_gate_events(monkeypatch, tmp_path) -> None:
    runtime_scan_support = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan_support"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    study_id = "002-dm-china-us-mortality-attribution"
    event = {
        "surface": "study_intervention_event",
        "intent": "owner_gate_decision",
        "event_id": "intervention-event-000001",
        "payload": {"decision": "route_back_to_mas_packet_materialization_bug"},
    }
    recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
    }

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "generated_at": "2026-06-14T02:30:00+00:00",
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
            },
            "study_intervention_events": [event],
            "paper_recovery_state": recovery,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = runtime_scan_support._with_fresh_progress_currentness(
        profile=object(),
        study_root=tmp_path / study_id,
        status_payload={"study_id": study_id},
    )

    assert result["study_intervention_events"] == [event]
    assert result["paper_recovery_state"] == recovery


def test_same_tick_report_currentness_carries_owner_gate_events(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    study_id = "002-dm-china-us-mortality-attribution"
    event = {
        "surface": "study_intervention_event",
        "intent": "owner_gate_decision",
        "event_id": "intervention-event-000001",
        "payload": {"decision": "route_back_to_mas_packet_materialization_bug"},
    }
    recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_action_ready",
    }

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "generated_at": "2026-06-14T02:30:00+00:00",
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
            },
            "study_intervention_events": [event],
            "paper_recovery_state": recovery,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module._fresh_progress_currentness_for_report(
        profile=object(),
        study_ids=(study_id,),
    )

    assert result[study_id]["study_intervention_events"] == [event]
    assert result[study_id]["paper_recovery_state"] == recovery


def test_same_tick_report_currentness_carries_gate_followthrough(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    followthrough = {
        "surface_kind": "gate_clearing_batch_followthrough",
        "gate_replay_status": "blocked",
        "work_unit_currentness": {
            "current_actionability_status": "actionable",
        },
    }

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "generated_at": "2026-06-14T02:30:00+00:00",
            "study_id": study_id,
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
            },
            "gate_clearing_batch_followthrough": followthrough,
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module._fresh_progress_currentness_for_report(
        profile=object(),
        study_ids=(study_id,),
    )

    assert result[study_id]["gate_clearing_batch_followthrough"] == followthrough
