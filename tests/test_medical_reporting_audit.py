from __future__ import annotations

import importlib
from pathlib import Path


def test_medical_reporting_audit_blocks_missing_population_accounting(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "medical_reporting_contract.json").write_text(
        '{"reporting_guideline_family": "TRIPOD"}',
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_cohort_flow" in report["blockers"]
    assert "missing_baseline_characteristics_schema" in report["blockers"]
    assert "missing_reporting_guideline_checklist" in report["blockers"]


def test_medical_reporting_audit_reads_active_worktree_paper_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk-reentry"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "paper_bundle_manifest.json").write_text("{}", encoding="utf-8")
    (paper_root / "medical_reporting_contract.json").write_text(
        '{"reporting_guideline_family": "TRIPOD"}',
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_medical_reporting_contract" not in report["blockers"]
    assert "missing_cohort_flow" in report["blockers"]
