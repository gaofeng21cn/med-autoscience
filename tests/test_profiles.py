from __future__ import annotations

import importlib
from pathlib import Path
import tomllib
import pytest

CANONICAL_NFPITNET_WORKSPACE_ROOT = Path("/Users/gaofeng/workspace/Yang/NF-PitNET")
STALE_NFPITNET_ALIAS_WORKSPACE_ROOT = Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")

PROFILE_LINES = [
    'name = "nfpitnet"',
    f'workspace_root = "{CANONICAL_NFPITNET_WORKSPACE_ROOT}"',
    f'runtime_root = "{CANONICAL_NFPITNET_WORKSPACE_ROOT / "runtime" / "quests"}"',
    f'studies_root = "{CANONICAL_NFPITNET_WORKSPACE_ROOT / "studies"}"',
    f'portfolio_root = "{CANONICAL_NFPITNET_WORKSPACE_ROOT / "portfolio"}"',
    'hermes_agent_repo_root = "/Users/gaofeng/workspace/_external/hermes-agent"',
    'hermes_home_root = "~/.hermes"',
    'default_publication_profile = "general_medical_journal"',
    'default_citation_style = "AMA"',
    'research_route_bias_policy = "high_plasticity_medical"',
    'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
    'default_startup_anchor_policy = "scout_first_for_continue_existing_state"',
    'legacy_code_execution_policy = "forbid_without_user_approval"',
    'public_data_discovery_policy = "required_for_scout_route_selection"',
    'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]',
    "",
    "[[default_submission_targets]]",
    'exporter_profile = "frontiers_family_harvard"',
    "primary = true",
    "package_required = true",
    'story_surface = "general_medical_journal"',
    "",
    "[source_provenance]",
    'source_role = "frozen_source_archive_or_historical_fixture"',
    f'runtime_root = "{CANONICAL_NFPITNET_WORKSPACE_ROOT / "runtime"}"',
    "",
    "[historical_fixture_ref]",
    f'runtime_root = "{CANONICAL_NFPITNET_WORKSPACE_ROOT / "runtime"}"',
    "",
    "[explicit_archive_import_ref]",
    'controlled_backend_repo_root = "/Users/gaofeng/workspace/med-deepscientist"',
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
    assert profile.workspace_root == CANONICAL_NFPITNET_WORKSPACE_ROOT
    assert profile.med_deepscientist_repo_root == Path("/Users/gaofeng/workspace/med-deepscientist")
    assert profile.hermes_agent_repo_root == Path("/Users/gaofeng/workspace/_external/hermes-agent")
    assert profile.hermes_home_root == Path.home() / ".hermes"
    assert profile.opl_runtime_ref == "opl_hosted_stage_runtime"
    assert profile.default_publication_profile == "general_medical_journal"
    assert profile.default_citation_style == "AMA"
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
    assert profile.default_submission_targets[0]["exporter_profile"] == "frontiers_family_harvard"
    assert profile.default_submission_targets[0]["primary"] is True


def test_load_profile_rejects_nfpitnet_stale_local_alias_scaffold(tmp_path: Path) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    stale_lines = [
        'name = "nfpitnet"',
        f'workspace_root = "{STALE_NFPITNET_ALIAS_WORKSPACE_ROOT}"',
        f'runtime_root = "{STALE_NFPITNET_ALIAS_WORKSPACE_ROOT / "runtime" / "quests"}"',
        f'studies_root = "{STALE_NFPITNET_ALIAS_WORKSPACE_ROOT / "studies"}"',
        f'portfolio_root = "{STALE_NFPITNET_ALIAS_WORKSPACE_ROOT / "portfolio"}"',
        f'med_deepscientist_runtime_root = "{STALE_NFPITNET_ALIAS_WORKSPACE_ROOT / "runtime"}"',
        'default_publication_profile = "general_medical_journal"',
        'default_citation_style = "AMA"',
    ]
    profile_path.write_text("\n".join(stale_lines) + "\n", encoding="utf-8")

    profiles = importlib.import_module("med_autoscience.profiles")

    with pytest.raises(ValueError, match="stale local alias/scaffold"):
        profiles.load_profile(profile_path)


def test_load_profile_uses_opl_runtime_defaults(tmp_path: Path) -> None:
    profile_path = tmp_path / "minimal.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "minimal"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/opl-stage-locator"',
                'managed_runtime_home = "/tmp/workspace/runtime"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert profile.med_deepscientist_runtime_root == Path("/tmp/workspace/runtime").resolve()
    assert profile.med_deepscientist_repo_root is None
    assert profile.hermes_agent_repo_root is None
    assert profile.hermes_home_root == Path.home() / ".hermes"
    assert profile.opl_runtime_ref == "opl_hosted_stage_runtime"
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


def test_workspace_profile_template_excludes_retired_overlay_settings() -> None:
    template_path = Path(__file__).resolve().parents[1] / "profiles" / "workspace.profile.template.toml"
    payload = tomllib.loads(template_path.read_text(encoding="utf-8"))

    assert "enable_medical_overlay" not in payload
    assert "medical_overlay_scope" not in payload
    assert "medical_overlay_skills" not in payload
    assert "medical_overlay_bootstrap_mode" not in payload
    assert "developer_supervisor_mode" not in payload
    assert "github_username" not in payload
    assert "mas_developer_github_usernames" not in payload


def test_load_profile_accepts_historical_reference_tables_without_top_level_mds_fields(tmp_path: Path) -> None:
    profile_path = tmp_path / "historical-reference.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "historical-reference"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/opl-stage-locator"',
                'managed_runtime_home = "/tmp/workspace/runtime"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "[source_provenance]",
                'source_role = "frozen_source_archive_or_historical_fixture"',
                'runtime_root = "/tmp/workspace/legacy/mds-runtime"',
                "[explicit_archive_import_ref]",
                'controlled_backend_repo_root = "/tmp/med-deepscientist"',
                "read_only = true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert profile.runtime_root == Path("/tmp/opl-stage-locator").resolve()
    assert profile.med_deepscientist_runtime_root == Path("/tmp/workspace/legacy/mds-runtime").resolve()
    assert profile.med_deepscientist_repo_root == Path("/tmp/med-deepscientist").resolve()


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
    assert contract["managed_runtime_home"] == str(profile.managed_runtime_home)
    assert contract["studies_root"] == str(profile.studies_root)
    assert contract["portfolio_root"] == str(profile.portfolio_root)
    assert "med_deepscientist_runtime_root" not in contract
    assert "med_deepscientist_repo_root" not in contract
    assert contract["source_provenance"] == {
        "surface_kind": "source_provenance",
        "source_role": "frozen_source_archive_or_historical_fixture",
        "runtime_root": str(profile.med_deepscientist_runtime_root),
        "controlled_backend_repo_root": str(profile.med_deepscientist_repo_root),
        "read_only": True,
    }
    assert contract["historical_fixture_ref"] == {
        "surface_kind": "historical_fixture_ref",
        "runtime_root": str(profile.med_deepscientist_runtime_root),
        "runtime_root_exists": profile.med_deepscientist_runtime_root.exists(),
        "read_only": True,
    }
    assert contract["explicit_archive_import_ref"] == {
        "surface_kind": "explicit_archive_import_ref",
        "runtime_root": str(profile.med_deepscientist_runtime_root),
        "controlled_backend_repo_root": str(profile.med_deepscientist_repo_root),
        "read_only": True,
    }
    assert contract["hermes_agent_repo_root"] == str(profile.hermes_agent_repo_root)
    assert contract["hermes_home_root"] == str(profile.hermes_home_root)
    assert contract["opl_runtime_ref"] == profile.opl_runtime_ref
    assert contract["opl_runtime_contract"] == {
        "runtime_owner": "one-person-lab",
        "runtime_substrate": "opl_hosted_stage_runtime",
        "runtime_ref": "opl_hosted_stage_runtime",
        "runtime_engine_id": "opl-hosted-stage-runtime",
        "runtime_backend_role": "mas_domain_owner_receipt_adapter",
        "runtime_backend_is_generic_owner": False,
        "default_autonomous_runtime": {
            "enabled_by_default": True,
            "hosted_runtime_owner": "one-person-lab",
            "hosted_runtime_provider": "temporal",
            "runtime_substrate": "opl_hosted_stage_runtime",
            "persistent_online_control_plane": "opl_temporal",
            "task_start_handoff": "mas_domain_intent_to_opl_stage_attempt",
            "wakeup_retry_resume_owner": "one-person-lab",
            "codex_app_outer_driver_required": False,
            "mas_daemon_scheduler_attempt_loop_allowed": False,
        },
        "default_runtime_backend_is_opl_provider_owned": True,
        "delegated_domain_adapter_id": "mas_domain_intent_adapter",
        "delegated_domain_adapter_engine_id": "mas-domain-intent-adapter",
        "domain_runtime_adapter_id": "mas_domain_intent_adapter",
        "domain_runtime_adapter_role": "mas_domain_owner_receipt_adapter",
        "generic_runtime_owner": "one-person-lab",
        "generic_runtime_substrate": "opl_hosted_stage_runtime",
        "domain_truth_owner": "med-autoscience",
        "domain_authority_retained": [
            "study_truth",
            "publication_quality_verdict",
            "artifact_authority",
            "memory_accept_reject_receipt",
            "owner_receipt",
            "typed_blocker",
        ],
        "mas_runtime_backend_registry_retired": True,
        "provider_attempt_owner": "one-person-lab",
        "provider_completion_is_domain_completion": False,
        "domain_progression_requires": [
            "mas_owner_receipt",
            "mas_typed_blocker",
            "ai_reviewer_backed_verdict",
            "publication_gate_receipt",
        ],
        "runtime_backend_retirement_gate": {
            "no_active_default_caller_required": True,
            "opl_replacement_parity_required": True,
            "domain_receipt_parity_required": True,
            "history_tombstone_required": True,
        },
        "research_backend_id": "mas_domain_intent_adapter",
        "research_engine_id": "mas-domain-intent-adapter",
        "external_mds_required_for_default_operation": False,
        "external_mds_runnable_dependency": False,
        "external_mds_retained_role": "frozen_source_archive_or_historical_fixture",
        "external_mds_allowed_uses": ["source_provenance_ref", "historical_fixture_ref"],
    }

    publication = contract["publication"]
    assert publication["default_publication_profile"] == profile.default_publication_profile
    assert publication["default_citation_style"] == profile.default_citation_style
    assert isinstance(publication["default_submission_targets"], list)
    assert publication["default_submission_targets"][0]["exporter_profile"] == "frontiers_family_harvard"

    policy = contract["policy"]
    assert policy["research_route_bias_policy"] == profile.research_route_bias_policy
    assert policy["default_startup_anchor_policy"] == profile.default_startup_anchor_policy
    assert policy["legacy_code_execution_policy"] == profile.legacy_code_execution_policy
    assert policy["public_data_discovery_policy"] == profile.public_data_discovery_policy
    assert policy["startup_boundary_requirements"] == list(profile.startup_boundary_requirements)
    assert "developer_supervisor_mode" not in policy
    assert "github_username" not in policy
    assert "mas_developer_github_usernames" not in policy

    archetype = contract["archetype"]
    assert archetype["preferred_study_archetypes"] == list(profile.preferred_study_archetypes)


def test_profile_to_dict_exposes_scholarskills_required_package_contract(tmp_path: Path) -> None:
    workspace_root = tmp_path / "DM-CVD-Mortality-Risk"
    profile_path = tmp_path / "dm-cvd.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "dm-cvd"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "runtime" / "quests"}"',
                f'managed_runtime_home = "{workspace_root / "runtime"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "memory" / "portfolio"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    required_package = importlib.import_module("med_autoscience.scholarskills_required_package")
    profile = profiles.load_profile(profile_path)
    contract = profiles.profile_to_dict(profile)

    requirement = contract["scholarskills_required_package"]
    assert requirement["package_id"] == "mas-scholar-skills"
    assert requirement["required"] is True
    assert requirement["dependency_kind"] == "hard_runtime_dependency"
    assert requirement["capability_abi"] == required_package.SCHOLARSKILLS_CAPABILITY_ABI
    assert requirement["required_skill_ids"] == list(
        required_package.SCHOLARSKILLS_REQUIRED_SKILL_IDS
    )
    assert requirement["required_module_ids"] == list(
        required_package.SCHOLARSKILLS_REQUIRED_MODULE_IDS
    )
    assert requirement["repair_command_templates"]["workspace"] == [
        "opl",
        "connect",
        "agent-packages",
        "repair",
        "--package-id",
        "mas",
        "--agent-root",
        "<agent-root>",
        "--json",
    ]
    assert "workspace" not in requirement
    assert "quest" not in requirement
    assert "optional_skill_ids" not in requirement


def test_render_profile_labels_backend_paths_as_diagnostics(tmp_path: Path) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    write_full_profile(profile_path)

    profiles = importlib.import_module("med_autoscience.profiles")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = profiles.load_profile(profile_path)

    rendered = doctor.render_profile(profile)

    assert "opl_runtime_locator: " in rendered
    assert "mas_runtime_home: " in rendered
    assert "historical_fixture_runtime_root: " in rendered
    assert "controlled_backend_audit_repo_root: " in rendered
    assert "legacy_diagnostic_runtime_root: " not in rendered
    assert "med_deepscientist_runtime_root: " not in rendered
    assert "med_deepscientist_repo_root: " not in rendered


def test_load_profile_resolves_relative_paths_from_profile_location(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    profile_path = profile_dir / "relative.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "relative"',
                'workspace_root = "../workspace"',
                'runtime_root = "../workspace/opl-stage-locator"',
                'studies_root = "../workspace/studies"',
                'portfolio_root = "../workspace/portfolio"',
                'hermes_agent_repo_root = "../../_external/hermes-agent"',
                'hermes_home_root = "../../.hermes-home"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "[historical_fixture_ref]",
                'runtime_root = "../workspace/runtime"',
                "[explicit_archive_import_ref]",
                'controlled_backend_repo_root = "../../med-deepscientist"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert profile.workspace_root == (profile_dir / "../workspace").resolve()
    assert profile.runtime_root == (profile_dir / "../workspace/opl-stage-locator").resolve()
    assert profile.med_deepscientist_runtime_root == (profile_dir / "../workspace/runtime").resolve()
    assert profile.med_deepscientist_repo_root == (profile_dir / "../../med-deepscientist").resolve()
    assert profile.hermes_agent_repo_root == (profile_dir / "../../_external/hermes-agent").resolve()
    assert profile.hermes_home_root == (profile_dir / "../../.hermes-home").resolve()


def test_load_profile_rejects_invalid_default_submission_targets_shape(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-submission-targets.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-targets"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/opl-stage-locator"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/runtime"',
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
                'runtime_root = "/tmp/opl-stage-locator"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/runtime"',
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


def test_load_profile_rejects_blank_research_route_bias_policy(tmp_path: Path) -> None:
    profile_path = tmp_path / "blank-policy.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "blank-policy"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/opl-stage-locator"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/runtime"',
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


def test_load_profile_rejects_invalid_legacy_code_execution_policy(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-legacy-code-policy.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-legacy-policy"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/opl-stage-locator"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/runtime"',
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


def test_load_profile_does_not_restore_retired_execution_admission_fields(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid-developer-supervisor.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "invalid-dev-supervisor"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/opl-stage-locator"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                'developer_supervisor_mode = "developer_supervisor"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.load_profile(profile_path)

    assert not hasattr(profile, "developer_supervisor_mode")
    assert not hasattr(profile, "github_username")
    assert not hasattr(profile, "mas_developer_github_usernames")


def test_load_profile_rejects_med_deepscientist_as_default_managed_backend(tmp_path: Path) -> None:
    profile_path = tmp_path / "mds-backend.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "mds-backend"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/opl-stage-locator"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/runtime"',
                'opl_runtime_ref = "med_deepscientist"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    profiles = importlib.import_module("med_autoscience.profiles")
    with pytest.raises(TypeError, match="frozen source provenance"):
        profiles.load_profile(profile_path)
