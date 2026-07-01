from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.reviewer_os_fixture_helpers import (
    claim_evidence_map_payload,
    evidence_ledger_payload,
)
from tests.test_publication_eval_latest_cases.shared import (
    _minimal_payload,
    _quality_assessment,
    _reviewer_operating_system,
    _write_json,
)

def test_ai_reviewer_publication_eval_record_controller_materializes_owner_record_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "execution": {"quest_id": "quest-001"}})
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["future_facing_limitations_plan"] = [
        {
            "limitation": "Current review is bound to the active manuscript digest.",
            "impact_on_claim": "Claims remain restrained until write repair and re-review.",
            "required_future_analysis_data_or_design": "Rerun AI reviewer after manuscript repair.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]

    def forbidden_progress_projection(**_: object) -> dict[str, object]:
        raise AssertionError("record-only materializer must not call progress_projection")

    monkeypatch.setattr(controller.domain_status_projection, "progress_projection", forbidden_progress_projection)

    result = controller.materialize_ai_reviewer_publication_eval_record(
        profile=SimpleNamespace(name="nfpitnet", studies_root=study_root.parent),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    assert result["status"] == "materialized"
    assert result["publication_eval_surface"] == "not_written"
    record_ref = Path(result["publication_eval_record_ref"])
    assert record_ref.name == "20260405T060000Z_publication_eval_record.json"
    assert record_ref.is_file()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    archived = json.loads(record_ref.read_text(encoding="utf-8"))
    assert archived["eval_id"] == payload["eval_id"]
def test_ai_reviewer_publication_eval_record_controller_preserves_latest_without_progress_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "execution": {"quest_id": "quest-001"}})
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    latest_before = {"surface": "publication_eval_latest_sentinel", "eval_id": "previous-eval"}
    _write_json(latest_path, latest_before)

    def forbidden_progress_projection(**_: object) -> dict[str, object]:
        raise AssertionError("record-only materializer must not call progress_projection")

    monkeypatch.setattr(controller.domain_status_projection, "progress_projection", forbidden_progress_projection)

    result = controller.materialize_ai_reviewer_publication_eval_record(
        profile=SimpleNamespace(name="nfpitnet", studies_root=study_root.parent),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    assert result["status"] == "materialized"
    assert result["publication_eval_surface"] == "not_written"
    assert json.loads(latest_path.read_text(encoding="utf-8")) == latest_before
def test_ai_reviewer_publication_eval_record_controller_blocks_empty_authoring_target_without_writes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "execution": {"quest_id": "quest-001"}})

    def forbidden_progress_projection(**_: object) -> dict[str, object]:
        raise AssertionError("record-only materializer must not call progress_projection")

    monkeypatch.setattr(controller.domain_status_projection, "progress_projection", forbidden_progress_projection)

    result = controller.materialize_ai_reviewer_publication_eval_record(
        profile=SimpleNamespace(name="nfpitnet", studies_root=study_root.parent),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "request_kind": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "owner_callable_payload_ref": str(
                study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
            ),
            "record_payload": None,
        },
        source="pytest",
        build_production_trace=True,
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "ai_reviewer_record_payload_missing"
    assert result["publication_eval_surface"] == "not_written"
    assert result["publication_eval_record_surface"] == "not_written"
    assert result["next_owner"] == "ai_reviewer"
    assert result["authority_boundary"]["publication_eval_latest_write_allowed"] is False
    assert result["authority_boundary"]["controller_decision_write_allowed"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()
def test_ai_reviewer_publication_eval_record_controller_rejects_invalid_reviewer_os_trace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "execution": {"quest_id": "quest-001"}})
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "request_kind": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "authority_contract": {"can_authorize_quality": False},
        "claim_boundary_review": {"status": "partial"},
    }

    def forbidden_progress_projection(**_: object) -> dict[str, object]:
        raise AssertionError("record-only materializer must not call progress_projection")

    monkeypatch.setattr(controller.domain_status_projection, "progress_projection", forbidden_progress_projection)

    with pytest.raises(ValueError, match="reviewer_operating_system invalid"):
        controller.materialize_ai_reviewer_publication_eval_record(
            profile=SimpleNamespace(name="nfpitnet", studies_root=study_root.parent),
            study_id="001-risk",
            study_root=None,
            entry_mode=None,
            record=payload,
            source="pytest",
        )

    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
def test_ai_reviewer_publication_eval_record_controller_rebuilds_production_trace_for_current_manuscript_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "execution": {"quest_id": "quest-001"}})
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["future_facing_limitations_plan"] = [
        {
            "limitation": "Current review is bound to the active manuscript digest.",
            "impact_on_claim": "Claims remain restrained until write repair and re-review.",
            "required_future_analysis_data_or_design": "Rerun AI reviewer after manuscript repair.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]
    manuscript_path = study_root / "paper" / "manuscript.md"
    manuscript_text = "# Current manuscript\n\nAI reviewer judged this current manuscript snapshot.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    manuscript_digest = "sha256:" + hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    body_authority_review_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_prose_review.json"
    )
    current_request_digest = "sha256:" + "b" * 64
    stale_request_digest = "sha256:" + "a" * 64
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": current_request_digest,
            "manuscript": {"path": str(manuscript_path), "digest": manuscript_digest},
        },
    )
    _write_json(
        review_path,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(request_path),
                "request_digest": stale_request_digest,
                "manuscript_ref": str(manuscript_path),
                "manuscript_digest": "sha256:" + "c" * 64,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Rewrite manuscript prose against the current evidence.",
                },
            },
        },
    )
    _write_json(
        body_authority_review_path,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "ai_reviewer_required": False,
            },
        },
    )
    evidence_ledger_ref = str(study_root / "paper" / "evidence_ledger.json")
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        claim_evidence_map_payload(evidence_ledger_ref=evidence_ledger_ref),
    )
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        evidence_ledger_payload(evidence_ledger_ref=evidence_ledger_ref),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"items": []})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    _write_json(study_root / "paper" / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_gate" / "latest.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": {
                    "medical_prose_review": {"path": str(body_authority_review_path)},
                },
            },
        },
    )
    payload["recommended_actions"] = [
        {
            "action_id": "route-current-record-to-write",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Route current manuscript record back to write.",
            "route_target": "write",
            "route_key_question": "Can write repair close the current reviewer record?",
            "route_rationale": "The current record is bound to the live manuscript.",
            "evidence_refs": [str(manuscript_path)],
            "requires_controller_decision": True,
        }
    ]
    payload["reviewer_operating_system"] = {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "request_kind": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "input_bundle": {
            "manuscript": str(manuscript_path),
            "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
            "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
            "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "medical_prose_review": str(review_path),
            "publication_gate_projection": str(study_root / "artifacts" / "publication_gate" / "latest.json"),
        },
        "currentness_checks": {
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": str(manuscript_path),
                "manuscript_digest": manuscript_digest,
            }
        },
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": current_request_digest,
            "evidence_ledger_digest": "sha256:" + "0" * 64,
            "claim_evidence_alignment_digest": "sha256:" + "1" * 64,
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{payload['eval_id']}",
            "fail_closed_when_missing": True,
            "missing_required_fields": ["current_package_freshness"],
        },
    }

    def forbidden_progress_projection(**_: object) -> dict[str, object]:
        raise AssertionError("record-only materializer must not call progress_projection")

    monkeypatch.setattr(controller.domain_status_projection, "progress_projection", forbidden_progress_projection)

    result = controller.materialize_ai_reviewer_publication_eval_record(
        profile=SimpleNamespace(name="nfpitnet", studies_root=study_root.parent),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
        build_production_trace=True,
    )

    assert result["status"] == "materialized"
    assert result["publication_eval_surface"] == "not_written"
    assert Path(result["publication_eval_record_ref"]).name != "20260405T060000Z_publication_eval_record.json"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    archived = json.loads(Path(result["publication_eval_record_ref"]).read_text(encoding="utf-8"))
    assert archived["emitted_at"] != payload["emitted_at"]
    reviewer_os = archived["reviewer_operating_system"]
    assert "request_kind" not in reviewer_os
    assert reviewer_os["decision_matrix"]
    assert reviewer_os["claim_evidence_alignment"]["status"] == "ready"
    assert reviewer_os["publication_quality_readiness"]["status"] == "blocked"
    assert reviewer_os["input_bundle"]["medical_prose_review"] == str(review_path.resolve())
    assert reviewer_os["currentness_checks"]["medical_prose_review"]["ref"] == str(review_path.resolve())
    assert reviewer_os["currentness_checks"]["medical_prose_review"]["request_digest"] == current_request_digest
    assert reviewer_os["currentness_checks"]["medical_prose_review"]["durable_medical_prose_review_status"] == (
        "stale_for_current_request"
    )
