from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_resolved_target(path: Path) -> None:
    write_text(
        path,
        """{
  "schema_version": 1,
  "updated_at": "2026-04-06T00:00:00+00:00",
  "primary_target": {
    "journal_name": "Diabetes Research and Clinical Practice",
    "publication_profile": "general_medical_journal",
    "citation_style": "numeric_square_brackets",
    "official_guidelines_url": "https://example.org/drcp-guide",
    "package_required": true,
    "story_surface": "clinical_diabetes_prognosis_internal_validation",
    "resolution_status": "resolved"
  },
  "blocked_items": []
}
""",
    )


def write_profile(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/tmp/workspace"',
                'runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/tmp/workspace/studies"',
                'portfolio_root = "/tmp/workspace/portfolio"',
                'med_deepscientist_runtime_root = "/tmp/workspace/ops/med-deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "",
                "[[default_submission_targets]]",
                'publication_profile = "general_medical_journal"',
                "primary = true",
                "package_required = true",
                'story_surface = "general_medical_journal"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_resolve_submission_targets_uses_profile_default_target_when_study_and_quest_missing(tmp_path: Path) -> None:
    profiles = importlib.import_module("med_autoscience.profiles")
    module = importlib.import_module("med_autoscience.submission_targets")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    contract = module.resolve_submission_target_contract(
        profile=profiles.load_profile(profile_path),
    )

    assert contract.primary_target.publication_profile == "general_medical_journal"
    assert contract.primary_target.citation_style == "AMA"
    assert contract.primary_target.story_surface == "general_medical_journal"
    assert contract.primary_target.package_required is True
    assert contract.primary_target.resolution_status == "resolved_profile"
    assert contract.export_publication_profiles == ("general_medical_journal",)


def test_resolve_submission_targets_merges_profile_study_and_quest_targets(tmp_path: Path) -> None:
    profiles = importlib.import_module("med_autoscience.profiles")
    module = importlib.import_module("med_autoscience.submission_targets")
    profile_path = tmp_path / "profile.local.toml"
    study_root = tmp_path / "workspace" / "studies" / "002-early-residual-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "002-early-residual-risk"
    write_profile(profile_path)
    write_text(
        study_root / "study.yaml",
        """study_id: 002-early-residual-risk
submission_targets:
  - publication_profile: frontiers_family_harvard
    primary: true
    package_required: true
    story_surface: specialty_medical
    narrative_emphasis:
      - clinical_translation
      - physiology_context
""",
    )
    write_text(
        quest_root / "quest.yaml",
        """quest_id: 002-early-residual-risk
startup_contract:
  submission_targets:
    - journal_name: Journal of Clinical Endocrinology & Metabolism
      official_guidelines_url: https://example.org/jcem-guide
      package_required: true
      story_surface: specialty_medical
""",
    )

    contract = module.resolve_submission_target_contract(
        profile=profiles.load_profile(profile_path),
        study_root=study_root,
        quest_root=quest_root,
    )

    assert [target.publication_profile for target in contract.targets if target.publication_profile] == [
        "general_medical_journal",
        "frontiers_family_harvard",
    ]
    assert contract.primary_target.publication_profile == "frontiers_family_harvard"
    assert contract.primary_target.narrative_emphasis == ("clinical_translation", "physiology_context")
    assert len(contract.unresolved_targets) == 1
    assert contract.unresolved_targets[0].journal_name == "Journal of Clinical Endocrinology & Metabolism"
    assert contract.unresolved_targets[0].resolution_status == "needs_journal_resolution"
    assert contract.export_publication_profiles == (
        "general_medical_journal",
        "frontiers_family_harvard",
    )


def test_resolve_submission_targets_replace_mode_drops_workspace_defaults(tmp_path: Path) -> None:
    profiles = importlib.import_module("med_autoscience.profiles")
    module = importlib.import_module("med_autoscience.submission_targets")
    profile_path = tmp_path / "profile.local.toml"
    study_root = tmp_path / "workspace" / "studies" / "002-early-residual-risk"
    write_profile(profile_path)
    write_text(
        study_root / "study.yaml",
        """study_id: 002-early-residual-risk
submission_targets_mode: replace
submission_targets:
  - publication_profile: frontiers_family_harvard
    primary: true
    package_required: true
""",
    )

    contract = module.resolve_submission_target_contract(
        profile=profiles.load_profile(profile_path),
        study_root=study_root,
    )

    assert [target.publication_profile for target in contract.targets] == ["frontiers_family_harvard"]
    assert contract.export_publication_profiles == ("frontiers_family_harvard",)


def test_resolve_submission_targets_uses_quest_paper_resolved_target(tmp_path: Path) -> None:
    profiles = importlib.import_module("med_autoscience.profiles")
    module = importlib.import_module("med_autoscience.submission_targets")
    profile_path = tmp_path / "profile.local.toml"
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "001-dm-cvd-mortality-risk-reentry-20260331"
    write_profile(profile_path)
    write_text(
        study_root / "study.yaml",
        "study_id: 001-dm-cvd-mortality-risk\n",
    )
    write_text(
        quest_root / "quest.yaml",
        """quest_id: 001-dm-cvd-mortality-risk-reentry-20260331
startup_contract:
  submission_targets: []
""",
    )
    write_resolved_target(quest_root / "paper" / "submission_targets.resolved.json")

    contract = module.resolve_submission_target_contract(
        profile=profiles.load_profile(profile_path),
        study_root=study_root,
        quest_root=quest_root,
    )

    assert len(contract.targets) == 1
    assert contract.primary_target.source == "quest_paper_resolved"
    assert contract.primary_target.publication_profile == "general_medical_journal"
    assert contract.primary_target.journal_name == "Diabetes Research and Clinical Practice"
    assert contract.primary_target.official_guidelines_url == "https://example.org/drcp-guide"
    assert contract.primary_target.citation_style == "numeric_square_brackets"
    assert contract.unresolved_targets == ()
    assert contract.export_publication_profiles == ("general_medical_journal",)
