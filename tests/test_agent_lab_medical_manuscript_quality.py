from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import write_text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_medical_manuscript_quality_agent_lab_suite_projects_blocked_domain_scorecard(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    write_text(study_root / "paper" / "draft.md", "# Draft\n")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"items": []})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer must re-evaluate manuscript quality.",
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_intent": "reviewer_revision",
            "summary": "Manual review requests HDL harmonization, tables, CI, calibration, and prose repair.",
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    task = suite["tasks"][0]

    assert suite["suite_kind"] == "agent_lab_external_suite"
    assert task["task_family"] == "high_quality_medical_manuscript_self_evolution"
    assert task["scorecard"]["domain_owned"] is True
    assert task["scorecard"]["opl_scorecard_role"] == "scorecard_ref_projection_only"
    assert task["scorecard"]["passed"] is False
    assert task["promotion_gate"]["gate_status"] == "blocked"
    assert task["improvement_candidate"]["candidate_kind"] == "rubric_gap"
    assert "hdl-harmonization-and-sensitivity" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "nhanes-survey-weighting-and-unweighted-framing" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "uncertainty-intervals-and-validation-metrics" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert task["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert task["authority_boundary"]["can_mutate_domain_artifact"] is False


def test_medical_manuscript_quality_agent_lab_suite_materializes_refs_only_surface(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "ready",
                    "summary": "AI reviewer judged the manuscript ready.",
                }
            },
        },
    )

    result = module.materialize_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    path = Path(result["suite_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert result["surface_kind"] == "mas_agent_lab_medical_manuscript_quality_suite"
    assert result["status"] == "materialized"
    assert payload["tasks"][0]["scorecard"]["passed"] is True
    assert payload["tasks"][0]["promotion_gate"]["gate_status"] == "passed"
    assert payload["authority_boundary"]["can_write_domain_truth"] is False
