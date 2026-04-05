from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_root_readme_has_bilingual_switch_and_chinese_mirror() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    zh_readme = REPO_ROOT / "README.zh-CN.md"

    assert zh_readme.exists()
    assert '<a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>' in readme
    assert '<a href="./README.md">English</a> | <a href="./README.zh-CN.md"><strong>中文</strong></a>' in zh_readme.read_text(encoding="utf-8")


def test_docs_index_has_bilingual_switch_and_chinese_mirror() -> None:
    docs_readme = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    docs_zh_readme = REPO_ROOT / "docs" / "README.zh-CN.md"

    assert docs_zh_readme.exists()
    assert '**English** | [中文](./README.zh-CN.md)' in docs_readme
    assert '[English](./README.md) | **中文**' in docs_zh_readme.read_text(encoding="utf-8")
