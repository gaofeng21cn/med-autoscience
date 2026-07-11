from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.paper_mission_opl_readback import (
    TERMINAL_READBACK_STATUS,
    WAITING_READBACK_STATUS,
    paper_mission_opl_runtime_carrier_readback,
)
from med_autoscience.paper_mission_opl_readback.receipt_events import (
    matches_opl_transition_receipt,
)
from tests.test_paper_mission_opl_readback_cases.shared import (
    _carrier,
    _opl_route_carrier,
    _opl_runtime_task_payload,
    _opl_transition_receipt,
    _write_closeout,
)


def test_opl_terminal_closeout_readback_observes_record_only_terminal_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_closeout(study_root, {})

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=_carrier(),
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["domain_ready_verdict"] == "domain_gate_pending"
    assert readback["provider_completion_is_domain_completion"] is False
    assert readback["provider_completion_is_domain_ready"] is False
    assert readback["can_claim_paper_progress"] is False
    assert readback["terminal_closeout"]["domain_ready_claimed"] is False


def test_opl_terminal_closeout_readback_ignores_domain_completion_claims_without_opl_readback(
    tmp_path: Path,
) -> None:
    for claim in ("domain_ready_claimed", "domain_completion_claimed"):
        study_root = tmp_path / claim
        _write_closeout(study_root, {claim: True})

        readback = paper_mission_opl_runtime_carrier_readback(
            carrier=_carrier(),
            study_root=study_root,
        )

        assert readback["carrier_status"] == WAITING_READBACK_STATUS
        assert readback["runtime_readback_status"] == "missing"
        assert readback["domain_ready_verdict"] == "opl_runtime_readback_missing"


def test_opl_terminal_closeout_readback_requires_record_only_boundary(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
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
        carrier=_carrier(),
        study_root=study_root,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"


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


def test_opl_terminal_closeout_readback_ignores_legacy_only_route_back_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    carrier = {
        **_opl_route_carrier(),
        "idempotency_key": "dm003::candidate-v2",
        "request_idempotency_key": "dm003::candidate-v2::request",
        "attempt_idempotency_key": "dm003::candidate-v2::attempt",
    }
    _write_closeout(
        study_root,
        {
            "status": "non_advancing_route_back_evidence_candidate",
            "stage_id": "publication_gate_replay",
            "stage_attempt_id": "sat-route-back",
            "stage_packet_ref": carrier["paper_mission_transaction_ref"],
            "route_impact": {
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-route-back/study/route_back_evidence_packet.json"
                ),
                "can_claim_paper_progress": False,
            },
            "closeout_refs": [
                {
                    "ref_kind": "route_back_evidence_packet",
                    "workspace_relative_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-route-back/study/route_back_evidence_packet.json"
                    ),
                }
            ],
            "authority_boundary": {
                "candidate_is_authority": False,
                "writes_authority_surface": False,
                "writes_owner_receipt": False,
                "writes_typed_blocker": False,
                "writes_human_gate": False,
                "writes_provider_attempt": False,
            },
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback
    assert "opl_transition_receipt" not in readback
    assert "receipt_evidence" not in readback
    assert "mas_receipt_consumption" not in readback


def test_opl_terminal_closeout_readback_consumes_matching_opl_runtime_task(
    tmp_path: Path,
) -> None:
    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=_opl_runtime_task_payload(),
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["provider_completion_is_domain_completion"] is False
    assert readback["can_claim_paper_progress"] is False
    assert readback["terminal_closeout"]["closeout_receipt_status"] == (
        "accepted_typed_closeout"
    )
    assert readback["opl_transition_receipt"]["receipt_status"] == (
        "terminal_closeout_observed"
    )
    assert readback["opl_transition_receipt"]["surface_kind"] == (
        "opl_domain_route_transition_receipt"
    )


def test_opl_terminal_closeout_readback_requires_transition_receipt(
    tmp_path: Path,
) -> None:
    payload = _opl_runtime_task_payload()
    payload["family_runtime_task"]["events"] = []

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"
    assert "terminal_closeout" not in readback
    assert "opl_transition_receipt" not in readback


def test_opl_terminal_closeout_readback_rejects_old_receipt_kind(
    tmp_path: Path,
) -> None:
    payload = _opl_runtime_task_payload()
    receipt = payload["family_runtime_task"]["events"][0]["payload"][
        "opl_transition_receipt"
    ]
    receipt["surface_kind"] = "opl_transition_receipt"

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=payload,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == WAITING_READBACK_STATUS
    assert readback["runtime_readback_status"] == "missing"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda receipt: receipt.__setitem__("surface_kind", "opl_transition_receipt"),
        lambda receipt: receipt.pop("domain_id"),
        lambda receipt: receipt.__setitem__(
            "domain_route_transaction_ref",
            "paper-mission-transaction::other",
        ),
        lambda receipt: receipt["authority_boundary"].__setitem__(
            "can_select_next_owner",
            True,
        ),
    ],
)
def test_shared_transition_receipt_matcher_rejects_noncanonical_receipts(mutate) -> None:
    carrier = _opl_route_carrier()
    receipt = _opl_transition_receipt()
    mutate(receipt)

    assert not matches_opl_transition_receipt(receipt=receipt, carrier=carrier)


def test_shared_transition_receipt_matcher_accepts_raw_receipt_without_study_id() -> None:
    receipt = _opl_transition_receipt()

    assert "study_id" not in receipt
    assert matches_opl_transition_receipt(
        receipt=receipt,
        carrier=_opl_route_carrier(),
    )


def test_local_closeout_does_not_wrap_incomplete_canonical_receipt(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    receipt = _opl_transition_receipt()
    receipt.pop("domain_id")
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "domain_route_handoff_ref": carrier["domain_route_handoff_ref"],
            "domain_route_transaction_ref": carrier["domain_route_transaction_ref"],
            "domain_route_command_ref": carrier["domain_route_command_ref"],
            "opl_transition_receipt": receipt,
        },
    )

    readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=False,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert "opl_transition_receipt" not in readback
    assert "receipt_evidence" not in readback
    assert "mas_receipt_consumption" not in readback
