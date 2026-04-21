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
        "evidence_strength": 35,
        "novelty_positioning": 20,
        "human_review_readiness": 20,
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
