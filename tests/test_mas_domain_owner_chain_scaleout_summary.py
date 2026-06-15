from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = (
    REPO_ROOT
    / "contracts"
    / "production_acceptance"
    / "mas-domain-owner-chain-scaleout-summary.json"
)
ACCEPTANCE_PATH = REPO_ROOT / "contracts" / "production_acceptance" / "mas-production-acceptance.json"
SNAPSHOT_PATH = (
    REPO_ROOT
    / "contracts"
    / "production_acceptance"
    / "mas-multiprofile-guarded-apply-receipt-scaleout-evidence-20260527.json"
)


def _summary() -> dict[str, object]:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def _acceptance() -> dict[str, object]:
    return json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))


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


def test_domain_owner_chain_scaleout_summary_is_body_free_non_ready_surface() -> None:
    payload = _summary()

    assert payload["surface_kind"] == "mas_domain_owner_chain_scaleout_summary"
    assert payload["domain_id"] == "med-autoscience"
    assert payload["owner"] == "MedAutoScience"
    assert payload["status"] == "owner_evidence_recorded_not_ready_claim"
    assert payload["body_included"] is False

    summary = payload["summary"]
    assert summary == {
        "paper_line_count": 9,
        "owner_receipt_payload_count": 4,
        "stable_typed_blocker_payload_count": 5,
        "domain_ready_claimed": False,
        "production_ready_claimed": False,
        "publication_ready_claimed": False,
        "artifact_mutation_authorized_count": 0,
    }
    assert set(payload["forbidden_claims"]) >= {
        "domain_ready",
        "production_ready",
        "publication_ready",
        "quality_or_export_ready",
        "artifact_mutation_authorized",
        "owner_receipt_or_typed_blocker_created_by_opl",
    }


def test_domain_owner_chain_scaleout_summary_matches_source_counts_and_refs() -> None:
    summary = _summary()
    acceptance = _acceptance()
    snapshot = _snapshot()

    source_refs = {item["role"]: item for item in summary["source_refs"]}
    assert source_refs == {
        "selected_existing_mas_evidence_surface": {
            "ref": "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence",
            "role": "selected_existing_mas_evidence_surface",
            "body_included": False,
        },
        "refs_only_multiprofile_owner_chain_snapshot": {
            "ref": "contracts/production_acceptance/mas-multiprofile-guarded-apply-receipt-scaleout-evidence-20260527.json",
            "role": "refs_only_multiprofile_owner_chain_snapshot",
            "body_included": False,
        },
    }
    assert acceptance["paper_line_guarded_apply_evidence"]["latest_live_scaleout_snapshot_ref"] == (
        source_refs["refs_only_multiprofile_owner_chain_snapshot"]
    )
    assert acceptance["paper_line_guarded_apply_evidence"][
        "domain_owner_chain_scaleout_summary_ref"
    ] == {
        "ref": "contracts/production_acceptance/mas-domain-owner-chain-scaleout-summary.json",
        "role": "domain_owner_chain_scaleout_summary",
        "body_included": False,
    }
    assert snapshot["selected_acceptance_surface"] == source_refs[
        "selected_existing_mas_evidence_surface"
    ]

    payload_summary = summary["summary"]
    source_summary = snapshot["paper_line_owner_payload_summary"]
    acceptance_summary = acceptance["paper_line_guarded_apply_evidence"][
        "latest_live_scaleout_snapshot_summary"
    ]
    owner_results = [
        item for item in snapshot["paper_line_owner_chain_results"] if item["result_kind"] == "owner_receipt"
    ]
    blocker_results = [
        item
        for item in snapshot["paper_line_owner_chain_results"]
        if item["result_kind"] == "stable_typed_blocker"
    ]

    assert payload_summary["paper_line_count"] == source_summary["paper_line_count"]
    assert payload_summary["paper_line_count"] == acceptance_summary["paper_line_count"]
    assert payload_summary["paper_line_count"] == len(snapshot["paper_line_owner_chain_results"])
    assert payload_summary["paper_line_count"] == len(snapshot["domain_dispatch_payload_summaries"])
    assert payload_summary["owner_receipt_payload_count"] == source_summary["success_payload_count"]
    assert payload_summary["owner_receipt_payload_count"] == len(owner_results)
    assert payload_summary["stable_typed_blocker_payload_count"] == source_summary[
        "typed_blocker_payload_count"
    ]
    assert payload_summary["stable_typed_blocker_payload_count"] == len(blocker_results)
    assert payload_summary["artifact_mutation_authorized_count"] == source_summary[
        "artifact_mutation_authorized_count"
    ]


def test_domain_owner_chain_scaleout_summary_accepts_only_opl_ref_shapes() -> None:
    summary = _summary()
    acceptance = _acceptance()

    accepted_shapes = summary["accepted_opl_intake_ref_shapes"]
    source_contract = acceptance["paper_line_guarded_apply_evidence"]["opl_ingestable_ref_contract"]

    assert accepted_shapes == source_contract["allowed_ref_roles"]
    assert accepted_shapes == [
        "owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_receipt_ref",
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    ]

    boundary = summary["authority_boundary"]
    assert boundary["opl_records_refs_only"] is True
    assert boundary["opl_can_create_owner_receipt"] is False
    assert boundary["opl_can_create_stable_typed_blocker"] is False
    assert boundary["opl_can_write_domain_truth"] is False
    assert boundary["opl_can_write_memory_body"] is False
    assert boundary["opl_can_write_artifact_body"] is False
    assert boundary["opl_can_authorize_publication_or_quality"] is False
    assert boundary["domain_ready_requires_mas_owner_receipt_or_typed_blocker"] is True
    assert boundary["owner_receipt_and_typed_blocker_owner"] == "MedAutoScience"


def test_domain_owner_chain_scaleout_summary_keeps_all_refs_body_free() -> None:
    payload = _summary()
    forbidden_body_fields = {
        "claim_body",
        "memory_body",
        "artifact_body",
        "publication_verdict_body",
        "medical_ready_body",
        "current_package_body",
    }

    for item in _walk_dicts(payload):
        assert not (forbidden_body_fields & set(item))
        if "body_included" in item:
            assert item["body_included"] is False
        if item.get("ref") and item.get("role"):
            assert set(item) <= {"ref", "role", "body_included"}
