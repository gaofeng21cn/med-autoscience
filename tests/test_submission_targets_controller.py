from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_resolved_target(
    path: Path,
    *,
    primary_target_block: str = """{
    "journal_name": "Diabetes Research and Clinical Practice",
    "publication_profile": "general_medical_journal",
    "citation_style": "numeric_square_brackets",
    "official_guidelines_url": "https://example.org/drcp-guide",
    "package_required": true,
    "story_surface": "clinical_diabetes_prognosis_internal_validation",
    "resolution_status": "resolved"
  }""",
    decision_kind: str = "journal_selected",
    decision_source: str = "controller_explicit",
    extra_root_fields: str = "",
) -> None:
    write_text(
        path,
        f"""{{
  "schema_version": 1,
  "updated_at": "2026-04-06T00:00:00+00:00",
  "decision_kind": "{decision_kind}",
  "decision_source": "{decision_source}",
  "primary_target": {primary_target_block},
  {extra_root_fields}
  "blocked_items": []
}}
""".replace('\n  \n', '\n'),
    )


def write_profile(path: Path, workspace_root: Path) -> None:
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
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


def make_submission_target_workspace(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "nfpitnet.local.toml"
    study_root = workspace_root / "studies" / "002-early-residual-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "002-early-residual-risk"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-12345678" / "paper"
    write_profile(profile_path, workspace_root)
    write_text(
        study_root / "study.yaml",
        """study_id: 002-early-residual-risk
submission_targets:
  - publication_profile: frontiers_family_harvard
    primary: true
    package_required: true
    citation_style: FrontiersHarvard
    story_surface: specialty_medical
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
    write_text(paper_root / "paper_bundle_manifest.json", "{\n  \"schema_version\": 1\n}\n")
    return profile_path, study_root, quest_root, paper_root


def test_resolve_submission_targets_controller_returns_contract_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_targets")
    profile_path, study_root, quest_root, _ = make_submission_target_workspace(tmp_path)

    result = module.resolve_submission_targets(
        profile_path=profile_path,
        study_root=study_root,
        quest_root=quest_root,
    )

    assert result["status"] == "resolved"
    assert result["primary_target"]["publication_profile"] == "frontiers_family_harvard"
    assert result["primary_target"]["citation_style"] == "FrontiersHarvard"
    assert result["unresolved_target_count"] == 1
    assert result["export_publication_profiles"] == [
        "general_medical_journal",
        "frontiers_family_harvard",
    ]


def test_resolve_submission_targets_controller_can_infer_study_root_from_profile_and_quest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_targets")
    profile_path, study_root, quest_root, _ = make_submission_target_workspace(tmp_path)

    result = module.resolve_submission_targets(
        profile_path=profile_path,
        quest_root=quest_root,
    )

    assert result["study_root"] == str(study_root)
    assert result["primary_target"]["publication_profile"] == "frontiers_family_harvard"


def test_export_submission_targets_exports_resolved_profiles_and_blocks_unresolved(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_targets")
    profile_path, study_root, quest_root, paper_root = make_submission_target_workspace(tmp_path)
    calls: list[tuple[Path, str, str | None]] = []

    def fake_export(*, paper_root: Path, publication_profile: str, citation_style: str | None = "auto") -> dict:
        calls.append((paper_root, publication_profile, citation_style))
        return {
            "publication_profile": publication_profile,
            "citation_style": citation_style,
            "output_root": str(paper_root / "journal_submissions" / publication_profile),
        }

    monkeypatch.setattr(module.submission_minimal, "create_submission_minimal_package", fake_export)

    result = module.export_submission_targets(
        profile_path=profile_path,
        study_root=study_root,
        quest_root=quest_root,
    )

    assert [item[1] for item in calls] == [
        "general_medical_journal",
        "frontiers_family_harvard",
    ]
    assert [item[2] for item in calls] == ["AMA", "FrontiersHarvard"]
    assert all(item[0] == paper_root for item in calls)
    assert result["status"] == "blocked"
    assert result["paper_root"] == str(paper_root)
    assert result["blocked_target_count"] == 1
    by_key = {item["target_key"]: item for item in result["targets"]}
    assert by_key["profile:general_medical_journal"]["export_status"] == "exported"
    assert by_key["profile:frontiers_family_harvard"]["export_status"] == "exported"
    assert (
        by_key["journal:journal of clinical endocrinology & metabolism"]["export_status"]
        == "blocked_needs_journal_resolution"
    )


def test_resolve_submission_targets_controller_reads_quest_paper_resolved_target(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_targets")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "dm.local.toml"
    study_root = workspace_root / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "001-dm-cvd-mortality-risk-reentry-20260331"
    write_profile(profile_path, workspace_root)
    write_text(study_root / "study.yaml", "study_id: 001-dm-cvd-mortality-risk\n")
    write_text(
        quest_root / "quest.yaml",
        """quest_id: 001-dm-cvd-mortality-risk-reentry-20260331
startup_contract:
  submission_targets: []
""",
    )
    write_resolved_target(quest_root / "paper" / "submission_targets.resolved.json")

    result = module.resolve_submission_targets(
        profile_path=profile_path,
        study_root=study_root,
        quest_root=quest_root,
    )

    assert result["primary_target"]["source"] == "quest_paper_resolved"
    assert result["primary_target"]["journal_name"] == "Diabetes Research and Clinical Practice"
    assert result["primary_target"]["official_guidelines_url"] == "https://example.org/drcp-guide"
    assert result["primary_target"]["citation_style"] == "numeric_square_brackets"
    assert result["primary_target"]["exporter_profile"] == "general_medical_journal"
    assert result["primary_target"]["exporter_family"] == "generic_medical_journal"
    assert result["primary_target"]["decision_kind"] == "journal_selected"
    assert result["primary_target"]["decision_source"] == "controller_explicit"
    assert result["primary_target"]["exporter_status"] == "blocked_generic_export_requires_explicit_controller_decision"
    assert result["unresolved_target_count"] == 0
    assert result["export_publication_profiles"] == []
    assert result["exporter_profiles"] == []


def test_export_submission_targets_blocks_controller_resolved_generic_target_without_explicit_generic_export(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_targets")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "dm.local.toml"
    study_root = workspace_root / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "001-dm-cvd-mortality-risk-reentry-20260331"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-12345678" / "paper"
    write_profile(profile_path, workspace_root)
    write_text(study_root / "study.yaml", "study_id: 001-dm-cvd-mortality-risk\n")
    write_text(quest_root / "quest.yaml", "quest_id: 001-dm-cvd-mortality-risk-reentry-20260331\n")
    write_text(paper_root / "paper_bundle_manifest.json", "{\n  \"schema_version\": 1\n}\n")
    write_resolved_target(quest_root / "paper" / "submission_targets.resolved.json")
    calls: list[tuple[Path, str, str | None]] = []

    def fake_export(*, paper_root: Path, publication_profile: str, citation_style: str | None = "auto") -> dict:
        calls.append((paper_root, publication_profile, citation_style))
        return {"publication_profile": publication_profile, "citation_style": citation_style}

    monkeypatch.setattr(module.submission_minimal, "create_submission_minimal_package", fake_export)

    result = module.export_submission_targets(
        profile_path=profile_path,
        study_root=study_root,
        quest_root=quest_root,
    )

    assert calls == []
    assert result["status"] == "blocked"
    assert result["blocked_target_count"] == 1
    assert result["exported_publication_profiles"] == []
    assert result["exported_exporter_profiles"] == []
    assert result["targets"][0]["export_status"] == "blocked_exporter_not_ready"
    assert (
        result["targets"][0]["export_reason"]
        == "blocked_generic_export_requires_explicit_controller_decision"
    )
