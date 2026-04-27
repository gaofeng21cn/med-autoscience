from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAS_RELEASE_DOWNLOAD_PREFIX = "/".join(
    ("github.com", "gaofeng21cn", "med-autoscience", "releases", "download")
)


def _tracked_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [REPO_ROOT / line for line in completed.stdout.splitlines() if line.strip()]


def test_package_version_matches_python_package_version() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    init_text = (REPO_ROOT / "src" / "med_autoscience" / "__init__.py").read_text(encoding="utf-8")
    version = pyproject_data["project"]["version"]

    assert f'__version__ = "{version}"' in init_text


def test_legacy_github_release_metadata_files_are_retired() -> None:
    assert not (REPO_ROOT / ".github" / "workflows" / "release.yml").exists()
    assert not (REPO_ROOT / ".github" / "release-notes.md").exists()
    assert not (REPO_ROOT / "scripts" / "install-macos.sh").exists()


def test_tracked_files_do_not_point_users_to_mas_github_release_downloads() -> None:
    offenders: list[str] = []
    for path in _tracked_files():
        if not path.exists() or path.is_dir():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if MAS_RELEASE_DOWNLOAD_PREFIX in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []
