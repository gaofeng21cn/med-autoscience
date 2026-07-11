from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.paper_mission_transaction import (
    PaperMissionTransaction,
    PaperMissionTransactionContractError,
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)
from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier


pytestmark = [pytest.mark.contract, pytest.mark.meta]

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "paper_mission_transaction_contract.json"
AUDIT_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)


def _audit_refs() -> dict[str, list[dict[str, str]]]:
    return {
        family: [
            {
                "ref_id": f"{family}::1",
                "ref_kind": "artifact_ref",
                "uri": f"mission://audit/{family}",
            }
        ]
        for family in AUDIT_FAMILIES
    }


def _artifact_refs() -> list[dict[str, str]]:
    return [
        {
            "ref_id": "delta::1",
            "ref_kind": "mission_candidate_artifact_delta",
            "uri": "mission://dm002/delta",
        }
    ]


def _valid_transaction(decision_kind: str = "advance") -> dict[str, object]:
    decision = {
        "decision_kind": decision_kind,
        "status": "accepted",
        "reason": "stage produced a MAS-consumable paper artifact delta",
        "next_owner": "analysis-campaign",
    }
    if decision_kind == "advance":
        decision["next_stage_id"] = "finalize_and_publication_handoff"
    elif decision_kind == "continue_same_stage":
        decision["next_work_unit"] = "claim_evidence_repair"
        decision["target_stage_id"] = "manuscript_authoring"
    elif decision_kind == "route_back":
        decision["target_stage_id"] = "review_and_quality_gate"
        decision["repair_scope"] = "refresh claim evidence map"
    elif decision_kind == "typed_blocker":
        decision["blocker_id"] = "source_readiness_missing"
        decision["unblock_condition"] = "OPL supplies source readiness receipt"
    elif decision_kind == "human_gate":
        decision["question"] = "Accept this evidence downgrade?"
        decision["required_receipt"] = "human-gate::dm002::evidence-downgrade"
    elif decision_kind == "mission_complete":
        decision["package_ref"] = "mission://dm002/submission-package"
    return build_paper_mission_transaction(
        mission_id="paper-mission::dm002::gate-clearing::one-shot",
        study_id="002-dm-china-us-mortality-attribution",
        stage_id="gate_clearing_claim_evidence_repair",
        stage_run_ref="opl-stage-run://dm002/gate-clearing/1",
        terminal_decision=decision,
        artifact_delta_refs=_artifact_refs(),
        paper_audit_pack_refs=_audit_refs(),
        idempotency_basis=decision_kind,
    )


def test_contract_declares_terminalizer_boundary() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["surface_kind"] == "mas_paper_mission_transaction_contract"
    assert contract["version"] == "paper-mission-transaction.v1"
    assert contract["stage_terminal_decision"]["owner"] == "MedAutoScience"
    assert contract["opl_route_command"]["owner"] == "one-person-lab"
    assert contract["stage_terminal_decision"]["allowed_decision_kinds"] == [
        "advance",
        "continue_same_stage",
        "route_back",
        "typed_blocker",
        "human_gate",
        "mission_complete",
    ]
    assert "read_model_status_is_stage_terminal_decision" in contract[
        "opl_route_command"
    ]["forbidden_runtime_claims"]
    assert contract["opl_runtime_carrier"]["surface_kind"] == (
        "opl_domain_route_runtime_request"
    )
    assert contract["opl_runtime_carrier"]["target_runtime_kind"] == (
        "domain_route/stage-route"
    )
    assert contract["opl_runtime_carrier"]["request_only_flags"][
        "writes_runtime_queue"
    ] is False
    assert contract["opl_runtime_carrier"]["domain_route_profile_ref"] == (
        "contracts/domain_route_profile.json"
    )
    attempt_consumer = contract["opl_runtime_carrier"]["runtime_attempt_consumer"]
    assert attempt_consumer["runtime_domain_id"] == "medautoscience"
    assert attempt_consumer["stage_argument_source"] == (
        "declarative_target_stage_id"
    )
    assert attempt_consumer["forbidden_command_surfaces"] == [
        "opl family-runtime enqueue",
        "opl family-runtime tick",
    ]
    assert contract["opl_route_command"]["required_fields_by_command_kind"][
        "start_next_stage"
    ] == ["declarative_target_stage_id"]
    assert "stage_run_identity" in contract["opl_runtime_carrier"][
        "forbidden_runtime_fields"
    ]


@pytest.mark.parametrize(
    ("decision_kind", "expected_command"),
    (
        ("advance", "start_next_stage"),
        ("continue_same_stage", "resume_stage"),
        ("route_back", "route_back"),
        ("typed_blocker", "stop_with_typed_blocker"),
        ("human_gate", "wait_for_human"),
        ("mission_complete", "complete_mission"),
    ),
)
def test_transaction_maps_terminal_decision_to_opl_route_command(
    decision_kind: str,
    expected_command: str,
) -> None:
    transaction = PaperMissionTransaction.from_payload(
        _valid_transaction(decision_kind)
    )
    carrier = paper_mission_opl_runtime_carrier(transaction.to_dict())

    assert transaction.stage_terminal_decision["decision_kind"] == decision_kind
    assert transaction.opl_route_command["command_kind"] == expected_command
    assert carrier["opl_route_command"]["command_kind"] == expected_command
    assert carrier["provider_admission_requires_opl_runtime_result"] is True
    assert transaction.authority_boundary["writes_runtime_queue"] is False
    assert transaction.authority_boundary["writes_provider_attempt"] is False


def test_advance_transaction_exports_explicit_declarative_target_stage() -> None:
    transaction = PaperMissionTransaction.from_payload(_valid_transaction("advance"))

    assert transaction.opl_route_command["declarative_target_stage_id"] == (
        transaction.stage_terminal_decision["next_stage_id"]
    )


def test_resume_transaction_rejects_missing_declarative_target_stage() -> None:
    payload = _valid_transaction("continue_same_stage")
    payload["stage_terminal_decision"].pop("target_stage_id")

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="target_stage_id must be a non-empty string",
    ):
        PaperMissionTransaction.from_payload(payload)


def test_transaction_fails_closed_without_audit_family() -> None:
    payload = _valid_transaction()
    audit_refs = dict(payload["paper_audit_pack_refs"])
    audit_refs.pop("failed_path_ledger")
    payload["paper_audit_pack_refs"] = audit_refs

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="paper_audit_pack_refs.failed_path_ledger must be a list of mappings",
    ):
        PaperMissionTransaction.from_payload(payload)


def test_transaction_rejects_provider_completion_as_domain_completion() -> None:
    payload = _valid_transaction()
    payload["opl_route_command"] = {
        **payload["opl_route_command"],
        "command_kind": "complete_mission",
    }

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="command_kind does not match stage_terminal_decision",
    ):
        PaperMissionTransaction.from_payload(payload)


def test_transaction_rejects_cross_identity_terminal_decision_ref() -> None:
    payload = _valid_transaction()
    payload["opl_route_command"] = {
        **payload["opl_route_command"],
        "source_terminal_decision_ref": (
            "paper-mission-transaction::other#stage_terminal_decision"
        ),
    }

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="source_terminal_decision_ref must match transaction",
    ):
        PaperMissionTransaction.from_payload(payload)


def test_transaction_rejects_cross_identity_stage_run_ref() -> None:
    payload = _valid_transaction()
    payload["opl_route_command"] = {
        **payload["opl_route_command"],
        "stage_run_ref": "opl-stage-run://other/stage/attempt",
    }

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="stage_run_ref must match transaction stage_run_ref",
    ):
        PaperMissionTransaction.from_payload(payload)


def test_transaction_preserves_external_fingerprint_for_opl_identity() -> None:
    payload = _valid_transaction()
    payload["idempotency"] = {
        **payload["idempotency"],
        "transaction_fingerprint": "external-fingerprint::opaque-owner-route",
    }

    transaction = PaperMissionTransaction.from_payload(payload)
    carrier = paper_mission_opl_runtime_carrier(transaction.to_dict())

    assert carrier["work_unit_fingerprint"] == "external-fingerprint::opaque-owner-route"
    assert carrier["aggregate_identity"]["work_unit_fingerprint"] == (
        "external-fingerprint::opaque-owner-route"
    )


def test_terminal_decision_for_not_consumed_continues_same_stage() -> None:
    decision = stage_terminal_decision_for_consume_result(
        mission_id="paper-mission::dm002::stage",
        study_id="002-dm-china-us-mortality-attribution",
        stage_id="gate_clearing_claim_evidence_repair",
        consume_result={"status": "not_consumed"},
        default_next_owner="analysis-campaign",
        default_next_stage_id="publication_gate_replay",
        default_next_work_unit="claim_evidence_repair",
        default_reason="candidate still needs MAS consume",
    )

    assert decision["decision_kind"] == "continue_same_stage"
    assert decision["target_stage_id"] == "gate_clearing_claim_evidence_repair"
    assert decision["next_work_unit"] == "claim_evidence_repair"
