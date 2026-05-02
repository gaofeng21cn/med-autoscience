from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


REQUIRED_READINESS_IDS = [
    "clinical_question",
    "population_design_outcome",
    "display_to_claim_map",
    "claim_evidence_map",
    "section_purpose",
    "reader_flow_plan",
    "journal_voice",
    "ai_prose_review_feedback_loop",
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _closed_readiness() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "closed",
        "required_before": "first_full_draft",
        "readiness_items": [
            {
                "readiness_id": readiness_id,
                "status": "closed",
                "evidence_refs": ["paper/medical_manuscript_blueprint.json"],
            }
            for readiness_id in REQUIRED_READINESS_IDS
        ],
    }


def _closed_ledger(*, surface: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": surface,
        "status": "closed",
        "closures": [
            {
                "closure_id": f"{surface}::core",
                "status": "closed",
                "evidence_refs": ["paper/medical_manuscript_blueprint.json"],
            }
        ],
    }


def _authorized_blueprint() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "medical_manuscript_blueprint",
        "canonical_ready": True,
        "clinical_problem": "Postoperative NF-PitNET follow-up needs a restrained risk framing.",
        "authoring_provenance": {
            "owner": "ai_author",
            "source_kind": "medical_manuscript_blueprint",
            "policy_id": "medical_manuscript_blueprint_v1",
            "ai_reviewer_required": False,
        },
    }


def _reviewer_operating_system(study_root: Path) -> dict[str, Any]:
    input_bundle = {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    dimensions = [
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    ]
    rubric_scores = {
        dimension: {
            "status": "ready",
            "rationale": f"{dimension} is ready from manuscript and ledger evidence.",
            "evidence_refs": [str(study_root / "paper" / "medical_manuscript_blueprint.json")],
        }
        for dimension in dimensions
    }
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": input_bundle,
        "rubric_scores": rubric_scores,
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is ready.",
            }
            for dimension in dimensions
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "first_full_draft",
            "rationale": "All required pre-draft authority surfaces are closed.",
        },
    }


def _ai_reviewer_publication_eval(study_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-01T00:00:00+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                str(study_root / "paper" / "evidence_ledger.json"),
                str(study_root / "paper" / "review_ledger.json"),
            ],
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "medical_journal_prose_quality": {
                "status": "ready",
                "summary": "AI reviewer cleared medical-journal prose readiness for first full draft.",
                "evidence_refs": [str(study_root / "paper" / "medical_manuscript_blueprint.json")],
            }
        },
        "reviewer_operating_system": _reviewer_operating_system(study_root),
        "verdict": {
            "overall_verdict": "not_blocked",
            "primary_claim_status": "supported",
            "summary": "Pre-draft quality authority is closed.",
        },
        "gaps": [],
        "recommended_actions": [],
    }


def _mechanical_projection_publication_eval(study_root: Path) -> dict[str, Any]:
    payload = _ai_reviewer_publication_eval(study_root)
    payload["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_report",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
        "ai_reviewer_required": True,
    }
    payload.pop("reviewer_operating_system")
    return payload


def _write_closed_authority_surfaces(study_root: Path) -> None:
    _write_json(study_root / "paper" / "pre_draft_writing_readiness.json", _closed_readiness())
    _write_json(study_root / "paper" / "evidence_ledger.json", _closed_ledger(surface="evidence_ledger"))
    _write_json(study_root / "paper" / "review_ledger.json", _closed_ledger(surface="review_ledger"))
    _write_json(study_root / "paper" / "medical_manuscript_blueprint.json", _authorized_blueprint())
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_publication_eval(study_root),
    )


def test_pre_draft_runtime_allows_first_full_draft_only_after_closed_ai_reviewer_authority(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.pre_draft_quality_runtime")
    study_root = tmp_path / "study"
    _write_closed_authority_surfaces(study_root)

    result = module.build_pre_draft_quality_runtime_state(study_root=study_root)

    assert result["surface"] == "pre_draft_quality_runtime_state"
    assert result["schema_version"] == 1
    assert result["status"] == "first_full_draft_ready"
    assert result["readiness"] == {
        "required_before": "first_full_draft",
        "draft_ready": True,
        "next_route": "first_full_draft",
        "mechanical_file_presence_can_authorize_ready": False,
    }
    assert result["blockers"] == []
    assert result["route_back"] == {
        "required": False,
        "status": "clear",
        "target": "first_full_draft",
        "reason": "pre_draft_quality_authority_closed",
    }
    assert result["authority"]["assessment_provenance"] == {
        "owner": "ai_reviewer",
        "policy_id": "medical_publication_critique_v1",
        "ai_reviewer_required": False,
        "source_refs": [
            str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            str(study_root / "paper" / "evidence_ledger.json"),
            str(study_root / "paper" / "review_ledger.json"),
        ],
    }
    assert result["authority"]["reviewer_operating_system_valid"] is True
    assert result["refs"]["publication_eval"]["exists"] is True


def test_pre_draft_runtime_missing_or_open_readiness_routes_back(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.pre_draft_quality_runtime")
    study_root = tmp_path / "study"
    _write_closed_authority_surfaces(study_root)
    (study_root / "paper" / "pre_draft_writing_readiness.json").unlink()

    missing_result = module.build_pre_draft_quality_runtime_state(study_root=study_root)

    assert missing_result["status"] == "route_back_required"
    assert missing_result["readiness"]["draft_ready"] is False
    assert "pre_draft_readiness_missing" in missing_result["blockers"]
    assert missing_result["route_back"]["target"] == "pre_draft_writing_readiness"

    _write_json(
        study_root / "paper" / "pre_draft_writing_readiness.json",
        {
            **_closed_readiness(),
            "status": "open",
        },
    )

    open_result = module.build_pre_draft_quality_runtime_state(study_root=study_root)

    assert open_result["status"] == "route_back_required"
    assert open_result["readiness"]["draft_ready"] is False
    assert "pre_draft_readiness_not_closed" in open_result["blockers"]
    assert open_result["route_back"]["target"] == "pre_draft_writing_readiness"


def test_pre_draft_runtime_missing_ledger_or_blueprint_routes_back(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.pre_draft_quality_runtime")
    study_root = tmp_path / "study"
    _write_closed_authority_surfaces(study_root)
    (study_root / "paper" / "evidence_ledger.json").unlink()
    (study_root / "paper" / "medical_manuscript_blueprint.json").unlink()

    result = module.build_pre_draft_quality_runtime_state(study_root=study_root)

    assert result["status"] == "route_back_required"
    assert result["readiness"]["draft_ready"] is False
    assert "evidence_ledger_missing" in result["blockers"]
    assert "medical_manuscript_blueprint_missing" in result["blockers"]
    assert result["route_back"]["target"] == "pre_draft_writing_readiness"


def test_pre_draft_runtime_mechanical_publication_eval_requires_review(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.pre_draft_quality_runtime")
    study_root = tmp_path / "study"
    _write_closed_authority_surfaces(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _mechanical_projection_publication_eval(study_root),
    )

    result = module.build_pre_draft_quality_runtime_state(study_root=study_root)

    assert result["status"] == "review_required"
    assert result["readiness"]["draft_ready"] is False
    assert "publication_eval_not_ai_reviewer_backed" in result["blockers"]
    assert result["route_back"]["target"] == "ai_reviewer_publication_eval"
    assert result["authority"]["assessment_provenance"]["owner"] == "mechanical_projection"
    assert result["authority"]["mechanical_file_presence_can_authorize_ready"] is False


def test_pre_draft_runtime_file_presence_without_ai_provenance_cannot_authorize(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.pre_draft_quality_runtime")
    study_root = tmp_path / "study"
    _write_closed_authority_surfaces(study_root)
    payload = _ai_reviewer_publication_eval(study_root)
    payload.pop("assessment_provenance")
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)

    result = module.build_pre_draft_quality_runtime_state(study_root=study_root)

    assert result["status"] == "review_required"
    assert result["readiness"]["draft_ready"] is False
    assert "publication_eval_ai_reviewer_provenance_missing" in result["blockers"]
    assert result["route_back"]["target"] == "ai_reviewer_publication_eval"
    assert result["authority"]["assessment_provenance"] == {}
    assert result["authority"]["mechanical_file_presence_can_authorize_ready"] is False
