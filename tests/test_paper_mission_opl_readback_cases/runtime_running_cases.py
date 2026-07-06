from __future__ import annotations

from pathlib import Path

from med_autoscience.paper_mission_opl_readback import (
    RUNNING_READBACK_STATUS,
    TERMINAL_READBACK_STATUS,
    WAITING_READBACK_STATUS,
    paper_mission_opl_runtime_carrier_readback,
)
from tests.test_paper_mission_opl_readback_cases.shared import (
    _opl_route_carrier,
    _opl_running_task_completed_attempt_payload,
    _opl_running_task_running_attempt_payload,
    _opl_runtime_task_payload,
    _opl_transition_receipt,
    _write_closeout,
)


def test_opl_terminal_closeout_readback_rejects_unsafe_transition_receipt(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    receipt = payload["family_runtime_task"]["events"][0]["payload"][
        "opl_transition_receipt"
    ]
    receipt["authority_boundary"]["writes_owner_receipt"] = True

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback
    assert "opl_transition_receipt" not in readback


def test_opl_terminal_closeout_readback_rejects_cross_transaction_opl_runtime_task(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "paper_mission_transaction_ref": "paper-mission-transaction::other",
    }

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_runtime_task_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_consumes_completed_stage_attempt_when_task_still_running(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_completed_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["dispatch_status"] == "terminal_closeout_observed"
    assert readback["can_claim_provider_running"] is False
    terminal = readback["terminal_closeout"]
    assert terminal["task_id"] == "frt-stage-route"
    assert terminal["task_status"] == "running"
    assert terminal["status"] == "completed"
    assert terminal["stage_attempt_id"] == "sat-completed"
    assert terminal["closeout_receipt_status"] == "accepted_typed_closeout"
    assert terminal["closeout_refs"] == [
        "paper-mission-transaction::dm002#opl_route_command",
        "opl://stage-attempts/sat-completed/runtime-blockers/no_typed_domain_handler_closeout_observed",
    ]
    assert terminal["provider_completion_is_domain_ready"] is False


def test_opl_terminal_closeout_readback_accepts_stage_terminal_ref_binding(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    payload = _opl_runtime_task_payload()
    runtime_task = payload["family_runtime_task"]
    task = runtime_task["task"]
    task["current_control_state"] = {}
    runtime_task["stage_attempts"] = [
        {
            "stage_attempt_id": "sat-stage-ref",
            "status": "completed",
            "stage_id": "publication_gate_replay",
            "workspace_locator": {
                "study_id": "002-dm-china-us-mortality-attribution",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm002",
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002#opl_route_command"
                ),
                "command_kind": "start_next_stage",
                "route_target": "publication_gate_replay",
            },
            "closeout_refs": [
                "paper-mission-transaction::dm002",
                "paper-mission-transaction::dm002#stage_terminal_decision",
            ],
            "opl_transition_receipt": _opl_transition_receipt(
                stage_attempt_id="sat-stage-ref",
            ),
            "closeout_receipt_status": "accepted_typed_closeout",
            "provider_run": {
                "provider_status": "completed",
                "workflow_id": "wf-stage-ref",
            },
        },
    ]
    runtime_task["events"] = []

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-stage-ref"
    assert readback["terminal_closeout"]["closeout_refs"] == [
        "paper-mission-transaction::dm002",
        "paper-mission-transaction::dm002#stage_terminal_decision",
    ]


def test_opl_runtime_readback_reports_same_identity_running_attempt(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert readback["dispatch_status"] == "provider_attempt_running"
    assert readback["domain_ready_verdict"] == "opl_runtime_attempt_running"
    assert readback["can_claim_provider_running"] is True
    assert readback["can_claim_paper_progress"] is False
    running = readback["running_attempt"]
    assert running["stage_attempt_id"] == "sat-running"
    assert running["provider_status"] == "running"
    assert running["workflow_id"] == "wf-running"
    assert running["provider_completion_is_domain_ready"] is False


def test_opl_runtime_readback_consumes_running_attempt_closeout_without_work_unit(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "status": "route_back_evidence_candidate",
            "stage_id": "publication_gate_replay",
            "stage_attempt_id": "sat-running",
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "work_unit_id": None,
            "work_unit_fingerprint": None,
            "blocked_reason": None,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-running"
    assert "running_attempt" not in readback
    assert readback["can_claim_paper_progress"] is False


def test_opl_runtime_readback_prefers_live_running_attempt_over_local_terminal_residue(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    _write_closeout(
        study_root,
        {
            "study_id": carrier["study_id"],
            "stage_id": "publication_gate_replay",
            "work_unit_id": carrier["work_unit_id"],
            "work_unit_fingerprint": carrier["work_unit_fingerprint"],
            "stage_packet_ref": carrier["stage_terminal_decision_ref"],
            "closeout_refs": [carrier["opl_route_command_ref"]],
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        opl_runtime_payload=_opl_running_task_running_attempt_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "running_attempt_observed"
    assert "terminal_closeout" not in readback
    assert readback["running_attempt"]["stage_attempt_id"] == "sat-running"
    assert readback["can_claim_paper_progress"] is False
