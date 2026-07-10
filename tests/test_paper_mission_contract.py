from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.paper_mission_run import (
    ALLOWED_CONSUME_RESULT_STATUSES,
    FORBIDDEN_AUTHORITY_CLAIMS,
    PaperMissionContractError,
    PaperMissionRun,
    REQUIRED_PAPER_AUDIT_PACK_FAMILIES,
    REQUIRED_FIELDS,
)
from med_autoscience.paper_mission_transaction import (
    build_paper_mission_transaction,
)


pytestmark = [pytest.mark.contract, pytest.mark.meta]
REPO_ROOT = Path(__file__).resolve().parents[1]
MISSION_ID = "paper-mission::dm002::gate-clearing::20260623T010000Z"
STUDY_ID = "002-dm-china-us-mortality-attribution"


def _audit_refs() -> dict[str, list[dict[str, str]]]:
    return {
        family: [{
            "ref_id": f"{family}::1",
            "ref_kind": "artifact_ref",
            "uri": f"mission://dm002/audit/{family}",
        }]
        for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    }


def _valid_payload() -> dict[str, object]:
    audit_refs = _audit_refs()
    transaction = build_paper_mission_transaction(
        mission_id=MISSION_ID,
        study_id=STUDY_ID,
        stage_id="gate_clearing_claim_evidence_repair",
        stage_run_ref="opl-stage-run://dm002/gate-clearing/20260623T010000Z",
        terminal_decision={
            "decision_kind": "advance",
            "status": "accepted",
            "reason": "candidate accepted for the next MAS paper stage",
            "next_owner": "analysis-campaign",
            "next_stage_id": "publication_gate_replay",
        },
        artifact_delta_refs=[{
            "ref_id": "artifact_delta::1",
            "ref_kind": "mission_candidate_artifact_delta",
            "uri": "mission://dm002/candidates/claim-evidence-map.json",
        }],
        paper_audit_pack_refs=audit_refs,
        idempotency_basis="20260623T010000Z",
    )
    return {
        "schema_version": "paper-mission-run.v1",
        "mission_id": MISSION_ID,
        "study_id": STUDY_ID,
        "objective": "Produce a gate-clearing candidate.",
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [{
            "delta_id": "delta::claim-evidence-map",
            "artifact_ref": "mission://dm002/candidates/claim-evidence-map.json",
            "delta_kind": "evidence_ledger_repair",
            "status": "candidate",
        }],
        "source_refs": [{
            "ref_id": "progress::dm002::20260623",
            "ref_kind": "study_progress",
            "uri": f"runtime://study-progress/{STUDY_ID}",
        }],
        "paper_audit_pack": {
            family: {"status": "candidate_ref_chain", "refs": refs}
            for family, refs in audit_refs.items()
        },
        "authority_touchpoints": [{
            "touchpoint_id": "touchpoint::pre-consume-boundary",
            "owner": "MedAutoScience",
            "surface": "MAS Authority Kernel",
            "status": "not_touched",
        }],
        "forbidden_write_guard": {
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready", "current_package", "owner_receipt_written"
            ],
            "candidate_writes_authority": False,
        },
        "consume_result": {"status": "route_back", "ref": "owner://consume/pending"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "paper_mission_transaction": transaction,
    }


def test_contract_declares_required_paper_mission_run_fields() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts" / "paper_mission_run_contract.json").read_text(encoding="utf-8")
    )
    assert contract["version"] == "paper-mission-run.v1"
    assert contract["owner"] == "MedAutoScience"
    assert contract["required_fields"] == list(REQUIRED_FIELDS)
    assert set(contract["forbidden_authority_claims"]) == FORBIDDEN_AUTHORITY_CLAIMS
    assert contract["paper_audit_pack"]["required_families"] == list(
        REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    )


def test_paper_mission_run_accepts_valid_payload_and_round_trips() -> None:
    payload = _valid_payload()
    run = PaperMissionRun.from_payload(payload)
    assert run.mission_id == MISSION_ID
    assert run.study_id == STUDY_ID
    assert run.to_dict() == payload


@pytest.mark.parametrize(
    "field",
    ["artifact_delta_ledger", "paper_audit_pack", "paper_mission_transaction"],
)
def test_paper_mission_run_fails_closed_when_required_field_is_missing(field: str) -> None:
    payload = _valid_payload()
    payload.pop(field)
    with pytest.raises(PaperMissionContractError, match=f"missing required field: {field}"):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_rejects_transaction_for_different_mission() -> None:
    payload = _valid_payload()
    payload["paper_mission_transaction"] = {
        **payload["paper_mission_transaction"],
        "mission_id": "paper-mission::other::mission",
    }
    with pytest.raises(PaperMissionContractError, match="mission_id does not match payload"):
        PaperMissionRun.from_payload(payload)


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("missing_family", "missing required family"),
        ("empty_refs", "refs must not be empty"),
        ("empty_uri", "missing required field: uri"),
        ("unknown_status", "unsupported status"),
        ("placeholder_ref", "candidate status cannot use placeholder ref"),
        ("gap_without_reason", "gap status missing required field: gap_reason"),
    ],
)
def test_paper_mission_run_rejects_invalid_audit_pack(case: str, message: str) -> None:
    payload = _valid_payload()
    pack = payload["paper_audit_pack"]
    if case == "missing_family":
        pack.pop("failed_path_ledger")
    elif case == "empty_refs":
        pack["analysis_rationale_log"]["refs"] = []
    elif case == "empty_uri":
        pack["decision_trace"]["refs"][0]["uri"] = ""
    elif case == "unknown_status":
        pack["analysis_rationale_log"]["status"] = "ready_for_publication"
    elif case == "placeholder_ref":
        pack["artifact_lineage"]["refs"] = [{
            "ref_id": "artifact_lineage::missing",
            "ref_kind": "missing_audit_ref",
            "uri": "mission://audit-pack/artifact_lineage/missing",
        }]
    else:
        pack["review_ledger_delta"].update({
            "status": "typed_blocker_required",
            "gap_class": "authority_gate",
        })
    with pytest.raises(PaperMissionContractError, match=message):
        PaperMissionRun.from_payload(payload)


def test_paper_mission_run_allows_explicit_audit_gap_with_reason() -> None:
    payload = _valid_payload()
    payload["paper_audit_pack"]["failed_path_ledger"].update({
        "status": "evidence_gap",
        "gap_class": "evidence_tail",
        "gap_reason": "pending reviewer owner output",
    })
    assert PaperMissionRun.from_payload(payload).paper_audit_pack[
        "failed_path_ledger"
    ]["status"] == "evidence_gap"


@pytest.mark.parametrize(
    "flag",
    [
        "can_claim_publication_ready",
        "can_claim_current_package",
        "can_claim_owner_receipt_written",
    ],
)
def test_paper_mission_run_requires_explicit_false_for_forbidden_claims(flag: str) -> None:
    for value in (True, None):
        payload = _valid_payload()
        if value is None:
            payload["claim_permissions"].pop(flag)
        else:
            payload["claim_permissions"][flag] = value
        with pytest.raises(PaperMissionContractError, match="forbidden authority claim"):
            PaperMissionRun.from_payload(payload)


@pytest.mark.parametrize("status", sorted(ALLOWED_CONSUME_RESULT_STATUSES))
def test_paper_mission_run_allows_declared_consume_result_statuses(status: str) -> None:
    payload = _valid_payload()
    payload["consume_result"]["status"] = status
    assert PaperMissionRun.from_payload(payload).consume_result["status"] == status


def test_paper_mission_run_rejects_unknown_consume_result_status() -> None:
    payload = _valid_payload()
    payload["consume_result"]["status"] = "publication_ready"
    with pytest.raises(PaperMissionContractError, match="unsupported consume_result status"):
        PaperMissionRun.from_payload(payload)
