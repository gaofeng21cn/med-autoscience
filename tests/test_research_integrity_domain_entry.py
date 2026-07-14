from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_INTEGRITY_PRIVATE_ACTION_IDS = {
    "research_integrity_gate_input",
    "research_integrity_reference_verification",
    "research_integrity_review_publication_gate_stage_hook",
}


def _read_json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_research_integrity_is_bound_to_stage_policy_not_private_actions() -> None:
    catalog = _read_json("contracts/action_catalog.json")
    manifest = _read_json("agent/stages/manifest.json")
    contract = _read_json("contracts/research-integrity-layer.json")
    action_ids = {action["action_id"] for action in catalog["actions"]}

    assert RESEARCH_INTEGRITY_PRIVATE_ACTION_IDS.isdisjoint(action_ids)
    assert contract["stage_hook_obligation"]["stage_action_refs"] == [
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    assert contract["stage_launch_required_input"]["stage_action_refs"] == [
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    stages = {stage["stage_id"]: stage for stage in manifest["stages"]}
    for stage_id in contract["stage_hook_obligation"]["stage_action_refs"]:
        capability_refs = {
            ref["ref"]
            for ref in stages[stage_id]["tool_affordance_boundary"]["capability_refs"]
        }
        assert "publication_quality_and_integrity_review_support" in capability_refs


def test_research_integrity_contract_points_to_pure_builders_only() -> None:
    contract = _read_json("contracts/research-integrity-layer.json")
    implementation = contract["implementation_contract"]
    serialized = json.dumps(contract, ensure_ascii=True, sort_keys=True)

    assert implementation["pure_builder_surfaces"] == [
        "med_autoscience.research_integrity.reference_authenticity",
        "med_autoscience.research_integrity.claim_citation_support_v2",
        "med_autoscience.research_integrity.manuscript_consistency",
        "med_autoscience.research_integrity.gate_bundle",
        "med_autoscience.research_integrity.provider_lookup",
        "med_autoscience.research_integrity.reference_verification",
        "med_autoscience.adapters.literature.opl_connect_receipts",
        "med_autoscience.research_integrity.stage_hooks",
    ]
    assert "MedAutoScienceDomainEntry" not in serialized
    assert "src/med_autoscience/domain_entry.py" not in serialized
    assert "action_catalog_descriptor" not in serialized
    assert "research-integrity-gate-input payload" not in serialized
