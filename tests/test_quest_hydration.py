from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_run_quest_hydration_writes_required_medical_runtime_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    report = module.run_hydration(
        quest_root=quest_root,
        hydration_payload={
            "medical_analysis_contract": {"study_archetype": "clinical_classifier"},
            "medical_reporting_contract": {"reporting_guideline_family": "TRIPOD"},
            "entry_state_summary": "Study root: /tmp/studies/001-risk",
            "literature_records": [
                {
                    "record_id": "pmid:12345",
                    "title": "Prediction model paper",
                    "authors": ["A. Author"],
                    "year": 2024,
                    "journal": "BMC Medicine",
                    "doi": "10.1000/example",
                    "pmid": "12345",
                    "pmcid": None,
                    "arxiv_id": None,
                    "abstract": "Structured abstract",
                    "full_text_availability": "abstract_only",
                    "source_priority": 2,
                    "citation_payload": {"journal": "BMC Medicine"},
                    "local_asset_paths": [],
                    "relevance_role": "anchor",
                    "claim_support_scope": ["primary_claim"],
                }
            ],
        },
    )

    assert (quest_root / "paper" / "medical_analysis_contract.json").exists()
    assert (quest_root / "paper" / "medical_reporting_contract.json").exists()
    assert (quest_root / "paper" / "cohort_flow.json").exists()
    assert (quest_root / "paper" / "baseline_characteristics_schema.json").exists()
    assert (quest_root / "paper" / "references.bib").exists()
    assert (quest_root / "paper" / "reference_coverage_report.json").exists()
    assert (quest_root / "literature" / "pubmed" / "records.jsonl").exists()
    assert (quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json").exists()
    assert report["status"] == "hydrated"
    assert report["literature_report"]["record_count"] == 1

    report_payload = json.loads(
        (quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json").read_text(encoding="utf-8")
    )
    assert report_payload["literature_report"]["record_count"] == 1
