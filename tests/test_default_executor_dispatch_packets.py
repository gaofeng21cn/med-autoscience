from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import default_executor_dispatch_packets


def test_immutable_default_executor_packet_is_abi_provenance_only(tmp_path: Path) -> None:
    dispatch_path = tmp_path / "default_executor_dispatches" / "run_quality_repair_batch.json"
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "action_type": "run_quality_repair_batch",
        "dispatch_authority": "consumer_default_executor_dispatch",
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

    packet = default_executor_dispatch_packets.dispatch_with_immutable_packet_ref(
        dispatch=dispatch,
        dispatch_path=dispatch_path,
    )

    assert packet["refs"]["dispatch_path"] == str(dispatch_path)
    assert packet["refs"]["stage_packet_path"] == packet["refs"]["immutable_dispatch_path"]
    assert packet["active_caller_class"] == "abi_provenance_carrier_only"
    assert packet["diagnostic_role"] == "retired_default_paper_dispatch"
    assert packet["replacement_task_kind"] == "paper_mission/start_or_resume"
    assert packet["default_paper_mission_entry"] is False
    assert packet["ordinary_schedulable"] is False
    assert packet["migration_diagnostic_only"] is True
    assert packet["can_select_next_paper_stage"] is False
    assert packet["can_authorize_provider_admission"] is False
    assert packet["counts_as_paper_progress"] is False
    assert packet["can_claim_runtime_ready"] is False
    assert packet["can_claim_publication_ready"] is False
    assert packet["legacy_default_executor_dispatch_packet_boundary"] == {
        **default_executor_dispatch_packets.LEGACY_DISPATCH_PACKET_BOUNDARY
    }
