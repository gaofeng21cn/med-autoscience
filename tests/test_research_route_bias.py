from __future__ import annotations

import importlib


def test_route_bias_markdown_contract_and_stage_render(tmp_path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.policies.research_route_bias")
    openers = "\n".join(f"- {stage_id}: {stage_id} opener" for stage_id in module.SUPPORTED_STAGE_IDS)
    markdown_path = tmp_path / "research_route_bias_policy.md"
    markdown_path.write_text(
        f"""# Research Route Bias Policy

## high_plasticity_medical
Title: Synthetic Route Bias
### Preferred Route Order
- preferred route
### Candidate Scoring Dimensions
- scoring dimension
### Downrank Patterns
- downrank pattern
### Public Data Rules
- public data rule
### Stage Openers
{openers}
### Stage Questions
- scout: scout question
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "RESEARCH_ROUTE_BIAS_MARKDOWN_PATH", markdown_path)
    policy = module.get_policy()
    assert policy.title == "Synthetic Route Bias"
    assert policy.preferred_route_order == ("preferred route",)
    assert policy.candidate_scoring_dimensions == ("scoring dimension",)
    assert policy.downrank_patterns == ("downrank pattern",)
    assert policy.public_data_rules == ("public data rule",)
    assert policy.stage_openers == {stage_id: f"{stage_id} opener" for stage_id in module.SUPPORTED_STAGE_IDS}
    assert policy.stage_questions == {"scout": ("scout question",)}
    block = module.render_policy_block(stage_id="scout")
    assert all(text in block for text in ("scout opener", "preferred route", "scout question"))
    assert "decision opener" not in block

    monkeypatch.undo()
    default = module.get_policy()
    assert default.policy_id == module.DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID
    assert default.title
    assert default.preferred_route_order
    assert default.candidate_scoring_dimensions
    assert default.downrank_patterns
    assert default.public_data_rules
    assert set(default.stage_openers) == set(module.SUPPORTED_STAGE_IDS)
