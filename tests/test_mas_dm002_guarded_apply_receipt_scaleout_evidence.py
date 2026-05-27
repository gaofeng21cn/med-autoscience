from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = (
    REPO_ROOT
    / "contracts"
    / "production_acceptance"
    / "mas-dm002-guarded-apply-receipt-scaleout-evidence-20260527.json"
)


def _snapshot() -> dict[str, object]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _walk_dicts(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def test_dm002_guarded_apply_snapshot_records_live_owner_chain_refs() -> None:
    payload = _snapshot()

    assert payload["surface_kind"] == "mas_dm002_guarded_apply_receipt_scaleout_evidence"
    assert payload["domain_id"] == "med-autoscience"
    assert payload["owner"] == "MedAutoScience"
    assert payload["snapshot_status"] == "refs_only_live_owner_chain_snapshot_observed"
    assert payload["selected_acceptance_surface"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence",
        "role": "selected_existing_mas_evidence_surface",
        "body_included": False,
    }

    summary = payload["live_summary"]
    assert summary["target_study_count"] == 1
    assert summary["guarded_receipt_count"] == 1
    assert summary["typed_blocker_count"] == 0
    assert summary["mas_owner_apply_receipt_count"] == 1
    assert summary["memory_final_proof_status"] == "final_ref_chain_proven"
    assert summary["forbidden_write_guard_result"] == "fail_closed_no_forbidden_writes"
    assert summary["writes_performed"] is False
    assert summary["real_workspace_mutation_allowed"] is False
    assert summary["guarded_apply_performed"] is False
    assert summary["mas_owner_receipt_observed"] is True


def test_dm002_guarded_apply_snapshot_keeps_body_free_owner_payload_shape() -> None:
    payload = _snapshot()
    owner_result = payload["paper_line_owner_chain_result"]
    dispatch = payload["domain_dispatch_payload_summary"]
    packet_summary = payload["body_free_evidence_packet_summary"]

    expected_owner_refs = [
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/002-dm-china-us-mortality-attribution/artifacts/controller/repair_execution_receipts/latest.json",
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/002-dm-china-us-mortality-attribution/artifacts/controller/gate_replay_requests/latest.json",
    ]
    expected_stage_refs = [
        *expected_owner_refs,
        "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard",
    ]

    assert owner_result["paper_line_id"] == "002-dm-china-us-mortality-attribution"
    assert owner_result["result_kind"] == "owner_receipt"
    assert owner_result["required_return_shape_satisfied"] is True
    assert owner_result["owner_receipt_refs"] == expected_owner_refs
    assert owner_result["ai_reviewer_gate_receipt_refs"] == expected_owner_refs
    assert owner_result["stable_typed_blocker_refs"] == []
    assert owner_result["artifact_movement_refs"] == []
    assert owner_result["human_gate_or_resume_refs"] == []
    assert owner_result["body_included"] is False
    assert owner_result["readiness_claims"] == {
        "claims_paper_closure": False,
        "claims_publication_ready": False,
        "claims_artifact_mutation_authorized": False,
        "claims_current_package_updated": False,
    }

    assert dispatch["mode"] == "refs_only_domain_owned_success_payload"
    assert dispatch["task_kind"] == "paper_autonomy/guarded-apply"
    assert dispatch["study_id"] == "002-dm-china-us-mortality-attribution"
    assert dispatch["stage_id"] == "finalize_and_publication_handoff"
    assert dispatch["domain_owner_receipt_refs"] == expected_owner_refs
    assert dispatch["typed_blocker_refs"] == []
    assert dispatch["stage_expected_receipt_refs"] == expected_stage_refs
    assert dispatch["stage_monitor_freshness_refs"] == expected_stage_refs
    assert dispatch["stage_evidence_handoff_status"] == "refs_only_stage_evidence_refs_observed"
    assert dispatch["closeout_semantics"] == (
        "domain_owner_receipt_refs_only_owner_chain_evidence_not_domain_ready"
    )
    assert dispatch["body_included"] is False
    assert dispatch["domain_ready_claimed"] is False
    assert dispatch["publication_ready_claimed"] is False
    assert dispatch["artifact_mutation_authorized"] is False
    assert dispatch["current_package_mutation_authorized"] is False

    assert packet_summary == {
        "packet_count": 5,
        "roles": [
            "owner_receipt_ref",
            "ai_reviewer_gate_receipt_ref",
            "no_forbidden_write_proof_ref",
        ],
        "observed_owner_receipt_ref_count": 2,
        "observed_ai_reviewer_gate_receipt_ref_count": 2,
        "no_forbidden_write_proof_ref_count": 1,
        "body_included": False,
        "all_packets_no_forbidden_write": True,
        "all_packet_writes_performed": False,
    }


def test_dm002_guarded_apply_snapshot_records_memory_refs_without_memory_body() -> None:
    payload = _snapshot()
    proof = payload["publication_route_memory_final_proof"]

    assert proof["surface_kind"] == "dm002_publication_route_memory_final_proof"
    assert proof["status"] == "final_ref_chain_proven"
    assert proof["writeback_receipt_refs"] == [
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/002-dm-china-us-mortality-attribution/artifacts/stage_knowledge/memory_write_router_receipts/dm002-paper-soak-memory-proof-20260512.json",
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio/research_memory/publication_route_memory/writeback_receipts/dm002-paper-soak-memory-proof-20260512.json",
    ]
    assert proof["body_included"] is False
    assert proof["memory_body_included"] is False
    assert proof["opl_can_read_memory_body"] is False
    assert proof["opl_can_accept_or_reject_writeback"] is False
    assert proof["mas_memory_owner"] == "med-autoscience"


def test_dm002_guarded_apply_snapshot_does_not_claim_domain_or_artifact_readiness() -> None:
    payload = _snapshot()
    boundary = payload["authority_boundary"]
    claims = payload["claim_boundary"]

    assert boundary["domain_truth_owner"] == "med-autoscience"
    assert boundary["provider_attempt_owner"] == "one-person-lab"
    assert boundary["owner_chain_authority"] == "MedAutoScience"
    assert boundary["provider_attempt_is_truth"] is False
    assert boundary["provider_completion_can_close_canary"] is False
    assert boundary["opl_records_refs_only"] is True
    assert boundary["opl_can_write_mas_truth"] is False
    assert boundary["opl_can_write_artifact_authority"] is False
    assert boundary["opl_can_write_artifact_body"] is False
    assert boundary["opl_can_write_memory_body"] is False
    assert boundary["opl_can_write_current_package"] is False
    assert boundary["opl_can_authorize_quality_or_publication"] is False
    assert boundary["stage_expected_receipt_refs_close_domain_ready"] is False

    assert claims == {
        "workspace_receipt_scaleout_claimed": False,
        "domain_ready_claimed": False,
        "production_ready_claimed": False,
        "publication_ready_claimed": False,
        "medical_ready_claimed": False,
        "paper_closure_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_update_claimed": False,
        "long_soak_claimed": False,
        "writes_visual_truth": False,
        "writes_artifact_blob": False,
        "writes_memory_body": False,
        "writes_publication_eval_body": False,
        "writes_controller_decision_body": False,
    }
    assert set(payload["forbidden_payload_fields"]) == {
        "study_truth_body",
        "paper_body",
        "publication_verdict_body",
        "artifact_body",
        "memory_body",
        "current_package_body",
    }


def test_dm002_guarded_apply_snapshot_is_refs_only_contract_summary() -> None:
    payload = _snapshot()

    source = payload["source_live_proof"]
    assert source["export_path"].endswith(
        "/runtime-state/evidence-scaleout/20260527-mas-dm002-guarded-apply/dm002-guarded-apply-proof.json"
    )
    assert source["sha256"] == "44d35d73024fb33ea66ca5e8219d227256be1a8c2c6b0769b4a5597bf02ec50c"
    assert source["body_included"] is False
    assert source["repo_tracks_live_proof_body"] is False

    assert len(payload["source_refs"]) == 5
    assert any(ref.endswith("/artifacts/publication_eval/latest.json") for ref in payload["source_refs"])
    assert any(ref.endswith("/artifacts/controller_decisions/latest.json") for ref in payload["source_refs"])

    forbidden_keys = {
        "study_truth_body",
        "paper_body",
        "publication_verdict_body",
        "artifact_body",
        "memory_body",
        "current_package_body",
    }
    for item in _walk_dicts(payload):
        assert not (forbidden_keys & set(item))
        if item.get("ref") and item.get("role"):
            assert item["body_included"] is False
