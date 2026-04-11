from __future__ import annotations

import importlib
from pathlib import Path


def make_profile(tmp_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    return profiles.WorkspaceProfile(
        name="pituitary",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline", "write"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )


def test_workspace_runtime_layout_derives_med_deepscientist_roots(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.layout")
    profile = make_profile(tmp_path)

    layout = module.build_workspace_runtime_layout_for_profile(profile)

    assert layout.workspace_root == profile.workspace_root
    assert layout.ops_root == profile.workspace_root / "ops" / "med-deepscientist"
    assert layout.runtime_root == profile.med_deepscientist_runtime_root
    assert layout.quests_root == profile.runtime_root
    assert layout.bin_root == layout.ops_root / "bin"
    assert layout.startup_briefs_root == layout.ops_root / "startup_briefs"
    assert layout.startup_payloads_root == layout.ops_root / "startup_payloads"
    assert layout.config_env_path == layout.ops_root / "config.env"
    assert layout.readme_path == layout.ops_root / "README.md"
    assert layout.behavior_gate_path == layout.ops_root / "behavior_equivalence_gate.yaml"


def test_workspace_runtime_layout_derives_quest_and_startup_payload_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.layout")

    layout = module.build_workspace_runtime_layout(workspace_root=tmp_path / "workspace")

    assert layout.quest_root("study-001") == layout.quests_root / "study-001"
    assert layout.startup_payload_root("study-001") == layout.startup_payloads_root / "study-001"
    assert layout.startup_brief_path("study-001") == layout.startup_briefs_root / "study-001.md"


def test_workspace_runtime_layout_follows_profile_runtime_root_for_hermes_substrate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.layout")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="pituitary",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "hermes" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline", "write"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
        managed_runtime_backend_id="hermes",
    )

    layout = module.build_workspace_runtime_layout_for_profile(profile)

    assert layout.ops_root == workspace_root / "ops" / "hermes"
    assert layout.runtime_root == workspace_root / "ops" / "hermes" / "runtime"
    assert layout.quests_root == workspace_root / "ops" / "hermes" / "runtime" / "quests"
    assert layout.behavior_gate_path == workspace_root / "ops" / "hermes" / "behavior_equivalence_gate.yaml"


def test_resolve_runtime_root_from_quest_root_returns_workspace_runtime_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.layout")
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "study-001"

    assert module.resolve_runtime_root_from_quest_root(quest_root) == (
        tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime"
    )
