from __future__ import annotations

import importlib
import json
from pathlib import Path


def _candidate(
    line_id: str,
    *,
    novelty: float,
    clinical_relevance: float,
    data_fit: float,
    external_validation: float,
    analysis_feasibility: float,
    journal_fit: float,
    risk_cost: float,
) -> dict[str, object]:
    return {
        "line_id": line_id,
        "title": f"{line_id} title",
        "dimensions": {
            "novelty": novelty,
            "clinical_relevance": clinical_relevance,
            "data_fit": data_fit,
            "external_validation": external_validation,
            "analysis_feasibility": analysis_feasibility,
            "journal_fit": journal_fit,
            "risk_cost": risk_cost,
            "stop_threshold": "stop if external validation is unavailable or calibration is poor",
        },
        "evidence_refs": [
            f"artifacts/medical_paper/literature_scout/{line_id}.json",
            f"paper/data_dictionary/{line_id}.json",
        ],
    }


def test_ranking_chooses_strongest_line(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_line_decision_engine")

    result = module.materialize_study_line_decision(
        study_root=tmp_path / "study",
        candidates=[
            _candidate(
                "descriptive-table",
                novelty=2,
                clinical_relevance=3,
                data_fit=5,
                external_validation=2,
                analysis_feasibility=5,
                journal_fit=3,
                risk_cost=1,
            ),
            _candidate(
                "transportable-risk-model",
                novelty=4,
                clinical_relevance=5,
                data_fit=5,
                external_validation=4,
                analysis_feasibility=4,
                journal_fit=5,
                risk_cost=2,
            ),
        ],
    )

    assert result["status"] == "selected"
    assert result["selected_line_id"] == "transportable-risk-model"
    assert result["route_decision"] == "proceed_to_baseline"
    assert [item["line_id"] for item in result["ranking"]] == [
        "transportable-risk-model",
        "descriptive-table",
    ]
    assert result["discarded_lines"] == [
        {
            "line_id": "descriptive-table",
            "total_score": 19.0,
            "status": "eligible",
            "blockers": [],
        }
    ]


def test_missing_dimension_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_line_decision_engine")
    candidate = _candidate(
        "underspecified-line",
        novelty=4,
        clinical_relevance=4,
        data_fit=4,
        external_validation=3,
        analysis_feasibility=4,
        journal_fit=4,
        risk_cost=1,
    )
    del candidate["dimensions"]["journal_fit"]  # type: ignore[index]

    result = module.materialize_study_line_decision(
        study_root=tmp_path / "study",
        candidates=[candidate],
    )

    assert result["status"] == "blocked"
    assert result["selected_line_id"] is None
    assert result["route_decision"] == "human_gate"
    assert {"candidate_id": "underspecified-line", "code": "candidate_missing_journal_fit"} in result["blockers"]
    assert result["quality_claim_authorized"] is False


def test_route_decision_writes_stable_artifact_path(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_line_decision_engine")
    study_root = tmp_path / "study"

    result = module.materialize_study_line_decision(
        study_root=study_root,
        candidates=[
            _candidate(
                "baseline-ready-line",
                novelty=3,
                clinical_relevance=5,
                data_fit=5,
                external_validation=4,
                analysis_feasibility=5,
                journal_fit=4,
                risk_cost=1,
            )
        ],
    )

    expected_path = study_root.resolve() / "artifacts" / "medical_paper" / "study_line_decision.json"
    assert result["artifact_path"] == str(expected_path)
    assert result["controller_decision_ref"] == "controller_decisions/latest.json"
    assert result["controller_decision_ref_suggestion"] == "controller_decisions/latest.json"
    assert result["route_decision"] == "proceed_to_baseline"
    assert expected_path.is_file()
    written = json.loads(expected_path.read_text(encoding="utf-8"))
    assert written["artifact_path"] == str(expected_path)
    assert written["selected_line_id"] == "baseline-ready-line"


def test_quality_claim_authorized_false(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_line_decision_engine")

    result = module.materialize_study_line_decision(
        study_root=tmp_path / "study",
        candidates=[
            _candidate(
                "clinically-grounded-line",
                novelty=4,
                clinical_relevance=5,
                data_fit=4,
                external_validation=4,
                analysis_feasibility=4,
                journal_fit=4,
                risk_cost=1,
            )
        ],
    )

    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False
