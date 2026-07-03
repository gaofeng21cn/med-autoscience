from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.research_integrity.stage_hooks import (
    FORBIDDEN_AUTHORITY_FLAGS,
    build_review_publication_gate_stage_hook_payload,
)


def test_review_publication_gate_stage_hook_builds_reference_verification_gate_input() -> None:
    payload = build_review_publication_gate_stage_hook_payload(
        payload={
            "stage_id": "publication_supervision",
            "stage_event": "review_gate_entered",
            "stage_hook_ref": "stage-hook:publication_supervision:review_gate",
            "source_refs": ["paper/references.bib"],
            "references": [{"id": "smith2024", "doi": "10.1000/example", "title": "Example Trial"}],
            "provider_evidence": [
                {
                    "provider": "crossref",
                    "reference_id": "smith2024",
                    "matched_identifiers": {"doi": "10.1000/example"},
                    "metadata": {"title": "Example Trial", "year": "2024"},
                }
            ],
            "claim": {
                "claim_id": "C1",
                "citation_refs": [{"ref": "ref:smith2024"}],
                "evidence_refs": ["analysis/results.json#/C1"],
                "support_grade": "direct_support",
            },
            "manuscript": {
                "results": {
                    "numeric_facts": [
                        {
                            "fact_id": "auc",
                            "reported_value": "0.71",
                            "unit": "AUROC",
                        }
                    ]
                }
            },
            "display_facts": [{"fact_id": "auc", "reported_value": "0.71", "unit": "AUROC"}],
        }
    )

    gate_bundle = payload["gate_input_bundle"]

    assert payload["surface_kind"] == "research_integrity_review_publication_gate_stage_hook"
    assert payload["hook_role"] == "mandatory_review_publication_gate_input"
    assert payload["triggered_action"] == "research-integrity-reference-verification"
    assert "reference_list_entered" in payload["trigger_points"]
    assert "publication_gate_entered" in payload["trigger_points"]
    assert payload["stage_context"] == {
        "stage_id": "publication_supervision",
        "stage_event": "review_gate_entered",
        "stage_hook_ref": "stage-hook:publication_supervision:review_gate",
    }
    assert gate_bundle["surface_kind"] == "research_integrity_gate_input_bundle"
    assert payload["surfaces"]["research_integrity_reference_verification"]["surfaces"][
        "research_integrity_gate_input_bundle"
    ] == gate_bundle
    assert set(payload["required_gate_input_surfaces"]) == {
        "reference_verification_attestations",
        "claim_citation_support_matrix_v2",
        "manuscript_consistency_meta_review",
    }
    assert gate_bundle["surfaces"]["manuscript_consistency_meta_review"]["status"] == "clear"
    assert all(payload["authority_boundary"][flag] is False for flag in FORBIDDEN_AUTHORITY_FLAGS)

    obligation = payload["stage_obligation"]
    assert obligation["obligation_level"] == "mandatory"
    assert obligation["target_stage_ids"] == [
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    assert obligation["mandatory_gate_input"] is True
    assert obligation["live_owner_consumption_claimed"] is False
    assert obligation["triggered_action"] == "research-integrity-reference-verification"
    assert payload["target_stage_ids"] == obligation["target_stage_ids"]
    assert payload["triggered_opl_connect_provider_lookup_contract"] == obligation[
        "triggered_opl_connect_provider_lookup_contract"
    ]
    assert payload["triggered_opl_connect_provider_lookup_contract"]["owner"] == (
        "OPL connector substrate"
    )
    assert payload["triggered_opl_connect_provider_lookup_contract"][
        "mandatory_gate_input_only"
    ] is True
    assert payload["triggered_opl_connect_provider_lookup_contract"][
        "live_owner_consumption_claimed"
    ] is False


def test_stage_control_plane_declares_mandatory_research_integrity_stage_hook_obligation() -> None:
    research_integrity_contract = json.loads(
        (
            Path(__file__).resolve().parents[1] / "contracts/research-integrity-layer.json"
        ).read_text()
    )
    contract = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/stage_control_plane.json").read_text()
    )
    stages = {stage["stage_id"]: stage for stage in contract["stages"]}
    contract_obligation = research_integrity_contract["stage_hook_obligation"]

    assert contract_obligation["surface_kind"] == "research_integrity_stage_hook_obligation"
    assert contract_obligation["obligation_level"] == "mandatory"
    assert contract_obligation["target_stage_ids"] == [
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    assert contract_obligation["live_owner_consumption_claimed"] is False

    for stage_id in ("review_and_quality_gate", "finalize_and_publication_handoff"):
        obligations = stages[stage_id]["mandatory_stage_hook_obligations"]
        obligation = next(
            item
            for item in obligations
            if item["hook_id"] == "research-integrity-review-publication-gate-stage-hook"
        )

        assert obligation["surface_kind"] == "research_integrity_stage_hook_obligation"
        assert obligation["obligation_level"] == "mandatory"
        assert obligation["target_stage_ids"] == [
            "review_and_quality_gate",
            "finalize_and_publication_handoff",
        ]
        assert obligation["triggered_action"] == "research-integrity-reference-verification"
        assert obligation["mandatory_gate_input"] is True
        assert obligation["live_owner_consumption_claimed"] is False
        assert obligation["authority_boundary"]["can_write_publication_eval_latest"] is False
        assert obligation["authority_boundary"]["can_write_controller_decisions"] is False
        assert obligation["authority_boundary"]["can_mutate_current_package"] is False
        assert obligation["authority_boundary"]["can_write_runtime_queue_or_provider_attempt"] is False
