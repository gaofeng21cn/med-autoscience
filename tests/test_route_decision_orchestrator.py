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


def _complete_exploration_depth_review() -> dict[str, dict[str, object]]:
    return {
        "subgroup": {"sufficient": True, "finding": "No subgroup route rescued the blocked endpoint."},
        "alternative_endpoint": {"sufficient": True, "finding": "Alternative endpoints did not preserve the claim."},
        "data_quality": {"sufficient": True, "finding": "Data limits were audited against the negative route."},
        "statistical_power": {"sufficient": True, "finding": "Power ceiling made bounded repair non-transportable."},
        "mechanism_plausibility": {"sufficient": True, "finding": "No mechanism-supported route remained."},
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
            "exploration_depth_review": _complete_exploration_depth_review(),
        },
    )

    assert projection["status"] == "ready"
    assert projection["route_control_decision"] == "stop_loss"
    assert projection["route_decision"] == "return_to_scout"
    assert projection["next_action"] == "stop_loss"
    assert projection["controller_decision"]["write_authorized"] is True


def test_orchestrator_explicit_continue_is_not_allowed_under_high_stop_pressure(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("weak-line", 4)],
        requested_action="select_line",
        route_signals={
            "requested_route_control_decision": "continue",
            "evidence_state": "weak",
            "stop_pressure": "high",
            "attempted_paths": ["baseline", "bounded_analysis"],
            "failure_reasons": ["validation_not_transportable"],
            "continuation_cost": {"runtime_hours": 8, "review_cycles": 2},
            "evidence_gain_ceiling": "low",
            "alternative_routes": ["stronger-line"],
        },
    )

    stop_loss_path = tmp_path / "study" / "artifacts" / "medical_paper" / "stop_loss_memo.json"
    decision_path = tmp_path / "study" / "artifacts" / "controller_decisions" / "latest.json"
    assert projection["status"] == "blocked"
    assert projection["route_control_decision"] == "stop_loss"
    assert projection["route_decision"] == "return_to_scout"
    assert projection["next_action"] == "stop_loss"
    assert "continue_blocked_by_weak_evidence" in projection["blockers"]
    assert "continue_blocked_by_high_stop_pressure" in projection["blockers"]
    assert projection["route_control_memo"]["requested_decision"] == "continue"
    assert projection["route_control_memo"]["decision"] == "stop_loss"
    assert projection["route_control_memo"]["materialized_paths"] == {"stop_loss_memo": str(stop_loss_path)}
    assert projection["route_control_memo"]["durable_refs"]["controller_decision_suggestion"] == (
        "artifacts/controller_decisions/latest.json"
    )
    assert projection["controller_decision"]["write_authorized"] is False
    assert projection["controller_decision"]["route_control_decision"] == "stop_loss"
    assert stop_loss_path.is_file()
    assert not decision_path.exists()


def test_negative_result_materializes_analysis_direction_decision_and_claim_policy(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("negative-line", 4)],
        requested_action="select_line",
        route_signals={
            "claim_id": "claim.primary_mortality_signal",
            "current_claim_status": "supported",
            "expected_result": "higher risk in exposed group",
            "observed_result": "no measurable association",
            "result_alignment": "negative",
            "evidence_refs": ["artifacts/evidence/primary_model.json"],
            "failed_path_refs": ["artifacts/analysis/primary_model.json"],
            "failure_reasons": ["effect_direction_not_reproduced"],
            "alternative_routes": ["guideline-gap-line"],
        },
    )

    decision_path = tmp_path / "study" / "artifacts" / "controller_decisions" / "latest.json"
    assert projection["status"] == "ready"
    assert projection["route_control_decision"] == "switch_line"
    assert projection["route_decision"] == "switch_line"
    assert projection["next_action"] == "switch_line"

    analysis_decision = projection["analysis_direction_decision"]
    assert projection["route_execution_plan"] == analysis_decision
    assert analysis_decision["decision"] == "switch_line"
    assert analysis_decision["action_type"] == "switch_line"
    assert analysis_decision["claim_id"] == "claim.primary_mortality_signal"
    assert analysis_decision["result_alignment"] == "negative"
    assert analysis_decision["failed_path_evidence_refs"] == [
        "artifacts/analysis/primary_model.json",
        "artifacts/evidence/primary_model.json",
    ]
    assert analysis_decision["claim_policy"] == {
        "claim_id": "claim.primary_mortality_signal",
        "previous_status": "supported",
        "supported": False,
        "claim_downgrade_required": True,
        "allowed_status": "downgraded",
        "reason": "negative_result_cannot_support_original_claim",
    }
    assert set(analysis_decision["required_repairs"]) == {
        "evidence_ledger",
        "manuscript",
        "review_ledger",
        "analysis",
    }
    assert analysis_decision["controller_decision_ref"] == str(decision_path.resolve())
    assert decision_path.is_file()

    written = json.loads(decision_path.read_text(encoding="utf-8"))
    assert written["analysis_direction_decision"] == analysis_decision
    assert written["route_execution_plan"] == analysis_decision
    assert written["analysis_direction_decision"]["claim_policy"]["supported"] is False


def test_negative_result_outputs_analysis_slice_contract_and_executable_owner_tasks(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("negative-line", 4)],
        requested_action="select_line",
        route_signals={
            "claim_id": "claim.primary_mortality_signal",
            "current_claim_status": "supported",
            "hypothesis": "Exposure increases mortality risk.",
            "endpoint": "90-day mortality",
            "method": "adjusted Cox model",
            "expected_result": "higher risk in exposed group",
            "observed_result": "no measurable association",
            "result_alignment": "negative",
            "interpretation": "The primary analysis failed to support the original claim.",
            "evidence_refs": ["artifacts/evidence/primary_model.json"],
            "failed_path_refs": ["artifacts/analysis/primary_model.json"],
            "failure_reasons": ["effect_direction_not_reproduced"],
            "alternative_routes": ["guideline-gap-line"],
        },
    )

    decision_path = tmp_path / "study" / "artifacts" / "controller_decisions" / "latest.json"
    analysis_decision = projection["analysis_direction_decision"]
    slice_contract = analysis_decision["analysis_slice_contract"]

    assert set(slice_contract) == {
        "hypothesis",
        "endpoint",
        "method",
        "expected_result",
        "failure_criteria",
        "actual_result",
        "interpretation",
        "route_impact",
    }
    assert slice_contract["hypothesis"] == "Exposure increases mortality risk."
    assert slice_contract["endpoint"] == "90-day mortality"
    assert slice_contract["method"] == "adjusted Cox model"
    assert slice_contract["expected_result"] == "higher risk in exposed group"
    assert slice_contract["failure_criteria"] == ["effect_direction_not_reproduced"]
    assert slice_contract["actual_result"] == "no measurable association"
    assert slice_contract["interpretation"] == "The primary analysis failed to support the original claim."
    assert slice_contract["route_impact"] == "switch_line"

    assert analysis_decision["claim_policy"]["supported"] is False
    assert analysis_decision["failed_path_evidence_refs"] == [
        "artifacts/analysis/primary_model.json",
        "artifacts/evidence/primary_model.json",
    ]

    tasks = analysis_decision["executable_owner_tasks"]
    assert [task["action"] for task in tasks] == ["claim_downgrade", "switch_line"]
    for task in tasks:
        assert task["owner"] == "MAS Route Decision Controller"
        assert task["callable_surface"]
        assert task["required_inputs"]
        assert task["required_outputs"]
        assert task["artifact_delta_predicate"]
        assert task["gate_replay_target"] == str(decision_path.resolve())
        assert task["idempotency_key"].startswith(
            "analysis_direction_decision:claim.primary_mortality_signal:negative:"
        )
        assert task["source_fingerprint"] == (
            "claim.primary_mortality_signal|negative|"
            "artifacts/analysis/primary_model.json|artifacts/evidence/primary_model.json"
        )

    written = json.loads(decision_path.read_text(encoding="utf-8"))
    assert written["analysis_direction_decision"]["analysis_slice_contract"] == slice_contract
    assert written["analysis_direction_decision"]["executable_owner_tasks"] == tasks
    assert written["quality_claim_authorized"] is False
    assert written["mechanical_projection_can_authorize_quality"] is False


def test_weak_blocked_result_uses_bounded_repair_without_supported_claim(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("repair-line", 5)],
        requested_action="select_line",
        route_signals={
            "claim_id": "claim.secondary_signal",
            "claim_status": "supported",
            "expected_result": "stable subgroup effect",
            "observed_result": "imprecise subgroup estimate",
            "result_alignment": "weak",
            "evidence_refs": ["artifacts/evidence/subgroup.json"],
            "failed_path_refs": ["artifacts/analysis/subgroup.json"],
            "statistical_blockers": ["wide_confidence_interval"],
            "failure_reasons": ["precision_ceiling_not_met"],
        },
    )

    analysis_decision = projection["analysis_direction_decision"]
    assert projection["status"] == "ready"
    assert projection["route_control_decision"] == "bounded_repair"
    assert projection["route_decision"] == "proceed_to_baseline"
    assert projection["next_action"] == "enter_bounded_analysis"
    assert analysis_decision["decision"] == "bounded_repair"
    assert analysis_decision["action_type"] == "bounded_repair"
    assert analysis_decision["claim_policy"]["supported"] is False
    assert analysis_decision["claim_policy"]["claim_downgrade_required"] is True
    assert analysis_decision["claim_policy"]["allowed_status"] == "pending_bounded_repair"
    assert "manuscript" in analysis_decision["required_repairs"]
    assert "analysis" in analysis_decision["required_repairs"]
    assert projection["controller_decision"]["analysis_direction_decision"] == analysis_decision


def test_contradictory_result_alignment_overrides_strong_evidence_state_continue_request(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("contradictory-line", 5)],
        requested_action="select_line",
        route_signals={
            "requested_route_control_decision": "continue",
            "claim_id": "claim.primary_signal",
            "claim_status": "supported",
            "expected_result": "positive external validation",
            "observed_result": "opposite-direction external validation",
            "result_alignment": "contradictory",
            "evidence_state": "strong",
            "evidence_refs": ["artifacts/evidence/external_validation.json"],
            "failed_path_refs": ["artifacts/analysis/external_validation.json"],
            "failure_reasons": ["external_validation_contradicted_primary_claim"],
            "exploration_depth_review": _complete_exploration_depth_review(),
        },
    )

    assert projection["route_control_decision"] == "stop_loss"
    assert projection["route_decision"] == "return_to_scout"
    assert projection["next_action"] == "stop_loss"
    assert projection["analysis_direction_decision"]["decision"] == "stop_loss"
    assert projection["analysis_direction_decision"]["claim_policy"]["supported"] is False
    assert projection["next_action"] not in {"enter_baseline", "continue"}


def test_weak_result_alignment_overrides_strong_evidence_state_in_stoploss_memo(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_orchestration(
        study_root=tmp_path / "study",
        candidates=[_candidate("weak-line", 5)],
        requested_action="select_line",
        route_signals={
            "claim_id": "claim.weak_signal",
            "claim_status": "supported",
            "expected_result": "large stable effect",
            "observed_result": "small unstable effect",
            "result_alignment": "weak",
            "evidence_state": "strong",
            "evidence_refs": ["artifacts/evidence/weak_signal.json"],
            "failed_path_refs": ["artifacts/analysis/weak_signal.json"],
            "statistical_blockers": ["low_events_per_variable"],
            "failure_reasons": ["effect_size_not_stable"],
        },
    )

    assert projection["route_control_decision"] == "bounded_repair"
    assert projection["route_control_memo"]["route_control_inputs"]["evidence_state"] == "weak"
    assert projection["analysis_direction_decision"]["decision"] == "bounded_repair"
    assert projection["analysis_direction_decision"]["claim_policy"]["supported"] is False


def test_route_decision_rehearsal_materializes_required_decision_memo(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.materialize_route_decision_rehearsal(
        study_root=tmp_path / "study",
        current_route="dpcc-003.primary-care-risk",
        alternative_routes=["dpcc-004.guideline-gap"],
    )

    memo_path = tmp_path / "study" / "artifacts" / "medical_paper" / "route_decision_rehearsal_memo.json"
    decision_path = tmp_path / "study" / "artifacts" / "controller_decisions" / "latest.json"

    assert projection["surface"] == "route_decision_rehearsal"
    assert projection["status"] == "ready"
    assert projection["rehearsal_classes"] == [
        "weak-result",
        "blocked-statistics",
        "missing-external-validation",
    ]
    assert projection["allowed_decisions"] == [
        "continue",
        "route_back",
        "bounded_repair",
        "stop_loss",
        "switch_line",
        "human_gate",
    ]
    assert projection["decision_coverage"] == {
        "continue": True,
        "route_back": True,
        "bounded_repair": True,
        "stop_loss": True,
        "switch_line": True,
        "human_gate": True,
    }
    assert projection["quality_claim_authorized"] is False
    assert projection["controller_decision_role"] == "route_recommendation_only"
    assert projection["materialized_paths"] == {"decision_memo": str(memo_path)}
    assert memo_path.is_file()
    assert not decision_path.exists()

    written = json.loads(memo_path.read_text(encoding="utf-8"))
    assert written == projection["decision_memo"]
    assert written["surface"] == "route_decision_rehearsal_memo"
    assert written["controller_decision_role"] == "route_recommendation_only"
    assert written["quality_claim_authorized"] is False
    assert written["authority"]["can_authorize_publication_quality"] is False
    assert written["durable_refs"]["controller_decision_suggestion"] == (
        "artifacts/controller_decisions/latest.json"
    )
    assert written["durable_refs"]["publication_quality_authority"] == (
        "artifacts/publication_eval/latest.json"
    )


def test_route_decision_rehearsal_maps_required_cases_without_quality_authority(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.build_route_decision_rehearsal(
        study_root=tmp_path / "study",
        current_route="dpcc-003.primary-care-risk",
        alternative_routes=["dpcc-004.guideline-gap"],
    )

    decisions_by_case = {case["case_id"]: case["decision"] for case in projection["cases"]}
    assert decisions_by_case == {
        "blocked-statistics-clear-control": "continue",
        "blocked-statistics-repair": "bounded_repair",
        "missing-external-validation-scout": "route_back",
        "missing-external-validation-human-gate": "human_gate",
        "weak-result-switch-line": "switch_line",
        "weak-result-stop-loss": "stop_loss",
    }

    for case in projection["cases"]:
        assert case["controller_decision"]["role"] == "route_recommendation_only"
        assert case["controller_decision"]["write_authorized"] is False
        assert case["controller_decision"]["quality_claim_authorized"] is False
        assert case["route_control_memo"]["quality_claim_authorized"] is False
        assert case["route_control_memo"]["authority"]["can_authorize_publication_quality"] is False


def test_weak_result_rehearsal_never_continues_or_piles_bounded_analysis(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")

    projection = module.build_route_decision_rehearsal(
        study_root=tmp_path / "study",
        current_route="dpcc-003.primary-care-risk",
        alternative_routes=["dpcc-004.guideline-gap"],
    )

    weak_cases = [case for case in projection["cases"] if case["rehearsal_class"] == "weak-result"]
    assert {case["case_id"] for case in weak_cases} == {
        "weak-result-switch-line",
        "weak-result-stop-loss",
    }
    for case in weak_cases:
        assert case["decision"] in {"switch_line", "stop_loss"}
        assert case["decision"] not in {"continue", "bounded_repair"}
        assert case["next_action"] in {"switch_line", "stop_loss"}
        assert case["analysis_continuation_allowed"] is False
        assert case["weak_route_analysis_guard"] == {
            "continue_blocked": True,
            "bounded_repair_blocked": True,
            "reason": "weak_result_cannot_continue_or_expand_analysis",
        }
