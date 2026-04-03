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


def test_write_audit_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_literature_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return (
            quest_root / "artifacts" / "reports" / report_group / "latest.json",
            quest_root / "artifacts" / "reports" / report_group / "latest.md",
        )

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-04-03T06:00:00+00:00",
        "quest_root": str(quest_root),
        "gap_report_path": str(quest_root / "paper" / "review" / "reference_gap_report.json"),
        "status": "blocked",
        "blockers": ["reference_gaps_present"],
        "action": "clear",
        "missing_pmids": ["12345"],
    }

    json_path, md_path = module.write_audit_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "medical_literature_audit"
    assert seen["timestamp"] == "2026-04-03T06:00:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
