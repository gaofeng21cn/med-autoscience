from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_domain_owner_action_dispatch_cases.medical_paper_readiness_dispatch import (
    ACTION_TYPE,
    _attach_readiness_closeout_binding,
    _readiness_dispatch,
    _write_readiness_dispatch,
    _write_ready_literature_intelligence,
)
from tests.test_literature_provider_runtime import _complete_provider_payload


def _write_selected_route_decision(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json",
        {
            "surface": "route_decision_orchestrator",
            "schema_version": 1,
            "status": "blocked",
            "requested_action": "open_auto_research_soak_review",
            "route_decision": "human_gate",
            "selected_line_id": "dm002-current-line",
            "blockers": ["unsupported_requested_action"],
            "study_line_decision": {
                "surface": "study_line_decision_engine",
                "schema_version": 1,
                "status": "selected",
                "selected_line_id": "dm002-current-line",
                "route_decision": "proceed_to_baseline",
                "controller_decision_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                "stage_output_refs": ["artifacts/stage_knowledge/idea/closeouts/dm002-current-line.json"],
                "current_route": {
                    "line_id": "dm002-current-line",
                    "status": "eligible",
                    "route_decision": "proceed_to_baseline",
                    "dimensions": {
                        "novelty": 4,
                        "clinical_relevance": 5,
                        "data_fit": 5,
                        "external_validation": 3,
                        "analysis_feasibility": 3,
                        "journal_fit": 4,
                        "risk_cost": 2,
                        "stop_threshold": "publication gate remains blocked",
                    },
                    "evidence_refs": ["artifacts/medical_paper/literature_provider_runtime.json"],
                    "stage_output_refs": ["artifacts/stage_knowledge/idea/closeouts/dm002-current-line.json"],
                },
                "ranking": [
                    {
                        "line_id": "dm002-current-line",
                        "status": "eligible",
                        "dimensions": {
                            "novelty": 4,
                            "clinical_relevance": 5,
                            "data_fit": 5,
                            "external_validation": 3,
                            "analysis_feasibility": 3,
                            "journal_fit": 4,
                            "risk_cost": 2,
                            "stop_threshold": "publication gate remains blocked",
                        },
                        "dimension_scores": {
                            "novelty": 4.0,
                            "clinical_relevance": 5.0,
                            "data_fit": 5.0,
                            "external_validation": 3.0,
                            "analysis_feasibility": 3.0,
                            "journal_fit": 4.0,
                            "risk_cost": 2.0,
                        },
                        "total_score": 22.0,
                        "evidence_refs": ["artifacts/medical_paper/literature_provider_runtime.json"],
                        "stage_output_refs": ["artifacts/stage_knowledge/idea/closeouts/dm002-current-line.json"],
                        "blockers": [],
                    }
                ],
                "blockers": [],
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
            },
        },
    )


def _prepare_study_through_study_line(tmp_path: Path) -> tuple[object, str, Path]:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    literature_module = importlib.import_module("med_autoscience.controllers.literature_provider_runtime")
    study_line_module = importlib.import_module("med_autoscience.controllers.study_line_decision_engine")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        quest_id=f"quest-{study_id}",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    _write_ready_literature_intelligence(study_root)
    literature_module.materialize_literature_provider_runtime(
        study_root=study_root,
        payload=_complete_provider_payload(),
    )
    _write_selected_route_decision(study_root)
    route_decision = json.loads(
        (study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json").read_text(
            encoding="utf-8"
        )
    )
    _write_json(
        study_line_module.stable_study_line_decision_path(study_root=study_root),
        route_decision["study_line_decision"],
    )
    readiness_module.build_medical_paper_readiness_surface(study_root=study_root)
    return profile, study_id, study_root


def test_execute_dispatch_authors_study_line_selection_from_route_decision_artifact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    literature_module = importlib.import_module("med_autoscience.controllers.literature_provider_runtime")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_ready_literature_intelligence(study_root)
    literature_module.materialize_literature_provider_runtime(
        study_root=study_root,
        payload=_complete_provider_payload(),
    )
    readiness_module.build_medical_paper_readiness_surface(study_root=study_root)
    _write_selected_route_decision(study_root)
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch.pop("surface_key", None)
    dispatch["prompt_contract"].pop("surface_key", None)
    binding = _attach_readiness_closeout_binding(dispatch, study_id=study_id)
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "study_line_selection"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_study_line_selection"
    assert action_result["status"] == "present"
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "quality_gate_receipt_with_stable_typed_blocker"
    assert owner_delta["required_return_shape_satisfied"] is True
    assert owner_delta["quality_gate_receipt"]["completed_surface_key"] == "study_line_selection"
    assert owner_delta["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    assert owner_delta["closeout_binding"]["stage_manifest_ref"] == binding["stage_manifest_ref"]
    assert owner_delta["closeout_binding"]["current_pointer_ref"] == binding["current_pointer_ref"]
    assert owner_delta["closeout_binding"]["source_fingerprint"] == binding["source_fingerprint"]
    assert owner_delta["idempotency_key"] == f"owner-route::{study_id}::{ACTION_TYPE}::MedAutoScience"
    line_decision = json.loads(
        (study_root / "artifacts" / "medical_paper" / "study_line_decision.json").read_text(encoding="utf-8")
    )
    assert line_decision["surface"] == "study_line_decision_engine"
    assert line_decision["status"] == "selected"
    assert line_decision["selected_line_id"] == "dm002-current-line"
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["study_line_selection"]["status"] == "present"
    assert readiness["next_action"]["surface_key"] == "archetype_analysis_contract"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_uses_current_readiness_surface_over_stale_dispatch_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    literature_module = importlib.import_module("med_autoscience.controllers.literature_provider_runtime")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_ready_literature_intelligence(study_root)
    literature_module.materialize_literature_provider_runtime(
        study_root=study_root,
        payload=_complete_provider_payload(),
    )
    readiness_module.build_medical_paper_readiness_surface(study_root=study_root)
    _write_selected_route_decision(study_root)
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    _write_json(
        study_root / request_ref,
        {
            "surface": "supervisor_request_handoff_packet",
            "action_type": ACTION_TYPE,
            "surface_key": "literature_provider_runtime",
            "operator_payload": _complete_provider_payload(),
            "payload_authoring_target": {
                "surface": "medical_paper_readiness_operator_payload_authoring_target",
                "surface_key": "literature_provider_runtime",
                "operator_payload": _complete_provider_payload(),
            },
        },
    )
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch["operator_payload_ref"] = request_ref
    dispatch["medical_paper_readiness_payload_ref"] = request_ref
    dispatch["prompt_contract"]["operator_payload_ref"] = request_ref
    dispatch["prompt_contract"]["medical_paper_readiness_payload_ref"] = request_ref
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "study_line_selection"
    assert execution["owner_result"]["guarded_operator_action_result"]["action_id"] == "materialize_study_line_selection"
    assert execution["owner_result"]["guarded_operator_action_result"]["idempotency_key"].endswith(
        "::surface::study_line_selection::action::materialize_study_line_selection"
    )
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["study_line_selection"]["status"] == "present"
    assert readiness["next_action"]["surface_key"] == "archetype_analysis_contract"


def test_execute_dispatch_authors_archetype_analysis_contract_from_study_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id, study_root = _prepare_study_through_study_line(tmp_path)
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch.pop("surface_key", None)
    dispatch["prompt_contract"].pop("surface_key", None)
    binding = _attach_readiness_closeout_binding(dispatch, study_id=study_id)
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "archetype_analysis_contract"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_archetype_analysis_contract"
    assert action_result["status"] == "present"
    owner_delta = execution["owner_delta_result"]
    assert owner_delta["result_kind"] == "quality_gate_receipt_with_stable_typed_blocker"
    assert owner_delta["required_return_shape_satisfied"] is True
    assert owner_delta["quality_gate_receipt"]["completed_surface_key"] == "archetype_analysis_contract"
    assert owner_delta["closeout_binding"]["stage_run_id"] == binding["stage_run_id"]
    assert owner_delta["closeout_binding"]["stage_manifest_ref"] == binding["stage_manifest_ref"]
    assert owner_delta["closeout_binding"]["current_pointer_ref"] == binding["current_pointer_ref"]
    assert owner_delta["closeout_binding"]["source_fingerprint"] == binding["source_fingerprint"]
    assert owner_delta["idempotency_key"] == f"owner-route::{study_id}::{ACTION_TYPE}::MedAutoScience"
    contract = json.loads((study_root / "paper" / "medical_analysis_contract.json").read_text(encoding="utf-8"))
    assert contract["status"] == "resolved"
    assert contract["study_archetype"] == "clinical_classifier"
    assert contract["endpoint_type"] == "time_to_event"
    assert contract["required_analysis_packages"] == [
        "discrimination_metrics",
        "calibration_assessment",
        "km_risk_stratification",
        "decision_curve_analysis",
        "censoring_aware_validation",
        "subgroup_heterogeneity",
        "sensitivity_support",
    ]
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["archetype_analysis_contract"]["status"] == "present"
    assert readiness["next_action"]["surface_key"] == "bounded_analysis_candidate_board"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (study_root / "manuscript" / "current_package.zip").exists()
    assert not (study_root / "paper" / "draft.md").exists()


def test_execute_dispatch_dry_run_does_not_materialize_archetype_analysis_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id, study_root = _prepare_study_through_study_line(tmp_path)
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch.pop("surface_key", None)
    dispatch["prompt_contract"].pop("surface_key", None)
    _write_readiness_dispatch(study_root, profile, dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=False,
    )

    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "archetype_analysis_contract"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_archetype_analysis_contract"
    assert action_result["status"] == "present"
    assert action_result["dry_run"] is True
    assert action_result["action_result_ref"]
    assert not (study_root / "paper" / "medical_analysis_contract.json").exists()
    assert not (study_root / action_result["action_result_ref"]).exists()
    assert not (study_root / action_result["replay_ref"]).exists()
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    assert readiness["ready_count"] == 3
    assert readiness["next_action"]["surface_key"] == "archetype_analysis_contract"


def test_execute_dispatch_authors_bounded_analysis_candidate_board_from_analysis_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id, study_root = _prepare_study_through_study_line(tmp_path)
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch.pop("surface_key", None)
    dispatch["prompt_contract"].pop("surface_key", None)
    _attach_readiness_closeout_binding(dispatch, study_id=study_id)
    _write_readiness_dispatch(study_root, profile, dispatch)
    first_result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )
    assert first_result["executions"][0]["owner_result"]["completed_surface_key"] == "archetype_analysis_contract"
    assert (study_root / "paper" / "medical_analysis_contract.json").exists()

    second_result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(ACTION_TYPE,),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = second_result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert execution["owner_result"]["completed_surface_key"] == "bounded_analysis_candidate_board"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_bounded_analysis_candidate_board"
    assert action_result["status"] == "present"
    board_path = study_root / "artifacts" / "medical_paper" / "bounded_analysis_candidate_board.json"
    board = json.loads(board_path.read_text(encoding="utf-8"))
    assert board["surface"] == "bounded_analysis_candidate_board"
    assert board["status"] == "present"
    assert board["quality_claim_authorized"] is False
    assert board["mechanical_projection_can_authorize_quality"] is False
    assert [candidate["analysis_package"] for candidate in board["candidates"]] == [
        "discrimination_metrics",
        "calibration_assessment",
        "km_risk_stratification",
        "decision_curve_analysis",
        "censoring_aware_validation",
        "subgroup_heterogeneity",
        "sensitivity_support",
    ]
    assert all(candidate["decision"] == "explore" for candidate in board["candidates"])
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["bounded_analysis_candidate_board"]["status"] == "present"
    assert readiness["ready_count"] == 5
    assert readiness["next_action"]["surface_key"] == "stop_loss_memo"
