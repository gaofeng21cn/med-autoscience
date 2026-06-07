from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study, write_text


def _write_profile(path: Path, profile) -> None:
    path.write_text(
        "\n".join(
            [
                f'name = "{profile.name}"',
                f'workspace_root = "{profile.workspace_root}"',
                f'runtime_root = "{profile.runtime_root}"',
                f'studies_root = "{profile.studies_root}"',
                f'portfolio_root = "{profile.portfolio_root}"',
                f'med_deepscientist_runtime_root = "{profile.med_deepscientist_runtime_root}"',
                f'med_deepscientist_repo_root = "{profile.med_deepscientist_repo_root}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_legacy_workspace(workspace_root: Path) -> None:
    write_text(workspace_root / "README.md", "Use portfolio/research_memory and refs/legacy as provenance.\n")
    write_text(workspace_root / "AGENTS.md", "workspace rules\n")
    write_text(workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md", "controller first\n")
    write_text(workspace_root / "WORKSPACE_STATUS.md", "status\n")
    write_text(workspace_root / "workspace.yaml", "portfolio_root: portfolio\n")
    write_text(workspace_root / "workspace_index.json", "{}\n")
    write_text(workspace_root / "datasets" / "master" / "v1" / "dataset_manifest.yaml", "id: dataset\n")
    write_text(workspace_root / "portfolio" / "research_memory" / "topic_landscape.md", "memory\n")
    write_text(workspace_root / "paper" / "paper_contract.json", "{}\n")
    write_text(workspace_root / "refs" / "legacy" / "README.md", "legacy\n")
    write_text(workspace_root / "contracts" / "variables.md", "legacy contract\n")
    write_text(workspace_root / "docs" / "old.md", "old plan\n")
    write_text(workspace_root / "experiments" / "old.md", "old experiment\n")
    write_text(workspace_root / "tests" / "old_test.py", "pass\n")
    write_text(workspace_root / "storage_audit" / "latest.json", "{}\n")
    write_text(workspace_root / "inbox" / "request.md", "old inbox\n")
    write_text(workspace_root / "RTK.md", "legacy rtk\n")
    write_text(workspace_root / ".python-version", "3.11\n")
    write_text(workspace_root / ".venv" / "bin" / "python3", "")
    write_text(workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh", 'WORKSPACE_PYTHON="${WORKSPACE_ROOT}/.venv/bin/python3"\n')
    write_text(workspace_root / "ops" / "medautoscience" / "config.env", 'WORKSPACE_PYTHON="${WORKSPACE_ROOT}/.venv/bin/python3"\n')
    write_text(workspace_root / "ops" / "data_assets" / "materialize.py", 'DEFAULT_RELEASE_ROOT = Path("datasets/master/v1")\n')
    write_text(workspace_root / "ops" / "framework_refs" / "_repo_compare" / "fixture.py", 'TEXT = "datasets/upstream-fixture"\n')
    write_text(workspace_root / "artifacts" / "runtime" / "domain_authority_refs.sqlite", "")
    write_text(workspace_root / "runtime" / "quests" / ".gitkeep", "")


def test_workspace_target_state_cleanup_rewrites_refs_before_physical_moves(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_target_state_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)
    study_root = write_study(profile.workspace_root, "003-dpcc", quest_id="003-dpcc")
    write_text(
        study_root / "study.yaml",
        "\n".join(
            [
                "study_id: 003-dpcc",
                "truth_surface_policy:",
                "  authoritative_sources:",
                "    - ../../datasets/master/v1/dataset_manifest.yaml",
                "    - ../../portfolio/research_memory/topic_landscape.md",
            ]
        )
        + "\n",
    )
    write_text(study_root / "brief.md", "Brief uses ../../refs/legacy and portfolio memory.\n")
    write_text(study_root / "analysis" / "scripts" / "prepare.py", 'INPUT = "datasets/master/v1"\n')
    provenance_files = {
        study_root / "artifacts" / "runtime" / "last_launch_report.json": '{"source": "datasets/master/v1"}\n',
        study_root
        / "artifacts"
        / "stage_knowledge"
        / "memory_write_router_receipts"
        / "receipt.json": '{"portfolio": "portfolio/research_memory"}\n',
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "closeout.json": '{"refs": "../../refs/legacy"}\n',
        study_root / "paper" / "draft.md": "Draft mentions datasets/master/v1 as historical text.\n",
        study_root / "publication" / "current_package" / "package.json": '{"source": "datasets/master/v1"}\n',
    }
    for path, text in provenance_files.items():
        write_text(path, text)
    original_provenance = {path: path.read_text(encoding="utf-8") for path in provenance_files}

    dry_run = module.run_workspace_target_state_cleanup(profile_path=profile_path, apply=False)

    assert dry_run["status"] == "typed_blocked"
    assert "path_ref_migration_pending" in dry_run["validation"]["blockers"]
    assert "legacy_datasets_refs_remaining" in dry_run["validation"]["blockers"]
    assert "legacy_portfolio_refs_remaining" in dry_run["validation"]["blockers"]
    root_decisions = {
        action["source_relative_path"]: action["decision"]
        for action in dry_run["root_cleanup"]["root_actions"]
    }
    assert root_decisions["datasets"] == "blocked_until_path_refs_rewritten"
    assert root_decisions["portfolio"] == "blocked_until_path_refs_rewritten"
    assert root_decisions["artifacts"] == "move"
    candidate_files = set(dry_run["path_ref_migration"]["candidate_files"])
    assert "studies/003-dpcc/study.yaml" in candidate_files
    assert "studies/003-dpcc/brief.md" in candidate_files
    assert "studies/003-dpcc/analysis/scripts/prepare.py" in candidate_files
    assert "studies/003-dpcc/artifacts/runtime/last_launch_report.json" not in candidate_files
    assert "studies/003-dpcc/artifacts/supervision/consumer/stage_attempt_closeouts/closeout.json" not in candidate_files
    assert "studies/003-dpcc/paper/draft.md" not in candidate_files
    assert "studies/003-dpcc/publication/current_package/package.json" not in candidate_files
    assert "ops/framework_refs/_repo_compare/fixture.py" not in candidate_files

    result = module.run_workspace_target_state_cleanup(profile_path=profile_path, apply=True)

    assert result["status"] == "ready"
    assert result["validation"]["non_terminal_blockers"] == []
    assert result["path_ref_migration"]["file_update_count"] == 0
    assert (profile.workspace_root / "data" / "datasets" / "master" / "v1" / "dataset_manifest.yaml").is_file()
    assert (profile.workspace_root / "memory" / "portfolio" / "research_memory" / "topic_landscape.md").is_file()
    assert (profile.workspace_root / "ops" / "medautoscience" / ".venv" / "bin" / "python3").is_file()
    assert not (profile.workspace_root / "datasets").exists()
    assert not (profile.workspace_root / "portfolio").exists()
    assert not (profile.workspace_root / "paper").exists()
    assert not (profile.workspace_root / "refs").exists()
    assert (profile.workspace_root / "runtime" / "artifacts" / "domain_authority_refs.sqlite").is_file()
    assert not (profile.workspace_root / "artifacts").exists()
    assert 'data/datasets/master/v1' in (study_root / "study.yaml").read_text(encoding="utf-8")
    assert 'memory/portfolio/research_memory' in (study_root / "study.yaml").read_text(encoding="utf-8")
    assert f'archive/legacy_root_surfaces/{result["archive_stamp"]}/refs/legacy' in (
        study_root / "brief.md"
    ).read_text(encoding="utf-8")
    assert 'data/datasets/master/v1' in (study_root / "analysis" / "scripts" / "prepare.py").read_text(encoding="utf-8")
    assert 'ops/medautoscience/.venv' in (
        profile.workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    ).read_text(encoding="utf-8")
    assert 'ops/medautoscience/.venv' in (
        profile.workspace_root / "ops" / "medautoscience" / "config.env"
    ).read_text(encoding="utf-8")
    for path, text in original_provenance.items():
        assert path.read_text(encoding="utf-8") == text
    manifest = json.loads((profile.workspace_root / "archive" / "root_cleanup_manifest" / "latest.json").read_text())
    archived_roots = {item["source"] for item in manifest["legacy_provenance_map"]}
    assert {"paper", "refs", "contracts", "docs", "experiments", "tests", "storage_audit", "inbox"}.issubset(
        archived_roots
    )
    assert manifest["validation"]["runtime_quests_current_paper_truth"] is False
    assert manifest["validation"]["root_paper_current_truth"] is False
    assert manifest["current_truth_map"]["workspace_runtime_artifacts_root"] == "runtime/artifacts"


def test_workspace_target_state_cleanup_fail_closed_for_unknown_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_target_state_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)
    write_text(profile.workspace_root / "unknown_live_root" / "note.md", "not classified\n")

    result = module.run_workspace_target_state_cleanup(profile_path=profile_path, apply=False)

    assert result["status"] == "typed_blocked"
    assert "unclassified_root_entry_unknown_live_root" in result["validation"]["non_terminal_blockers"]


def test_workspace_target_state_cleanup_archives_known_legacy_workspace_roots(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_target_state_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)
    for relpath in (
        "analysis/report.md",
        "assets/input.csv",
        "pipeline/src/job.py",
        "registry/raw_snapshots/manifest.yaml",
        "raw data/source.xlsx",
        ".tmp/probe/result.json",
        "354/scratch.txt",
    ):
        write_text(profile.workspace_root / relpath, "legacy\n")

    result = module.run_workspace_target_state_cleanup(profile_path=profile_path, apply=True)

    archive_root = profile.workspace_root / "archive" / "legacy_root_surfaces" / result["archive_stamp"]
    assert (archive_root / "analysis" / "report.md").is_file()
    assert (archive_root / "assets" / "input.csv").is_file()
    assert (archive_root / "pipeline" / "src" / "job.py").is_file()
    assert (archive_root / "registry" / "raw_snapshots" / "manifest.yaml").is_file()
    assert (archive_root / "raw data" / "source.xlsx").is_file()
    assert (archive_root / ".tmp" / "probe" / "result.json").is_file()
    assert (archive_root / "numeric_scratch" / "354" / "scratch.txt").is_file()


def test_workspace_target_state_cleanup_cli_alias(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)

    exit_code = cli.main(
        [
            "workspace",
            "target-state-cleanup",
            "--profile",
            str(profile_path),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["surface_kind"] == "workspace_target_state_cleanup"
    assert output["mode"] == "dry_run"


def test_workspace_target_state_cleanup_is_not_runtime_public_alias() -> None:
    cli_public_surface = importlib.import_module("med_autoscience.cli_public_surface")

    assert "target-state-cleanup" in cli_public_surface.GROUPED_SUBCOMMANDS["workspace"]
    assert "workspace-target-state-cleanup" not in cli_public_surface.GROUPED_SUBCOMMANDS["runtime"]
    try:
        cli_public_surface.normalize_public_command_argv(["runtime", "workspace-target-state-cleanup", "--dry-run"])
    except SystemExit as exc:
        assert str(exc) == "Grouped command requires a supported subcommand under `runtime`."
    else:
        raise AssertionError("runtime workspace-target-state-cleanup should fail closed")
