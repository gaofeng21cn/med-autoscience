from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "prepare-sentrux-gitstats-clone.sh"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _read_key_value_output(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_sentrux_gitstats_helper_script_contract() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert os.access(SCRIPT, os.X_OK)
    assert 'repo_root="$(git -C "${repo_root_arg}" rev-parse --show-toplevel)"' in script
    assert "git clone --quiet --shared --no-checkout" in script
    assert 'git -C "${clone_path}" checkout --quiet --detach "${source_head}"' in script
    assert "extensions.relativeWorktrees" in script
    assert "worktree.useRelativePaths" in script
    assert "git config --unset" not in script
    assert "git -C \"${repo_root}\" config" not in script
    assert "cleanup_command=rm -rf" in script


def test_prepare_sentrux_gitstats_clone_preserves_source_relative_worktree_config(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init")
    _git(source, "config", "user.email", "test@example.com")
    _git(source, "config", "user.name", "Test User")
    _git(source, "config", "commit.gpgsign", "false")
    _git(source, "config", "worktree.useRelativePaths", "true")
    (source / "README.md").write_text("sentrux helper fixture\n", encoding="utf-8")
    _git(source, "add", "README.md")
    _git(source, "commit", "-m", "initial fixture")
    source_head = _git(source, "rev-parse", "HEAD").stdout.strip()

    result = subprocess.run(
        [str(SCRIPT), "--repo-root", str(source), "--tmp-root", str(tmp_path / "clones")],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    values = _read_key_value_output(result.stdout)
    clone_path = Path(values["sentrux_git_stats_clone"])
    try:
        assert clone_path.is_dir()
        assert values["source_head"] == source_head
        assert values["extensions_relativeWorktrees"] == "absent"
        assert values["cleanup_command"].startswith("rm -rf ")
        assert (clone_path / "README.md").read_text(encoding="utf-8") == "sentrux helper fixture\n"
        assert _git(clone_path, "rev-parse", "HEAD").stdout.strip() == source_head
        assert _git(source, "config", "worktree.useRelativePaths").stdout.strip() == "true"

        clone_extension = subprocess.run(
            ["git", "-C", str(clone_path), "config", "--local", "--get", "extensions.relativeWorktrees"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert clone_extension.returncode != 0
    finally:
        shutil.rmtree(clone_path.parent, ignore_errors=True)
