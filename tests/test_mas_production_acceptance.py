from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_PATH = REPO_ROOT / "contracts" / "production_acceptance" / "mas-production-acceptance.json"


def _acceptance() -> dict[str, object]:
    return json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))


def _walk_dicts(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def test_mas_production_acceptance_surface_exists_and_records_domain_owned_tail_closure() -> None:
    payload = _acceptance()

    assert payload["surface_kind"] == "mas_domain_owned_production_acceptance"
    assert payload["domain_id"] == "med-autoscience"
    assert payload["owner"] == "MedAutoScience"
    assert payload["acceptance_status"] in {
        "closed_by_domain_owned_acceptance_receipt",
        "domain_owned_typed_blocker_with_next_verification_ref",
    }

    scope = payload["acceptance_scope"]
    assert scope["production_live_soak_not_claimed_by_conformance"] == payload["acceptance_status"]
    assert scope["domain_ready_not_claimed_by_conformance"] == payload["acceptance_status"]
    assert scope["domain_readiness_owner"] == "MedAutoScience"
    assert scope["structural_conformance_already_passed"] is True
    assert scope["physical_conformance_already_passed"] is True
    assert scope["production_like_receipt_chain_present"] is True
    assert scope["publication_or_medical_ready_claimed"] is False


def test_mas_production_acceptance_is_refs_only() -> None:
    payload = _acceptance()

    policy = payload["refs_only_policy"]
    assert policy["body_included"] is False
    assert policy["all_evidence_entries_must_be_refs"] is True
    assert set(policy["forbidden_body_fields"]) == {
        "claim_body",
        "memory_body",
        "artifact_body",
        "publication_verdict_body",
        "medical_ready_body",
        "current_package_body",
    }
    assert not (set(policy["forbidden_body_fields"]) & set(payload))

    ref_entries = [
        item
        for item in _walk_dicts(payload)
        if isinstance(item.get("ref"), str) and item.get("role")
    ]
    assert ref_entries
    assert all(item["body_included"] is False for item in ref_entries)
    assert all(set(item) <= {"ref", "role", "body_included"} for item in ref_entries)


def test_opl_and_provider_completion_do_not_authorize_mas_domain_ready() -> None:
    payload = _acceptance()
    conformance = payload["conformance_evidence"]
    boundary = payload["authority_boundary"]

    assert conformance["structural_conformance_status"] == "passed"
    assert conformance["physical_conformance_status"] == "passed"
    assert set(conformance["does_not_authorize"]) == {
        "domain_ready",
        "publication_ready",
        "medical_ready",
        "artifact_mutation",
        "current_package_update",
    }
    assert boundary["opl_can_authorize_domain_ready"] is False
    assert boundary["provider_completion_is_domain_ready"] is False
    assert boundary["provider_completion_is_publication_ready"] is False
    assert boundary["provider_completion_is_medical_ready"] is False
    assert boundary["structural_conformance_is_domain_ready"] is False
    assert boundary["physical_conformance_is_domain_ready"] is False
    assert boundary["publication_ready_requires_mas_quality_publication_gate"] is True
    assert boundary["medical_ready_requires_mas_quality_publication_gate"] is True
    assert "opl_authorizes_domain_ready" in payload["forbidden_claims"]
    assert "provider_completion_authorizes_medical_ready" in payload["forbidden_claims"]


def test_acceptance_requires_owner_receipt_or_typed_blocker_and_next_verification() -> None:
    payload = _acceptance()
    receipt = payload["domain_acceptance_receipt"]

    owner_receipt_refs = receipt["owner_receipt_refs"]
    typed_blocker_refs = receipt["typed_blocker_refs"]
    next_verification = receipt["next_verification_command_refs"]

    assert owner_receipt_refs or typed_blocker_refs
    assert next_verification
    assert {item["role"] for item in next_verification} == {
        "focused_contract_test",
        "minimum_repo_verification",
        "whitespace_integrity_check",
    }
    assert payload["authority_boundary"][
        "domain_ready_requires_mas_owner_receipt_or_typed_blocker"
    ] is True

    if payload["acceptance_status"] == "closed_by_domain_owned_acceptance_receipt":
        assert receipt["receipt_class"] == "owner_receipt"
        assert receipt["receipt_status"] == "accepted"
        assert owner_receipt_refs
    else:
        assert typed_blocker_refs
        assert payload["consumer_contract"]["current_evidence_tail_status"] == (
            "domain_owned_typed_blocker_with_next_verification_ref"
        )
