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
    "live_runtime_ready",
    "paper_progress",
    "publication_ready",
    "submission_ready",
    "production_ready",
    "provider_running",
    "owner_receipt_closed",
}


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _policy() -> dict[str, object]:
    return _json(POLICY_PATH)


def _schema() -> dict[str, object]:
    return _json(SCHEMA_PATH)


def _examples() -> dict[str, object]:
    return _json(EXAMPLES_PATH)


def _validate_example_against_schema(
    example: dict[str, object],
    schema: dict[str, object],
) -> None:
    required = schema["required"]
    properties = schema["properties"]
    assert isinstance(required, list)
    assert isinstance(properties, dict)

    for field in required:
        assert field in example, field

    for field, value in example.items():
        definition = properties.get(field)
        assert definition is not None, field
        assert isinstance(definition, dict)
        if "const" in definition:
            assert value == definition["const"], field
        if "enum" in definition:
            assert value in definition["enum"], field
        expected_type = definition.get("type")
        if expected_type == "string":
            assert isinstance(value, str) and value, field
        elif expected_type == "array":
            assert isinstance(value, list), field
        elif expected_type == "object":
            assert isinstance(value, dict), field
        elif expected_type == "boolean":
            assert isinstance(value, bool), field


def test_evidence_gap_decision_policy_declares_schema_and_boundary() -> None:
    policy = _policy()
    schema = _schema()

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
    policy = _policy()
    gap_classes = policy["gap_classes"]
    materialization = policy["typed_blocker_materialization_policy"]

    assert set(gap_classes) == GAP_CLASSES
    assert materialization["typed_blocker_countable_gap_classes"] == [
        "authority_gate",
        "human_gate",
    ]
    assert materialization["allowed_materialization_reasons"] == [
        "authority_gate",
        "human_gate",
        "forbidden_write_boundary",
        "stop_loss_materialized",
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

    assert gap_classes["evidence_tail"]["blocks_completion_or_readiness_claim"] is True
    assert gap_classes["evidence_tail"]["typed_blocker_countable"] is False


def test_evidence_gap_decision_examples_cover_every_gap_class_and_match_schema() -> None:
    schema = _schema()
    examples = _examples()

    assert examples["surface_kind"] == "mas_evidence_gap_decision_examples"
    assert examples["schema_ref"] == "contracts/schemas/evidence-gap-decision.schema.json"
    decisions = examples["examples"]
    assert isinstance(decisions, list)
    assert {decision["gap_class"] for decision in decisions} == GAP_CLASSES

    for decision in decisions:
        assert isinstance(decision, dict)
        _validate_example_against_schema(decision, schema)
        assert decision["current_owner_delta_ref"]
        assert decision["evidence_refs"]
        assert decision["claim_boundary"] == {
            "paper_progress_claim_allowed": False,
            "live_runtime_readiness_claim_allowed": False,
            "publication_readiness_claim_allowed": False,
            "production_readiness_claim_allowed": False,
        }


def test_soft_gap_examples_never_enter_typed_blocker_count() -> None:
    decisions = {
        decision["gap_class"]: decision
        for decision in _examples()["examples"]
    }

    for gap_class in NON_TYPED_BLOCKER_GAP_CLASSES:
        decision = decisions[gap_class]
        typed_blocker_policy = decision["typed_blocker_policy"]
        assert decision["typed_blocker_eligibility"] is False, gap_class
        assert typed_blocker_policy["typed_blocker_countable"] is False, gap_class
        assert typed_blocker_policy["materialization_allowed"] is False, gap_class
        assert typed_blocker_policy["typed_blocker_ref"] is None, gap_class

    assert decisions["proceed_with_assumption"]["assumption_ref"]
    assert decisions["soft_quality_gap"]["followup_work_order_ref"]
    assert decisions["observability_backlog"]["followup_work_order_ref"]
    assert decisions["evidence_tail"]["blocks_completion_claim"] is True


def test_evidence_gap_policy_forbids_readiness_and_progress_claims() -> None:
    policy = _policy()
    examples = _examples()

    assert FORBIDDEN_CLAIMS <= set(policy["forbidden_claim_terms"])
    assert {
        "docs_updated",
        "contract_landed",
        "focused_tests_passed",
        "evidence_gap_policy_landed",
        "evidence_tail_recorded",
    } <= set(policy["forbidden_completion_interpretations"])

    for decision in examples["examples"]:
        assert FORBIDDEN_CLAIMS <= set(decision["forbidden_claim_terms"])
        assert decision["completion_claim_allowed"] is False
