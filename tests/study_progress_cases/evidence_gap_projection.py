from __future__ import annotations

from med_autoscience.controllers.evidence_gap_projection import attach_evidence_gap_projection


def test_evidence_gap_projection_hard_and_soft_accounting_do_not_collapse_to_generic_blocker() -> None:
    payload = attach_evidence_gap_projection(
        {
            "study_id": "DM003",
            "quest_id": "quest-dm003",
            "current_executable_owner_action": {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-1",
            },
            "evidence_gap_inputs": [
                {
                    "surface_kind": "opl_stage_run_currentness",
                    "missing_ref_family": "StageRun currentness provider authorization",
                },
                {
                    "surface_kind": "reviewer_polish",
                    "missing_ref_family": "reviewer structure non-hard concern",
                },
                {
                    "surface_kind": "telemetry_report",
                    "missing_ref_family": "telemetry token cost trace report freshness",
                },
                {
                    "surface_kind": "source_reference_note",
                    "missing_ref_family": "safe non-critical bibliography helper ref",
                },
            ],
        }
    )

    assert payload["evidence_gap_decision_summary"]["hard_gate_count"] == 1
    assert payload["evidence_gap_decision_summary"]["soft_gap_count"] == 1
    assert payload["evidence_gap_decision_summary"]["observability_backlog_count"] == 1
    assert payload["evidence_gap_decision_summary"]["assumption_count"] == 1
    assert payload["evidence_gap_typed_blocker_count"] == 1
    assert payload["current_action_can_continue"] is False
    assert payload["soft_gap_ledger"][0]["gap_class"] == "soft_quality_gap"
    assert payload["observability_backlog"][0]["gap_class"] == "observability_backlog"
    assert payload["assumption_ledger"][0]["gap_class"] == "proceed_with_assumption"
    assert "paper_progress" in payload["forbidden_claims"]


def test_evidence_gap_projection_does_not_infer_from_runtime_pending_counts() -> None:
    payload = {
        "study_id": "DM003",
        "quest_id": "quest-dm003",
        "provider_admission_pending_count": 1,
        "transition_request_pending_count": 1,
        "provider_admission_candidates": [
            {
                "stage_packet_ref": "runtime/stage-packets/provider-admission.json",
                "evidence_refs": ["runtime/outbox/provider-admission.json"],
            }
        ],
        "transition_request_candidates": [
            {
                "stage_packet_ref": "runtime/stage-packets/transition-request.json",
                "diagnostic_refs": ["runtime/diagnostics/transition-request.json"],
            }
        ],
    }

    projected = attach_evidence_gap_projection(payload)

    assert projected == payload
