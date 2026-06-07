from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_domain_owner_action_dispatch_cases.medical_paper_readiness_dispatch_cases.shared import (
    ACTION_TYPE,
    _attach_readiness_closeout_binding,
    _readiness_dispatch,
    _readiness_dispatch_for_surface,
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


def _bind_stale_readiness_owner_route_currentness(
    dispatch: dict[str, object],
    *,
    study_id: str,
    study_root: Path,
    stale_surface_key: str,
) -> None:
    currentness_basis = {
        "work_unit_id": ACTION_TYPE,
        "work_unit_fingerprint": (
            f"stage-current-owner-delta::{ACTION_TYPE}::{stale_surface_key}::"
            f"{study_root}/artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
        ),
        "truth_epoch": f"truth-event::{study_id}::{stale_surface_key}",
        "runtime_health_epoch": f"runtime-health-event::{study_id}::{stale_surface_key}",
    }
    currentness_contract = {
        "status": "currentness_basis_required",
        "basis": currentness_basis,
        "required_fields": [
            "work_unit_fingerprint",
            "truth_epoch",
            "runtime_health_epoch_or_source_eval_id",
        ],
        "missing_required_fields": [],
        "fail_closed_when_missing": True,
    }
    dispatch["owner_route_currentness_basis"] = currentness_basis
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["owner_route_currentness_basis"] = currentness_basis
    owner_route = dispatch["owner_route"]
    assert isinstance(owner_route, dict)
    owner_route["currentness_contract"] = currentness_contract
    prompt_owner_route = prompt_contract["owner_route"]
    assert isinstance(prompt_owner_route, dict)
    prompt_owner_route["currentness_contract"] = currentness_contract


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
    _bind_stale_readiness_owner_route_currentness(
        dispatch,
        study_id=study_id,
        study_root=study_root,
        stale_surface_key="literature_provider_runtime",
    )
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


def test_execute_dispatch_repairs_route_decision_requested_action_from_selected_line(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id, study_root = _prepare_study_through_study_line(tmp_path)
    contract = {
        "surface": "archetype_specific_analysis_contract",
        "schema_version": 1,
        "status": "resolved",
        "study_archetype": "clinical_classifier",
        "endpoint_type": "time_to_event",
        "required_analysis_packages": ["discrimination_metrics"],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    _write_json(study_root / "paper" / "medical_analysis_contract.json", contract)
    _write_json(
        study_root / "artifacts" / "medical_paper" / "bounded_analysis_candidate_board.json",
        {
            "surface": "bounded_analysis_candidate_board",
            "schema_version": 1,
            "status": "present",
            "candidates": [
                {
                    "analysis_package": "discrimination_metrics",
                    "target_claim": "Validate discrimination for the selected time-to-event mortality model.",
                    "expected_evidence_gain": "Quantify discrimination evidence before route execution.",
                    "cost_risk": "bounded",
                    "clinical_interpretability": "owner-review-required-before-quality-claim",
                    "decision": "explore",
                    "decision_reason": "Generated as a bounded candidate for the route decision handoff test.",
                    "evidence_refs": ["paper/medical_analysis_contract.json"],
                }
            ],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "stop_loss_memo.json",
        {
            "surface": "route_control_stop_loss_memo",
            "schema_version": 1,
            "status": "present",
            "decision": "continue",
            "decision_allowed": True,
            "attempted_paths": ["study_line_selection", "bounded_analysis_candidate_board"],
            "evidence_gain_ceiling": "moderate_with_current_selected_line",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "paper" / "target_journal_writing_layer.json",
        {
            "surface": "target_journal_writing_layer",
            "schema_version": 1,
            "status": "present",
            "target_journal_family": "general_internal_medicine",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "surface": "real_study_soak_matrix_evidence",
            "schema_version": 1,
            "overall_status": "complete",
            "checks": [{"check_id": "study_line", "status": "pass"}],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    readiness_module.build_medical_paper_readiness_surface(study_root=study_root)
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch.pop("surface_key", None)
    dispatch["prompt_contract"].pop("surface_key", None)
    _attach_readiness_closeout_binding(dispatch, study_id=study_id)
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
    assert execution["owner_result"]["completed_surface_key"] == "route_decision_orchestrator"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "materialize_route_decision"
    assert action_result["status"] == "ready"
    route = json.loads(
        (study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json").read_text(
            encoding="utf-8"
        )
    )
    assert route["requested_action"] == "select_line"
    assert route["route_decision"] == "proceed_to_baseline"
    assert route["blockers"] == []
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["route_decision_orchestrator"]["status"] == "present"
    assert readiness["next_action"]["surface_key"] == "statistical_discipline_operations"


def test_execute_dispatch_uses_current_readiness_over_stale_dispatch_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile, study_id, study_root = _prepare_study_through_study_line(tmp_path)
    _write_json(
        study_root / "paper" / "medical_analysis_contract.json",
        {
            "surface": "archetype_specific_analysis_contract",
            "schema_version": 1,
            "status": "resolved",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "required_analysis_packages": ["discrimination_metrics"],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "bounded_analysis_candidate_board.json",
        {
            "surface": "bounded_analysis_candidate_board",
            "schema_version": 1,
            "status": "present",
            "candidates": [
                {
                    "analysis_package": "discrimination_metrics",
                    "target_claim": "Validate discrimination for the selected mortality model.",
                    "expected_evidence_gain": "Quantify discrimination before promotion.",
                    "statistical_risk": "requires_precision_and_calibration_binding",
                    "clinical_interpretability": "owner-review-required-before-quality-claim",
                    "decision": "explore",
                    "decision_reason": "Bounded candidate selected for statistical discipline checks.",
                    "evidence_refs": ["paper/medical_analysis_contract.json"],
                }
            ],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json",
        {
            "surface": "route_decision_orchestrator",
            "schema_version": 1,
            "status": "ready",
            "requested_action": "select_line",
            "route_decision": "proceed_to_baseline",
            "route_control_decision": "continue",
            "selected_line_id": "dm002-current-line",
            "next_action": "proceed_to_baseline",
            "controller_decision_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            "controller_decision": {
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
            },
            "blockers": [],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "stop_loss_memo.json",
        {
            "surface": "route_control_stop_loss_memo",
            "schema_version": 1,
            "status": "present",
            "decision": "continue",
            "decision_allowed": True,
            "attempted_paths": ["study_line_selection", "bounded_analysis_candidate_board"],
            "evidence_gain_ceiling": "moderate_with_current_selected_line",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "paper" / "target_journal_writing_layer.json",
        {
            "surface": "target_journal_writing_layer",
            "schema_version": 1,
            "status": "present",
            "target_journal_family": "general_internal_medicine",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "surface": "real_study_soak_matrix_evidence",
            "schema_version": 1,
            "overall_status": "complete",
            "checks": [{"check_id": "study_line", "status": "pass"}],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    readiness_module.build_medical_paper_readiness_surface(study_root=study_root)
    dispatch = _readiness_dispatch_for_surface(
        study_id=study_id,
        surface_key="route_decision_orchestrator",
    )
    _attach_readiness_closeout_binding(dispatch, study_id=study_id)
    _bind_stale_readiness_owner_route_currentness(
        dispatch,
        study_id=study_id,
        study_root=study_root,
        stale_surface_key="route_decision_orchestrator",
    )
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
    assert execution["owner_result"]["completed_surface_key"] == "statistical_discipline_operations"
    action_result = execution["owner_result"]["guarded_operator_action_result"]
    assert action_result["action_id"] == "resolve_statistical_blockers"
    assert action_result["status"] == "ready"
    readiness = json.loads((study_root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8"))
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["statistical_discipline_operations"]["status"] == "present"
    assert readiness["ready_count"] == 10
    assert readiness["next_action"]["surface_key"] == "revision_rebuttal_loop"


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
