from __future__ import annotations

import pytest

from med_autoscience.paper_mission_opl_carrier import (
    paper_mission_opl_runtime_carrier,
    validate_paper_mission_opl_runtime_carrier,
)
from med_autoscience.paper_mission_transaction import (
    PaperMissionTransactionContractError,
    build_paper_mission_transaction,
)


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


def _transaction(decision_kind: str = "advance") -> dict[str, object]:
    decision: dict[str, object] = {
        "decision_kind": decision_kind,
        "status": "accepted",
        "reason": "MAS stage terminalized a paper mission candidate",
        "next_owner": "analysis-campaign",
    }
    if decision_kind == "advance":
        decision["next_stage_id"] = "finalize_and_publication_handoff"
    elif decision_kind == "typed_blocker":
        decision["blocker_id"] = "current_owner_route_superseded"
        decision["unblock_condition"] = "OPL or MAS authority consumes blocker"
    return build_paper_mission_transaction(
        mission_id="paper-mission::dm002::gate-clearing::one-shot",
        study_id="002-dm-china-us-mortality-attribution",
        stage_id="gate_clearing_claim_evidence_repair",
        stage_run_ref="opl-stage-run://dm002/gate-clearing/1",
        terminal_decision=decision,
        artifact_delta_refs=[
            {
                "ref_id": "delta::dm002::gate-clearing",
                "ref_kind": "mission_candidate_artifact_delta",
                "uri": "mission://dm002/gate-clearing",
            }
        ],
        paper_audit_pack_refs={
            family: [
                {
                    "ref_id": f"{family}::dm002",
                    "ref_kind": family,
                    "uri": f"mission://dm002/{family}",
                }
            ]
            for family in AUDIT_FAMILIES
        },
        idempotency_basis=decision_kind,
    )


def test_paper_mission_opl_carrier_is_request_only_runtime_intent() -> None:
    carrier = paper_mission_opl_runtime_carrier(_transaction())

    assert carrier["surface_kind"] == "mas_domain_progress_transition_request"
    assert carrier["source_kind"] == "paper_mission_transaction_opl_route_command"
    assert carrier["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert carrier["domain_id"] == "mas"
    assert carrier["paper_mission_transaction_ref"].startswith(
        "paper-mission-transaction::002-dm-china-us-mortality-attribution"
    )
    assert carrier["domain_route_transaction_ref"] == carrier[
        "paper_mission_transaction_ref"
    ]
    assert carrier["domain_route_handoff_ref"].endswith("#domain_route_handoff")
    assert carrier["domain_route_command_ref"] == carrier["opl_route_command_ref"]
    assert carrier["opl_route_command"]["command_kind"] == "start_next_stage"
    assert carrier["declarative_target_stage_id"] == "finalize_and_publication_handoff"
    assert carrier["opl_route_command"]["declarative_target_stage_id"] == (
        "finalize_and_publication_handoff"
    )
    assert carrier["required_postcondition"]["mas_can_satisfy_readback"] is False
    assert carrier["provider_admission_pending"] is False
    assert carrier["provider_admission_requires_opl_runtime_result"] is True
    assert carrier["provider_completion_is_domain_completion"] is False
    assert carrier["can_write_opl_outbox"] is False
    assert carrier["can_write_opl_event"] is False
    assert carrier["can_write_opl_stage_run"] is False
    assert carrier["can_write_provider_attempt"] is False
    assert carrier["can_claim_provider_running"] is False
    assert carrier["can_claim_paper_progress"] is False


def test_paper_mission_opl_carrier_rejects_runtime_authority_fields() -> None:
    carrier = paper_mission_opl_runtime_carrier(_transaction())
    carrier["stage_run_identity"] = {"stage_run_id": "forbidden"}

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="must not include runtime field: stage_run_identity",
    ):
        validate_paper_mission_opl_runtime_carrier(carrier)


def test_paper_mission_opl_carrier_rejects_cross_transaction_refs() -> None:
    carrier = paper_mission_opl_runtime_carrier(_transaction())
    carrier["opl_route_command_ref"] = "paper-mission-transaction::other#opl_route_command"

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="opl_route_command_ref must match transaction",
    ):
        validate_paper_mission_opl_runtime_carrier(carrier)


def test_paper_mission_opl_carrier_rejects_route_stage_run_mismatch() -> None:
    carrier = paper_mission_opl_runtime_carrier(_transaction())
    carrier["opl_route_command"] = {
        **carrier["opl_route_command"],
        "stage_run_ref": "opl-stage-run://other/stage/attempt",
    }

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="route stage_run_ref must match carrier",
    ):
        validate_paper_mission_opl_runtime_carrier(carrier)


def test_paper_mission_opl_carrier_rejects_aggregate_identity_mismatch() -> None:
    carrier = paper_mission_opl_runtime_carrier(_transaction())
    carrier["aggregate_identity"] = {
        **carrier["aggregate_identity"],
        "work_unit_fingerprint": "paper-mission::other::wrong",
    }

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="aggregate_identity work_unit_fingerprint must match carrier",
    ):
        validate_paper_mission_opl_runtime_carrier(carrier)


def test_paper_mission_opl_carrier_rejects_stage_identity_mismatch() -> None:
    carrier = paper_mission_opl_runtime_carrier(_transaction())
    carrier["declarative_target_stage_id"] = "other-stage"

    with pytest.raises(
        PaperMissionTransactionContractError,
        match="declarative_target_stage_id must match route",
    ):
        validate_paper_mission_opl_runtime_carrier(carrier)
