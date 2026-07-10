from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]
GAP_CLASSES = {
    "authority_gate",
    "human_gate",
    "proceed_with_assumption",
    "soft_quality_gap",
    "observability_backlog",
    "evidence_tail",
}
SOFT_GAPS = GAP_CLASSES - {"authority_gate", "human_gate"}
FORBIDDEN_CLAIMS = {
    "owner_receipt_closed",
    "paper_progress",
    "publication_ready",
    "submission_ready",
    "live_runtime_ready",
    "production_ready",
    "provider_running",
}


def _json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_evidence_gap_policy_schema_and_classes_fail_closed() -> None:
    policy = _json("contracts/evidence-gap-decision-policy.json")
    schema = _json("contracts/schemas/evidence-gap-decision.schema.json")

    assert policy["schema_ref"] == schema["$id"]
    assert policy["consumption_abi_ref"] == "contracts/evidence-gap-consumption-abi.json"
    assert set(schema["properties"]["gap_class"]["enum"]) == GAP_CLASSES
    assert set(policy["gap_classes"]) == GAP_CLASSES
    assert FORBIDDEN_CLAIMS <= set(policy["forbidden_claim_terms"])
    for gap_class, definition in policy["gap_classes"].items():
        hard = gap_class in {"authority_gate", "human_gate"}
        assert definition["typed_blocker_countable"] is hard
        assert definition["blocks_current_owner_action"] is hard
        assert definition["blocks_completion_or_readiness_claim"] is True


def test_evidence_gap_consumption_abi_matches_runtime_builder() -> None:
    from med_autoscience.evidence_gap_abi import build_evidence_gap_consumption_abi

    abi = _json("contracts/evidence-gap-consumption-abi.json")

    assert abi == build_evidence_gap_consumption_abi()
    registry = abi["components"]["HardGateRegistry"]
    assert registry["typed_blocker_countable_gap_classes"] == [
        "authority_gate",
        "human_gate",
    ]
    assert set(registry["forbidden_gap_classes_for_typed_blocker_count"]) == SOFT_GAPS
    assert set(abi["consumer_refs"]) >= {
        "study_progress",
        "domain_action_materializer",
        "opl_stage_control_plane",
        "workbench",
        "mcp_action_catalog",
    }


def test_evidence_gap_examples_cover_schema_and_forbid_high_order_claims() -> None:
    examples = _json("contracts/evidence-gap-decision-examples.json")
    schema = _json("contracts/schemas/evidence-gap-decision.schema.json")
    decisions = examples["examples"]

    assert {decision["gap_class"] for decision in decisions} == GAP_CLASSES
    for decision in decisions:
        assert set(schema["required"]) <= set(decision)
        assert FORBIDDEN_CLAIMS <= set(decision["forbidden_claims"])
        assert decision["claim_boundary"]["paper_progress_claim_allowed"] is False
        assert decision["claim_boundary"]["publication_readiness_claim_allowed"] is False
        if decision["gap_class"] in SOFT_GAPS:
            assert decision["typed_blocker_eligibility"] is False


def test_stage_control_plane_references_projection_only_evidence_gap_abi() -> None:
    stage_plane = _json("contracts/stage_control_plane.json")

    assert stage_plane["stages"]
    for stage in stage_plane["stages"]:
        gap_abi = stage["stage_contract"]["human_gate_progress_evidence"][
            "evidence_gap_consumption_abi"
        ]
        assert gap_abi["contract_ref"] == "contracts/evidence-gap-consumption-abi.json"
        assert gap_abi["projection_only"] is True
        assert gap_abi["can_write_domain_truth"] is False
        assert gap_abi["can_authorize_publication_quality"] is False
        assert gap_abi["can_authorize_submission_readiness"] is False
