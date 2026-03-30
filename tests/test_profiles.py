from __future__ import annotations

import importlib
from pathlib import Path

PROFILE_LINES = [
    'name = "nfpitnet"',
    'workspace_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤"',
    'runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime/quests"',
    'studies_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/studies"',
    'portfolio_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/portfolio"',
    'deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime"',
    'deepscientist_repo_root = "/Users/gaofeng/workspace/DeepScientist"',
    'default_publication_profile = "general_medical_journal"',
    'default_citation_style = "AMA"',
    "enable_medical_overlay = true",
    'medical_overlay_scope = "workspace"',
    'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
    'research_route_bias_policy = "high_plasticity_medical"',
    'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
    "",
    "[[default_submission_targets]]",
    'publication_profile = "frontiers_family_harvard"',
    "primary = true",
    "package_required = true",
    'story_surface = "general_medical_journal"',
]


def write_full_profile(path: Path) -> None:
    path.write_text("\n".join(PROFILE_LINES) + "\n", encoding="utf-8")


def test_load_profile_parses_expected_fields(tmp_path: Path) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_full_profile(profile_path)

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
    assert profile.deepscientist_repo_root == Path("/Users/gaofeng/workspace/DeepScientist")
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
    assert len(profile.default_submission_targets) == 1
    assert profile.default_submission_targets[0]["publication_profile"] == "frontiers_family_harvard"
    assert profile.default_submission_targets[0]["primary"] is True


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

    assert profile.deepscientist_repo_root is None
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


def test_profile_to_dict_exposes_machine_readable_contract(tmp_path: Path) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_full_profile(profile_path)

    try:
        profiles = importlib.import_module("med_autoscience.profiles")
    except ModuleNotFoundError:
        profiles = None

    assert profiles is not None
    load_profile = getattr(profiles, "load_profile", None)
    profile_to_dict = getattr(profiles, "profile_to_dict", None)
    assert callable(load_profile)
    assert callable(profile_to_dict)

    profile = load_profile(profile_path)
    contract = profile_to_dict(profile)

    assert contract["name"] == profile.name
    assert contract["workspace_root"] == str(profile.workspace_root)
    assert contract["runtime_root"] == str(profile.runtime_root)
    assert contract["studies_root"] == str(profile.studies_root)
    assert contract["portfolio_root"] == str(profile.portfolio_root)
    assert contract["deepscientist_runtime_root"] == str(profile.deepscientist_runtime_root)
    assert contract["deepscientist_repo_root"] == str(profile.deepscientist_repo_root)

    publication = contract["publication"]
    assert publication["default_publication_profile"] == profile.default_publication_profile
    assert publication["default_citation_style"] == profile.default_citation_style
    assert isinstance(publication["default_submission_targets"], list)
    assert publication["default_submission_targets"][0]["publication_profile"] == "frontiers_family_harvard"

    overlay = contract["overlay"]
    assert overlay["enable_medical_overlay"] is True
    assert overlay["medical_overlay_scope"] == profile.medical_overlay_scope
    assert overlay["medical_overlay_skills"] == list(profile.medical_overlay_skills)

    policy = contract["policy"]
    assert policy["research_route_bias_policy"] == profile.research_route_bias_policy

    archetype = contract["archetype"]
    assert archetype["preferred_study_archetypes"] == list(profile.preferred_study_archetypes)
