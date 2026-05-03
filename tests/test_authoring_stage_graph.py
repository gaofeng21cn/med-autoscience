from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _closed_pre_draft_readiness() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "pre_draft_writing_readiness",
        "status": "closed",
        "readiness_items": [
            {
                "readiness_id": readiness_id,
                "status": "closed",
                "evidence_refs": ["paper/medical_manuscript_blueprint.json"],
            }
            for readiness_id in (
                "clinical_question",
                "display_to_claim_map",
                "claim_evidence_map",
                "section_purpose",
                "reader_flow_plan",
                "ai_prose_review_feedback_loop",
            )
        ],
    }


def _closed_authoring_workplan() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "authoring_workplan",
        "status": "closed",
        "sections": [
            {"section_id": "introduction", "status": "closed"},
            {"section_id": "methods", "status": "closed"},
        ],
        "work_units": [
            {"work_unit_id": "outline_clinical_problem", "status": "closed"},
            {"work_unit_id": "write_introduction", "status": "closed"},
            {"work_unit_id": "write_methods", "status": "closed"},
            {"work_unit_id": "refine_journal_voice", "status": "closed"},
        ],
        "authority": {
            "source_family": "PaperOrchestra-inspired",
            "read_model_only": True,
            "can_authorize_draft_readiness": False,
        },
    }


def _closed_blueprint() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "medical_manuscript_blueprint",
        "canonical_ready": True,
        "clinical_problem": "Postoperative NF-PitNET follow-up needs restrained risk framing.",
        "authoring_provenance": {
            "owner": "ai_author",
            "source_kind": "medical_manuscript_blueprint",
            "ai_reviewer_required": False,
        },
    }


def _closed_ledger(surface: str) -> dict[str, Any]:
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


def _ai_reviewer_publication_eval(study_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "publication_eval",
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-03T00:00:00+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "source_refs": [
                str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                str(study_root / "paper" / "evidence_ledger.json"),
                str(study_root / "paper" / "review_ledger.json"),
            ],
        },
        "verdict": {
            "overall_verdict": "not_blocked",
            "summary": "Pre-draft quality authority is closed.",
        },
        "gaps": [],
    }


def _write_closed_surfaces(study_root: Path) -> None:
    _write_json(study_root / "paper" / "authoring_workplan.json", _closed_authoring_workplan())
    _write_json(study_root / "paper" / "pre_draft_writing_readiness.json", _closed_pre_draft_readiness())
    _write_json(study_root / "paper" / "medical_manuscript_blueprint.json", _closed_blueprint())
    _write_json(study_root / "paper" / "evidence_ledger.json", _closed_ledger("evidence_ledger"))
    _write_json(study_root / "paper" / "review_ledger.json", _closed_ledger("review_ledger"))
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_publication_eval(study_root),
    )


def test_authoring_stage_graph_projects_closed_paper_authoring_dag(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.authoring_stage_graph")
    study_root = tmp_path / "study"
    _write_closed_surfaces(study_root)

    result = module.build_authoring_stage_graph(study_root=study_root)

    assert result["surface"] == "authoring_stage_graph"
    assert result["schema_version"] == 1
    assert result["status"] == "projected"
    assert [node["stage_id"] for node in result["nodes"]] == [
        "outline",
        "display_planning",
        "literature_grounding",
        "section_writing",
        "refinement",
    ]
    assert {node["stage_id"]: node["status"] for node in result["nodes"]} == {
        "outline": "closed",
        "display_planning": "closed",
        "literature_grounding": "closed",
        "section_writing": "closed",
        "refinement": "closed",
    }
    assert result["edges"] == [
        {"from_stage_id": "outline", "to_stage_id": "display_planning"},
        {"from_stage_id": "outline", "to_stage_id": "literature_grounding"},
        {"from_stage_id": "display_planning", "to_stage_id": "section_writing"},
        {"from_stage_id": "literature_grounding", "to_stage_id": "section_writing"},
        {"from_stage_id": "section_writing", "to_stage_id": "refinement"},
    ]
    assert result["blocking_stage_ids"] == []
    assert result["authority"] == {
        "owner": "MAS",
        "read_model_only": True,
        "can_authorize_draft_readiness": False,
        "can_mutate_runtime": False,
        "runtime_owner": "MAS controller",
        "publication_owner": "MAS",
        "paper_orchestra_runtime_owner": False,
        "paper_orchestra_skill_pack_owner": False,
    }
    assert "PaperOrchestra" not in json.dumps(result["authority"], ensure_ascii=False)


def test_authoring_stage_graph_missing_workplan_fails_closed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.authoring_stage_graph")
    study_root = tmp_path / "study"
    _write_closed_surfaces(study_root)
    (study_root / "paper" / "authoring_workplan.json").unlink()

    result = module.build_authoring_stage_graph(study_root=study_root)

    nodes = {node["stage_id"]: node for node in result["nodes"]}
    assert result["status"] == "blocked"
    assert result["blocking_stage_ids"] == ["outline", "section_writing"]
    assert nodes["outline"]["status"] == "blocked"
    assert nodes["section_writing"]["status"] == "blocked"
    assert "authoring_workplan_missing" in nodes["outline"]["blockers"]
    assert "authoring_workplan_missing" in nodes["section_writing"]["blockers"]
    assert result["authority"]["can_authorize_draft_readiness"] is False


def test_authoring_stage_graph_mechanical_eval_blocks_refinement(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.authoring_stage_graph")
    study_root = tmp_path / "study"
    _write_closed_surfaces(study_root)
    publication_eval = _ai_reviewer_publication_eval(study_root)
    publication_eval["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_report",
        "policy_id": "publication_gate_projection_v1",
        "ai_reviewer_required": True,
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)

    result = module.build_authoring_stage_graph(study_root=study_root)

    nodes = {node["stage_id"]: node for node in result["nodes"]}
    assert result["status"] == "blocked"
    assert result["blocking_stage_ids"] == ["refinement"]
    assert nodes["refinement"]["status"] == "blocked"
    assert "publication_eval_not_ai_reviewer_backed" in nodes["refinement"]["blockers"]
    assert "publication_eval_still_requires_ai_reviewer" in nodes["refinement"]["blockers"]
    assert result["authority"]["can_authorize_draft_readiness"] is False
