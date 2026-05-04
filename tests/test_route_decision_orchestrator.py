from __future__ import annotations

import importlib
import json
from pathlib import Path


def _candidate(line_id: str, score: float, *, risk_cost: float = 1.0) -> dict[str, object]:
    return {
        "line_id": line_id,
        "title": f"{line_id} title",
        "question": f"Can {line_id} answer the locked research question?",
        "expected_artifact": f"artifacts/medical_paper/candidate_paths/{line_id}.json",
        "claim_boundary_change": "unchanged",
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


def test_orchestrator_persists_line_decision_summary_in_controller_decision(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    study_root = tmp_path / "study"

    projection = module.materialize_route_decision_orchestration(
        study_root=study_root,
        candidates=[_candidate("baseline-line", 4), _candidate("validation-line", 5, risk_cost=2)],
        requested_action="select_line",
    )

    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    written = json.loads(decision_path.read_text(encoding="utf-8"))
    line_decision = written["study_line_decision"]

    assert projection["study_line_decision"]["controller_decision_ref"] == str(decision_path.resolve())
    assert line_decision["controller_decision_ref"] == str(decision_path.resolve())
    assert line_decision["current_route"]["line_id"] == "validation-line"
    assert line_decision["current_route"]["route_decision"] == "proceed_to_baseline"
    assert line_decision["route_back"]["route_decision"] == "return_to_scout"
    assert line_decision["switch_line"]["route_decision"] == "switch_line"
    assert line_decision["human_gate"]["route_decision"] == "human_gate"
    assert [route["line_id"] for route in line_decision["alternative_routes"]] == ["baseline-line"]


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


def test_orchestrator_projects_bounded_candidate_path_graph_without_replacing_controller_truth(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    study_root = tmp_path / "study"

    projection = module.build_route_decision_orchestration(
        study_root=study_root,
        candidates=[_candidate("line-a", 3), _candidate("line-b", 5)],
        requested_action="select_line",
    )

    graph = projection["candidate_path_graph"]
    assert graph["surface"] == "candidate_path_graph"
    assert graph["authority"] == "read_model_only"
    assert graph["replaces_controller_decision"] is False
    assert graph["can_replace_controller_decision_latest"] is False
    assert graph["can_replace_study_runtime_status"] is False
    assert graph["replaces_study_truth"] is False
    assert graph["can_replace_study_truth"] is False
    assert graph["can_authorize_submission_readiness"] is False
    assert graph["can_authorize_publication_quality"] is False
    assert graph["controller_decision_ref"] == projection["controller_decision_ref"]
    assert graph["allowed_decisions"] == ["proceed", "refine", "pivot", "stop", "human_gate"]
    assert graph["decision"] == "proceed"
    assert graph["selected_candidate_id"] == "line-b"

    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    assert not decision_path.exists()

    for candidate in graph["candidates"]:
        assert set(candidate) >= {
            "question",
            "evidence_basis",
            "expected_artifact",
            "stop_rule",
            "decision",
            "controller_decision_ref",
        }
        assert candidate["controller_decision_ref"] == projection["controller_decision_ref"]
        assert candidate["decision"] in graph["allowed_decisions"]


def test_candidate_path_graph_normalizes_hostile_authority_claims_to_read_model_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    hostile = _candidate("hostile-line", 5)
    hostile.update(
        {
            "decision": "proceed",
            "can_replace_controller_decision_latest": True,
            "can_replace_study_runtime_status": True,
            "can_replace_study_truth": True,
            "can_authorize_submission_readiness": True,
            "can_authorize_publication_quality": True,
        }
    )

    projection = module.build_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[hostile],
        requested_action="select_line",
    )

    graph = projection["candidate_path_graph"]
    assert graph["authority"] == "read_model_only"
    assert graph["decision"] == "proceed"
    assert graph["can_replace_controller_decision_latest"] is False
    assert graph["can_replace_study_runtime_status"] is False
    assert graph["can_replace_study_truth"] is False
    assert graph["can_authorize_submission_readiness"] is False
    assert graph["can_authorize_publication_quality"] is False
    assert projection["controller_decision"]["quality_claim_authorized"] is False
    assert projection["controller_decision"]["mechanical_projection_can_authorize_quality"] is False
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False


def test_orchestrator_human_gates_pivot_when_claim_boundary_expands(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    expanded = _candidate("expanded-line", 5)
    expanded["claim_boundary_change"] = "expanded"

    projection = module.build_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("line-a", 4), expanded],
        requested_action="switch_line",
        alternative_line_id="expanded-line",
    )

    graph = projection["candidate_path_graph"]
    assert projection["status"] == "blocked"
    assert projection["route_decision"] == "human_gate"
    assert projection["next_action"] == "human_gate"
    assert graph["decision"] == "human_gate"
    assert graph["selected_candidate_id"] == "expanded-line"
    assert "pivot_requires_unchanged_claim_boundary" in projection["blockers"]
    pivot_candidate = next(candidate for candidate in graph["candidates"] if candidate["candidate_id"] == "expanded-line")
    assert pivot_candidate["decision"] == "human_gate"


def test_orchestrator_human_gates_candidate_path_graph_when_required_fields_are_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    incomplete = _candidate("line-a", 4)
    incomplete.pop("expected_artifact")

    projection = module.build_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[incomplete],
        requested_action="select_line",
    )

    graph = projection["candidate_path_graph"]
    assert projection["status"] == "blocked"
    assert projection["route_decision"] == "human_gate"
    assert graph["decision"] == "human_gate"
    assert "candidate_line-a_missing_expected_artifact" in projection["blockers"]
    assert graph["candidates"][0]["decision"] == "human_gate"


def test_orchestrator_requires_bounded_repair_for_statistical_blockers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("line-a", 5)],
        requested_action="select_line",
        route_signals={
            "statistical_blockers": ["missing_precision_statement", "external_validation_waiver_missing"],
            "attempted_paths": ["primary_analysis"],
            "evidence_gain_ceiling": "moderate_if_repaired",
        },
    )

    decision_path = tmp_path / "study" / "artifacts" / "controller_decisions" / "latest.json"
    assert projection["status"] == "ready"
    assert projection["route_control_decision"] == "bounded_repair"
    assert projection["next_action"] == "enter_bounded_analysis"
    assert projection["route_control_memo"]["decision"] == "bounded_repair"
    assert projection["controller_decision"]["route_control_decision"] == "bounded_repair"
    assert projection["controller_decision"]["write_authorized"] is True
    assert decision_path.is_file()


def test_orchestrator_materializes_stop_loss_before_continuing_weak_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("weak-line", 4)],
        requested_action="select_line",
        route_signals={
            "evidence_state": "weak",
            "stop_pressure": "high",
            "attempted_paths": ["baseline", "bounded_analysis"],
            "failure_reasons": ["no_external_transportability"],
            "continuation_cost": {"review_cycles": 2},
            "evidence_gain_ceiling": "low",
            "alternative_routes": ["stronger-guideline-gap"],
        },
    )

    stop_loss_path = tmp_path / "study" / "artifacts" / "medical_paper" / "stop_loss_memo.json"
    decision_path = tmp_path / "study" / "artifacts" / "controller_decisions" / "latest.json"
    assert projection["status"] == "ready"
    assert projection["route_control_decision"] == "switch_line"
    assert projection["route_decision"] == "switch_line"
    assert projection["selected_line_id"] is None
    assert projection["study_line_decision"]["selected_line_id"] is None
    assert projection["study_line_decision"]["current_route"] is None
    assert projection["next_action"] == "switch_line"
    assert projection["route_control_memo"]["decision"] == "switch_line"
    assert projection["route_control_memo"]["materialized_paths"] == {"stop_loss_memo": str(stop_loss_path)}
    assert stop_loss_path.is_file()
    assert decision_path.is_file()
    written = json.loads(decision_path.read_text(encoding="utf-8"))
    assert written["route_control_decision"] == "switch_line"
    assert written["study_line_decision"]["selected_line_id"] is None
    assert written["study_line_decision"]["current_route"] is None
    assert written["write_authorized"] is True
    assert written["quality_claim_authorized"] is False


def test_orchestrator_blocks_continue_when_weak_route_has_no_alternative(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("weak-line", 4)],
        requested_action="select_line",
        route_signals={
            "evidence_state": "blocked",
            "stop_pressure": "high",
            "attempted_paths": ["baseline", "bounded_analysis"],
            "failure_reasons": ["endpoint_unresolvable"],
            "evidence_gain_ceiling": "low",
        },
    )

    assert projection["status"] == "ready"
    assert projection["route_control_decision"] == "stop_loss"
    assert projection["route_decision"] == "return_to_scout"
    assert projection["next_action"] == "stop_loss"
    assert projection["controller_decision"]["write_authorized"] is True
