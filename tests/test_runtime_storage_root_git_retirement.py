from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_audit_workspace_storage_git_only_retires_workspace_root_git_with_restore_bundle(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    workspace_root = profile.workspace_root
    workspace_root.mkdir(parents=True, exist_ok=True)
    module.git_garbage._run_git_command(["init"], workspace_root=workspace_root, check=True)
    module.git_garbage._run_git_command(["config", "user.email", "test@example.com"], workspace_root=workspace_root, check=True)
    module.git_garbage._run_git_command(["config", "user.name", "Test User"], workspace_root=workspace_root, check=True)
    (workspace_root / "README.md").write_text("tracked\n", encoding="utf-8")
    module.git_garbage._run_git_command(["add", "README.md"], workspace_root=workspace_root, check=True)
    module.git_garbage._run_git_command(["commit", "-m", "baseline"], workspace_root=workspace_root, check=True)
    dirty_file = workspace_root / "studies" / "001-risk" / "paper" / "draft.md"
    dirty_file.parent.mkdir(parents=True, exist_ok=True)
    dirty_file.write_text("dirty paper truth remains untouched\n", encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        all_studies=False,
        apply=True,
        git_only=True,
        retire_workspace_root_git=True,
    )

    git_report = result["categories"]["git"]
    retirement = git_report["workspace_root_git_retirement_result"]
    assert retirement["status"] == "retired"
    assert retirement["verified_git_absent"] is True
    assert not (workspace_root / ".git").exists()
    assert dirty_file.read_text(encoding="utf-8") == "dirty paper truth remains untouched\n"
    archive_path = Path(retirement["archive_path"])
    manifest_path = Path(retirement["manifest_path"])
    latest_path = Path(retirement["latest_path"])
    assert archive_path.is_file()
    assert manifest_path.is_file()
    assert latest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["archive"]["sha256"] == retirement["archive_sha256"]
    assert manifest["before"]["health"]["has_commits"] is True
    assert manifest["after"]["health"]["git_exists"] is False
    assert "tar -xzf" in manifest["restore_command"]
    assert result["selection"]["retire_workspace_root_git"] is True
    assert result["summary"]["git_actual_release_bytes"] >= retirement["released_bytes"]


def test_audit_workspace_storage_git_only_blocks_workspace_root_git_retirement_with_remote(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    workspace_root = profile.workspace_root
    workspace_root.mkdir(parents=True, exist_ok=True)
    module.git_garbage._run_git_command(["init"], workspace_root=workspace_root, check=True)
    module.git_garbage._run_git_command(
        ["remote", "add", "origin", "https://example.invalid/repo.git"],
        workspace_root=workspace_root,
        check=True,
    )

    result = module.audit_workspace_storage(
        profile=profile,
        all_studies=False,
        apply=True,
        git_only=True,
        retire_workspace_root_git=True,
    )

    retirement = result["categories"]["git"]["workspace_root_git_retirement_result"]
    assert retirement["status"] == "blocked_not_eligible"
    assert "has_remotes" in retirement["blockers"]
    assert (workspace_root / ".git").is_dir()
