from __future__ import annotations

import importlib
from pathlib import Path
import subprocess


def test_workspace_gitignore_excludes_sqlite_runtime_sidecars() -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_git_boundary")

    gitignore_text = module.render_workspace_gitignore()

    assert "*.sqlite" in gitignore_text
    assert "*.sqlite-wal" in gitignore_text
    assert "*.sqlite-shm" in gitignore_text
    assert "*.db-wal" in gitignore_text
    assert "*.db-shm" in gitignore_text


def test_workspace_gitignore_declares_lightweight_study_artifact_boundary() -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_git_boundary")

    gitignore_text = module.render_workspace_gitignore()

    assert "studies/*/artifacts/**" in gitignore_text
    assert "!studies/*/artifacts/README.md" in gitignore_text
    assert "!studies/*/artifacts/evidence_ledger.json" in gitignore_text
    assert "!studies/*/artifacts/review_ledger.json" in gitignore_text
    assert "studies/*/runtime_binding.yaml" in gitignore_text
    assert "studies/*/manuscript/current_package/**" in gitignore_text
    assert "studies/*/manuscript/*.zip" in gitignore_text
    assert "studies/*/manuscript/*.pdf" in gitignore_text
    assert "studies/*/manuscript/*.docx" in gitignore_text
    assert "studies/*/manuscript/*manifest.json" in gitignore_text
    assert "studies/*/paper/submission_minimal/**" in gitignore_text
    assert "studies/*/paper/build/**" in gitignore_text
    assert "studies/*/paper/latex/**" in gitignore_text
    assert "studies/*/paper/figures/**" in gitignore_text
    assert "studies/*/paper/tables/**" in gitignore_text
    assert "studies/*/paper/derived/**" in gitignore_text
    assert "studies/*/analysis/**/*.png" in gitignore_text
    assert "studies/*/analysis/**/*.svg" in gitignore_text


def test_workspace_gitignore_excludes_local_intake_archives_and_framework_mirrors() -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_git_boundary")

    gitignore_text = module.render_workspace_gitignore()

    assert "ops/medautoscience/config.env" in gitignore_text
    assert "ops/mas/config.env" in gitignore_text
    assert "runtime/quests/" in gitignore_text
    assert "runtime/archives/**" in gitignore_text
    assert "!runtime/archives/README.md" in gitignore_text
    assert "runtime/restore_index/**" in gitignore_text
    assert "!runtime/restore_index/README.md" in gitignore_text
    assert "runtime/logs/" in gitignore_text
    assert "artifacts/runtime/" in gitignore_text
    assert "ops/med-deepscientist/config.env" in gitignore_text
    assert "inbox/**" in gitignore_text
    assert "!inbox/README.md" in gitignore_text
    assert "ops/med-deepscientist/runtime/archives/**" in gitignore_text
    assert "!ops/med-deepscientist/runtime/archives/README.md" in gitignore_text
    assert "ops/med-deepscientist/runtime/recovery/**" in gitignore_text
    assert "ops/med-deepscientist/runtime/runtime/**" in gitignore_text
    assert "ops/med-deepscientist/paper/**" in gitignore_text
    assert "ops/framework_refs/_repo_compare/**" in gitignore_text
    assert "!ops/framework_refs/README.md" in gitignore_text
    assert "refs/**/logs/**" in gitignore_text
    assert "refs/**/data/**" in gitignore_text
    assert "refs/**/*.pdf" in gitignore_text
    assert "refs/**/*.html" in gitignore_text
    assert "refs/**/*.Rhistory" in gitignore_text
    assert "refs/**/.cursor/**" in gitignore_text
    assert "datasets/**/*.csv" in gitignore_text
    assert "!datasets/**/dataset_manifest.yaml" in gitignore_text
    assert "portfolio/**/*.csv" in gitignore_text
    assert "studies/*/analysis/**/*.csv" in gitignore_text


def test_workspace_gitignore_merge_preserves_user_rules_and_is_idempotent() -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_git_boundary")
    existing = "# local rules\ncustom_local_state/\n"

    merged = module.merge_workspace_gitignore_content(existing)
    merged_again = module.merge_workspace_gitignore_content(merged)

    assert merged.startswith(existing.rstrip())
    assert "custom_local_state/" in merged
    assert "studies/*/artifacts/**" in merged
    assert merged == merged_again


def test_init_workspace_dry_run_reports_workspace_git_plan(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "dry-run-git-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="dry-run-git",
        dry_run=True,
        force=False,
    )

    assert str(workspace_root / ".gitignore") in result["created_files"]
    assert result["workspace_git"] == {
        "enabled": True,
        "initialized": False,
        "already_initialized": False,
        "would_initialize": True,
        "git_dir": str(workspace_root / ".git"),
        "gitignore_path": str(workspace_root / ".gitignore"),
    }
    assert not workspace_root.exists()


def test_init_workspace_creates_outer_git_boundary_and_ignores_generated_study_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "git-boundary-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="git-boundary",
        dry_run=False,
        force=False,
    )

    assert (workspace_root / ".git").exists()
    assert result["workspace_git"]["enabled"] is True
    assert result["workspace_git"]["initialized"] is True
    assert result["workspace_git"]["already_initialized"] is False
    workspace_gitignore = workspace_root / ".gitignore"
    assert workspace_gitignore.is_file()
    workspace_gitignore_text = workspace_gitignore.read_text(encoding="utf-8")
    assert "runtime/quests/" in workspace_gitignore_text
    assert "ops/med-deepscientist/runtime/quests/" in workspace_gitignore_text

    mas_quest_payload = workspace_root / "runtime" / "quests" / "001" / "scratch.txt"
    mas_quest_payload.parent.mkdir(parents=True, exist_ok=True)
    mas_quest_payload.write_text("runtime-owned\n", encoding="utf-8")
    check_mas_quest_payload = subprocess.run(
        ["git", "check-ignore", str(mas_quest_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_mas_quest_payload.returncode == 0

    nested_quest_payload = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "001" / "scratch.txt"
    nested_quest_payload.parent.mkdir(parents=True, exist_ok=True)
    nested_quest_payload.write_text("runtime-owned\n", encoding="utf-8")
    check_ignore = subprocess.run(
        ["git", "check-ignore", str(nested_quest_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_ignore.returncode == 0
    branch_name = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    relative_paths = subprocess.run(
        ["git", "config", "worktree.useRelativePaths"],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    assert branch_name == "main"
    assert relative_paths == "true"
    assert _git_config(workspace_root, "gc.auto") == "0"
    assert _git_config(workspace_root, "gc.autoPackLimit") == "0"
    assert _git_config(workspace_root, "maintenance.auto") == "false"

    large_download = workspace_root / "portfolio" / "data_assets" / "public" / "downloads" / "asset.zip"
    large_download.parent.mkdir(parents=True, exist_ok=True)
    large_download.write_text("data\n", encoding="utf-8")
    check_large_download = subprocess.run(
        ["git", "check-ignore", str(large_download.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_large_download.returncode == 0

    generated_artifact = workspace_root / "studies" / "001" / "artifacts" / "runtime" / "event.json"
    generated_artifact.parent.mkdir(parents=True, exist_ok=True)
    generated_artifact.write_text("{}\n", encoding="utf-8")
    check_generated_artifact = subprocess.run(
        ["git", "check-ignore", str(generated_artifact.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_generated_artifact.returncode == 0

    runtime_binding = workspace_root / "studies" / "001" / "runtime_binding.yaml"
    runtime_binding.parent.mkdir(parents=True, exist_ok=True)
    runtime_binding.write_text("last_action_at: '2026-05-01T00:00:00+00:00'\n", encoding="utf-8")
    check_runtime_binding = subprocess.run(
        ["git", "check-ignore", str(runtime_binding.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_runtime_binding.returncode == 0

    current_package_docx = workspace_root / "studies" / "001" / "manuscript" / "current_package" / "paper.docx"
    current_package_docx.parent.mkdir(parents=True, exist_ok=True)
    current_package_docx.write_text("docx placeholder\n", encoding="utf-8")
    check_current_package = subprocess.run(
        ["git", "check-ignore", str(current_package_docx.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_current_package.returncode == 0

    inbox_payload = workspace_root / "inbox" / "raw-upload.zip"
    inbox_payload.parent.mkdir(parents=True, exist_ok=True)
    inbox_payload.write_text("binary placeholder\n", encoding="utf-8")
    check_inbox_payload = subprocess.run(
        ["git", "check-ignore", str(inbox_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_inbox_payload.returncode == 0

    mas_archived_runtime_payload = workspace_root / "runtime" / "archives" / "quests" / "001" / ".ds" / "log.jsonl"
    mas_archived_runtime_payload.parent.mkdir(parents=True, exist_ok=True)
    mas_archived_runtime_payload.write_text("{}\n", encoding="utf-8")
    check_mas_archived_runtime_payload = subprocess.run(
        ["git", "check-ignore", str(mas_archived_runtime_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_mas_archived_runtime_payload.returncode == 0

    mas_restore_index_payload = workspace_root / "runtime" / "restore_index" / "quests" / "001.json"
    mas_restore_index_payload.parent.mkdir(parents=True, exist_ok=True)
    mas_restore_index_payload.write_text("{}\n", encoding="utf-8")
    check_mas_restore_index_payload = subprocess.run(
        ["git", "check-ignore", str(mas_restore_index_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_mas_restore_index_payload.returncode == 0

    archived_runtime_payload = workspace_root / "ops" / "med-deepscientist" / "runtime" / "archives" / "quests" / "001" / ".ds" / "log.jsonl"
    archived_runtime_payload.parent.mkdir(parents=True, exist_ok=True)
    archived_runtime_payload.write_text("{}\n", encoding="utf-8")
    check_archived_runtime_payload = subprocess.run(
        ["git", "check-ignore", str(archived_runtime_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_archived_runtime_payload.returncode == 0

    framework_mirror_payload = workspace_root / "ops" / "framework_refs" / "_repo_compare" / "DeepScientist" / ".git" / "objects" / "pack" / "pack.idx"
    framework_mirror_payload.parent.mkdir(parents=True, exist_ok=True)
    framework_mirror_payload.write_text("git object placeholder\n", encoding="utf-8")
    check_framework_mirror_payload = subprocess.run(
        ["git", "check-ignore", str(framework_mirror_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_framework_mirror_payload.returncode == 0

    legacy_paper_payload = workspace_root / "ops" / "med-deepscientist" / "paper" / "submission_minimal" / "paper.pdf"
    legacy_paper_payload.parent.mkdir(parents=True, exist_ok=True)
    legacy_paper_payload.write_text("pdf placeholder\n", encoding="utf-8")
    check_legacy_paper_payload = subprocess.run(
        ["git", "check-ignore", str(legacy_paper_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_legacy_paper_payload.returncode == 0

    dataset_payload = workspace_root / "datasets" / "master" / "v1" / "analysis.csv"
    dataset_payload.parent.mkdir(parents=True, exist_ok=True)
    dataset_payload.write_text("id\n1\n", encoding="utf-8")
    check_dataset_payload = subprocess.run(
        ["git", "check-ignore", str(dataset_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_dataset_payload.returncode == 0

    local_runtime_config = workspace_root / "ops" / "medautoscience" / "config.env"
    local_runtime_config.parent.mkdir(parents=True, exist_ok=True)
    local_runtime_config.write_text("MED_AUTOSCIENCE_REPO=/local/path\n", encoding="utf-8")
    check_local_runtime_config = subprocess.run(
        ["git", "check-ignore", str(local_runtime_config.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_local_runtime_config.returncode == 0

    runtime_lifecycle_db = workspace_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    runtime_lifecycle_db.parent.mkdir(parents=True, exist_ok=True)
    runtime_lifecycle_db.write_text("sqlite placeholder\n", encoding="utf-8")
    check_runtime_lifecycle_db = subprocess.run(
        ["git", "check-ignore", str(runtime_lifecycle_db.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_runtime_lifecycle_db.returncode == 0

    runtime_lifecycle_wal = workspace_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite-wal"
    runtime_lifecycle_wal.write_text("wal placeholder\n", encoding="utf-8")
    check_runtime_lifecycle_wal = subprocess.run(
        ["git", "check-ignore", str(runtime_lifecycle_wal.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_runtime_lifecycle_wal.returncode == 0

    portfolio_evidence_table = workspace_root / "portfolio" / "legacy_audit" / "evidence" / "metrics.csv"
    portfolio_evidence_table.parent.mkdir(parents=True, exist_ok=True)
    portfolio_evidence_table.write_text("metric,value\nc_index,0.7\n", encoding="utf-8")
    check_portfolio_evidence_table = subprocess.run(
        ["git", "check-ignore", str(portfolio_evidence_table.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_portfolio_evidence_table.returncode == 0

    legacy_html_report = workspace_root / "refs" / "legacy" / "reports" / "final.html"
    legacy_html_report.parent.mkdir(parents=True, exist_ok=True)
    legacy_html_report.write_text("<html></html>\n", encoding="utf-8")
    check_legacy_html_report = subprocess.run(
        ["git", "check-ignore", str(legacy_html_report.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_legacy_html_report.returncode == 0

    legacy_cursor_rule = workspace_root / "refs" / "legacy" / ".cursor" / "rules" / "local.mdc"
    legacy_cursor_rule.parent.mkdir(parents=True, exist_ok=True)
    legacy_cursor_rule.write_text("local editor rule\n", encoding="utf-8")
    check_legacy_cursor_rule = subprocess.run(
        ["git", "check-ignore", str(legacy_cursor_rule.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_legacy_cursor_rule.returncode == 0

    dataset_manifest = workspace_root / "datasets" / "master" / "v1" / "dataset_manifest.yaml"
    dataset_manifest.write_text("dataset_id: master\n", encoding="utf-8")
    check_dataset_manifest = subprocess.run(
        ["git", "check-ignore", str(dataset_manifest.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_dataset_manifest.returncode == 1

    analysis_payload = workspace_root / "studies" / "001" / "analysis" / "run1" / "outputs.csv"
    analysis_payload.parent.mkdir(parents=True, exist_ok=True)
    analysis_payload.write_text("id\n1\n", encoding="utf-8")
    check_analysis_payload = subprocess.run(
        ["git", "check-ignore", str(analysis_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_analysis_payload.returncode == 0

    analysis_figure = workspace_root / "studies" / "001" / "analysis" / "run1" / "figures" / "Figure1.png"
    analysis_figure.parent.mkdir(parents=True, exist_ok=True)
    analysis_figure.write_text("png placeholder\n", encoding="utf-8")
    check_analysis_figure = subprocess.run(
        ["git", "check-ignore", str(analysis_figure.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_analysis_figure.returncode == 0

    paper_derived_payload = workspace_root / "studies" / "001" / "paper" / "derived" / "run1" / "means.csv"
    paper_derived_payload.parent.mkdir(parents=True, exist_ok=True)
    paper_derived_payload.write_text("id\n1\n", encoding="utf-8")
    check_paper_derived_payload = subprocess.run(
        ["git", "check-ignore", str(paper_derived_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_paper_derived_payload.returncode == 0

    manuscript_manifest = workspace_root / "studies" / "001" / "manuscript" / "delivery_manifest.json"
    manuscript_manifest.parent.mkdir(parents=True, exist_ok=True)
    manuscript_manifest.write_text("{}\n", encoding="utf-8")
    check_manuscript_manifest = subprocess.run(
        ["git", "check-ignore", str(manuscript_manifest.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_manuscript_manifest.returncode == 0


def test_init_workspace_backfills_gitignore_and_git_config_for_existing_repo(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "existing-git-workspace"
    workspace_root.mkdir()
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, text=True, capture_output=True)
    (workspace_root / ".gitignore").write_text("custom-local-rule/\n", encoding="utf-8")

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="existing-git",
        dry_run=False,
        force=False,
    )

    assert result["workspace_git"]["initialized"] is False
    assert result["workspace_git"]["already_initialized"] is True
    workspace_gitignore = (workspace_root / ".gitignore").read_text(encoding="utf-8")
    assert "custom-local-rule/" in workspace_gitignore
    assert "datasets/standardized_longitudinal/" in workspace_gitignore
    assert "storage_audit/" in workspace_gitignore
    assert "studies/*/artifacts/**" in workspace_gitignore
    assert _git_config(workspace_root, "worktree.useRelativePaths") == "true"
    assert _git_config(workspace_root, "gc.auto") == "0"
    assert _git_config(workspace_root, "gc.autoPackLimit") == "0"
    assert _git_config(workspace_root, "maintenance.auto") == "false"


def test_init_workspace_can_skip_workspace_git_initialization(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "no-git-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="no-git",
        dry_run=False,
        force=False,
        initialize_git=False,
    )

    assert result["workspace_git"] == {
        "enabled": False,
        "initialized": False,
        "already_initialized": False,
        "would_initialize": False,
        "git_dir": str(workspace_root / ".git"),
        "gitignore_path": str(workspace_root / ".gitignore"),
    }
    assert not (workspace_root / ".git").exists()
    assert (workspace_root / ".gitignore").is_file()


def _git_config(workspace_root: Path, key: str) -> str:
    return subprocess.run(
        ["git", "config", "--get", key],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
