from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_paper_recovery_state_cases.shared import _typed_blocker_work_unit


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
    assert recovery["phase"] == "human_gate"
    assert recovery["conditions"][0]["condition"] == "accepted_owner_gate_decision"
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "human_gate"
    assert action["decision"] == "human_gate"
    assert action["reason"] == "accepted_owner_gate_decision"
    assert action["running_provider_attempt"] is False


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

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "generated_at": "2026-06-14T02:30:00+00:00",
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
            },
            "study_intervention_events": [event],
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = runtime_scan_support._with_fresh_progress_currentness(
        profile=object(),
        study_root=tmp_path / study_id,
        status_payload={"study_id": study_id},
    )

    assert result["study_intervention_events"] == [event]


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

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "generated_at": "2026-06-14T02:30:00+00:00",
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
            },
            "study_intervention_events": [event],
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module._fresh_progress_currentness_for_report(
        profile=object(),
        study_ids=(study_id,),
    )

    assert result[study_id]["study_intervention_events"] == [event]
