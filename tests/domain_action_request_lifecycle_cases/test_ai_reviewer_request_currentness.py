from __future__ import annotations

import hashlib
import json

from med_autoscience.controllers.domain_action_requests import (
    build_ai_reviewer_publication_eval_request,
)
from med_autoscience.controllers.domain_action_request_lifecycle import (
    AI_REVIEWER_REQUIRED_INPUT_SURFACES,
    materialize_ai_reviewer_request,
    project_ai_reviewer_request_lifecycle,
    read_ai_reviewer_request,
)
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_ai_reviewer_request_materialization_rehydrates_missing_required_refs_from_canonical_surfaces(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    paper_root = study_root / "paper"
    (paper_root / "review").mkdir(parents=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent canonical manuscript.\n", encoding="utf-8")
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1})
    _write_json(paper_root / "review" / "review_ledger.json", {"schema_version": 1})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {"schema_version": 1},
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", {"schema_version": 1})
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="legacy_request_surface",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
        lifecycle_state="assigned",
        assigned_to="ai_reviewer",
    )

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert persisted is not None
    required_refs = materialized["input_contract"]["required_refs"]
    assert set(required_refs) == set(AI_REVIEWER_REQUIRED_INPUT_SURFACES)
    assert materialized["input_contract"]["all_required_refs_present"] is True
    assert materialized["input_contract"]["missing_or_invalid_refs"] == []
    assert persisted["input_contract"] == materialized["input_contract"]
    assert required_refs["manuscript"]["relative_path"] == "paper/draft.md"
    assert required_refs["evidence_ledger"]["relative_path"] == "paper/evidence_ledger.json"
    assert required_refs["review_ledger"]["relative_path"] == "paper/review/review_ledger.json"
    assert required_refs["study_charter"]["relative_path"] == "artifacts/controller/study_charter.json"
    assert required_refs["medical_prose_review"]["relative_path"] == (
        "artifacts/publication_eval/medical_prose_review.json"
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


def test_stale_current_inputs_lifecycle_clears_when_current_record_consumes_refs(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    review_path = study_root / "paper" / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    blueprint_path = study_root / "paper" / "medical_manuscript_blueprint.json"
    prose_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_text = "# Draft\n\nCurrent manuscript.\n"
    evidence_payload = {"schema_version": 1, "claim": "current evidence"}
    claim_payload = {"schema_version": 1, "claim": "current claim map"}
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_payload)
    _write_json(review_path, {"schema_version": 1})
    _write_json(charter_path, {"schema_version": 1})
    _write_json(blueprint_path, {"schema_version": 1})
    _write_json(prose_review_path, {"schema_version": 1})
    _write_json(latest_eval_path, {"schema_version": 1})
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "schema_version": 1,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": str(
                        study_root
                        / "artifacts"
                        / "publication_eval"
                        / "ai_reviewer_responses"
                        / "20260528T010000Z_publication_eval_record.json"
                    ),
                    "required_currentness_refs": [
                        str(manuscript_path.resolve()),
                        str(evidence_path.resolve()),
                        str(claim_map_path.resolve()),
                    ],
                },
                "input_contract": {
                    "required_refs": {
                        "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                        "evidence_ledger": {"path": str(evidence_path.resolve()), "present": True, "valid": True},
                        "claim_evidence_map": {"path": str(claim_map_path.resolve()), "present": True, "valid": True},
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    current_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::003-dpcc::current-inputs::20260528T094456Z",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(request_path.resolve())],
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "evidence_ledger": {
                    "status": "current",
                    "ref": str(evidence_path.resolve()),
                    "digest": _sha256_text(json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n"),
                },
                "claim_evidence_map": {
                    "status": "current",
                    "ref": str(claim_map_path.resolve()),
                    "digest": _sha256_text(json.dumps(claim_payload, ensure_ascii=False, indent=2) + "\n"),
                },
            }
        },
    }

    lifecycle = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=current_eval,
    )

    assert lifecycle is not None
    assert lifecycle["state"] == "assessment_written"
    assert lifecycle["assessment_written"] is True
    assert lifecycle["blocked_reason"] is None
    assert lifecycle["stale_record_ref"] is None
    assert lifecycle["required_currentness_refs"] == []


def test_current_input_record_only_request_is_written_when_lifecycle_blocker_was_cleared(tmp_path) -> None:
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
        / "20260528T214013Z_publication_eval_record.json"
    )
    manuscript_text = "# Draft\n\nCurrent manuscript.\n"
    evidence_payload = {"schema_version": 1, "claim": "current evidence"}
    claim_payload = {"schema_version": 1, "claim": "current claim map"}
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_payload)
    _write_json(review_path, {"schema_version": 1})
    _write_json(charter_path, {"schema_version": 1})
    _write_json(blueprint_path, {"schema_version": 1})
    _write_json(prose_review_path, {"schema_version": 1})
    _write_json(latest_eval_path, {"schema_version": 1})
    current_record = {
        "schema_version": 1,
        "eval_id": "publication-eval::003-dpcc::current-inputs::20260528T214013Z",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(record_path.resolve())],
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "evidence_ledger": {
                    "status": "current",
                    "ref": str(evidence_path.resolve()),
                    "digest": _sha256_text(json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n"),
                },
                "claim_evidence_map": {
                    "status": "current",
                    "ref": str(claim_map_path.resolve()),
                    "digest": _sha256_text(json.dumps(claim_payload, ensure_ascii=False, indent=2) + "\n"),
                },
            }
        },
    }
    _write_json(record_path, current_record)
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "assessment_ref": str(record_path.resolve()),
                "blocked_reason": None,
            },
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": current_record,
            "source_workflow_ref": {
                "surface": "owner_route_reconcile",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
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
    assert lifecycle["stale_record_ref"] is None
    assert lifecycle["required_currentness_refs"] == []
    assert lifecycle["owner_output_consumption"] == {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "record_ref": str(record_path.resolve()),
        "eval_id": current_record["eval_id"],
        "consumption_mode": "refs_only_current_ai_reviewer_record",
        "required_currentness_refs": [
            str(manuscript_path.resolve()),
            str(evidence_path.resolve()),
            str(claim_map_path.resolve()),
        ],
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }


def test_request_refresh_accepts_current_record_when_source_refs_cover_required_input_refs(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T100000Z_publication_eval_record.json"
    )
    manuscript_text = "# Draft\n\nCurrent manuscript reviewed by AI reviewer.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(
        evidence_path,
        {
            "updated_at": "2026-05-28T09:00:00+00:00",
            "claims": [{"claim_id": "claim-primary"}],
        },
    )
    _write_json(
        claim_map_path,
        {
            "updated_at": "2026-05-28T09:00:00+00:00",
            "claims": [{"claim_id": "claim-primary"}],
        },
    )
    current_record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id="003-dpcc",
        quest_id="quest-003",
        eval_id="publication-eval::003-dpcc::current-inputs::2026-05-28T10:00:00+00:00::ai-reviewer",
        emitted_at="2026-05-28T10:00:00+00:00",
    )
    current_record["assessment_provenance"]["source_refs"] = [
        str(manuscript_path.resolve()),
        str(evidence_path.resolve()),
        str(claim_map_path.resolve()),
    ]
    _write_json(record_path, current_record)
    packet = build_ai_reviewer_publication_eval_request(
        study_id="003-dpcc",
        quest_id="quest-003",
        source_surface="runtime_supervisor_scan",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
        input_refs={
            "evidence_ledger": {"path": str(evidence_path.resolve()), "present": True, "valid": True},
            "claim_evidence_map": {"path": str(claim_map_path.resolve()), "present": True, "valid": True},
        },
    )
    packet["request_lifecycle"]["blocked_reason"] = "ai_reviewer_record_stale_after_current_inputs"
    packet["request_lifecycle"]["required_currentness_refs"] = [
        str(evidence_path.resolve()),
        str(claim_map_path.resolve()),
    ]

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert persisted is not None
    assert materialized["publication_eval_record_ref"] == str(record_path.resolve())
    assert materialized["ai_reviewer_record"]["eval_id"] == current_record["eval_id"]
    assert materialized["request_lifecycle"]["blocked_reason"] is None
    assert "required_currentness_refs" not in materialized["request_lifecycle"]
    assert "missing_currentness_refs" not in materialized["request_lifecycle"]
    assert persisted["publication_eval_record_ref"] == str(record_path.resolve())
    assert persisted["request_lifecycle"]["blocked_reason"] is None


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


def test_ai_reviewer_request_materialization_rejects_record_stale_after_current_claim_evidence_inputs(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    stale_record_path = response_root / "20260527T111037Z_publication_eval_record.json"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-05-27T14:30:00+00:00",
                "claims": [{"claim_id": "A1_boundary_metric_provenance"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    claim_map_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-05-27T14:30:00+00:00",
                "claims": [{"claim_id": "A1_boundary_metric_provenance"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    quality_assessment = {
        dimension: {
            "status": "blocked" if dimension == "evidence_strength" else "ready",
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
    stale_evidence_digest = _sha256_text("old evidence ledger")
    stale_claim_map_digest = _sha256_text("old claim map")
    stale_record = {
        "eval_id": "publication-eval::003-dpcc::quest-003::2026-05-27T11:10:37+00:00",
        "study_id": "003-dpcc",
        "quest_id": "quest-003",
        "emitted_at": "2026-05-27T11:10:37+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(evidence_path), str(claim_map_path)],
            "ai_reviewer_required": False,
        },
        "quality_assessment": quality_assessment,
        "reviewer_operating_system": {
            "currentness_checks": {
                "evidence_ledger": {
                    "status": "current",
                    "ref": str(evidence_path.resolve()),
                    "digest": stale_evidence_digest,
                },
                "claim_evidence_map": {
                    "status": "current",
                    "ref": str(claim_map_path.resolve()),
                    "digest": stale_claim_map_digest,
                },
            }
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "The old reviewer record predates claim-evidence repair.",
                "impact_on_claim": "The evidence-strength verdict cannot authorize current claim-evidence quality.",
                "required_future_analysis_data_or_design": "Re-run AI reviewer against the current claim-evidence inputs.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
    }
    stale_record_path.parent.mkdir(parents=True)
    stale_record_path.write_text(json.dumps(stale_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="003-dpcc",
        quest_id="quest-003",
        source_surface="runtime_supervisor_scan",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
        input_refs={
            "evidence_ledger": {
                "path": str(evidence_path),
                "present": True,
                "valid": True,
            },
            "claim_evidence_map": {
                "path": str(claim_map_path),
                "present": True,
                "valid": True,
            },
        },
    )

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert "ai_reviewer_record" not in materialized
    assert "publication_eval_record_ref" not in materialized
    assert persisted is not None
    assert "ai_reviewer_record" not in persisted
    assert persisted["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert persisted["request_lifecycle"]["stale_record_ref"] == str(stale_record_path.resolve())
    assert persisted["request_lifecycle"]["required_currentness_refs"] == [
        str(evidence_path.resolve()),
        str(claim_map_path.resolve()),
    ]
    evidence = persisted["request_lifecycle"]["currentness_evidence"]
    assert evidence["blocked_reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert evidence["stale_record_ref"] == str(stale_record_path.resolve())
    assert evidence["authority_boundary"] == {
        "owner": "ai_reviewer",
        "can_authorize_quality": False,
        "can_authorize_submission": False,
    }
    by_ref = {item["required_ref"]: item for item in evidence["missing_refs"]}
    assert by_ref[str(evidence_path.resolve())]["live_digest"] == _sha256_text(
        evidence_path.read_text(encoding="utf-8")
    )
    assert by_ref[str(evidence_path.resolve())]["record_checks"] == [
        {
            "status": "current",
            "ref": str(evidence_path.resolve()),
            "digest": stale_evidence_digest,
        }
    ]
    assert by_ref[str(claim_map_path.resolve())]["live_digest"] == _sha256_text(
        claim_map_path.read_text(encoding="utf-8")
    )
    assert by_ref[str(claim_map_path.resolve())]["record_checks"] == [
        {
            "status": "current",
            "ref": str(claim_map_path.resolve()),
            "digest": stale_claim_map_digest,
        }
    ]


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
