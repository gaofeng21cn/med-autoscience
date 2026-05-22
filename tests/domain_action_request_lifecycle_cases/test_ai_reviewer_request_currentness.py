from __future__ import annotations

from med_autoscience.controllers.domain_action_requests import (
    build_ai_reviewer_publication_eval_request,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    materialize_ai_reviewer_request,
    project_ai_reviewer_request_lifecycle,
)


def test_ai_reviewer_request_lifecycle_keeps_new_request_pending_until_eval_consumes_it(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    manuscript = study_root / "paper" / "manuscript.md"
    manuscript.parent.mkdir(parents=True)
    manuscript.write_text("# Draft\n\nCurrent manuscript.\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="quality_repair_batch",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "review_required"},
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": [],
        },
        input_refs={
            "manuscript": {"relative_path": "paper/manuscript.md"},
            "evidence_ledger": {"relative_path": "paper/evidence_ledger.json"},
            "review_ledger": {"relative_path": "paper/review/review_ledger.json"},
            "study_charter": {"relative_path": "artifacts/controller/study_charter.json"},
            "medical_manuscript_blueprint": {"relative_path": "paper/medical_manuscript_blueprint.json"},
            "claim_evidence_map": {"relative_path": "paper/claim_evidence_map.json"},
            "medical_prose_review": {"relative_path": "artifacts/publication_eval/medical_prose_review.json"},
            "publication_gate_projection": {"relative_path": "artifacts/publication_eval/latest.json"},
        },
        lifecycle_state="assigned",
        assigned_to="ai_reviewer",
    )
    materialize_ai_reviewer_request(study_root=study_root, packet=packet)

    stale_eval = {
        "eval_id": "publication-eval::002-risk::quest-002::2026-05-22T01:00:00+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [],
        },
    }

    pending = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=stale_eval,
    )
    assert pending is not None
    assert pending["state"] == "assigned"
    assert pending["assessment_written"] is False

    consumed_eval = dict(stale_eval)
    consumed_eval["assessment_provenance"] = dict(stale_eval["assessment_provenance"])
    consumed_eval["assessment_provenance"]["source_refs"] = [
        str(study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json")
    ]
    consumed = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=consumed_eval,
    )
    assert consumed is not None
    assert consumed["state"] == "assessment_written"
    assert consumed["assessment_written"] is True
