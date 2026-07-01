from __future__ import annotations

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
from tests.domain_action_request_lifecycle_cases.ai_reviewer_request_currentness_cases.shared import (
    _sha256_text,
    _write_json,
)

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
def test_stale_current_inputs_lifecycle_ignores_downstream_gate_projection_refs(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    gate_report_path = (
        study_root
        / "runtime"
        / "quests"
        / "003-dpcc"
        / "artifacts"
        / "reports"
        / "publishability_gate"
        / "latest.json"
    )
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    manuscript_text = "# Draft\n\nCurrent manuscript.\n"
    evidence_payload = {"schema_version": 1, "claim": "current evidence"}
    claim_payload = {"schema_version": 1, "claim": "current claim map"}
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_payload)
    _write_json(gate_report_path, {"schema_version": 1, "generated_at": "after-reviewer-record"})
    _write_json(latest_eval_path, {"schema_version": 1, "eval_id": "current-eval"})
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
                        str(gate_report_path.resolve()),
                        str(latest_eval_path.resolve()),
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
    assert lifecycle["required_currentness_refs"] == []
    consumed_refs = lifecycle.get("consumed_currentness_refs", [])
    assert str(gate_report_path.resolve()) not in consumed_refs
    assert str(latest_eval_path.resolve()) not in consumed_refs
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
