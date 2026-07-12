from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.paper_mission_stage_run_readback import (
    RUNNING_READBACK_STATUS,
    TERMINAL_READBACK_STATUS,
    WAITING_READBACK_STATUS,
    paper_mission_stage_run_context_readback,
)
from med_autoscience.paper_mission_stage_run_readback.receipt_events import (
    matches_opl_stage_attempt_receipt,
)
from med_autoscience.paper_mission_stage_run_readback.opl_task_readback import (
    matching_opl_runtime_payload_closeout,
)
from tests.test_paper_mission_stage_run_readback_cases.shared import (
    _carrier,
    _opl_route_carrier,
    _opl_running_query_payload,
    _opl_runtime_query_payload,
    _opl_stage_attempt,
    _opl_stage_attempt_receipt,
    _write_closeout,
)


def test_opl_terminal_closeout_without_canonical_route_identity_is_unresolved(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_closeout(study_root, {})

    readback = paper_mission_stage_run_context_readback(
        carrier=_carrier(),
        study_root=study_root,
    )

    assert readback["carrier_status"] == "context_available"
    assert readback["runtime_readback_status"] == "optional_transport_readback_missing"
    assert readback["writes_runtime"] is False
    assert readback["next_stage_may_start"] is True
    assert readback["route_selection_owner"] == "codex_cli"
    assert readback["can_claim_provider_running"] is False


def test_opl_terminal_closeout_readback_requires_record_only_boundary(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_closeout(
        study_root,
        {"authority_boundary": {"record_only_surface": False}},
    )

    readback = paper_mission_stage_run_context_readback(
        carrier=_carrier(),
        study_root=study_root,
    )

    assert readback["carrier_status"] == "context_available"
    assert readback["runtime_readback_status"] == "optional_transport_readback_missing"
    assert readback["next_stage_may_start"] is True


def test_opl_terminal_closeout_readback_consumes_scoped_stage_attempt_query(
    tmp_path: Path,
) -> None:
    readback = paper_mission_stage_run_context_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=_opl_runtime_query_payload(),
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-terminal"
    assert readback["terminal_closeout"]["runtime_readback_source"] == (
        "opl_family_runtime_stage_attempt_query"
    )
    assert readback["opl_stage_attempt_receipt"]["surface_kind"] == (
        "opl_stage_attempt_transport_receipt"
    )


def test_opl_stage_attempt_readback_requires_typed_closeout_not_transport_terminal_status() -> None:
    payload = _opl_runtime_query_payload()
    query = payload["family_runtime_stage_attempt_query"]["stage_attempt_query"]
    attempt = query["attempt"]
    packet = query["closeouts"][0]["packet"]
    attempt["status"] = "transport_observed"
    attempt["provider_run"]["provider_status"] = "transport_observed"
    packet["status"] = "transport_observed"

    closeout = matching_opl_runtime_payload_closeout(
        carrier=_opl_route_carrier(),
        payload=payload,
    )

    assert closeout is not None
    assert closeout[0]["closeout_receipt_status"] == "accepted_typed_closeout"

    attempt["status"] = "dead_lettered"
    attempt["provider_run"]["provider_status"] = "dead_lettered"
    packet["status"] = "dead_lettered"
    attempt.pop("closeout_receipt_status")
    attempt.pop("closeout_refs")
    packet.pop("closeout_receipt_status")
    packet.pop("closeout_refs")
    packet.pop("typed_blocker_ref")

    assert matching_opl_runtime_payload_closeout(
        carrier=_opl_route_carrier(),
        payload=payload,
    ) is None


def test_opl_terminal_closeout_readback_rejects_query_without_stage_attempt_receipt(
    tmp_path: Path,
) -> None:
    readback = paper_mission_stage_run_context_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=_opl_runtime_query_payload(include_stage_attempt_receipt=False),
    )

    assert readback["carrier_status"] == "context_available"
    assert readback["runtime_readback_status"] == "optional_transport_readback_missing"
    assert readback["next_stage_may_start"] is True


def test_opl_terminal_closeout_readback_rejects_mismatched_query_attempt_receipt(
    tmp_path: Path,
) -> None:
    payload = _opl_runtime_query_payload()
    packet = payload["family_runtime_stage_attempt_query"]["stage_attempt_query"][
        "closeouts"
    ][0]["packet"]
    packet["opl_stage_attempt_receipt"]["stage_attempt_id"] = "sat-other"

    readback = paper_mission_stage_run_context_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=payload,
    )

    assert readback["carrier_status"] == "context_available"
    assert readback["runtime_readback_status"] == "optional_transport_readback_missing"
    assert readback["next_stage_may_start"] is True


def test_opl_terminal_closeout_readback_rejects_retired_queue_payload(tmp_path: Path) -> None:
    readback = paper_mission_stage_run_context_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload={"family_runtime_task": {"task": {}}},
    )

    assert readback["carrier_status"] == "context_available"
    assert readback["runtime_readback_status"] == "optional_transport_readback_missing"
    assert readback["next_stage_may_start"] is True


def test_opl_hosted_payload_provides_scoped_terminal_attempt_readback(tmp_path: Path) -> None:
    readback = paper_mission_stage_run_context_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=_opl_runtime_query_payload(),
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert readback["terminal_closeout"]["stage_attempt_id"] == "sat-terminal"


def test_opl_hosted_payload_preserves_running_stage_attempt_precedence(tmp_path: Path) -> None:
    readback = paper_mission_stage_run_context_readback(
        carrier=_opl_route_carrier(),
        study_root=tmp_path / "study",
        opl_runtime_payload=_opl_running_query_payload(),
    )

    assert readback["carrier_status"] == RUNNING_READBACK_STATUS
    assert readback["running_attempt"]["stage_attempt_id"] == "sat-running"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda receipt: receipt.__setitem__("surface_kind", "opl_stage_attempt_receipt"),
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
def test_shared_stage_attempt_receipt_matcher_rejects_noncanonical_receipts(mutate) -> None:
    receipt = _opl_stage_attempt_receipt()
    mutate(receipt)

    assert not matches_opl_stage_attempt_receipt(receipt=receipt, carrier=_opl_route_carrier())


def test_shared_stage_attempt_receipt_matcher_accepts_raw_receipt_without_study_id() -> None:
    receipt = _opl_stage_attempt_receipt()

    assert "study_id" not in receipt
    assert matches_opl_stage_attempt_receipt(receipt=receipt, carrier=_opl_route_carrier())


def test_local_closeout_does_not_wrap_incomplete_canonical_receipt(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    carrier = _opl_route_carrier()
    receipt = _opl_stage_attempt_receipt()
    receipt.pop("domain_id")
    _write_closeout(
        study_root,
        {
            "stage_id": "publication_gate_replay",
            "domain_route_handoff_ref": carrier["domain_route_handoff_ref"],
            "domain_route_transaction_ref": carrier["domain_route_transaction_ref"],
            "domain_route_command_ref": carrier["domain_route_command_ref"],
            "opl_stage_attempt_receipt": receipt,
        },
    )

    readback = paper_mission_stage_run_context_readback(
        carrier=carrier,
        study_root=study_root,
    )

    assert readback["carrier_status"] == TERMINAL_READBACK_STATUS
    assert "opl_stage_attempt_receipt" not in readback
    assert "receipt_evidence" not in readback
