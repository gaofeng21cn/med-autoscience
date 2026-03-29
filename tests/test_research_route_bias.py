from __future__ import annotations

import importlib


def test_default_route_bias_policy_exposes_expected_contract() -> None:
    module = importlib.import_module("med_autoscience.policies.research_route_bias")

    policy = module.get_policy()

    assert policy.policy_id == "high_plasticity_medical"
    assert policy.preferred_route_order[0] == (
        "supervised prediction or risk-stratification routes with clinically interpretable downstream analyses"
    )
    assert "clinical significance if the result is positive" in policy.candidate_scoring_dimensions
    assert "the main value would hinge on one fixed clinical factor being significant" in policy.downrank_patterns
    assert "Do not add public data only as decorative workload." in policy.public_data_rules


def test_render_route_bias_block_is_stage_specific_and_publication_facing() -> None:
    module = importlib.import_module("med_autoscience.policies.research_route_bias")

    scout_block = module.render_policy_block(stage_id="scout")
    decision_block = module.render_policy_block(stage_id="decision")

    assert "## Medical publication route bias" in scout_block
    assert "do not treat all reasonable frames as equally good scouting outputs" in scout_block
    assert "clinically meaningful classifier / risk-stratification / utility package" in decision_block
    assert "Default priority order" in scout_block
    assert "Candidate scoring dimensions" in scout_block
    assert "Down-rank routes with these failure patterns" in scout_block

