from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "repo_hygiene_audit.py"


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)


def _run_audit(root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--root", str(root)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_repo_hygiene_audit_allows_explicit_root_exceptions(tmp_path: Path) -> None:
    _git_init(tmp_path)
    (tmp_path / ".worktrees" / "lane" / "build").mkdir(parents=True)
    (tmp_path / "RTK.md").write_text("runtime toolkit notes\n", encoding="utf-8")

    result = _run_audit(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "repo hygiene audit passed" in result.stdout


def test_repo_hygiene_audit_rejects_banned_root_artifacts(tmp_path: Path) -> None:
    _git_init(tmp_path)
    for directory_name in (
        "ops",
        "build",
        "dist",
        "tmp",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    ):
        (tmp_path / directory_name).mkdir()
    (tmp_path / ".DS_Store").write_text("", encoding="utf-8")
    (tmp_path / "src" / "med_autoscience.egg-info").mkdir(parents=True)

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert "repo hygiene audit failed" in result.stderr
    for expected_path in (
        "ops",
        "build",
        "dist",
        "tmp",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".DS_Store",
        "src/med_autoscience.egg-info",
    ):
        assert expected_path in result.stderr


def test_repo_hygiene_audit_rejects_nested_banned_artifacts(tmp_path: Path) -> None:
    _git_init(tmp_path)
    (tmp_path / "src" / "med_autoscience" / "__pycache__").mkdir(parents=True)

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert "src/med_autoscience/__pycache__" in result.stderr
