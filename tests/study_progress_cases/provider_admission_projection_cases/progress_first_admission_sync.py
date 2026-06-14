from __future__ import annotations

import importlib


def test_sync_progress_first_owner_action_admission_suppresses_stale_identity() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.payload_sync"
    )

    result = module.sync_progress_first_owner_action_admission(
        {
            "current_work_unit": {
                "status": "running_provider_attempt",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:current-gate-replay",
                "action_fingerprint": "sha256:current-gate-replay",
            },
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "progress_first_monitoring_summary": {
                "owner_action_admission": {
                    "admission_requested": True,
                    "admission_pending": True,
                    "provider_attempt_start_requested": True,
                    "provider_attempt_running_proven": False,
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "allowed_actions": ["run_quality_repair_batch"],
                }
            },
        }
    )

    admission = result["owner_action_admission"]
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["blocked_by"] == "current_execution_identity_mismatch"
    assert admission["stale_admission_suppressed"] is True
    monitoring = result["progress_first_monitoring_summary"]["owner_action_admission"]
    assert monitoring == admission
