from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.controllers.mas_stage_semantic_receipts import (
    AUTHORITY_CAPABILITY_PREFIX,
    MAS_AUTHORITY_SEMANTIC_REF_REQUIREMENTS,
    MAS_STAGE_AUTHORITY_TYPES,
    REQUIRED_SCHEMA_REFS,
    validate_mas_stage_semantic_receipt,
)


def _valid_receipt(authority_type: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "stage_id": "07-independent_review_and_revision",
        "authority_type": authority_type,
        "receipt_ref": f"mas-semantic-receipt:{authority_type}:attempt-001",
        "schema_refs": list(REQUIRED_SCHEMA_REFS),
        "capability_refs": [f"{AUTHORITY_CAPABILITY_PREFIX}{authority_type}"],
        "domain_semantic_refs": {
            role: [f"mas-semantic-ref:{authority_type}:{role}:attempt-001"]
            for role in MAS_AUTHORITY_SEMANTIC_REF_REQUIREMENTS[authority_type]
        },
    }
    payload.update(overrides)
    return payload


def test_validator_accepts_body_free_schema_capability_and_domain_refs_for_all_authorities() -> None:
    statuses = {
        authority_type: validate_mas_stage_semantic_receipt(_valid_receipt(authority_type))
        for authority_type in MAS_STAGE_AUTHORITY_TYPES
    }

    assert tuple(statuses) == MAS_STAGE_AUTHORITY_TYPES
    for authority_type, validation in statuses.items():
        if authority_type == "typed_blocker":
            assert validation["status"] == "typed_blocker"
            assert validation["semantic_receipt_accepted"] is False
            assert validation["typed_blocker_is_domain_outcome_not_runtime_failure"] is True
        else:
            assert validation["status"] == "accepted"
            assert validation["semantic_receipt_accepted"] is True
        assert validation["authority_type"] == authority_type
        assert validation["validation_scope"] == [
            "receipt_ref",
            "schema_refs",
            "capability_refs",
            "domain_semantic_refs",
        ]
        assert validation["receipt_body_read"] is False
        assert validation["body_included"] is False
        assert validation["manifest_validity_is_semantic_receipt_validity"] is False
        assert validation["ready_claims"] == {
            "publication_ready": False,
            "quality_ready": False,
            "submission_ready": False,
            "artifact_mutation_authorized": False,
            "memory_writeback_authorized": False,
        }


def test_format_valid_publication_gate_without_domain_semantic_refs_fails_closed() -> None:
    receipt = _valid_receipt(
        "publication_gate",
        domain_semantic_refs={"publication_route_decision_refs": ["route:decision:attempt-001"]},
    )

    validation = validate_mas_stage_semantic_receipt(receipt)

    assert validation["status"] == "fail_closed"
    assert validation["semantic_receipt_accepted"] is False
    assert validation["fail_closed_reason"] == "missing_domain_semantic_refs"
    assert validation["missing_domain_semantic_refs"] == ["publication_gate_receipt_refs"]
    assert validation["typed_blocker_required"] is True
    assert validation["ready_claims"]["publication_ready"] is False
    assert validation["ready_claims"]["quality_ready"] is False


def test_typed_blocker_refs_block_semantic_acceptance_without_publication_or_quality_ready() -> None:
    receipt = _valid_receipt(
        "reviewer_quality",
        domain_semantic_refs={},
        typed_blocker_refs=["mas-typed-blocker:reviewer_quality:attempt-001"],
    )

    validation = validate_mas_stage_semantic_receipt(receipt)

    assert validation["status"] == "typed_blocker"
    assert validation["semantic_receipt_accepted"] is False
    assert validation["typed_blocker_refs"] == ["mas-typed-blocker:reviewer_quality:attempt-001"]
    assert validation["typed_blocker_is_domain_outcome_not_runtime_failure"] is True
    assert validation["fail_closed_reason"] is None
    assert validation["ready_claims"]["quality_ready"] is False
    assert validation["ready_claims"]["publication_ready"] is False


def test_missing_schema_or_capability_fails_closed_before_domain_readiness() -> None:
    receipt = _valid_receipt("source_readiness", schema_refs=[], capability_refs=[])

    validation = validate_mas_stage_semantic_receipt(receipt)

    assert validation["status"] == "fail_closed"
    assert validation["semantic_receipt_accepted"] is False
    assert validation["fail_closed_reason"] == "missing_schema_or_capability_refs"
    assert validation["missing_schema_refs"] == list(REQUIRED_SCHEMA_REFS)
    assert validation["missing_capability_refs"] == [f"{AUTHORITY_CAPABILITY_PREFIX}source_readiness"]
    assert validation["ready_claims"]["quality_ready"] is False
    assert validation["ready_claims"]["publication_ready"] is False


def test_forbidden_body_fields_fail_closed_and_are_not_echoed() -> None:
    receipt = _valid_receipt(
        "artifact_package_authority",
        body={"artifact_body": "must not be inspected or echoed"},
    )

    validation = validate_mas_stage_semantic_receipt(receipt)

    assert validation["status"] == "fail_closed"
    assert validation["fail_closed_reason"] == "receipt_body_present"
    assert validation["forbidden_body_fields"] == ["artifact_body", "body"]
    assert validation["receipt_body_read"] is False
    assert validation["body_included"] is False
    assert "must not be inspected" not in str(validation)
    assert "artifact_body" in validation["forbidden_body_fields"]


def test_receipt_ref_is_not_read_as_body(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text('{"body": "this file must not be read"}\n', encoding="utf-8")

    def _forbid_read_text(self: Path, *args: object, **kwargs: object) -> str:
        raise AssertionError(f"receipt body read attempted: {self}")

    monkeypatch.setattr(Path, "read_text", _forbid_read_text)
    receipt = _valid_receipt("medical_owner_receipt", receipt_ref=str(receipt_path))

    validation = validate_mas_stage_semantic_receipt(receipt)

    assert validation["status"] == "accepted"
    assert validation["receipt_ref"] == str(receipt_path)
    assert validation["receipt_body_read"] is False
