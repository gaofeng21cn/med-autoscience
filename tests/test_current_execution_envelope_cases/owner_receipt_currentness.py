from __future__ import annotations

import importlib


def test_envelope_projects_owner_receipt_recorded_as_terminal_owner_outcome() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        current_work_unit_payload={
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "state": {
                "state_kind": "owner_receipt_recorded",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
            },
        },
        progress={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "explicit_resume_pending",
                "parked_owner": "user",
                "awaiting_explicit_wakeup": True,
            },
        },
    )

    assert envelope["state_kind"] == "owner_receipt_recorded"
    assert envelope["owner"] == "write"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None


def test_envelope_projects_owner_receipt_recorded_from_paper_recovery_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"

    envelope = module.build_current_execution_envelope(
        progress={
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_receipt_recorded",
                "evidence_refs": [receipt_ref],
                "current_authority": {
                    "obligation": {
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
                    "owner_receipt_ref": receipt_ref,
                },
            }
        }
    )

    assert envelope["state_kind"] == "owner_receipt_recorded"
    assert envelope["owner"] == "write"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None
