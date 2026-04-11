from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_runtime_supervision_doc_freezes_outer_supervisor_loop_contract() -> None:
    content = _read("docs/runtime/runtime_supervision_loop.md")
    docs_index = _read("docs/README.md")
    docs_index_zh = _read("docs/README.zh-CN.md")

    assert "supervisor loop" in content
    assert "fail-closed" in content
    assert "watch --runtime-root" in content
    assert "runtime_supervision/latest.json" in content
    assert "study_progress" in content
    assert "fresh" in content
    assert "stale" in content
    assert "监管心跳异常" in content
    assert "不是第二个 authority daemon" in content
    assert "clinician_update" in content
    assert "独立安装的 Hermes host" in content
    assert "恢复请求、告警升级与人话汇报" in content
    assert "runtime_supervision_loop.md" in docs_index
    assert "runtime_supervision_loop.md" in docs_index_zh
