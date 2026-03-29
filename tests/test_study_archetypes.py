from __future__ import annotations

import importlib


def test_default_study_archetypes_include_classifier_and_llm_agent_routes() -> None:
    module = importlib.import_module("med_autoscience.policies.study_archetypes")

    archetypes = module.resolve_archetypes()

    assert [item.archetype_id for item in archetypes] == [
        "clinical_classifier",
        "llm_agent_clinical_task",
    ]
    assert "decision-curve / threshold / net-benefit analysis" in archetypes[0].expected_paper_package
    assert "prompt / reasoning / agent-architecture variants" in archetypes[1].expected_paper_package


def test_render_study_archetype_block_surfaces_paper_package_expectations() -> None:
    module = importlib.import_module("med_autoscience.policies.study_archetypes")

    block = module.render_archetype_block(archetype_ids=("clinical_classifier", "llm_agent_clinical_task"))

    assert "## Preferred study archetypes" in block
    assert "### Clinical classifier / risk stratification" in block
    assert "### LLM agent for a clinical task" in block
    assert "subgroup comparison" in block
    assert "error taxonomy or failure-mode review" in block
