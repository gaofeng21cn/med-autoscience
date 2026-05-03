from __future__ import annotations

import importlib
import json
from pathlib import Path


def _candidate(line_id: str, score: float, *, risk_cost: float = 1.0) -> dict[str, object]:
    return {
        "line_id": line_id,
        "title": f"{line_id} title",
        "dimensions": {
            "novelty": score,
            "clinical_relevance": score,
            "data_fit": score,
            "external_validation": score,
            "analysis_feasibility": score,
            "journal_fit": score,
            "risk_cost": risk_cost,
            "stop_threshold": "stop if transportability cannot be evaluated",
        },
        "evidence_refs": [f"artifacts/medical_paper/literature/{line_id}.json"],
    }


def test_orchestrator_selects_line_and_materializes_controller_decision(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    study_root = tmp_path / "study"

    projection = module.materialize_route_decision_orchestration(
        study_root=study_root,
        candidates=[_candidate("weak-line", 2), _candidate("strong-line", 5, risk_cost=2)],
        requested_action="select_line",
    )

    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    assert projection["status"] == "ready"
    assert projection["selected_line_id"] == "strong-line"
    assert projection["route_decision"] == "proceed_to_baseline"
    assert projection["next_action"] == "enter_baseline"
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
    assert projection["controller_decision_ref"] == str(decision_path.resolve())
    assert decision_path.is_file()
    written = json.loads(decision_path.read_text(encoding="utf-8"))
    assert written["decision_type"] == "study_line_route_decision"
    assert written["route_decision"] == "proceed_to_baseline"
    assert written["selected_line_id"] == "strong-line"
    assert written["write_authorized"] is True
    assert written["quality_claim_authorized"] is False


def test_orchestrator_routes_back_to_scout_when_literature_is_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.build_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("line-a", 4)],
        requested_action="select_line",
        readiness={"literature_status": "blocked", "literature_missing_reason": "missing_search_date"},
    )

    assert projection["status"] == "blocked"
    assert projection["route_decision"] == "return_to_scout"
    assert projection["next_action"] == "run_literature_scout"
    assert "literature_scout_blocked:missing_search_date" in projection["blockers"]
    assert projection["controller_decision"]["write_authorized"] is False


def test_orchestrator_switch_line_requires_alternative_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.build_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("line-a", 4)],
        requested_action="switch_line",
    )

    assert projection["status"] == "blocked"
    assert projection["route_decision"] == "human_gate"
    assert projection["next_action"] == "human_gate"
    assert "switch_line_requires_alternative_route" in projection["blockers"]
    assert projection["controller_decision"]["write_authorized"] is False


def test_orchestrator_switches_to_explicit_alternative_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("line-a", 3), _candidate("line-b", 4)],
        requested_action="switch_line",
        alternative_line_id="line-b",
    )

    assert projection["status"] == "ready"
    assert projection["selected_line_id"] == "line-b"
    assert projection["route_decision"] == "switch_line"
    assert projection["next_action"] == "enter_baseline"
    assert projection["controller_decision"]["route_target"] == "line-b"
