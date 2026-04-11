from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_study_progress_doc_freezes_projection_contract_and_doctor_readout() -> None:
    content = _read("docs/program/study_progress_projection.md")
    docs_index = _read("docs/README.md")
    docs_index_zh = _read("docs/README.zh-CN.md")

    assert "controller-owned progress projection" in content
    assert "不是第二个 authority daemon" in content
    assert "study_runtime_status" in content
    assert "runtime_watch" in content
    assert "runtime_supervision/latest.json" in content
    assert "supervisor_tick_audit" in content
    assert "监管心跳异常" in content
    assert "publication_eval/latest.json" in content
    assert "controller_decisions/latest.json" in content
    assert "医生" in content
    assert "clinician_update" in content
    assert "bash_exec summary" in content
    assert "宿主机尚无 external `Hermes` runtime" in content
    assert "study_progress_projection.md" in docs_index
    assert "study_progress_projection.md" in docs_index_zh
