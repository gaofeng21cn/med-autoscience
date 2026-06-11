from __future__ import annotations

from med_autoscience.controllers.stage_route_currentness_identity import (
    currentness_identities_match,
    currentness_identity,
)


def test_currentness_identity_extracts_owner_route_basis_and_handoff_refs() -> None:
    identity = currentness_identity(
        {
            "action_type": "run_gate_clearing_batch",
            "handoff_packet": {
                "next_work_unit": {"unit_id": "gate-replay"},
                "owner_route": {
                    "work_unit_fingerprint": "route-fp",
                    "source_refs": {
                        "owner_route_currentness_basis": {
                            "work_unit_id": "basis-work-unit",
                            "work_unit_fingerprint": "basis-fp",
                        }
                    },
                },
            },
        }
    )

    assert identity.action_type == "run_gate_clearing_batch"
    assert identity.work_unit_id == "basis-work-unit"
    assert identity.fingerprints == frozenset({"route-fp", "basis-fp"})


def test_currentness_identity_reads_currentness_contract_basis_without_owner_reason_fallback() -> None:
    identity = currentness_identity(
        {
            "action_type": "run_gate_clearing_batch",
            "owner_route": {
                "owner_reason": "stale_stage_packet_current_owner_route_changed",
                "currentness_contract": {
                    "basis": {
                        "work_unit_id": "gate-replay",
                        "work_unit_fingerprint": "gate-replay-fp",
                    },
                },
            },
        }
    )

    assert identity.work_unit_id == "gate-replay"
    assert identity.fingerprints == frozenset({"gate-replay-fp"})


def test_currentness_identity_does_not_treat_owner_reason_as_work_unit() -> None:
    identity = currentness_identity(
        {
            "action_type": "run_gate_clearing_batch",
            "owner_route": {
                "owner_reason": "stale_stage_packet_current_owner_route_changed",
            },
        }
    )

    assert identity.work_unit_id is None
    assert identity.fingerprints == frozenset()


def test_currentness_match_requires_shared_strong_identity() -> None:
    left = {
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "gate-replay",
        "work_unit_fingerprint": "fresh-fp",
    }
    right = {
        "action_type": "run_gate_clearing_batch",
        "owner_route": {
            "source_refs": {
                "owner_route_currentness_basis": {
                    "work_unit_id": "gate-replay",
                    "work_unit_fingerprint": "fresh-fp",
                }
            }
        },
    }

    assert currentness_identities_match(left, right)


def test_currentness_match_rejects_different_fingerprints_even_when_action_matches() -> None:
    left = {
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "gate-replay",
        "work_unit_fingerprint": "fresh-fp",
    }
    stale = {
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "gate-replay",
        "work_unit_fingerprint": "stale-fp",
    }

    assert not currentness_identities_match(left, stale)


def test_currentness_match_can_require_fingerprint_for_repair_followup() -> None:
    left = {"action_type": "run_gate_clearing_batch", "work_unit_id": "gate-replay"}
    right = {"action_type": "run_gate_clearing_batch", "work_unit_id": "gate-replay"}

    assert currentness_identities_match(left, right)
    assert not currentness_identities_match(left, right, require_fingerprint=True)
