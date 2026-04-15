from __future__ import annotations

import importlib


def test_default_study_archetypes_include_classifier_and_llm_agent_routes() -> None:
    module = importlib.import_module("med_autoscience.policies.study_archetypes")

    archetypes = module.resolve_archetypes()

    assert [item.archetype_id for item in archetypes] == [
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    ]
    assert "decision-curve / threshold / net-benefit analysis" in archetypes[0].expected_paper_package
    assert "cluster stability or reproducibility assessment" in archetypes[1].expected_paper_package
    assert "transportability / recalibration / model-updating analysis" in archetypes[2].expected_paper_package
    assert "rule-in / rule-out / gray-zone yield analysis" in archetypes[3].expected_paper_package
    assert "prompt / reasoning / agent-architecture variants" in archetypes[4].expected_paper_package
    assert "functional / pathway / regulator-level interpretation" in archetypes[5].expected_paper_package


def test_render_study_archetype_block_surfaces_paper_package_expectations() -> None:
    module = importlib.import_module("med_autoscience.policies.study_archetypes")

    block = module.render_archetype_block(
        archetype_ids=(
            "clinical_classifier",
            "clinical_subtype_reconstruction",
            "external_validation_model_update",
            "gray_zone_triage",
            "llm_agent_clinical_task",
            "mechanistic_sidecar_extension",
        )
    )

    assert "## Preferred study archetypes" in block
    assert "### Clinical classifier / risk stratification" in block
    assert "### Clinical subtype reconstruction" in block
    assert "### External validation / model update" in block
    assert "### Gray-zone triage / reflex-testing support" in block
    assert "### LLM agent for a clinical task" in block
    assert "### Mechanistic sidecar extension" in block
    assert "subgroup comparison" in block
    assert "error taxonomy or failure-mode review" in block
    assert "cluster stability or reproducibility assessment" in block
    assert "transportability / recalibration / model-updating analysis" in block
    assert "functional / pathway / regulator-level interpretation" in block


def test_resolve_explicit_survey_trend_analysis_archetype() -> None:
    module = importlib.import_module("med_autoscience.policies.study_archetypes")

    archetypes = module.resolve_archetypes(("survey_trend_analysis",))

    assert [item.archetype_id for item in archetypes] == ["survey_trend_analysis"]
    assert archetypes[0].title == "Survey trend / guideline correspondence"
    assert "trend comparison across timepoints" in archetypes[0].expected_paper_package
    assert "practice or preference drift" in archetypes[0].public_data_roles
