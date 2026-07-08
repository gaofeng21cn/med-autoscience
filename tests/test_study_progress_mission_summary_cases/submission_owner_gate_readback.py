from __future__ import annotations

import importlib


SUBMISSION_AUTHORITY_ACTION = "await_human_or_mas_authority_decision_for_submission_blocker"


def test_submission_authority_owner_gate_removes_superseded_next_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly"
    )

    payload = _submission_authority_payload()

    updated = module._attach_submission_authority_owner_gate_readback(payload)

    assert "next_action" not in updated
    assert "canonical_next_action_source" not in updated
    assert "next_action" not in updated["paper_mission_transaction_readback"]
    assert updated["current_executable_owner_action"] is None
    assert updated["submission_authority_owner_gate_readback"]["status"] == (
        "owner_gate_recorded"
    )


def test_submission_authority_owner_gate_keeps_new_next_action_for_different_identity() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly"
    )

    payload = _submission_authority_payload(
        event_work_unit_id="old_submission_blocker_work_unit",
    )

    updated = module._attach_submission_authority_owner_gate_readback(payload)

    assert updated["next_action"]["work_unit_id"] == (
        "submission_blocker_degraded_handoff_or_quality_repair"
    )
    assert updated["canonical_next_action_source"] == "precomputed_canonical_next_action"
    assert "submission_authority_owner_gate_readback" not in updated


def _submission_authority_payload(
    *,
    event_work_unit_id: str = "submission_blocker_degraded_handoff_or_quality_repair",
) -> dict[str, object]:
    return {
        "study_id": "obesity_multicenter_phenotype_atlas",
        "canonical_next_action_source": "precomputed_canonical_next_action",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "paper.package.submission_minimal",
            "action_type": SUBMISSION_AUTHORITY_ACTION,
            "allowed_actions": [SUBMISSION_AUTHORITY_ACTION],
            "study_id": "obesity_multicenter_phenotype_atlas",
            "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
            "work_unit_fingerprint": "7ca5e4d5e993dd9304f45400",
        },
        "current_executable_owner_action": {
            "action_type": SUBMISSION_AUTHORITY_ACTION
        },
        "paper_mission_transaction_readback": {
            "next_action": {
                "action_type": SUBMISSION_AUTHORITY_ACTION
            },
            "stage_closure_decision": {"status": "typed_blocker"},
        },
        "study_intervention_events": [
            {
                "event_id": "intervention-event-000005-6184dcc4d3988930",
                "intent": "owner_gate_decision",
                "recorded_at": "2026-07-01T15:03:32+00:00",
                "source": "codex",
                "payload": {
                    "owner_gate_kind": "submission_authority_gate",
                    "decision": "request_submission_blocker_human_gate",
                    "current_required_action": SUBMISSION_AUTHORITY_ACTION,
                    "human_gate_ref": (
                        "human_gate:owner-gate-decision:5e98e1fda062290f848cd795"
                    ),
                    "owner_gate_decision_ref": (
                        "owner-gate-decision:5e98e1fda062290f848cd795"
                    ),
                    "current_owner_identity": {
                        "study_id": "obesity_multicenter_phenotype_atlas",
                        "action_type": SUBMISSION_AUTHORITY_ACTION,
                        "work_unit_id": event_work_unit_id,
                        "work_unit_fingerprint": "7ca5e4d5e993dd9304f45400",
                    },
                    "submission_authority_closeout": {
                        "status": "owner_gate_recorded",
                        "authority_materialized": False,
                    },
                },
            }
        ],
    }
