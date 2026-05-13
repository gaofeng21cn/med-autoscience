from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


MODULE_NAME = "med_autoscience.controllers.revision_rebuttal_loop"


def _complete_payload() -> dict[str, Any]:
    return {
        "reviewer_comments": [
            {
                "comment_id": "R1-C1",
                "source": "reviewer_1",
                "concern": "Additional analysis is required for the major subgroup claim.",
                "severity": "major",
                "target_claim": "Subgroup effect is robust across centers.",
                "requested_change": "Please provide additional analysis with sensitivity checks.",
            },
            {
                "comment_id": "R2-C1",
                "source": "reviewer_2",
                "concern": "The manuscript uses overstrong causal wording.",
                "severity": "major",
                "target_section": "Discussion",
                "requested_change": "Downgrade the causal wording to an association claim.",
            },
            {
                "comment_id": "R3-C1",
                "source": "editor",
                "concern": "Clarify the methods paragraph.",
                "severity": "minor",
                "target_section": "Methods",
                "requested_change": "Revise prose for clarity.",
            },
        ],
        "evidence_ledger_refs": ["paper/evidence_ledger.json#revision-intake"],
        "review_ledger_refs": ["paper/review/review_ledger.json#reviewer-round-1"],
    }


def test_revision_rebuttal_loop_builds_canonical_projection() -> None:
    module = importlib.import_module(MODULE_NAME)

    projection = module.build_revision_rebuttal_loop_projection(_complete_payload())

    assert projection["surface"] == "revision_rebuttal_loop"
    assert projection["schema_version"] == 1
    assert projection["status"] == "ready"
    assert projection["reviewer_comment_count"] == 3
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
    assert projection["durable_refs"] == {
        "evidence_ledger_refs": ["paper/evidence_ledger.json#revision-intake"],
        "review_ledger_refs": ["paper/review/review_ledger.json#reviewer-round-1"],
    }
    assert projection["next_action"] == {
        "action": "repair_recheck_required",
        "reason": "analysis_repair_requires_ai_reviewer_recheck",
    }

    matrix = projection["action_matrix"]
    assert matrix[0] == {
        "comment_id": "R1-C1",
        "stable_concern_id": "reviewer_1:R1-C1",
        "repair_type": "analysis_repair",
        "action_type": "analysis_repair",
        "action_label": "AUTHOR_INPUT_NEEDED",
        "missing_context_fields": ["line_number", "citation_ref", "statistical_result"],
        "required_surface_refs": [
            "paper/evidence_ledger.json#revision-intake",
            "paper/review/review_ledger.json#reviewer-round-1",
        ],
        "work_units": {
            "analysis_repair": {
                "work_unit_type": "analysis_repair",
                "required": True,
                "target_claim": "Subgroup effect is robust across centers.",
                "target_section": None,
                "ledger_refs": [
                    "paper/evidence_ledger.json#revision-intake",
                    "paper/review/review_ledger.json#reviewer-round-1",
                ],
            },
            "text_repair": {
                "work_unit_type": "text_repair",
                "required": False,
                "target_claim": "Subgroup effect is robust across centers.",
                "target_section": None,
                "ledger_refs": [
                    "paper/evidence_ledger.json#revision-intake",
                    "paper/review/review_ledger.json#reviewer-round-1",
                ],
            },
            "ai_reviewer_recheck": {
                "work_unit_type": "ai_reviewer_recheck",
                "required": True,
                "reason": "analysis_repair_requires_ai_reviewer_recheck",
                "ledger_refs": [
                    "paper/evidence_ledger.json#revision-intake",
                    "paper/review/review_ledger.json#reviewer-round-1",
                ],
            },
        },
        "repair_routes": {
            "analysis_repair": {
                "required": True,
                "target_claim": "Subgroup effect is robust across centers.",
                "target_section": None,
                "ledger_refs": [
                    "paper/evidence_ledger.json#revision-intake",
                    "paper/review/review_ledger.json#reviewer-round-1",
                ],
            },
            "text_repair": {
                "required": False,
                "target_claim": "Subgroup effect is robust across centers.",
                "target_section": None,
                "ledger_refs": [
                    "paper/evidence_ledger.json#revision-intake",
                    "paper/review/review_ledger.json#reviewer-round-1",
                ],
            },
            "ai_reviewer_recheck": {
                "required": True,
                "reason": "analysis_repair_requires_ai_reviewer_recheck",
            },
        },
        "ai_reviewer_recheck_required": True,
        "response_letter_point": (
            "Response to R1-C1: route to analysis_repair for the requested change; "
            "cite the repaired surfaces before rebuttal closure."
        ),
    }
    assert matrix[1]["repair_type"] == "claim_downgrade"
    assert matrix[1]["action_type"] == "text_repair"
    assert matrix[1]["ai_reviewer_recheck_required"] is True
    assert matrix[1]["repair_routes"]["text_repair"]["required"] is True
    assert matrix[1]["work_units"]["text_repair"]["required"] is True
    assert matrix[1]["repair_routes"]["ai_reviewer_recheck"] == {
        "required": True,
        "reason": "text_repair_requires_ai_reviewer_recheck",
    }
    assert matrix[2]["repair_type"] == "prose_revision"
    assert matrix[2]["action_type"] == "text_repair"
    assert matrix[2]["ai_reviewer_recheck_required"] is True
    assert matrix[2]["repair_routes"]["text_repair"]["required"] is True
    assert matrix[2]["work_units"]["ai_reviewer_recheck"]["work_unit_type"] == "ai_reviewer_recheck"
    assert matrix[2]["repair_routes"]["ai_reviewer_recheck"] == {
        "required": True,
        "reason": "text_repair_requires_ai_reviewer_recheck",
    }


def test_revision_rebuttal_loop_blocks_without_reviewer_comments() -> None:
    module = importlib.import_module(MODULE_NAME)
    payload = _complete_payload()
    payload["reviewer_comments"] = []

    projection = module.build_revision_rebuttal_loop_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["blockers"] == ["missing_reviewer_comments"]
    assert projection["reviewer_comment_count"] == 0
    assert projection["action_matrix"] == []
    assert projection["next_action"] == {
        "action": "collect_revision_intake",
        "reason": "missing_reviewer_comments",
    }


def test_revision_rebuttal_loop_blocks_without_evidence_or_review_ledger_refs() -> None:
    module = importlib.import_module(MODULE_NAME)
    payload = _complete_payload()
    payload["evidence_ledger_refs"] = []
    payload["review_ledger_refs"] = []

    projection = module.build_revision_rebuttal_loop_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["blockers"] == ["missing_evidence_ledger_refs", "missing_review_ledger_refs"]
    assert projection["next_action"] == {
        "action": "collect_revision_intake",
        "reason": "missing_evidence_ledger_refs",
    }


def test_revision_rebuttal_loop_blocks_comments_missing_required_fields() -> None:
    module = importlib.import_module(MODULE_NAME)
    payload = _complete_payload()
    del payload["reviewer_comments"][0]["requested_change"]

    projection = module.build_revision_rebuttal_loop_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["blockers"] == ["reviewer_comment_missing_requested_change:R1-C1"]
    assert projection["action_matrix"] == []


def test_revision_rebuttal_loop_requires_every_comment_to_route_to_repair_and_recheck() -> None:
    module = importlib.import_module(MODULE_NAME)
    projection = module.build_revision_rebuttal_loop_projection(_complete_payload())

    for item in projection["comment_to_action_matrix"]:
        assert item["action_type"] in {"analysis_repair", "text_repair", "human_gate", "rebuttal_only"}
        assert item["work_units"]["ai_reviewer_recheck"]["required"] is True
        assert item["work_units"]["ai_reviewer_recheck"]["work_unit_type"] == "ai_reviewer_recheck"
        assert item["work_units"]["ai_reviewer_recheck"]["ledger_refs"] == item[
            "required_surface_refs"
        ]
        assert item["work_units"]["analysis_repair"]["work_unit_type"] == "analysis_repair"
        assert item["work_units"]["text_repair"]["work_unit_type"] == "text_repair"


def test_revision_rebuttal_loop_requires_target_section_or_target_claim() -> None:
    module = importlib.import_module(MODULE_NAME)
    payload = _complete_payload()
    payload["reviewer_comments"][0].pop("target_claim")
    payload["reviewer_comments"][0].pop("target_section", None)

    projection = module.build_revision_rebuttal_loop_projection(payload)

    assert projection["status"] == "blocked"
    assert projection["blockers"] == ["reviewer_comment_missing_target:R1-C1"]


def test_revision_rebuttal_loop_materializes_only_study_medical_paper_artifact(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "study"

    result = module.materialize_revision_rebuttal_loop(study_root, _complete_payload())

    artifact_path = study_root / "artifacts" / "medical_paper" / "revision_rebuttal_loop.json"
    assert result == {
        "surface": "revision_rebuttal_loop",
        "status": "ready",
        "artifact_path": str(artifact_path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    assert artifact_path.exists()
    read_model = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert read_model["surface"] == "revision_rebuttal_loop"
    assert read_model["status"] == "ready"
    assert read_model["reviewer_comment_count"] == 3
