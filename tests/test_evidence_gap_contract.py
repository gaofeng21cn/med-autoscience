from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "contracts" / "evidence-gap-decision-policy.json"
SCHEMA_PATH = REPO_ROOT / "contracts" / "schemas" / "evidence-gap-decision.schema.json"
EXAMPLES_PATH = REPO_ROOT / "contracts" / "evidence-gap-decision-examples.json"

GAP_CLASSES = {
    "authority_gate",
    "human_gate",
    "proceed_with_assumption",
    "soft_quality_gap",
    "observability_backlog",
    "evidence_tail",
}
NON_TYPED_BLOCKER_GAP_CLASSES = {
    "proceed_with_assumption",
    "soft_quality_gap",
    "observability_backlog",
    "evidence_tail",
}
FORBIDDEN_CLAIMS = {
    "owner_receipt_closed",
    "paper_progress",
    "publication_ready",
    "submission_ready",
    "live_runtime_ready",
    "production_ready",
    "provider_running",
}


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_evidence_gap_decision_policy_declares_schema_and_boundary() -> None:
    policy = _json(POLICY_PATH)
    schema = _json(SCHEMA_PATH)

    assert policy["surface_kind"] == "mas_evidence_gap_decision_policy"
    assert policy["version"] == "evidence-gap-decision-policy.v1"
    assert policy["owner"] == "MedAutoScience"
    assert policy["state"] == "active_contract"
    assert policy["schema_ref"] == "contracts/schemas/evidence-gap-decision.schema.json"
    assert schema["$id"] == policy["schema_ref"]
    assert schema["properties"]["surface_kind"]["const"] == "mas_evidence_gap_decision"
    assert set(schema["properties"]["gap_class"]["enum"]) == GAP_CLASSES
    assert "live runtime ready" not in policy["purpose"].lower()
    assert "paper progress" in policy["machine_boundary"]
    assert "does not declare" in policy["machine_boundary"]


def test_gap_class_policy_separates_hard_blockers_from_soft_gap_accounting() -> None:
    policy = _json(POLICY_PATH)
    gap_classes = policy["gap_classes"]
    materialization = policy["typed_blocker_materialization_policy"]

    assert set(gap_classes) == GAP_CLASSES
    assert materialization["typed_blocker_countable_gap_classes"] == [
        "authority_gate",
        "human_gate",
    ]
    assert set(materialization["forbidden_gap_classes_for_typed_blocker_count"]) == (
        NON_TYPED_BLOCKER_GAP_CLASSES
    )

    for gap_class, definition in gap_classes.items():
        if gap_class in {"authority_gate", "human_gate"}:
            assert definition["typed_blocker_countable"] is True, gap_class
            assert definition["blocks_current_owner_action"] is True, gap_class
        else:
            assert definition["typed_blocker_countable"] is False, gap_class
            assert definition["blocks_current_owner_action"] is False, gap_class
        assert definition["blocks_completion_or_readiness_claim"] is True, gap_class


def test_examples_cover_every_gap_class_and_forbid_high_order_claims() -> None:
    examples = _json(EXAMPLES_PATH)
    schema = _json(SCHEMA_PATH)
    required = schema["required"]
    properties = schema["properties"]
    decisions = examples["examples"]

    assert examples["schema_ref"] == "contracts/schemas/evidence-gap-decision.schema.json"
    assert {decision["gap_class"] for decision in decisions} == GAP_CLASSES

    for decision in decisions:
        for field in required:
            assert field in decision, field
        assert decision["surface_kind"] == "mas_evidence_gap_decision"
        assert decision["gap_class"] in properties["gap_class"]["enum"]
        assert FORBIDDEN_CLAIMS <= set(decision["forbidden_claims"])
        assert decision["claim_boundary"]["paper_progress_claim_allowed"] is False
        assert decision["claim_boundary"]["publication_readiness_claim_allowed"] is False
        if decision["gap_class"] in NON_TYPED_BLOCKER_GAP_CLASSES:
            assert decision["typed_blocker_eligibility"] is False


def test_policy_forbids_contract_or_test_green_as_completion_claims() -> None:
    policy = _json(POLICY_PATH)

    assert FORBIDDEN_CLAIMS <= set(policy["forbidden_claim_terms"])
    assert {
        "docs_updated",
        "contract_landed",
        "focused_tests_passed",
        "evidence_gap_policy_landed",
        "evidence_tail_recorded",
    } <= set(policy["forbidden_completion_interpretations"])
