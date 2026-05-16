from __future__ import annotations

import importlib
import json
from pathlib import Path


MODULE_NAME = "med_autoscience.study_charter"


def test_materialize_study_charter_adds_phenotype_treatment_gap_reporting_guardrails(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"

    module.materialize_study_charter(
        study_root=study_root,
        study_id="003-dpcc",
        study_payload={
            "title": "Primary care diabetes phenotype and treatment gap atlas",
            "study_archetype": "clinical_subtype_reconstruction",
            "paper_archetype": "phenotype_real_world_treatment_gap",
            "manuscript_family": "clinical_observation",
            "endpoint_type": "descriptive",
        },
        execution={},
        required_first_anchor=None,
    )

    payload = json.loads(
        (study_root / "artifacts" / "controller" / "study_charter.json").read_text(
            encoding="utf-8"
        )
    )
    contract = payload["paper_quality_contract"]["structured_reporting_contract"]

    assert contract["clinical_actionability_required"] is True
    assert contract["paper_archetype"] == "phenotype_real_world_treatment_gap"
    assert contract["manuscript_family"] == "clinical_observation"
    assert contract["endpoint_type"] == "descriptive"
    assert contract["reporting_guideline_family"] == "STROBE"
    assert contract["clinical_actionability"] == {
        "treatment_gap": {"status": "required_before_first_full_draft"},
        "follow_up_or_outcome_relevance": {"status": "required_before_first_full_draft"},
    }
    for item in policy.TREATMENT_GAP_REPORTING_ITEMS:
        assert contract["treatment_gap_reporting"][item] == {
            "status": "required_before_first_full_draft"
        }
    for item in policy.PHENOTYPE_DERIVATION_REPORTING_ITEMS:
        assert contract["phenotype_derivation_reporting"][item] == {
            "status": "required_before_first_full_draft"
        }
    for item in policy.BASELINE_CHARACTERISTICS_REPORTING_ITEMS:
        assert contract["baseline_characteristics_reporting"][item] == {
            "status": "required_before_first_full_draft"
        }
    for item in policy.DATA_QUALITY_REPORTING_ITEMS:
        assert contract["data_quality_reporting"][item] == {
            "status": "required_before_first_full_draft"
        }
