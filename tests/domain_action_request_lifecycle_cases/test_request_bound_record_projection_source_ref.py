from __future__ import annotations

import json

from med_autoscience.controllers.domain_action_request_lifecycle import (
    project_ai_reviewer_request_lifecycle,
)


def _write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_request_bound_record_projection_source_ref_closes_cleared_lifecycle_request(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    review_path = study_root / "paper" / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    blueprint_path = study_root / "paper" / "medical_manuscript_blueprint.json"
    prose_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260605T080613Z_publication_eval_record.json"
    )
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent manuscript.\n", encoding="utf-8")
    _write_json(evidence_path, {"schema_version": 1})
    _write_json(claim_map_path, {"schema_version": 1})
    _write_json(review_path, {"schema_version": 1})
    _write_json(charter_path, {"schema_version": 1})
    _write_json(blueprint_path, {"schema_version": 1})
    _write_json(prose_review_path, {"schema_version": 1})
    _write_json(latest_eval_path, {"schema_version": 1})
    current_record = {
        "schema_version": 1,
        "eval_id": "publication-eval::003-dpcc::ai-reviewer-record::20260605T080529Z::sat_current",
        "emitted_at": "2026-06-05T08:06:13+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "clinical_significance": {"status": "ready"},
            "evidence_strength": {"status": "ready"},
            "novelty_positioning": {"status": "ready"},
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "partial"},
        },
        "future_facing_limitations_plan": [{"limitation": "bounded descriptive claims"}],
        "_projection_source_ref": str(record_path.resolve()),
    }
    _write_json(record_path, current_record)
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": None,
                "assessment_ref": str(record_path.resolve()),
            },
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": current_record,
            "source_workflow_ref": {
                "surface": "owner_route_reconcile",
                "authority_owner": "ai_reviewer",
                "authority_state": "projection_only",
                "route_back_required": True,
                "route_back_target": "ai_reviewer",
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(evidence_path.resolve()), "present": True, "valid": True},
                    "review_ledger": {"path": str(review_path.resolve()), "present": True, "valid": True},
                    "study_charter": {"path": str(charter_path.resolve()), "present": True, "valid": True},
                    "medical_manuscript_blueprint": {
                        "path": str(blueprint_path.resolve()),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {"path": str(claim_map_path.resolve()), "present": True, "valid": True},
                    "medical_prose_review": {
                        "path": str(prose_review_path.resolve()),
                        "present": True,
                        "valid": True,
                    },
                    "publication_gate_projection": {
                        "path": str(latest_eval_path.resolve()),
                        "present": True,
                        "valid": True,
                    },
                }
            },
        },
    )

    lifecycle = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=current_record,
    )

    assert lifecycle is not None
    assert lifecycle["state"] == "assessment_written"
    assert lifecycle["assessment_written"] is True
    assert lifecycle["blocked_reason"] is None
    assert lifecycle["publication_eval_record_ref"] == str(record_path.resolve())
    assert lifecycle["owner_output_consumption"] == {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "record_ref": str(record_path.resolve()),
        "eval_id": current_record["eval_id"],
        "consumption_mode": "refs_only_current_ai_reviewer_record",
        "required_currentness_refs": [],
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
