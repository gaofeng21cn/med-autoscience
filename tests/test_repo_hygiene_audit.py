from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "repo_hygiene_audit.py"


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)


def _track(root: Path, relative_path: str, content: str = "") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", relative_path], cwd=root, check=True, capture_output=True, text=True)


def _run_audit(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--root", str(root), *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
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


@pytest.mark.parametrize(
    ("relative_path", "is_directory"),
    [
        ("ops", True), ("build", True), ("dist", True),
        ("tmp", True), (".venv", True), ("__pycache__", True),
        (".pytest_cache", True), (".ruff_cache", True), (".mypy_cache", True),
        ("src/med_autoscience/__pycache__", True),
        ("src/med_autoscience.egg-info", True),
        (".DS_Store", False),
    ],
)
def test_repo_hygiene_audit_rejects_banned_artifacts(
    tmp_path: Path,
    relative_path: str,
    is_directory: bool,
) -> None:
    _git_init(tmp_path)
    path = tmp_path / relative_path
    if is_directory:
        path.mkdir(parents=True)
    else:
        path.write_text("", encoding="utf-8")

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert relative_path in result.stderr


@pytest.mark.parametrize(
    ("relative_path", "content", "reason"),
    [
        (
            "src/med_autoscience/domain_owner_action_dispatch.py",
            "def main(): pass\n",
            "retired_domain_owner_action_dispatch_active_path",
        ),
        (
            "src/med_autoscience/mas_runtime_scheduler.py",
            "def main(): pass\n",
            "retired_mas_local_scheduler_active_path",
        ),
        (
            "src/med_autoscience/cli/parser.py",
            'parser.add_parser("domain-health-diagnostic")\n',
            "retired_domain_health_diagnostic_entrypoint",
        ),
    ],
)
def test_repo_hygiene_audit_rejects_retired_active_surfaces(
    tmp_path: Path,
    relative_path: str,
    content: str,
    reason: str,
) -> None:
    _git_init(tmp_path)
    _track(tmp_path, relative_path, content)

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert reason in result.stderr


def test_repo_hygiene_audit_allows_opl_scheduler_contract_vocabulary(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _track(
        tmp_path,
        "contracts/runtime/opl_scheduler_boundary.json",
        '{"scheduler_owner": "opl_current_control_state"}\n',
    )

    result = _run_audit(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_repo_hygiene_audit_fix_removes_only_ignored_artifacts(tmp_path: Path) -> None:
    _git_init(tmp_path)
    ignored = tmp_path / "src" / "med_autoscience" / "__pycache__"
    ignored.mkdir(parents=True)
    (ignored / "module.pyc").write_bytes(b"cache")
    unignored = tmp_path / "other" / "__pycache__"
    unignored.mkdir(parents=True)
    (tmp_path / ".gitignore").write_text("src/med_autoscience/__pycache__/\n", encoding="utf-8")

    result = _run_audit(tmp_path, "--fix")

    assert result.returncode == 1
    assert not ignored.exists()
    assert unignored.exists()
    assert "other/__pycache__" in result.stderr


def test_repo_hygiene_audit_remove_path_is_idempotent_and_does_not_dereference_symlink(
    tmp_path: Path,
) -> None:
    spec = importlib.util.spec_from_file_location("repo_hygiene_audit", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = tmp_path / "outside-target"
    target.mkdir()
    target_file = target / "keep.txt"
    target_file.write_text("keep\n", encoding="utf-8")
    cache_link = tmp_path / "__pycache__"
    cache_link.symlink_to(target, target_is_directory=True)

    module._remove_path(cache_link)
    module._remove_path(cache_link)

    assert not cache_link.exists()
    assert not cache_link.is_symlink()
    assert target_file.read_text(encoding="utf-8") == "keep\n"
