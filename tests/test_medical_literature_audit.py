from __future__ import annotations

import importlib
from pathlib import Path


def test_medical_literature_audit_apply_triggers_literature_hydration(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_literature_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper" / "review").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "review" / "reference_gap_report.json").write_text(
        '{"missing_queries": ["residual disease prediction"], "missing_pmids": ["12345"]}',
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    monkeypatch.setattr(
        module.pubmed_adapter,
        "fetch_pubmed_summary",
        lambda *, pmids: [{"record_id": "pmid:12345", "title": "Paper title", "pmid": "12345"}],
    )
    monkeypatch.setattr(
        module.literature_hydration_controller,
        "run_literature_hydration",
        lambda *, quest_root, records: called.update({"quest_root": quest_root, "records": records})
        or {"status": "hydrated"},
    )

    report = module.run_controller(quest_root=quest_root, apply=True)

    assert report["status"] == "blocked"
    assert report["action"] == "supplemented"
    assert called["quest_root"] == quest_root
    assert called["records"][0]["record_id"] == "pmid:12345"
