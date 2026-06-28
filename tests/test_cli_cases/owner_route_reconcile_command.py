from __future__ import annotations

import importlib


def test_owner_route_reconcile_explicit_study_scan_output_stays_scoped() -> None:
    scan_output = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.scan_output"
    )

    studies, action_queue = scan_output.merge_previous_unscanned_study_handoff(
        previous_payload={
            "generated_at": "2026-06-02T00:00:00Z",
            "studies": [{"study_id": "003-dpcc", "handoff_scan_status": "scanned"}],
            "action_queue": [{"study_id": "003-dpcc", "action_id": "stale-003"}],
        },
        scanned_studies=[{"study_id": "002-dm", "handoff_scan_status": "scanned"}],
        scanned_action_queue=[{"study_id": "002-dm", "action_id": "current-002"}],
        retain_unscanned_studies=False,
    )

    assert studies == [{"study_id": "002-dm", "handoff_scan_status": "scanned"}]
    assert action_queue == [{"study_id": "002-dm", "action_id": "current-002"}]


def test_owner_route_reconcile_scoped_scan_does_not_retain_previous_execution_envelopes() -> None:
    scan_output = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.scan_output"
    )

    envelopes = scan_output.merge_current_execution_envelopes(
        previous_payload={
            "current_execution_envelopes": {
                "003-dpcc": {"state_kind": "running_provider_attempt"},
            },
        },
        output_studies=[
            {
                "study_id": "002-dm",
                "current_execution_envelope": {"state_kind": "executable_owner_action"},
            }
        ],
        scanned_studies=[{"study_id": "002-dm"}],
        retain_unscanned_studies=False,
    )

    assert envelopes == {"002-dm": {"state_kind": "executable_owner_action"}}


def test_owner_route_reconcile_persistent_payload_retains_unscanned_provider_admission() -> None:
    scan_output = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.scan_output"
    )

    payload = {
        "surface": "opl_current_control_state_handoff",
        "generated_at": "2026-06-21T00:29:16+00:00",
        "studies": [
            {
                "study_id": "002-dm",
                "handoff_scan_status": "scanned",
                "provider_admission_pending_count": 0,
                "action_queue": [{"study_id": "002-dm", "action_id": "current-002"}],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                },
            }
        ],
        "action_queue": [{"study_id": "002-dm", "action_id": "current-002"}],
        "current_execution_envelopes": {
            "002-dm": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            }
        },
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
    }
    previous_payload = {
        "surface": "opl_current_control_state_handoff",
        "generated_at": "2026-06-21T00:24:00+00:00",
        "studies": [
            {
                "study_id": "003-dpcc",
                "handoff_scan_status": "provider_admission_from_mas_handoff",
                "provider_admission_pending_count": 1,
                "provider_admission_candidates": [
                    {"study_id": "003-dpcc", "action_id": "provider-003"}
                ],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
            }
        ],
        "action_queue": [{"study_id": "003-dpcc", "action_id": "provider-003"}],
        "current_execution_envelopes": {
            "003-dpcc": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            }
        },
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [{"study_id": "003-dpcc", "action_id": "provider-003"}],
    }

    merged = scan_output.merge_persistent_current_control_payload(
        payload=payload,
        previous_payload=previous_payload,
        scanned_study_ids=("002-dm",),
    )

    assert [study["study_id"] for study in merged["studies"]] == ["003-dpcc", "002-dm"]
    assert [action["study_id"] for action in merged["action_queue"]] == ["003-dpcc", "002-dm"]
    assert merged["provider_admission_pending_count"] == 1
    assert merged["provider_admission_candidates"] == [{"study_id": "003-dpcc", "action_id": "provider-003"}]
    assert sorted(merged["current_execution_envelopes"]) == ["002-dm", "003-dpcc"]


def test_owner_route_reconcile_retained_study_keeps_previous_live_running_envelope() -> None:
    scan_output = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.scan_output"
    )

    envelopes = scan_output.merge_current_execution_envelopes(
        previous_payload={
            "current_execution_envelopes": {
                "002-dm": {
                    "state_kind": "running_provider_attempt",
                    "owner": "med-autoscience",
                    "next_work_unit": "ai_reviewer_record_gate_consumption",
                    "source": "opl_provider_attempt",
                },
            },
        },
        output_studies=[
            {
                "study_id": "002-dm",
                "handoff_scan_status": "retained_from_previous_scan",
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "ai_reviewer_record_gate_consumption",
                    "source": "older_retained_study_projection",
                },
            },
            {
                "study_id": "003-dpcc",
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
        ],
        scanned_studies=[{"study_id": "003-dpcc"}],
        retain_unscanned_studies=True,
    )

    assert envelopes["002-dm"]["state_kind"] == "running_provider_attempt"
    assert envelopes["002-dm"]["source"] == "opl_provider_attempt"
    assert envelopes["003-dpcc"]["owner"] == "ai_reviewer"
