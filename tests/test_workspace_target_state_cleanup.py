from __future__ import annotations

import importlib
import json
import shutil
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
    write_text(workspace_root / "ops" / "medautoscience" / "bin" / "legacy-control-surface-clean-migration", "legacy\n")
    write_text(workspace_root / "ops" / "medautoscience" / "config.env", 'WORKSPACE_PYTHON="${WORKSPACE_ROOT}/.venv/bin/python3"\n')
    write_text(workspace_root / "ops" / "medautoscience" / "config.env.bak-20260504T124135Z", "legacy backup\n")
    write_text(workspace_root / "ops" / "medautoscience" / "logs" / "watch-runtime.stdout.log", "legacy log\n")
    write_text(workspace_root / "ops" / "medautoscience" / "python_pycache" / "cache.pyc", "cache\n")
    write_text(workspace_root / "ops" / "mas" / "bin" / "status", "legacy bridge\n")
    write_text(workspace_root / "ops" / "mas" / "config.env", "legacy bridge config\n")
    write_text(workspace_root / "ops" / "mas" / "README.md", "legacy bridge readme\n")
    write_text(workspace_root / "ops" / "mas" / "behavior_equivalence_gate.yaml", "schema_version: v1\n")
    write_text(workspace_root / "ops" / "mas" / "progress" / "index.html", "<html></html>\n")
    write_text(workspace_root / "ops" / "deepscientist" / "README.md", "legacy ds\n")
    write_text(workspace_root / "ops" / "med-deepscientist.TOMBSTONE.json", "{}\n")
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


def test_workspace_target_state_cleanup_visual_clean_archives_study_local_residue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_target_state_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)
    study_root = write_study(profile.workspace_root, "003-dpcc", quest_id="003-dpcc")
    write_text(study_root / "STUDY_STATUS.md", "status\n")
    write_text(study_root / "paper.yaml", "{}\n")
    write_text(study_root / "control" / "stage_index.json", "{}\n")
    write_text(study_root / "artifacts" / "stage_outputs" / "01-intake" / "stage_manifest.json", "{}\n")
    write_text(study_root / "paper" / "draft.md", "draft\n")
    write_text(study_root / "analysis" / "analysis_plan.md", "plan\n")
    write_text(study_root / "evidence" / "evidence_ledger.json", "{}\n")
    write_text(study_root / "publication" / "current_package" / "STATUS.json", "{}\n")
    write_text(study_root / ".ds" / "runtime_state.json", "{}\n")
    write_text(study_root / "manuscript" / "current_package" / "paper.docx", "")
    write_text(study_root / "notes" / "old.md", "old\n")
    write_text(study_root / "experiments" / "analysis-results" / "result.json", "{}\n")
    write_text(study_root / "submission_packages" / "journal" / "package.zip", "")
    write_text(study_root / "portfolio" / "research_memory" / "note.md", "memory\n")
    write_text(study_root / "tmp" / "scratch.txt", "scratch\n")
    write_text(study_root / "CHECKLIST.md", "legacy checklist\n")
    write_text(study_root / "PLAN.md", "legacy plan\n")

    dry_run = module.run_workspace_target_state_cleanup(
        profile_path=profile_path,
        apply=False,
        visual_clean=True,
    )

    visual_plan = dry_run["study_visual_cleanup"]
    assert visual_plan["enabled"] is True
    decisions = {
        action["source_relative_path"]: action["decision"]
        for action in visual_plan["study_actions"]
        if action["study_id"] == "003-dpcc"
    }
    assert decisions["runtime_binding.yaml"] == "keep_active_locator_tail"
    assert decisions["manuscript"] == "archive"
    assert decisions["notes"] == "archive"
    assert decisions["experiments"] == "archive"
    assert decisions["submission_packages"] == "archive"
    assert decisions["portfolio"] == "archive"
    assert decisions["tmp"] == "archive"
    assert decisions["CHECKLIST.md"] == "archive"
    assert decisions["PLAN.md"] == "archive"

    result = module.run_workspace_target_state_cleanup(
        profile_path=profile_path,
        apply=True,
        visual_clean=True,
    )

    archive_root = study_root / "_archive" / "legacy_surfaces" / result["archive_stamp"]
    assert (archive_root / ".ds" / "runtime_state.json").is_file()
    assert (archive_root / "manuscript" / "current_package" / "paper.docx").is_file()
    assert (archive_root / "notes" / "old.md").is_file()
    assert (archive_root / "experiments" / "analysis-results" / "result.json").is_file()
    assert (archive_root / "submission_packages" / "journal" / "package.zip").is_file()
    assert (archive_root / "portfolio" / "research_memory" / "note.md").is_file()
    assert (archive_root / "tmp" / "scratch.txt").is_file()
    assert (archive_root / "CHECKLIST.md").is_file()
    assert (archive_root / "PLAN.md").is_file()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "notes").exists()
    assert not (study_root / "experiments").exists()
    assert not (study_root / "submission_packages").exists()
    assert (study_root / "runtime_binding.yaml").is_file()
    assert set(item.name for item in study_root.iterdir()) == {
        "STUDY_STATUS.md",
        "_archive",
        "analysis",
        "artifacts",
        "control",
        "evidence",
        "paper",
        "paper.yaml",
        "publication",
        "runtime_binding.yaml",
        "study.yaml",
    }
    assert result["validation"]["study_visual_locator_tails"][0]["source"] == "runtime_binding.yaml"


def test_workspace_target_state_cleanup_visual_clean_archives_ops_residue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_target_state_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)

    dry_run = module.run_workspace_target_state_cleanup(
        profile_path=profile_path,
        apply=False,
        visual_clean=True,
    )

    ops_decisions = {
        action["workspace_relative_path"]: action["decision"]
        for action in dry_run["ops_visual_cleanup"]["ops_actions"]
    }
    assert ops_decisions["ops/medautoscience"] == "keep_active_ops_root"
    assert ops_decisions["ops/medautoscience/bin/_shared.sh"] == "keep_active_ops_child"
    assert ops_decisions["ops/medautoscience/logs"] == "archive"
    assert ops_decisions["ops/medautoscience/python_pycache"] == "archive"
    assert ops_decisions["ops/medautoscience/bin/legacy-control-surface-clean-migration"] == "archive"
    assert ops_decisions["ops/medautoscience/config.env.bak-20260504T124135Z"] == "archive"
    assert ops_decisions["ops/mas"] == "keep_active_ops_root"
    assert ops_decisions["ops/mas/progress"] == "keep_active_ops_child"
    assert ops_decisions["ops/mas/bin"] == "archive"
    assert ops_decisions["ops/mas/config.env"] == "archive"
    assert ops_decisions["ops/mas/behavior_equivalence_gate.yaml"] == "archive"
    assert ops_decisions["ops/deepscientist"] == "archive"
    assert ops_decisions["ops/framework_refs"] == "archive"
    assert ops_decisions["ops/med-deepscientist.TOMBSTONE.json"] == "archive"

    result = module.run_workspace_target_state_cleanup(
        profile_path=profile_path,
        apply=True,
        visual_clean=True,
    )

    archive_root = profile.workspace_root / "archive" / "legacy_ops_surfaces" / result["archive_stamp"]
    assert (archive_root / "medautoscience" / "logs" / "watch-runtime.stdout.log").is_file()
    assert (archive_root / "medautoscience" / "python_pycache" / "cache.pyc").is_file()
    assert (archive_root / "medautoscience" / "bin" / "legacy-control-surface-clean-migration").is_file()
    assert (archive_root / "medautoscience" / "config.env.bak-20260504T124135Z").is_file()
    assert (archive_root / "mas" / "bin" / "status").is_file()
    assert (archive_root / "mas" / "config.env").is_file()
    assert (archive_root / "mas" / "behavior_equivalence_gate.yaml").is_file()
    assert (archive_root / "deepscientist" / "README.md").is_file()
    assert (archive_root / "framework_refs" / "_repo_compare" / "fixture.py").is_file()
    assert (archive_root / "med-deepscientist.TOMBSTONE.json").is_file()
    assert not (profile.workspace_root / "ops" / "medautoscience" / "logs").exists()
    assert not (profile.workspace_root / "ops" / "medautoscience" / "python_pycache").exists()
    assert not (profile.workspace_root / "ops" / "medautoscience" / "bin" / "legacy-control-surface-clean-migration").exists()
    assert not (profile.workspace_root / "ops" / "mas" / "bin").exists()
    assert not (profile.workspace_root / "ops" / "deepscientist").exists()
    assert not (profile.workspace_root / "ops" / "framework_refs").exists()
    assert (profile.workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh").is_file()
    assert (profile.workspace_root / "ops" / "mas" / "progress" / "index.html").is_file()
    assert result["validation"]["ops_visual_clean_enabled"] is True
    assert result["validation"]["legacy_ops_current_truth"] is False
    target_map = {(item["source"], item["target"]) for item in result["target_path_map"]}
    assert (
        "ops/mas/bin",
        f"archive/legacy_ops_surfaces/{result['archive_stamp']}/mas/bin",
    ) in target_map


def test_workspace_target_state_cleanup_visual_clean_blocks_unknown_medautoscience_wrapper(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_target_state_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)
    write_text(profile.workspace_root / "ops" / "medautoscience" / "bin" / "local-debug-wrapper", "custom\n")

    result = module.run_workspace_target_state_cleanup(
        profile_path=profile_path,
        apply=False,
        visual_clean=True,
    )

    assert result["status"] == "typed_blocked"
    assert (
        "unclassified_ops_root_entry_medautoscience_bin_local_debug_wrapper"
        in result["validation"]["non_terminal_blockers"]
    )
    actions = {
        action["workspace_relative_path"]: action
        for action in result["ops_visual_cleanup"]["ops_actions"]
    }
    assert actions["ops/medautoscience/bin/local-debug-wrapper"]["decision"] == "blocked_unclassified_ops_root"


def test_workspace_target_state_cleanup_visual_clean_archives_broken_ops_symlink(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_target_state_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    _write_legacy_workspace(profile.workspace_root)
    legacy_link = profile.workspace_root / "ops" / "deepscientist"
    shutil.rmtree(legacy_link)
    legacy_link.symlink_to("med-deepscientist")

    dry_run = module.run_workspace_target_state_cleanup(
        profile_path=profile_path,
        apply=False,
        visual_clean=True,
    )

    actions = {
        action["workspace_relative_path"]: action
        for action in dry_run["ops_visual_cleanup"]["ops_actions"]
    }
    assert actions["ops/deepscientist"]["decision"] == "archive"
    assert actions["ops/deepscientist"]["exists"] is True
    assert actions["ops/deepscientist"]["kind"] == "symlink"
    assert actions["ops/deepscientist"]["symlink_target"] == "med-deepscientist"

    result = module.run_workspace_target_state_cleanup(
        profile_path=profile_path,
        apply=True,
        visual_clean=True,
    )

    archived_link = profile.workspace_root / "archive" / "legacy_ops_surfaces" / result["archive_stamp"] / "deepscientist"
    assert archived_link.is_symlink()
    assert archived_link.readlink() == Path("med-deepscientist")
    assert not legacy_link.exists()
    assert not legacy_link.is_symlink()


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
            "--visual-clean",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["surface_kind"] == "workspace_target_state_cleanup"
    assert output["mode"] == "dry_run"
    assert output["visual_clean_enabled"] is True


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
