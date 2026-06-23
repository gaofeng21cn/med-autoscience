from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.paper_mission_run import (
    ALLOWED_CONSUME_RESULT_STATUSES,
    ALLOWED_PAPER_AUDIT_PACK_STATUSES,
    PaperMissionContractError,
    PaperMissionRun,
    REQUIRED_PAPER_AUDIT_PACK_FAMILIES,
)
from med_autoscience.paper_mission_transaction import PaperMissionTransaction


pytestmark = [pytest.mark.contract, pytest.mark.meta]

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "paper_mission_run_contract.json"


def _valid_payload() -> dict[str, object]:
    return {
        "schema_version": "paper-mission-run.v1",
        "mission_id": "paper-mission::dm002::gate-clearing::20260623T010000Z",
        "study_id": "002-dm-china-us-mortality-attribution",
        "objective": "Produce a gate-clearing candidate with claim/evidence repairs.",
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::claim-evidence-map",
                "artifact_ref": "mission://dm002/candidates/claim-evidence-map.json",
                "delta_kind": "evidence_ledger_repair",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "progress::dm002::20260623",
                "ref_kind": "study_progress",
                "uri": "runtime://study-progress/002-dm-china-us-mortality-attribution",
            }
        ],
        "paper_audit_pack": _valid_paper_audit_pack(),
        "authority_touchpoints": [
            {
                "touchpoint_id": "touchpoint::pre-consume-boundary",
                "owner": "MedAutoScience",
                "surface": "MAS Authority Kernel",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
            "candidate_writes_authority": False,
        },
        "consume_result": {
            "status": "route_back",
            "ref": "owner://consume/pending",
        },
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "paper_mission_transaction": _valid_transaction_payload(),
    }


def _valid_paper_audit_pack() -> dict[str, object]:
    families = [
        "analysis_rationale_log",
        "decision_trace",
        "evidence_ledger_delta",
        "review_ledger_delta",
        "revision_log_delta",
        "failed_path_ledger",
        "artifact_lineage",
        "reproducibility_refs",
    ]
    return {
        family: {
            "status": "candidate_ref_chain",
            "refs": [
                {
                    "ref_id": f"{family}::1",
                    "ref_kind": "artifact_ref",
                    "uri": f"mission://dm002/audit/{family}",
                }
            ],
        }
        for family in families
    }


def _valid_transaction_payload() -> dict[str, object]:
    audit_refs = {
        family: [
            {
                "ref_id": f"{family}::1",
                "ref_kind": "artifact_ref",
                "uri": f"mission://dm002/audit/{family}",
            }
        ]
        for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    }
    return {
        "schema_version": "paper-mission-transaction.v1",
        "transaction_id": (
            "paper-mission-transaction::dm002::gate-clearing::"
            "paper-mission::dm002::gate-clearing::20260623T010000Z"
        ),
        "mission_id": "paper-mission::dm002::gate-clearing::20260623T010000Z",
        "study_id": "002-dm-china-us-mortality-attribution",
        "stage_id": "gate_clearing_claim_evidence_repair",
        "stage_run_ref": "opl-stage-run://dm002/gate-clearing/20260623T010000Z",
        "stage_terminal_decision": {
            "decision_kind": "advance",
            "status": "accepted",
            "reason": "candidate accepted for the next MAS paper stage",
            "next_owner": "analysis-campaign",
            "next_stage_id": "publication_gate_replay",
        },
        "opl_route_command": {
            "command_kind": "start_next_stage",
            "target": "publication_gate_replay",
            "reason": "candidate accepted for the next MAS paper stage",
            "source_terminal_decision_ref": (
                "paper-mission-transaction::dm002::gate-clearing::"
                "paper-mission::dm002::gate-clearing::20260623T010000Z"
                "#stage_terminal_decision"
            ),
        },
        "artifact_delta_refs": [
            {
                "ref_id": "artifact_delta::1",
                "ref_kind": "mission_candidate_artifact_delta",
                "uri": "mission://dm002/candidates/claim-evidence-map.json",
            }
        ],
        "paper_audit_pack_refs": audit_refs,
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
        },
        "idempotency": {
            "idempotency_key": "dm002::gate-clearing::20260623T010000Z",
            "transaction_fingerprint": (
                "paper-mission::dm002::gate-clearing::20260623T010000Z::"
                "advance::accepted"
            ),
        },
    }


def test_contract_declares_required_paper_mission_run_fields() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["surface_kind"] == "mas_paper_mission_run_contract"
    assert contract["version"] == "paper-mission-run.v1"
    assert contract["owner"] == "MedAutoScience"
    assert contract["state"] == "active_contract"
    assert contract["required_fields"] == [
        "mission_id",
        "study_id",
        "objective",
        "mission_state",
        "artifact_delta_ledger",
        "source_refs",
        "paper_audit_pack",
        "authority_touchpoints",
        "forbidden_write_guard",
        "consume_result",
        "claim_permissions",
        "paper_mission_transaction",
    ]
    assert {
        "publication_ready",
        "submission_ready",
        "current_package",
        "owner_receipt_written",
        "typed_blocker_written",
        "human_gate_written",
        "controller_decision_written",
        "publication_eval_written",
    } <= set(contract["forbidden_authority_claims"])
    assert set(contract["consume_result"]["allowed_statuses"]) == set(
        ALLOWED_CONSUME_RESULT_STATUSES
    )
    assert contract["paper_audit_pack"]["required_families"] == [
        "analysis_rationale_log",
        "decision_trace",
        "evidence_ledger_delta",
        "review_ledger_delta",
        "revision_log_delta",
        "failed_path_ledger",
        "artifact_lineage",
        "reproducibility_refs",
    ]
    assert contract["paper_audit_pack"]["required_family_fields"] == [
        "status",
        "refs",
    ]
    assert set(contract["paper_audit_pack"]["allowed_statuses"]) == (
        ALLOWED_PAPER_AUDIT_PACK_STATUSES
    )
    assert contract["paper_audit_pack"]["gap_status_required_fields"] == [
        "gap_class",
        "gap_reason",
    ]
    assert "missing_audit_ref" in contract["paper_audit_pack"][
        "candidate_status_forbidden_ref_kinds"
    ]
    assert "/missing" in contract["paper_audit_pack"][
        "candidate_status_forbidden_uri_markers"
    ]
    assert contract["paper_mission_transaction"]["contract_ref"] == (
        "contracts/paper_mission_transaction_contract.json"
    )


def test_paper_mission_run_accepts_valid_payload_and_round_trips() -> None:
    payload = _valid_payload()

    run = PaperMissionRun.from_payload(payload)

    assert run.mission_id == payload["mission_id"]
    assert run.study_id == payload["study_id"]
    assert run.mission_state == "candidate_ready_for_consumption"
    assert run.validate() is run
    assert PaperMissionTransaction.from_payload(run.paper_mission_transaction).mission_id == (
        payload["mission_id"]
    )
    assert run.to_dict() == payload


def test_paper_mission_run_fails_closed_when_required_field_is_missing() -> None:
    payload = _valid_payload()
    payload.pop("artifact_delta_ledger")

    with pytest.raises(
        PaperMissionContractError,
        match="missing required field: artifact_delta_ledger",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_requires_paper_audit_pack() -> None:
    payload = _valid_payload()
    payload.pop("paper_audit_pack")

    with pytest.raises(
        PaperMissionContractError,
        match="missing required field: paper_audit_pack",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_requires_stage_terminal_transaction() -> None:
    payload = _valid_payload()
    payload.pop("paper_mission_transaction")

    with pytest.raises(
        PaperMissionContractError,
        match="missing required field: paper_mission_transaction",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_rejects_transaction_for_different_mission() -> None:
    payload = _valid_payload()
    transaction = dict(payload["paper_mission_transaction"])
    transaction["mission_id"] = "paper-mission::other::mission"
    payload["paper_mission_transaction"] = transaction

    with pytest.raises(
        PaperMissionContractError,
        match="paper_mission_transaction mission_id does not match payload",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_rejects_missing_audit_family() -> None:
    payload = _valid_payload()
    audit_pack = dict(payload["paper_audit_pack"])
    audit_pack.pop("failed_path_ledger")
    payload["paper_audit_pack"] = audit_pack

    with pytest.raises(
        PaperMissionContractError,
        match="paper_audit_pack missing required family: failed_path_ledger",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_rejects_empty_audit_family_refs() -> None:
    payload = _valid_payload()
    audit_pack = dict(payload["paper_audit_pack"])
    family = dict(audit_pack["analysis_rationale_log"])
    family["refs"] = []
    audit_pack["analysis_rationale_log"] = family
    payload["paper_audit_pack"] = audit_pack

    with pytest.raises(
        PaperMissionContractError,
        match="paper_audit_pack.analysis_rationale_log.refs must not be empty",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_rejects_audit_ref_with_empty_uri() -> None:
    payload = _valid_payload()
    audit_pack = dict(payload["paper_audit_pack"])
    family = dict(audit_pack["decision_trace"])
    family["refs"] = [
        {
            "ref_id": "decision_trace::1",
            "ref_kind": "artifact_ref",
            "uri": "",
        }
    ]
    audit_pack["decision_trace"] = family
    payload["paper_audit_pack"] = audit_pack

    with pytest.raises(
        PaperMissionContractError,
        match="paper_audit_pack.decision_trace.refs\\[0\\] missing required field: uri",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_rejects_unknown_audit_family_status() -> None:
    payload = _valid_payload()
    audit_pack = dict(payload["paper_audit_pack"])
    family = dict(audit_pack["analysis_rationale_log"])
    family["status"] = "ready_for_publication"
    audit_pack["analysis_rationale_log"] = family
    payload["paper_audit_pack"] = audit_pack

    with pytest.raises(
        PaperMissionContractError,
        match="paper_audit_pack.analysis_rationale_log unsupported status",
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_rejects_candidate_audit_status_with_placeholder_ref() -> None:
    payload = _valid_payload()
    audit_pack = dict(payload["paper_audit_pack"])
    family = dict(audit_pack["artifact_lineage"])
    family["refs"] = [
        {
            "ref_id": "artifact_lineage::missing",
            "ref_kind": "missing_audit_ref",
            "uri": "mission://audit-pack/artifact_lineage/missing",
        }
    ]
    audit_pack["artifact_lineage"] = family
    payload["paper_audit_pack"] = audit_pack

    with pytest.raises(
        PaperMissionContractError,
        match=(
            "paper_audit_pack.artifact_lineage.refs\\[0\\] "
            "candidate status cannot use placeholder ref"
        ),
    ):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_allows_explicit_audit_gap_with_reason() -> None:
    payload = _valid_payload()
    audit_pack = dict(payload["paper_audit_pack"])
    family = dict(audit_pack["failed_path_ledger"])
    family.update(
        {
            "status": "evidence_gap",
            "gap_class": "evidence_tail",
            "gap_reason": "failed path ledger is pending reviewer owner output",
            "refs": [
                {
                    "ref_id": "failed_path_ledger::missing",
                    "ref_kind": "missing_audit_ref",
                    "uri": "mission://audit-pack/failed_path_ledger/missing",
                }
            ],
        }
    )
    audit_pack["failed_path_ledger"] = family
    payload["paper_audit_pack"] = audit_pack

    run = PaperMissionRun.from_payload(payload)

    assert run.paper_audit_pack["failed_path_ledger"]["status"] == "evidence_gap"


def test_paper_mission_run_rejects_audit_gap_without_reason() -> None:
    payload = _valid_payload()
    audit_pack = dict(payload["paper_audit_pack"])
    family = dict(audit_pack["review_ledger_delta"])
    family.update({"status": "typed_blocker_required", "gap_class": "authority_gate"})
    family.pop("gap_reason", None)
    audit_pack["review_ledger_delta"] = family
    payload["paper_audit_pack"] = audit_pack

    with pytest.raises(
        PaperMissionContractError,
        match=(
            "paper_audit_pack.review_ledger_delta gap status missing required "
            "field: gap_reason"
        ),
    ):
        PaperMissionRun.from_payload(payload)


@pytest.mark.parametrize(
    "claim_patch",
    [
        {"can_claim_publication_ready": True},
        {"can_claim_current_package": True},
        {"can_claim_owner_receipt_written": True},
    ],
)
def test_paper_mission_run_rejects_forbidden_authority_claims(
    claim_patch: dict[str, bool],
) -> None:
    payload = _valid_payload()
    claim_permissions = dict(payload["claim_permissions"])
    claim_permissions.update(claim_patch)
    payload["claim_permissions"] = claim_permissions

    with pytest.raises(PaperMissionContractError, match="forbidden authority claim"):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_requires_explicit_false_for_forbidden_claim_flags() -> None:
    payload = _valid_payload()
    claim_permissions = dict(payload["claim_permissions"])
    claim_permissions.pop("can_claim_publication_ready")
    payload["claim_permissions"] = claim_permissions

    with pytest.raises(PaperMissionContractError, match="forbidden authority claim"):
        PaperMissionRun.from_payload(payload)


@pytest.mark.parametrize("status", sorted(ALLOWED_CONSUME_RESULT_STATUSES))
def test_paper_mission_run_allows_declared_consume_result_statuses(status: str) -> None:
    payload = _valid_payload()
    consume_result = dict(payload["consume_result"])
    consume_result["status"] = status
    payload["consume_result"] = consume_result

    run = PaperMissionRun.from_payload(payload)

    assert run.consume_result["status"] == status


def test_paper_mission_run_rejects_unknown_consume_result_status() -> None:
    payload = _valid_payload()
    consume_result = dict(payload["consume_result"])
    consume_result["status"] = "publication_ready"
    payload["consume_result"] = consume_result

    with pytest.raises(
        PaperMissionContractError,
        match="unsupported consume_result status",
    ):
        PaperMissionRun.from_payload(payload)
