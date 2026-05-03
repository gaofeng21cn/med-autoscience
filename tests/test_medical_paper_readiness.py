from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _complete_surface_payloads() -> dict[str, dict[str, object]]:
    return {
        "literature_scout": {
            "search_strategy": {"query": "diabetes mortality prediction", "mesh_terms": ["Diabetes Mellitus"]},
            "search_date": "2026-05-03",
            "anchor_papers": ["pmid:1"],
            "guidelines": ["TRIPOD+AI"],
            "journal_neighbor_refs": ["paper:near-neighbor"],
        },
        "study_line_selection": {
            "selected_line_id": "primary-risk-model",
            "dimensions": {
                "novelty": "moderate",
                "clinical_relevance": "high",
                "data_fit": "high",
                "analysis_plasticity": "moderate",
                "external_validation": "available",
                "journal_fit": "good",
                "cost_risk": "bounded",
                "stop_threshold": "no external validation or poor calibration",
            },
            "discarded_alternatives": ["weak-clustering"],
        },
        "archetype_analysis_contract": {
            "status": "resolved",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "guideline_family": "TRIPOD+AI",
        },
        "bounded_analysis_candidate_board": {
            "candidates": [
                {
                    "mode": "exploit",
                    "target_claim": "primary transportability claim",
                    "expected_evidence_gain": "close calibration concern",
                    "cost_risk": "bounded",
                    "clinical_interpretability": "high",
                    "decision": "run",
                    "decision_reason": "reviewer concern targets calibration",
                }
            ]
        },
        "stop_loss_memo": {
            "attempted_paths": ["primary-risk-model"],
            "failure_reason": "",
            "evidence_gain_ceiling": "not reached",
            "alternative_routes": ["external-validation-only"],
            "human_gate_question": "",
            "decision": "continue",
        },
    }


def _complete_soak_stage_evidence() -> dict[str, list[str]]:
    return {
        "literature_scout": ["artifacts/medical_paper/literature_scout.json"],
        "line_selection": ["artifacts/medical_paper/study_line_selection.json"],
        "main_analysis": ["paper/medical_analysis_contract.json"],
        "bounded_analysis": ["artifacts/medical_paper/bounded_analysis_candidate_board.json"],
        "route_back": ["artifacts/controller_decisions/latest.json"],
        "stop_loss": ["artifacts/medical_paper/stop_loss_memo.json"],
        "revision_reopen": ["artifacts/task_intake/latest.json"],
        "runtime_recovery": ["artifacts/runtime/runtime_supervision/latest.json"],
        "finalize_rebuild": ["paper/submission_minimal/current_package.zip"],
        "final_pre_submission_audit": ["artifacts/publication_eval/latest.json"],
    }


def _materialize_complete_readiness_inputs(module: object, study_root: Path) -> None:
    for surface_key, payload in _complete_surface_payloads().items():
        module.materialize_medical_paper_readiness_surface(
            study_root=study_root,
            surface_key=surface_key,
            payload=payload,
        )
    _write_json(
        study_root / "paper" / "target_journal_writing_layer.json",
        {
            "surface": "target_journal_writing_layer",
            "schema_version": 1,
            "role": "ai_reviewer_quality_context",
            "target_journal_family": "general_internal_medicine",
            "near_neighbor_style_corpus": [{"journal": "JAMA", "style_ref": "workspace_lit:jama"}],
            "section_plan": {
                "Introduction": "gap and objective",
                "Methods": "cohort and analysis",
                "Results": "primary finding",
                "Discussion": "interpretation and limits",
            },
            "claim_to_paragraph_map": [
                {"claim_id": "primary_claim", "section": "Results", "evidence_refs": ["evidence:primary"]}
            ],
            "display_to_claim_map": [{"display_id": "Table 2", "claim_id": "primary_claim"}],
            "restrained_language_strategy": {"required_claim_qualifiers": ["was associated with"]},
            "mechanical_projection_can_authorize_quality": False,
            "quality_claim_authorized": False,
        },
    )


def test_medical_paper_readiness_surface_marks_complete_study_ready(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "study"
    _materialize_complete_readiness_inputs(module, study_root)
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {"stage_evidence": _complete_soak_stage_evidence()},
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    assert readiness["surface"] == "medical_paper_readiness"
    assert readiness["overall_status"] == "ready"
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False
    assert readiness["next_action"]["action_id"] == "continue_managed_execution"
    assert {item["surface_key"]: item["status"] for item in readiness["capability_surfaces"]} == {
        "literature_scout": "present",
        "study_line_selection": "present",
        "archetype_analysis_contract": "present",
        "bounded_analysis_candidate_board": "present",
        "stop_loss_memo": "present",
        "target_journal_writing_layer": "present",
        "real_study_soak_matrix_evidence": "present",
    }


def test_medical_paper_readiness_marks_sanitized_real_study_soak_evidence_present(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "sanitized-study"
    _materialize_complete_readiness_inputs(module, study_root)
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "fixture_kind": "sanitized_real_study_soak_fixture",
            "contains_phi": False,
            "stage_evidence": _complete_soak_stage_evidence(),
        },
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    soak_surface = by_key["real_study_soak_matrix_evidence"]
    assert readiness["overall_status"] == "ready"
    assert soak_surface["status"] == "present"
    assert soak_surface["missing_reason"] == ""
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False


def test_medical_paper_readiness_blocks_sanitized_soak_fixture_with_missing_stage(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "sanitized-study"
    _materialize_complete_readiness_inputs(module, study_root)
    stage_evidence = _complete_soak_stage_evidence()
    stage_evidence.pop("runtime_recovery")
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "fixture_kind": "sanitized_real_study_soak_fixture",
            "contains_phi": False,
            "stage_evidence": stage_evidence,
        },
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    soak_surface = by_key["real_study_soak_matrix_evidence"]
    assert readiness["overall_status"] == "blocked"
    assert soak_surface["status"] == "partial"
    assert soak_surface["missing_reason"] == "missing_required_soak_stage"
    assert soak_surface["missing_stage_gaps"] == [
        {
            "stage": "runtime_recovery",
            "missing_reason": "missing_durable_evidence_ref",
        }
    ]
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False


def test_medical_paper_readiness_surface_fails_closed_when_inputs_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "study"
    module.materialize_medical_paper_readiness_surface(
        study_root=study_root,
        surface_key="literature_scout",
        payload=_complete_surface_payloads()["literature_scout"],
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    assert readiness["overall_status"] == "blocked"
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False
    assert readiness["next_action"] == {
        "action_id": "complete_medical_paper_readiness_surface",
        "surface_key": "study_line_selection",
        "summary": "补齐 Study Line Selection Scorecard 后再继续自动论文链路。",
    }
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["literature_scout"]["status"] == "present"
    assert by_key["study_line_selection"]["status"] == "missing"
    assert by_key["study_line_selection"]["missing_reason"] == "missing_canonical_artifact"


def test_medical_paper_readiness_materializer_rejects_incomplete_payload(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")

    result = module.materialize_medical_paper_readiness_surface(
        study_root=tmp_path / "study",
        surface_key="bounded_analysis_candidate_board",
        payload={"candidates": []},
    )

    assert result["surface_key"] == "bounded_analysis_candidate_board"
    assert result["status"] == "blocked"
    assert result["artifact_path"].endswith("artifacts/medical_paper/bounded_analysis_candidate_board.json")

    readiness = module.build_medical_paper_readiness_surface(study_root=tmp_path / "study")
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["bounded_analysis_candidate_board"]["status"] == "blocked"
    assert by_key["bounded_analysis_candidate_board"]["missing_reason"] == "missing_candidates"
