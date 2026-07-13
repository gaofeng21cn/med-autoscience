from __future__ import annotations

import importlib


def test_study_archetype_markdown_contract_and_render(tmp_path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.policies.study_archetypes")
    markdown_path = tmp_path / "study_archetypes.md"
    markdown_path.write_text(
        """# Study Archetypes

## clinical_classifier
Title: Synthetic Classifier
### When To Prefer
- fit signal
### Expected Paper Package
- evidence package
### Public Data Roles
- public data role
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "STUDY_ARCHETYPES_MARKDOWN_PATH", markdown_path)
    archetype = module.get_archetype("clinical_classifier")
    assert archetype.title == "Synthetic Classifier"
    assert archetype.when_to_prefer == ("fit signal",)
    assert archetype.expected_paper_package == ("evidence package",)
    assert archetype.public_data_roles == ("public data role",)

    block = module.render_archetype_block(("clinical_classifier",))
    assert all(text in block for text in ("Synthetic Classifier", "evidence package", "public data role"))


def test_default_and_survey_archetypes_keep_structural_contract() -> None:
    module = importlib.import_module("med_autoscience.policies.study_archetypes")

    assert tuple(item.archetype_id for item in module.resolve_archetypes()) == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
        "computational_biomechanics",
    )

    survey = module.get_archetype("survey_trend_analysis")
    assert survey.archetype_id == "survey_trend_analysis"
    assert all(
        (
            survey.title,
            survey.when_to_prefer,
            survey.expected_paper_package,
            survey.public_data_roles,
        )
    )

    computational = module.get_archetype("computational_biomechanics")
    assert computational.archetype_id == "computational_biomechanics"
    assert "模型" in " ".join(computational.expected_paper_package)
