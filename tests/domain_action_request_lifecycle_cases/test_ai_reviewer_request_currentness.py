from __future__ import annotations

import hashlib
import json

from med_autoscience.controllers.domain_action_requests import (
    build_ai_reviewer_publication_eval_request,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    materialize_ai_reviewer_request,
    project_ai_reviewer_request_lifecycle,
    read_ai_reviewer_request,
)


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def test_ai_reviewer_request_materialization_rejects_record_stale_after_current_manuscript(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    stale_record_path = response_root / "20260521T213722Z_publication_eval_record.json"
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True)
    manuscript_path.write_text(
        "# Draft\n\n## Abstract\n\nCurrent numeric abstract with 95% CIs.\n",
        encoding="utf-8",
    )
    quality_assessment = {
        dimension: {
            "status": "blocked" if dimension == "medical_journal_prose_quality" else "ready",
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
    stale_record = {
        "eval_id": "publication-eval::002-risk::quest-002::2026-05-21T21:37:22+00:00",
        "study_id": "002-risk",
        "quest_id": "quest-002",
        "emitted_at": "2026-05-21T21:37:22+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(manuscript_path)],
            "ai_reviewer_required": False,
        },
        "quality_assessment": quality_assessment,
        "future_facing_limitations_plan": [
            {
                "limitation": "The old reviewer record predates the current manuscript.",
                "impact_on_claim": "The prose verdict cannot authorize current manuscript quality.",
                "required_future_analysis_data_or_design": "Re-run AI reviewer against the current manuscript.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
    }
    stale_record_path.parent.mkdir(parents=True)
    stale_record_path.write_text(json.dumps(stale_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="runtime_supervisor_scan",
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
    assert persisted["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert persisted["request_lifecycle"]["stale_record_ref"] == str(stale_record_path.resolve())
    assert persisted["request_lifecycle"]["required_currentness_refs"] == [str(manuscript_path.resolve())]


def test_stale_record_lifecycle_stays_requested_despite_old_publication_eval_timestamp(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    manuscript_path = study_root / "paper" / "draft.md"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_path.parent.mkdir(parents=True)
    manuscript_path.write_text("# Draft\n\nCurrent manuscript after the old AI reviewer record.\n", encoding="utf-8")
    request_path.parent.mkdir(parents=True)
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "created_at": "2026-05-21T20:00:00+00:00",
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "stale_record_ref": str(
                        study_root
                        / "artifacts"
                        / "publication_eval"
                        / "ai_reviewer_responses"
                        / "20260521T213722Z_publication_eval_record.json"
                    ),
                    "required_currentness_refs": [str(manuscript_path.resolve())],
                },
                "input_contract": {
                    "required_refs": {
                        "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                        "evidence_ledger": {
                            "path": str(study_root / "paper" / "evidence_ledger.json"),
                            "present": True,
                            "valid": True,
                        },
                        "review_ledger": {
                            "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                            "present": True,
                            "valid": True,
                        },
                        "study_charter": {
                            "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                            "present": True,
                            "valid": True,
                        },
                        "medical_manuscript_blueprint": {
                            "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                            "present": True,
                            "valid": True,
                        },
                        "claim_evidence_map": {
                            "path": str(study_root / "paper" / "claim_evidence_map.json"),
                            "present": True,
                            "valid": True,
                        },
                        "medical_prose_review": {
                            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                            "present": True,
                            "valid": True,
                        },
                        "publication_gate_projection": {
                            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                            "present": True,
                            "valid": True,
                        },
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    old_publication_eval = {
        "eval_id": "publication-eval::002-risk::quest-002::2026-05-21T21:37:22+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "clinical_significance": {},
            "evidence_strength": {},
            "novelty_positioning": {},
            "medical_journal_prose_quality": {},
            "human_review_readiness": {},
        },
        "future_facing_limitations_plan": [{"limitation": "old"}],
    }

    lifecycle = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=old_publication_eval,
    )

    assert lifecycle is not None
    assert lifecycle["state"] == "requested"
    assert lifecycle["assessment_written"] is False
    assert lifecycle["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert lifecycle["required_currentness_refs"] == [str(manuscript_path.resolve())]


def test_stale_record_lifecycle_closes_when_ai_reviewer_eval_covers_current_manuscript(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    manuscript_path = study_root / "paper" / "draft.md"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_text = "# Draft\n\nCurrent manuscript after the old AI reviewer record.\n"
    manuscript_path.parent.mkdir(parents=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    request_path.parent.mkdir(parents=True)
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "created_at": "2026-05-21T20:00:00+00:00",
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "required_currentness_refs": [str(manuscript_path.resolve())],
                },
                "input_contract": {
                    "required_refs": {
                        "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                        "evidence_ledger": {
                            "path": str(study_root / "paper" / "evidence_ledger.json"),
                            "present": True,
                            "valid": True,
                        },
                        "review_ledger": {
                            "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                            "present": True,
                            "valid": True,
                        },
                        "study_charter": {
                            "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                            "present": True,
                            "valid": True,
                        },
                        "medical_manuscript_blueprint": {
                            "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                            "present": True,
                            "valid": True,
                        },
                        "claim_evidence_map": {
                            "path": str(study_root / "paper" / "claim_evidence_map.json"),
                            "present": True,
                            "valid": True,
                        },
                        "medical_prose_review": {
                            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                            "present": True,
                            "valid": True,
                        },
                        "publication_gate_projection": {
                            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                            "present": True,
                            "valid": True,
                        },
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    current_publication_eval = {
        "eval_id": "publication-eval::002-risk::quest-002::2026-05-22T15:39:23+00:00::ai-reviewer",
        "emitted_at": "2026-05-22T15:39:23+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "clinical_significance": {},
            "evidence_strength": {},
            "novelty_positioning": {},
            "medical_journal_prose_quality": {},
            "human_review_readiness": {},
        },
        "future_facing_limitations_plan": [{"limitation": "current"}],
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "request_digest": "sha256:" + "a" * 64,
                }
            }
        },
    }

    lifecycle = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=current_publication_eval,
    )

    assert lifecycle is not None
    assert lifecycle["state"] == "assessment_written"
    assert lifecycle["assessment_written"] is True


def test_stale_record_lifecycle_stays_requested_when_currentness_digest_mismatches_live_manuscript(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    manuscript_path = study_root / "paper" / "draft.md"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_text = "# Draft\n\nCurrent manuscript after the old AI reviewer record.\n"
    manuscript_path.parent.mkdir(parents=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    request_path.parent.mkdir(parents=True)
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "created_at": "2026-05-21T20:00:00+00:00",
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "required_currentness_refs": [str(manuscript_path.resolve())],
                },
                "input_contract": {
                    "required_refs": {
                        "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                        "evidence_ledger": {
                            "path": str(study_root / "paper" / "evidence_ledger.json"),
                            "present": True,
                            "valid": True,
                        },
                        "review_ledger": {
                            "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                            "present": True,
                            "valid": True,
                        },
                        "study_charter": {
                            "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                            "present": True,
                            "valid": True,
                        },
                        "medical_manuscript_blueprint": {
                            "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                            "present": True,
                            "valid": True,
                        },
                        "claim_evidence_map": {
                            "path": str(study_root / "paper" / "claim_evidence_map.json"),
                            "present": True,
                            "valid": True,
                        },
                        "medical_prose_review": {
                            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                            "present": True,
                            "valid": True,
                        },
                        "publication_gate_projection": {
                            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                            "present": True,
                            "valid": True,
                        },
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    stale_publication_eval = {
        "eval_id": "publication-eval::002-risk::quest-002::2026-05-22T15:39:23+00:00::ai-reviewer",
        "emitted_at": "2026-05-22T15:39:23+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "clinical_significance": {},
            "evidence_strength": {},
            "novelty_positioning": {},
            "medical_journal_prose_quality": {},
            "human_review_readiness": {},
        },
        "future_facing_limitations_plan": [{"limitation": "current"}],
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": "sha256:" + "0" * 64,
                    "request_digest": "sha256:" + "a" * 64,
                }
            }
        },
    }

    lifecycle = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=stale_publication_eval,
    )

    assert lifecycle is not None
    assert lifecycle["state"] == "requested"
    assert lifecycle["assessment_written"] is False
