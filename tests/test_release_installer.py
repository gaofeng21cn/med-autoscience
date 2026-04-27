from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPO_ROOT / "scripts" / "install-macos.sh"


def test_macos_release_installer_is_retired_from_domain_repo() -> None:
    assert not INSTALLER_PATH.exists()


def test_scripts_directory_does_not_contain_github_release_asset_installers() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "scripts").glob("**/*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "releases/download" in text or "softprops/action-gh-release" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []
