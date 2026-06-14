from __future__ import annotations

import importlib


def test_progress_projection_recomputes_actions_after_consumed_closeout_typed_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )

    handoff = {
        "typed_blocker": {
            "blocker_type": "opl_execution_authorization_required",
            "blocked_reason": "opl_execution_authorization_required",
            "owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:2c4793",
            "action_fingerprint": "sha256:2c4793",
            "source_ref": "artifacts/supervision/consumer/default_executor_execution/sat_e106.closeout.json",
            "typed_blocker_ref": (
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
                "consumer/default_executor_execution/sat_e106.closeout.json#domain_blocker"
            ),
            "stage_attempt_id": "sat_e106",
            "terminal_closeout_status": "blocked",
            "terminal_closeout_outcome": "typed_blocker",
            "progress_delta_classification": "typed_blocker",
        },
        "blocked_reason": "opl_execution_authorization_required",
        "next_owner": "gate_clearing_batch",
        "running_provider_attempt": False,
    }
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "next_owner": "gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "sha256:2c4793",
        "action_fingerprint": "sha256:2c4793",
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
    }
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_executable_owner_action": action,
        "progress_first_sprint_state": {"paper_progress_delta_counted": True},
    }

    payload = module._refresh_current_execution_surfaces(  # noqa: SLF001
        payload=payload,
        status={},
        handoff=handoff,
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006800",
        },
    )

    assert payload["current_work_unit"]["status"] == "typed_blocker"
    assert payload["current_work_unit"]["state"]["source"] == "typed_blocker"
    assert payload["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert payload["current_executable_owner_action"] is None
    assert payload["current_execution_evidence"]["action_queue"] == []
    assert payload["current_execution_evidence"]["opl_current_control_state_handoff"]["typed_blocker"] == (
        handoff["typed_blocker"]
    )
