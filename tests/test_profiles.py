from __future__ import annotations

import importlib
from pathlib import Path


def test_load_profile_parses_expected_fields(tmp_path: Path) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤"',
                'runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime/quests"',
                'studies_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/studies"',
                'portfolio_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/portfolio"',
                'deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        profiles = importlib.import_module("med_autoscience.profiles")
    except ModuleNotFoundError:
        profiles = None

    assert profiles is not None
    load_profile = getattr(profiles, "load_profile", None)
    assert callable(load_profile)

    profile = load_profile(profile_path)

    assert profile.name == "nfpitnet"
    assert profile.workspace_root == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert profile.default_publication_profile == "general_medical_journal"
    assert profile.default_citation_style == "AMA"
    assert profile.enable_medical_overlay is True
    assert profile.medical_overlay_scope == "workspace"
    assert profile.medical_overlay_skills == ("scout", "idea", "decision", "write", "finalize")
    assert profile.research_route_bias_policy == "high_plasticity_medical"
    assert profile.preferred_study_archetypes == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )


def test_load_profile_uses_default_medical_overlay_settings_when_missing(tmp_path: Path) -> None:
    profile_path = tmp_path / "minimal.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "minimal"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'deepscientist_runtime_root = "/tmp/workspace/ops/deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert profile.enable_medical_overlay is True
    assert profile.medical_overlay_scope == "global"
    assert profile.medical_overlay_skills == ("scout", "idea", "decision", "write", "finalize")
    assert profile.research_route_bias_policy == "high_plasticity_medical"
    assert profile.preferred_study_archetypes == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )
