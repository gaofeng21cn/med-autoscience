from __future__ import annotations

import json

from med_autoscience.controllers.domain_action_requests import build_ai_reviewer_publication_eval_request
from med_autoscience.controllers.domain_action_request_lifecycle import (
    materialize_ai_reviewer_request,
    read_ai_reviewer_request,
)


def test_ai_reviewer_request_materialization_skips_invalid_record_scope(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    record_path = response_root / "20260517T074205Z_publication_eval_record.json"
    quality_assessment = {
        dimension: {
            "status": "partial" if dimension == "medical_journal_prose_quality" else "ready",
            "summary": f"{dimension} reviewer assessment.",
        }
        for dimension in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "medical_journal_prose_quality",
            "human_review_readiness",
        )
    }
    record = {
        "eval_id": "publication-eval::002-risk::quest-002::2026-05-17T07:42:05+00:00",
        "study_id": "002-risk",
        "quest_id": "quest-002",
        "evaluation_scope": {
            "scope_id": "record_only_publication_eval_after_analysis_harmonization",
            "record_only": True,
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "quality_assessment": quality_assessment,
        "future_facing_limitations_plan": [
            {
                "limitation": "Current review is bound to the active manuscript digest.",
                "impact_on_claim": "Claims remain restrained until a canonical record is produced.",
                "required_future_analysis_data_or_design": "Rerun AI reviewer record production.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
    }
    record_path.parent.mkdir(parents=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="owner_route_reconcile",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
    )

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert "ai_reviewer_record" not in materialized
    assert "publication_eval_record_ref" not in materialized
    assert persisted is not None
    assert "ai_reviewer_record" not in persisted
    assert "publication_eval_record_ref" not in persisted
