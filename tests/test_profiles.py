from __future__ import annotations

import importlib
from pathlib import Path
import pytest

PROFILE_LINES = [
    'name = "nfpitnet"',
    'workspace_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤"',
    'runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist/runtime/quests"',
    'studies_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/studies"',
    'portfolio_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/portfolio"',
    'med_deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist/runtime"',
    'med_deepscientist_repo_root = "/Users/gaofeng/workspace/med-deepscientist"',
    'hermes_agent_repo_root = "/Users/gaofeng/workspace/_external/hermes-agent"',
    'hermes_home_root = "~/.hermes"',
    'default_publication_profile = "general_medical_journal"',
    'default_citation_style = "AMA"',
    "enable_medical_overlay = true",
    'medical_overlay_scope = "workspace"',
    'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
    'medical_overlay_bootstrap_mode = "ensure_ready"',
    'research_route_bias_policy = "high_plasticity_medical"',
    'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
    'default_startup_anchor_policy = "scout_first_for_continue_existing_state"',
    'legacy_code_execution_policy = "forbid_without_user_approval"',
    'public_data_discovery_policy = "required_for_scout_route_selection"',
    'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]',
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
    assert profile.med_deepscientist_repo_root == Path("/Users/gaofeng/workspace/med-deepscientist")
    assert profile.hermes_agent_repo_root == Path("/Users/gaofeng/workspace/_external/hermes-agent")
    assert profile.hermes_home_root == Path.home() / ".hermes"
    assert profile.managed_runtime_backend_id == "hermes"
    assert profile.default_publication_profile == "general_medical_journal"
    assert profile.default_citation_style == "AMA"
    assert profile.enable_medical_overlay is True
    assert profile.medical_overlay_scope == "workspace"
    assert profile.medical_overlay_skills == ("scout", "idea", "decision", "write", "finalize")
    assert profile.medical_overlay_bootstrap_mode == "ensure_ready"
    assert profile.research_route_bias_policy == "high_plasticity_medical"
    assert profile.preferred_study_archetypes == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )
    assert profile.default_startup_anchor_policy == "scout_first_for_continue_existing_state"
    assert profile.legacy_code_execution_policy == "forbid_without_user_approval"
    assert profile.public_data_discovery_policy == "required_for_scout_route_selection"
    assert profile.startup_boundary_requirements == ("paper_framing", "journal_shortlist", "evidence_package")
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
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert profile.med_deepscientist_repo_root is None
    assert profile.hermes_agent_repo_root is None
    assert profile.hermes_home_root == Path.home() / ".hermes"
    assert profile.managed_runtime_backend_id == "hermes"
    assert profile.enable_medical_overlay is True
    assert profile.medical_overlay_scope == "global"
    assert profile.medical_overlay_skills == (
        "intake-audit",
        "scout",
        "baseline",
        "idea",
        "decision",
        "experiment",
        "analysis-campaign",
        "figure-polish",
        "write",
        "review",
        "rebuttal",
        "finalize",
    )
    assert profile.medical_overlay_bootstrap_mode == "ensure_ready"
    assert profile.research_route_bias_policy == "high_plasticity_medical"
    assert profile.preferred_study_archetypes == (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "gray_zone_triage",
        "llm_agent_clinical_task",
        "mechanistic_sidecar_extension",
    )
    assert profile.default_startup_anchor_policy == "scout_first_for_continue_existing_state"
    assert profile.legacy_code_execution_policy == "forbid_without_user_approval"
    assert profile.public_data_discovery_policy == "required_for_scout_route_selection"
    assert profile.startup_boundary_requirements == ("paper_framing", "journal_shortlist", "evidence_package")


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
    assert contract["med_deepscientist_runtime_root"] == str(profile.med_deepscientist_runtime_root)
    assert contract["med_deepscientist_repo_root"] == str(profile.med_deepscientist_repo_root)
    assert contract["hermes_agent_repo_root"] == str(profile.hermes_agent_repo_root)
    assert contract["hermes_home_root"] == str(profile.hermes_home_root)
    assert contract["managed_runtime_backend_id"] == profile.managed_runtime_backend_id

    publication = contract["publication"]
    assert publication["default_publication_profile"] == profile.default_publication_profile
    assert publication["default_citation_style"] == profile.default_citation_style
    assert isinstance(publication["default_submission_targets"], list)
    assert publication["default_submission_targets"][0]["publication_profile"] == "frontiers_family_harvard"

    overlay = contract["overlay"]
    assert overlay["enable_medical_overlay"] is True
    assert overlay["medical_overlay_scope"] == profile.medical_overlay_scope
    assert overlay["medical_overlay_skills"] == list(profile.medical_overlay_skills)
    assert overlay["medical_overlay_bootstrap_mode"] == profile.medical_overlay_bootstrap_mode

    policy = contract["policy"]
    assert policy["research_route_bias_policy"] == profile.research_route_bias_policy
    assert policy["default_startup_anchor_policy"] == profile.default_startup_anchor_policy
    assert policy["legacy_code_execution_policy"] == profile.legacy_code_execution_policy
    assert policy["public_data_discovery_policy"] == profile.public_data_discovery_policy
    assert policy["startup_boundary_requirements"] == list(profile.startup_boundary_requirements)

    archetype = contract["archetype"]
    assert archetype["preferred_study_archetypes"] == list(profile.preferred_study_archetypes)


def test_load_profile_resolves_relative_paths_from_profile_location(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    profile_path = profile_dir / "relative.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "relative"',
                'workspace_root = "../workspace"',
                'runtime_root = "../workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "../workspace/studies"',
                'portfolio_root = "../workspace/portfolio"',
                'med_deepscientist_runtime_root = "../workspace/ops/med-deepscientist/runtime"',
                'med_deepscientist_repo_root = "../../med-deepscientist"',
                'hermes_agent_repo_root = "../../_external/hermes-agent"',
                'hermes_home_root = "../../.hermes-home"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert profile.workspace_root == (profile_dir / "../workspace").resolve()
    assert profile.runtime_root == (profile_dir / "../workspace/ops/med-deepscientist/runtime/quests").resolve()
    assert profile.med_deepscientist_runtime_root == (profile_dir / "../workspace/ops/med-deepscientist/runtime").resolve()
    assert profile.med_deepscientist_repo_root == (profile_dir / "../../med-deepscientist").resolve()
    assert profile.hermes_agent_repo_root == (profile_dir / "../../_external/hermes-agent").resolve()
    assert profile.hermes_home_root == (profile_dir / "../../.hermes-home").resolve()


def test_load_profile_rejects_invalid_boolean_shape(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-bool.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-bool"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'enable_medical_overlay = "false"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="enable_medical_overlay"):
        profiles.load_profile(profile_path)


def test_load_profile_rejects_invalid_list_shape(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-list.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-list"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'medical_overlay_skills = "write"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="medical_overlay_skills"):
        profiles.load_profile(profile_path)


def test_load_profile_rejects_invalid_default_submission_targets_shape(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-submission-targets.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-targets"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'default_submission_targets = ["frontiers_family_harvard"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="default_submission_targets"):
        profiles.load_profile(profile_path)


def test_load_profile_treats_empty_med_deepscientist_repo_root_as_unconfigured(tmp_path: Path) -> None:
    profile_path = tmp_path / "empty-ds-repo.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "empty-ds-repo"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'med_deepscientist_repo_root = ""',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert profile.med_deepscientist_repo_root is None


def test_load_profile_rejects_blank_medical_overlay_scope(tmp_path: Path) -> None:
    profile_path = tmp_path / "blank-strings.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "blank-strings"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'medical_overlay_scope = "   "',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="medical_overlay_scope"):
        profiles.load_profile(profile_path)


def test_load_profile_rejects_blank_research_route_bias_policy(tmp_path: Path) -> None:
    profile_path = tmp_path / "blank-policy.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "blank-policy"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'research_route_bias_policy = "   "',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="research_route_bias_policy"):
        profiles.load_profile(profile_path)


def test_load_profile_rejects_invalid_medical_overlay_bootstrap_mode(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-overlay-bootstrap-mode.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-bootstrap-mode"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'medical_overlay_bootstrap_mode = "rebuild_everything"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="medical_overlay_bootstrap_mode"):
        profiles.load_profile(profile_path)


def test_load_profile_rejects_invalid_legacy_code_execution_policy(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-legacy-code-policy.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-legacy-policy"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'legacy_code_execution_policy = "always_yes"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="legacy_code_execution_policy"):
        profiles.load_profile(profile_path)
