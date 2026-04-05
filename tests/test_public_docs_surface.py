from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_public_docs_surface_has_no_root_guides_directory() -> None:
    assert not (REPO_ROOT / "guides").exists()


def test_docs_index_links_to_checked_in_ci_preflight_doc() -> None:
    docs_index = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    assert "repository_ci_preflight.md" in docs_index
    assert (REPO_ROOT / "docs" / "repository_ci_preflight.md").exists()
