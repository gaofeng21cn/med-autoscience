from __future__ import annotations

import re
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_makefile_exposes_layered_test_entrypoints() -> None:
    makefile = _read("Makefile")

    assert "test-fast:" in makefile
    assert 'uv run pytest -q -m "not meta and not display_heavy"' in makefile
    assert "test-meta:" in makefile
    assert "uv run pytest -q -m meta" in makefile
    assert "test-display:" in makefile
    assert "uv run pytest -q -m display_heavy" in makefile
    assert "test-full:" in makefile
    assert "uv run pytest -q" in makefile


def test_pyproject_registers_meta_and_display_markers() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    markers = pyproject["tool"]["pytest"]["ini_options"]["markers"]

    assert "meta: repo-tracked docs, workflow, packaging, and command-surface checks" in markers
    assert "display_heavy: display materialization and golden-regression tests that dominate wall-clock time" in markers


def test_pyproject_pins_opl_harness_shared_to_a_full_commit() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dependency = next(
        item
        for item in pyproject["project"]["dependencies"]
        if item.startswith("opl-harness-shared @ ")
    )

    assert re.fullmatch(
        r"opl-harness-shared @ git\+https://github\.com/gaofeng21cn/one-person-lab\.git@[0-9a-f]{40}#subdirectory=python/opl-harness-shared",
        dependency,
    )


def test_public_readmes_publish_layered_test_entrypoints() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")

    assert "make test-full" in readme
    assert "make test-fast" in readme
    assert "make test-meta" in readme
    assert "make test-display" in readme
    assert "make test-full" in readme_zh
    assert "make test-fast" in readme_zh
    assert "make test-meta" in readme_zh
    assert "make test-display" in readme_zh


def test_root_agents_describe_current_verification_entrypoints() -> None:
    agents = _read("AGENTS.md")

    assert "统一验证入口：`scripts/verify.sh`。" in agents
    assert "默认最小验证：`scripts/verify.sh`（内部运行 `make test-fast`）。" in agents
    assert "full lane：`scripts/verify.sh full`（内部运行 `make test-full`）。" in agents
    assert "修改 docs/contract surface 或运行语义时，至少补跑 `make test-meta`。" in agents


def test_verify_script_exposes_named_lanes_for_ci_workflows() -> None:
    verify_script = _read("scripts/verify.sh")

    assert 'if [[ -z "${lane}" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "meta" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "display" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "full" ]]; then' in verify_script
    assert "make test-fast" in verify_script
    assert "make test-meta" in verify_script
    assert "make test-display" in verify_script
    assert "make test-full" in verify_script


def test_docs_indexes_link_series_doc_governance_checklist() -> None:
    docs_readme = _read("docs/README.md")
    docs_readme_zh = _read("docs/README.zh-CN.md")
    checklist = _read("docs/references/series-doc-governance-checklist.md")
    previous_index = -1

    for heading in (
        "## 目标",
        "## 一、默认入口",
        "## 二、核心五件套",
        "## 三、公开层与内部层",
        "## 四、系列一致性检查",
        "## 五、默认验证",
    ):
        current_index = checklist.find(heading)
        assert current_index >= 0
        assert current_index > previous_index
        previous_index = current_index

    assert "series-doc-governance-checklist.md" in docs_readme
    assert "series-doc-governance-checklist.md" in docs_readme_zh

    for label in ("One Person Lab", "Med Auto Science", "Med Auto Grant", "RedCube AI"):
        assert label in checklist

    for doc_name in ("project.md", "status.md", "architecture.md", "invariants.md", "decisions.md"):
        assert doc_name in checklist

    assert "docs/runtime/**" in checklist
    assert "docs/program/**" in checklist
    assert "docs/capabilities/**" in checklist
    assert "docs/policies/**" in checklist
    assert "Hermes-Agent" in checklist
    assert "AGENTS.md" in checklist
    assert "第二真相源" in checklist
    assert "scripts/verify.sh meta" in checklist
    assert "make test-meta" in checklist
    assert "Documentation governance rules are maintained in [`AGENTS.md`](../AGENTS.md)." not in docs_readme
    assert "文档治理规则统一收口在 [`AGENTS.md`](../AGENTS.md)。" not in docs_readme_zh
