from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def test_default_publication_critique_policy_exposes_weight_and_action_contract() -> None:
    from med_autoscience.policies.publication_critique import (
        DEFAULT_PUBLICATION_CRITIQUE_POLICY,
        build_revision_action_contract,
        build_weight_contract,
    )

    assert DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"] == "medical_publication_critique_v1"
    assert build_weight_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY) == {
        "clinical_significance": 25,
        "evidence_strength": 30,
        "novelty_positioning": 20,
        "medical_journal_prose_quality": 15,
        "human_review_readiness": 10,
    }
    assert build_revision_action_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY) == (
        "tighten_clinical_framing",
        "close_evidence_gap",
        "tighten_novelty_framing",
        "refresh_review_surface",
        "stabilize_submission_bundle",
    )
    assert "revision_items" in [
        item["field"]
        for item in DEFAULT_PUBLICATION_CRITIQUE_POLICY["required_outputs"]
    ]
    assert "style_diagnosis" in [
        item["field"]
        for item in DEFAULT_PUBLICATION_CRITIQUE_POLICY["required_outputs"]
    ]
    style_dimension = next(
        item
        for item in DEFAULT_PUBLICATION_CRITIQUE_POLICY["weighted_dimensions"]
        if item["field"] == "medical_journal_prose_quality"
    )
    assert "medical journal prose" in style_dimension["focus"]


def test_publication_critique_policy_exposes_target_journal_writing_layer() -> None:
    from med_autoscience.policies.publication_critique import (
        DEFAULT_PUBLICATION_CRITIQUE_POLICY,
        build_ai_reviewer_operating_system_contract,
    )

    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)

    assert contract["target_journal_writing_layer"] == {
        "surface": "target_journal_writing_layer",
        "role": "ai_reviewer_quality_context",
        "mechanical_projection_can_authorize_quality": False,
        "required_fields": [
            "target_journal_family",
            "near_neighbor_style_corpus",
            "section_plan",
            "claim_to_paragraph_map",
            "display_to_claim_map",
            "restrained_language_strategy",
        ],
        "near_neighbor_style_corpus": {
            "role": "style_and_structure_calibration_only",
            "can_supply_claims": False,
            "can_override_evidence_ledger": False,
        },
        "restrained_language_strategy": {
            "requires_claim_evidence_alignment": True,
            "forbids_overstatement_from_style_examples": True,
        },
    }
