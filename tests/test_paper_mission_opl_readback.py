from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.paper_mission_opl_readback import (
    TERMINAL_READBACK_STATUS,
    WAITING_READBACK_STATUS,
    paper_mission_opl_runtime_carrier_readback,
)


def test_opl_terminal_closeout_readback_observes_record_only_terminal_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(study_root, {})

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["domain_ready_verdict"] == "domain_gate_pending"
    assert readback["provider_completion_is_domain_completion"] is False
    assert readback["provider_completion_is_domain_ready"] is False
    assert readback["can_claim_paper_progress"] is False
    assert readback["terminal_closeout"]["domain_ready_claimed"] is False


def test_opl_terminal_closeout_readback_ignores_domain_ready_claims(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "domain_ready_claimed": True,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert readback["domain_ready_verdict"] == "opl_runtime_readback_missing"


def test_opl_terminal_closeout_readback_ignores_domain_completion_claims(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "domain_completion_claimed": True,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert readback["domain_ready_verdict"] == "opl_runtime_readback_missing"


def test_opl_terminal_closeout_readback_requires_record_only_boundary(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = _carrier()
    _write_closeout(
        study_root,
        {
            "authority_boundary": {
                "record_only_surface": False,
                "provider_completion_is_domain_completion": False,
            },
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"


def test_opl_terminal_closeout_readback_ignores_prior_default_executor_closeout_for_next_stage(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_carrier(),
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "domain_owner/default-executor-dispatch",
            "blocked_reason": "opl_runtime_lifecycle_readback_required",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback


def test_opl_terminal_closeout_readback_accepts_current_route_target_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_carrier(),
        "command_kind": "start_next_stage",
        "route_target": "publication_gate_replay",
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
        },
    }
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "blocked_reason": "domain_gate_pending",
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_id"] == "publication_gate_replay"


def _carrier() -> dict[str, str]:
    return {
        "study_id": "002-dm-china-us-mortality-attribution",
        "work_unit_id": "gate_clearing_claim_evidence_repair",
        "work_unit_fingerprint": (
            "paper-mission::002-dm-china-us-mortality-attribution::"
            "gate-clearing::gate_clearing_claim_evidence_repair::advance::accepted"
        ),
        "dispatch_status": "transition_request_pending",
    }


def _write_closeout(study_root: Path, override: dict[str, object]) -> None:
    closeout_root = (
        study_root / "artifacts" / "supervision" / "consumer" / "stage_attempt_closeouts"
    )
    closeout_root.mkdir(parents=True)
    payload = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "blocked",
        "study_id": "002-dm-china-us-mortality-attribution",
        "stage_id": "gate_clearing_claim_evidence_repair",
        "stage_attempt_id": "sat-terminal",
        "work_unit_id": "gate_clearing_claim_evidence_repair",
        "work_unit_fingerprint": (
            "paper-mission::002-dm-china-us-mortality-attribution::"
            "gate-clearing::gate_clearing_claim_evidence_repair::advance::accepted"
        ),
        "stage_packet_ref": "opl-stage-run://paper-mission-summary/dm002",
        "provider_attempt_ref": "temporal://attempt/sat-terminal",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "blocked_reason": "domain_gate_pending",
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }
    payload.update(override)
    (closeout_root / "sat-terminal.closeout.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
