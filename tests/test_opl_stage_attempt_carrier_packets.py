from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import opl_stage_attempt_carrier_packets


def test_immutable_opl_stage_attempt_packet_is_abi_provenance_only(tmp_path: Path) -> None:
    dispatch_path = tmp_path / "owner_callable_adapters" / "run_quality_repair_batch.json"
    dispatch = {
        "surface": "owner_callable_dispatch_request",
        "action_type": "run_quality_repair_batch",
        "dispatch_authority": "consumer_owner_callable_dispatch",
        "active_caller_class": "ordinary_task",
        "default_paper_mission_entry": True,
        "ordinary_schedulable": True,
        "can_select_next_paper_stage": True,
        "can_authorize_provider_admission": True,
        "counts_as_paper_progress": True,
        "can_claim_runtime_ready": True,
        "can_claim_publication_ready": True,
        "owner_route": {
            "idempotency_key": "idem-1",
            "source_refs": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-1",
            },
        },
    }

    packet = opl_stage_attempt_carrier_packets.dispatch_with_immutable_packet_ref(
        dispatch=dispatch,
        dispatch_path=dispatch_path,
    )

    assert packet["refs"]["dispatch_path"] == str(dispatch_path)
    assert packet["refs"]["stage_packet_path"] == packet["refs"]["immutable_dispatch_path"]
    assert packet["active_caller_class"] == "abi_provenance_carrier_only"
    assert packet["allowed_reference_class"] == "retired_handoff_provenance"
    assert packet["diagnostic_role"] == "retired_default_paper_dispatch"
    assert packet["replacement_task_kind"] == "domain_route/start-or-resume"
    assert packet["default_paper_mission_entry"] is False
    assert packet["ordinary_schedulable"] is False
    assert packet["migration_diagnostic_only"] is True
    assert packet["can_select_next_paper_stage"] is False
    assert packet["can_authorize_provider_admission"] is False
    assert packet["counts_as_paper_progress"] is False
    assert packet["can_claim_runtime_ready"] is False
    assert packet["can_claim_publication_ready"] is False
    assert set(packet["forbidden_claims"]) >= {
        "paper_progress",
        "runtime_ready",
        "provider_running",
        "owner_receipt_written",
        "typed_blocker_written",
        "human_gate_written",
        "current_package",
    }
    assert packet["opl_stage_attempt_carrier_boundary"] == {
        **opl_stage_attempt_carrier_packets.OPL_STAGE_ATTEMPT_CARRIER_BOUNDARY
    }
    assert "legacy_owner_callable_dispatch_packet_boundary" not in packet
