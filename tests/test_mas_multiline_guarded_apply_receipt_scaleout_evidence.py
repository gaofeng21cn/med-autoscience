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
    / "mas-multiline-guarded-apply-receipt-scaleout-evidence-20260527.json"
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


def test_multiline_guarded_apply_snapshot_records_two_receipts_and_one_blocker() -> None:
    payload = _snapshot()

    assert payload["surface_kind"] == "mas_multiline_guarded_apply_receipt_scaleout_evidence"
    assert payload["snapshot_status"] == "refs_only_multiline_owner_chain_snapshot_observed"
    assert payload["selected_acceptance_surface"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence",
        "role": "selected_existing_mas_evidence_surface",
        "body_included": False,
    }

    summary = payload["live_summary"]
    assert summary["target_study_count"] == 3
    assert summary["guarded_receipt_count"] == 3
    assert summary["mas_owner_apply_receipt_count"] == 2
    assert summary["typed_blocker_count"] == 1
    assert summary["memory_final_proof_status"] == "final_ref_chain_proven"
    assert summary["forbidden_write_guard_result"] == "fail_closed_no_forbidden_writes"
    assert summary["writes_performed"] is False
    assert summary["real_workspace_mutation_allowed"] is False
    assert summary["guarded_apply_performed"] is False
    assert summary["mas_owner_receipt_observed"] is True

    payload_summary = payload["paper_line_owner_payload_summary"]
    assert payload_summary == {
        "paper_line_count": 3,
        "success_payload_count": 2,
        "typed_blocker_payload_count": 1,
        "domain_ready_claim_count": 0,
        "production_ready_claim_count": 0,
        "artifact_mutation_authorized_count": 0,
    }


def test_multiline_guarded_apply_snapshot_preserves_per_line_owner_results() -> None:
    payload = _snapshot()
    results = {item["paper_line_id"]: item for item in payload["paper_line_owner_chain_results"]}

    assert set(results) == {
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "Obesity",
    }
    assert results["002-dm-china-us-mortality-attribution"]["result_kind"] == "owner_receipt"
    assert len(results["002-dm-china-us-mortality-attribution"]["owner_receipt_refs"]) == 2
    assert results["003-dpcc-primary-care-phenotype-treatment-gap"]["result_kind"] == "owner_receipt"
    assert results["003-dpcc-primary-care-phenotype-treatment-gap"]["owner_receipt_refs"] == [
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/gate_replay_requests/latest.json"
    ]
    assert results["Obesity"]["result_kind"] == "stable_typed_blocker"
    assert results["Obesity"]["stable_typed_blocker_refs"] == [
        "mas_owner_apply_receipt_missing:obesity"
    ]

    for result in results.values():
        assert result["required_return_shape_satisfied"] is True
        assert result["body_included"] is False
        assert result["no_forbidden_write_proof_ref"] == (
            "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard"
        )
        assert result["readiness_claims"] == {
            "claims_paper_closure": False,
            "claims_publication_ready": False,
            "claims_artifact_mutation_authorized": False,
            "claims_current_package_updated": False,
        }


def test_multiline_guarded_apply_snapshot_keeps_success_and_blocker_payload_paths_separate() -> None:
    payload = _snapshot()
    dispatches = {item["study_id"]: item for item in payload["domain_dispatch_payload_summaries"]}

    success_ids = [
        study_id
        for study_id, item in dispatches.items()
        if item["mode"] == "refs_only_domain_owned_success_payload"
    ]
    blocker_ids = [
        study_id
        for study_id, item in dispatches.items()
        if item["mode"] == "refs_only_domain_owned_typed_blocker_payload"
    ]

    assert success_ids == [
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    assert blocker_ids == ["Obesity"]
    assert dispatches["Obesity"]["typed_blocker_refs"] == [
        "mas_owner_apply_receipt_missing:obesity"
    ]
    assert dispatches["Obesity"]["domain_owner_receipt_refs"] == []
    assert dispatches["Obesity"]["closeout_semantics"] == (
        "typed_blocker_until_real_owner_receipt_or_live_paper_line_closeout"
    )

    for study_id in success_ids:
        dispatch = dispatches[study_id]
        assert dispatch["domain_owner_receipt_refs"]
        assert dispatch["typed_blocker_refs"] == []
        assert dispatch["closeout_semantics"] == (
            "domain_owner_receipt_refs_only_owner_chain_evidence_not_domain_ready"
        )

    for dispatch in dispatches.values():
        assert dispatch["task_kind"] == "paper_autonomy/guarded-apply"
        assert dispatch["stage_id"] == "finalize_and_publication_handoff"
        assert dispatch["body_included"] is False
        assert dispatch["domain_ready_claimed"] is False
        assert dispatch["publication_ready_claimed"] is False
        assert dispatch["artifact_mutation_authorized"] is False
        assert dispatch["current_package_mutation_authorized"] is False
        assert "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence" in dispatch["owner_chain_refs"]


def test_multiline_guarded_apply_snapshot_does_not_claim_ready_or_body_authority() -> None:
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
    assert boundary["typed_blocker_is_domain_ready"] is False

    assert not any(claims.values())
    assert set(payload["forbidden_payload_fields"]) == {
        "study_truth_body",
        "paper_body",
        "publication_verdict_body",
        "artifact_body",
        "memory_body",
        "current_package_body",
    }

    forbidden_keys = set(payload["forbidden_payload_fields"])
    for item in _walk_dicts(payload):
        assert not (forbidden_keys & set(item))
        if item.get("ref") and item.get("role"):
            assert item["body_included"] is False


def test_multiline_guarded_apply_snapshot_is_compact_and_replayable() -> None:
    payload = _snapshot()
    source = payload["source_live_proof"]

    assert source["command"].startswith(
        "scripts/run-python-clean.sh -m med_autoscience.cli real-paper-autonomy-guarded-apply-proof"
    )
    assert source["compact_projection_sha256"] == (
        "d815823fba57e24868713c7dac5e5b204c560f23508a77931382d783738c157d"
    )
    assert source["body_included"] is False
    assert source["repo_tracks_live_proof_body"] is False

    assert payload["verification_refs"] == [
        {
            "ref": "tests/test_mas_multiline_guarded_apply_receipt_scaleout_evidence.py",
            "role": "focused_contract_test",
            "body_included": False,
        },
        {
            "ref": "tests/test_real_paper_autonomy_soak_inventory_cases/test_canary_body_free_packets.py",
            "role": "canary_body_free_packet_shape_test",
            "body_included": False,
        },
    ]
