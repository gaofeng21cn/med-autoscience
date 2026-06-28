from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "contracts" / "evidence-gap-decision-policy.json"
ABI_PATH = REPO_ROOT / "contracts" / "evidence-gap-consumption-abi.json"
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
    assert policy["consumption_abi_ref"] == "contracts/evidence-gap-consumption-abi.json"
    assert schema["$id"] == policy["schema_ref"]
    assert schema["properties"]["surface_kind"]["const"] == "mas_evidence_gap_decision"
    assert set(schema["properties"]["gap_class"]["enum"]) == GAP_CLASSES
    assert "live runtime ready" not in policy["purpose"].lower()
    assert "paper progress" in policy["machine_boundary"]
    assert "does not declare" in policy["machine_boundary"]


def test_evidence_gap_consumption_abi_declares_opl_workbench_mcp_surface() -> None:
    from med_autoscience.evidence_gap_abi import build_evidence_gap_consumption_abi

    abi = _json(ABI_PATH)

    assert abi == build_evidence_gap_consumption_abi()
    assert abi["surface_kind"] == "mas_evidence_gap_consumption_abi"
    assert abi["missing_evidence_policy"] == "classify_with_evidence_gap_decision_then_progress_first"
    assert set(abi["components"]) == {
        "EvidenceCondition",
        "EvidenceBudget",
        "HardGateRegistry",
        "SoftGapLedger",
        "AssumptionLedger",
        "WorkbenchGapView",
    }
    assert abi["components"]["HardGateRegistry"]["typed_blocker_countable_gap_classes"] == [
        "authority_gate",
        "human_gate",
    ]
    assert set(abi["components"]["HardGateRegistry"]["forbidden_gap_classes_for_typed_blocker_count"]) == (
        NON_TYPED_BLOCKER_GAP_CLASSES
    )
    assert abi["components"]["EvidenceBudget"]["default_policy"] == (
        "continue_current_action_for_nonblocking_gap_classes"
    )
    assert set(abi["consumer_refs"]) >= {
        "study_progress",
        "domain_diagnostic_report",
        "domain_action_materializer",
        "opl_stage_control_plane",
        "workbench",
        "mcp_action_catalog",
    }
    assert abi["legacy_policy_replacement"]["retired_policy"] == "missing evidence -> typed_blocker"


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


def test_ordinary_missing_evidence_fallback_strings_are_not_resurrected() -> None:
    forbidden = {
        "return_to_ai_executor_for_minimum_forward_delta_or_typed_blocker",
        "typed_blocker:bounded_search_evidence_ref_missing",
        "blocker_on_missing_evidence",
    }
    scanned_roots = [
        REPO_ROOT / "contracts" / "stage_control_plane.json",
        REPO_ROOT / "src" / "med_autoscience" / "opl_domain_pack" / "stage_throughput_contracts.py",
        REPO_ROOT / "src" / "med_autoscience" / "controllers" / "owner_callable_action_policy.py",
    ]

    for path in scanned_roots:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{token} resurrected in {path}"


def test_stage_control_plane_static_contract_carries_evidence_gap_abi_ref() -> None:
    stage_plane = _json(REPO_ROOT / "contracts" / "stage_control_plane.json")
    abi = _json(ABI_PATH)
    expected_ref = {
        "surface_kind": abi["surface_kind"],
        "version": abi["version"],
        "contract_ref": "contracts/evidence-gap-consumption-abi.json",
        "decision_policy_ref": abi["decision_policy_ref"],
        "decision_schema_ref": abi["decision_schema_ref"],
        "missing_evidence_policy": abi["missing_evidence_policy"],
        "component_refs": list(abi["components"]),
        "projection_only": True,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
    }

    stages = stage_plane["stages"]
    assert stages
    for stage in stages:
        human_gate = stage["stage_contract"]["human_gate_progress_evidence"]
        assert human_gate["missing_evidence_policy"] == (
            "classify_with_evidence_gap_decision_then_progress_first"
        )
        assert human_gate["evidence_gap_consumption_abi"] == expected_ref
