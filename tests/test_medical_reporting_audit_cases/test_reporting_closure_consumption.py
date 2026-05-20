from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_medical_reporting_audit_consumes_closed_reporting_guideline_and_claim_map(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")
    quest_root = tmp_path / "runtime" / "quests" / "002-dm-transportability"
    paper_root = quest_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    contract = policy.build_default_structured_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
        endpoint_type="time_to_event",
        external_validation_dataset="NHANES",
    )
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "TRIPOD",
                "display_registry_required": False,
                "cohort_flow_required": False,
                "baseline_characteristics_required": False,
                "display_shell_plan": [],
                "structured_reporting_contract": contract,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "reporting_guideline_checklist.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "guideline_family": "TRIPOD",
                "status": "closed",
                "domains": [
                    {
                        "domain_id": domain_id,
                        "status": "closed",
                        "evidence": ["paper/reporting_guideline_checklist.json"],
                    }
                    for domain_id in [
                        "source_of_data_and_participants",
                        "outcome_definition_and_follow_up",
                        "candidate_predictors_and_missing_data",
                        "model_specification_or_validation",
                        "performance_calibration_and_clinical_utility",
                        "interpretation_limitations_and_use_case",
                    ]
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "table_figure_claim_map.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "items": [
                    {
                        "claim_id": "C1",
                        "claim": "The transported score preserves risk ordering after harmonized preprocessing.",
                        "table_figure_refs": ["F2", "T2"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "_medical_story_contract_blockers", lambda _: [])

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "clear"
    assert report["blockers"] == []
    report_payload = json.loads(Path(report["report_json"]).read_text(encoding="utf-8"))
    checklist = report_payload["structured_reporting_checklist"]
    assert checklist["status"] == "clear"
    assert checklist["blockers"] == []
    assert checklist["reporting_guideline_closure_consumed"]["status"] == "consumed"
    assert checklist["table_figure_claim_map_consumed"]["mapped_claim_count"] == 1
