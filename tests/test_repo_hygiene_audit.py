from __future__ import annotations

import os
import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "repo_hygiene_audit.py"


def _load_repo_hygiene_module():
    spec = importlib.util.spec_from_file_location("repo_hygiene_audit", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_repo_hygiene_audit_rejects_retired_active_surface_paths(tmp_path: Path) -> None:
    _git_init(tmp_path)
    active_file = tmp_path / "src" / "med_autoscience" / "domain_owner_action_dispatch.py"
    active_file.parent.mkdir(parents=True)
    active_file.write_text("def main(): pass\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/med_autoscience/domain_owner_action_dispatch.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert "retired_domain_owner_action_dispatch_active_path" in result.stderr


def test_repo_hygiene_audit_rejects_retired_mas_local_scheduler_paths(tmp_path: Path) -> None:
    _git_init(tmp_path)
    active_file = tmp_path / "src" / "med_autoscience" / "mas_runtime_scheduler.py"
    active_file.parent.mkdir(parents=True)
    active_file.write_text("def main(): pass\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/med_autoscience/mas_runtime_scheduler.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert "retired_mas_local_scheduler_active_path" in result.stderr


def test_repo_hygiene_audit_allows_opl_scheduler_contract_vocabulary(tmp_path: Path) -> None:
    _git_init(tmp_path)
    contract_file = tmp_path / "contracts" / "runtime" / "opl_scheduler_boundary.json"
    contract_file.parent.mkdir(parents=True)
    contract_file.write_text('{"scheduler_owner": "opl_current_control_state"}\n', encoding="utf-8")
    subprocess.run(
        ["git", "add", "contracts/runtime/opl_scheduler_boundary.json"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run_audit(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_repo_hygiene_audit_rejects_retired_entrypoint_tokens(tmp_path: Path) -> None:
    _git_init(tmp_path)
    entrypoint = tmp_path / "src" / "med_autoscience" / "cli_parts" / "parser.py"
    entrypoint.parent.mkdir(parents=True)
    entrypoint.write_text('parser.add_parser("domain-health-diagnostic")\n', encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/med_autoscience/cli_parts/parser.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert "retired_domain_health_diagnostic_entrypoint" in result.stderr


def test_repo_hygiene_audit_allows_retired_terms_in_history_paths(tmp_path: Path) -> None:
    _git_init(tmp_path)
    history_file = tmp_path / "docs" / "history" / "domain_owner_action_dispatch.md"
    history_file.parent.mkdir(parents=True)
    history_file.write_text("domain-owner-action-dispatch tombstone\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "docs/history/domain_owner_action_dispatch.md"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run_audit(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_repo_hygiene_audit_allows_retired_terms_in_runtime_docs(tmp_path: Path) -> None:
    _git_init(tmp_path)
    runtime_doc = tmp_path / "docs" / "runtime" / "contracts" / "runtime_boundary.md"
    runtime_doc.parent.mkdir(parents=True)
    runtime_doc.write_text("default-executor is retired; OPL owns scheduler.\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "docs/runtime/contracts/runtime_boundary.md"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run_audit(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_repo_hygiene_audit_fix_removes_only_ignored_artifacts(tmp_path: Path) -> None:
    _git_init(tmp_path)
    ignored_cache = tmp_path / "src" / "med_autoscience" / "__pycache__"
    ignored_cache.mkdir(parents=True)
    (ignored_cache / "module.pyc").write_bytes(b"cache")
    unignored_cache = tmp_path / "other" / "__pycache__"
    unignored_cache.mkdir(parents=True)
    (tmp_path / ".gitignore").write_text("src/med_autoscience/__pycache__/\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--root", str(tmp_path), "--fix"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "repo hygiene audit removed ignored artifact: src/med_autoscience/__pycache__" in result.stdout
    assert ignored_cache.exists() is False
    assert unignored_cache.exists() is True
    assert "other/__pycache__" in result.stderr


def test_repo_hygiene_audit_remove_path_is_idempotent(tmp_path: Path) -> None:
    module = _load_repo_hygiene_module()
    cache_dir = tmp_path / "src" / "med_autoscience.egg-info"
    cache_dir.mkdir(parents=True)
    (cache_dir / "PKG-INFO").write_text("metadata\n", encoding="utf-8")

    module._remove_path(cache_dir)
    module._remove_path(cache_dir)

    assert cache_dir.exists() is False


def test_repo_hygiene_audit_remove_path_does_not_dereference_directory_symlink(tmp_path: Path) -> None:
    module = _load_repo_hygiene_module()
    target_dir = tmp_path / "outside-target"
    target_dir.mkdir()
    target_file = target_dir / "keep.txt"
    target_file.write_text("keep\n", encoding="utf-8")
    cache_link = tmp_path / "__pycache__"
    cache_link.symlink_to(target_dir, target_is_directory=True)

    module._remove_path(cache_link)

    assert cache_link.exists() is False
    assert cache_link.is_symlink() is False
    assert target_file.read_text(encoding="utf-8") == "keep\n"
