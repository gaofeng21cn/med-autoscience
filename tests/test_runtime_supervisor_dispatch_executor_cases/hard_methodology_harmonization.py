from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_hands_terminal_hard_methodology_route_to_analysis_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    route = _owner_route(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
    )
    route.update(
        {
            "failure_signature": "unit_harmonized_rerun_required",
            "owner_reason": "unit_harmonized_rerun_required",
            "work_unit_fingerprint": "hard-methodology::unit_harmonized_external_validation_rerun::hdl",
            "source_fingerprint": "truth-snapshot::hdl-unit-blocker",
            "idempotency_key": "owner-route::dm002::analysis-harmonization::hdl",
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::hdl-unit-blocker",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
        required_output_surface=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        owner_route=route,
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["request_packet_ref"] = "artifacts/supervision/requests/analysis_harmonization/latest.json"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("unit_harmonized_external_validation_rerun",),
        mode="developer_apply_safe",
        apply=True,
    )

    request_path = study_root / "artifacts" / "supervision" / "requests" / "analysis_harmonization" / "latest.json"
    owner_result_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["dispatch_contract_valid"] is True
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["owner_callable_surface"] == (
        "analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker"
    )
    assert execution["owner_result"]["request_path"] == str(request_path)
    assert execution["owner_result"]["result_ref"] == str(owner_result_path)
    assert execution["owner_result"]["surface"] == "analysis_harmonization_owner_result"
    assert execution["owner_result"]["status"] == "blocked"
    assert execution["owner_result"]["blocked_reason"] == "unit_harmonized_rerun_required"
    assert execution["owner_result"]["typed_blocker_owner"] == "analysis_harmonization_owner"
    assert execution["owner_result"]["work_unit"] == "unit_harmonized_external_validation_rerun"
    assert execution["owner_result"]["paper_package_mutation_allowed"] is False
    assert execution["owner_result"]["quality_gate_relaxation_allowed"] is False
    assert execution["owner_result"]["medical_claim_authoring_allowed"] is False
    assert execution["owner_result"]["publication_eval_written"] is False
    assert execution["owner_result"]["controller_decision_written"] is False
    assert request_path.is_file()
    assert owner_result_path.is_file()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    owner_result = json.loads(owner_result_path.read_text(encoding="utf-8"))
    assert request["request_kind"] == "unit_harmonized_external_validation_rerun"
    assert request["request_owner"] == "analysis_harmonization_owner"
    assert request["blocked_reason"] == "unit_harmonized_rerun_required"
    assert request["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert request["paper_package_mutation_allowed"] is False
    assert request["quality_gate_relaxation_allowed"] is False
    assert request["medical_claim_authoring_allowed"] is False
    assert owner_result["request_ref"]["path"] == str(request_path)
    assert owner_result["typed_blocker"]["blocker_id"] == "unit_harmonized_rerun_required"
    assert owner_result["unit_harmonized_rerun_completed"] is False
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()


def test_explicit_harmonization_dispatch_survives_empty_consumer_latest_with_owner_request(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    route = _owner_route(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
    )
    route.update(
        {
            "failure_signature": "unit_harmonized_rerun_required",
            "owner_reason": "unit_harmonized_rerun_required",
            "work_unit_fingerprint": "hard-methodology::unit_harmonized_external_validation_rerun::hdl",
            "source_fingerprint": "truth-snapshot::hdl-unit-blocker",
            "idempotency_key": "owner-route::dm002::analysis-harmonization::hdl",
        }
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
        required_output_surface=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "unit_harmonized_external_validation_rerun.json"
    )
    dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "analysis_harmonization" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "request_kind": "unit_harmonized_external_validation_rerun",
            "request_owner": "analysis_harmonization_owner",
            "status": "requested",
            "blocked_reason": "unit_harmonized_rerun_required",
            "next_owner": "analysis_harmonization_owner",
            "next_work_unit": "unit_harmonized_external_validation_rerun",
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
        },
    )
    stale_route = _owner_route(
        study_id=study_id,
        action_type="methodology_reframe_route_decision",
        owner="decision",
    )
    stale_route.update(
        {
            "failure_signature": "methodology_reframe_required",
            "owner_reason": "methodology_reframe_required",
            "allowed_actions": [],
            "current_owner": "managed_runtime",
        }
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": stale_route}],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "schema_version": 1,
            "default_executor_dispatch_count": 0,
            "default_executor_dispatches": [],
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("unit_harmonized_external_validation_rerun",),
        mode="developer_apply_safe",
        apply=True,
    )

    request_path = study_root / "artifacts" / "supervision" / "requests" / "analysis_harmonization" / "latest.json"
    owner_result_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    execution = result["executions"][0]
    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "owner_request"
    assert execution["dispatch_path"] == str(dispatch_path.resolve())
    assert execution["owner_callable_surface"] == (
        "analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker"
    )
    assert execution["owner_result"]["request_path"] == str(request_path)
    assert execution["owner_result"]["result_ref"] == str(owner_result_path)
    assert request_path.is_file()
    assert owner_result_path.is_file()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()


def test_execute_dispatch_hands_model_provenance_route_to_source_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    route = _owner_route(
        study_id=study_id,
        action_type="recover_transport_model_provenance",
        owner="source_provenance_owner",
    )
    route.update(
        {
            "failure_signature": "transport_model_provenance_recovery_required",
            "owner_reason": "transport_model_provenance_recovery_required",
            "work_unit_fingerprint": "source-provenance::recover_transport_model_provenance::hdl",
            "source_fingerprint": "truth-snapshot::cox-provenance-blocker",
            "idempotency_key": "owner-route::dm002::source-provenance::cox-model",
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::cox-provenance-blocker",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="recover_transport_model_provenance",
        owner="source_provenance_owner",
        required_output_surface=(
            "canonical transport model provenance bundle or "
            "typed blocker:transport_model_provenance_recovery_required"
        ),
        owner_route=route,
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["request_packet_ref"] = "artifacts/supervision/requests/source_provenance/latest.json"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    request_path = study_root / "artifacts" / "supervision" / "requests" / "source_provenance" / "latest.json"
    owner_result_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["dispatch_contract_valid"] is True
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["owner_callable_surface"] == (
        "source_provenance_owner.recover_transport_model_provenance_or_typed_blocker"
    )
    assert execution["owner_result"]["request_path"] == str(request_path)
    assert execution["owner_result"]["result_ref"] == str(owner_result_path)
    assert execution["owner_result"]["surface"] == "source_provenance_owner_result"
    assert execution["owner_result"]["status"] == "blocked"
    assert execution["owner_result"]["blocked_reason"] == "transport_model_provenance_recovery_required"
    assert execution["owner_result"]["typed_blocker_owner"] == "source_provenance_owner"
    assert execution["owner_result"]["work_unit"] == "recover_transport_model_provenance"
    assert execution["owner_result"]["paper_package_mutation_allowed"] is False
    assert execution["owner_result"]["quality_gate_relaxation_allowed"] is False
    assert execution["owner_result"]["medical_claim_authoring_allowed"] is False
    assert execution["owner_result"]["publication_eval_written"] is False
    assert execution["owner_result"]["controller_decision_written"] is False
    assert request_path.is_file()
    assert owner_result_path.is_file()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    owner_result = json.loads(owner_result_path.read_text(encoding="utf-8"))
    assert request["request_kind"] == "recover_transport_model_provenance"
    assert request["request_owner"] == "source_provenance_owner"
    assert request["blocked_reason"] == "transport_model_provenance_recovery_required"
    assert request["next_work_unit"] == "recover_transport_model_provenance"
    assert request["input_contract"]["substitute_refit_forbidden"] is True
    assert request["paper_package_mutation_allowed"] is False
    assert request["quality_gate_relaxation_allowed"] is False
    assert request["medical_claim_authoring_allowed"] is False
    assert owner_result["request_ref"]["path"] == str(request_path)
    assert owner_result["typed_blocker"]["blocker_id"] == "transport_model_provenance_recovery_required"
    assert owner_result["transport_model_provenance_recovered"] is False
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_routes_terminal_source_provenance_blocker_to_decision_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    route = _owner_route(
        study_id=study_id,
        action_type="methodology_reframe_route_decision",
        owner="decision",
    )
    route.update(
        {
            "failure_signature": "methodology_reframe_required",
            "owner_reason": "methodology_reframe_required",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "source_fingerprint": "truth-snapshot::terminal-source-provenance-blocker",
            "idempotency_key": "owner-route::dm002::decision::methodology-reframe",
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::terminal-source-provenance-blocker",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="methodology_reframe_route_decision",
        owner="decision",
        required_output_surface=(
            "controller route decision for a provenance-limited reframe, "
            "reproducible-model restart, stop-loss, or human gate"
        ),
        owner_route=route,
    )
    dispatch["source_action"] = {
        "action_type": "methodology_reframe_route_decision",
        "source_ref": "artifacts/controller/source_provenance/latest.json",
        "terminal_source_provenance_blocker": True,
        "blocked_reason": "methodology_reframe_required",
    }
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["request_packet_ref"] = "artifacts/supervision/requests/decision/latest.json"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "methodology_reframe_route_decision.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("methodology_reframe_route_decision",),
        mode="developer_apply_safe",
        apply=True,
    )

    request_path = study_root / "artifacts" / "supervision" / "requests" / "decision" / "latest.json"
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["dispatch_contract_valid"] is True
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["owner_callable_surface"] == "decision_owner.methodology_reframe_route_decision"
    assert execution["owner_result"]["request_path"] == str(request_path)
    assert execution["owner_result"]["controller_decision_ref"] == str(decision_path)
    assert execution["owner_result"]["surface"] == "methodology_reframe_decision_owner_result"
    assert execution["owner_result"]["status"] == "routed"
    assert execution["owner_result"]["blocked_reason"] == "methodology_reframe_required"
    assert execution["owner_result"]["next_owner"] == "decision"
    assert execution["owner_result"]["work_unit"] == "methodology_reframe_route_decision"
    assert execution["owner_result"]["paper_package_mutation_allowed"] is False
    assert execution["owner_result"]["quality_gate_relaxation_allowed"] is False
    assert execution["owner_result"]["medical_claim_authoring_allowed"] is False
    assert execution["owner_result"]["publication_eval_written"] is False
    assert execution["owner_result"]["controller_decision_written"] is True
    assert request_path.is_file()
    assert decision_path.is_file()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert request["request_kind"] == "methodology_reframe_route_decision"
    assert request["request_owner"] == "decision"
    assert request["blocked_reason"] == "methodology_reframe_required"
    assert request["next_work_unit"] == "methodology_reframe_route_decision"
    assert request["paper_package_mutation_allowed"] is False
    assert request["quality_gate_relaxation_allowed"] is False
    assert request["medical_claim_authoring_allowed"] is False
    assert request["decision_options"] == [
        "stop_loss_current_transport_claim",
        "provenance_limited_harmonization_audit",
        "rebuild_reproducible_model_route",
        "human_gate",
    ]
    assert decision["decision_type"] == "route_back_same_line"
    assert decision["route_target"] == "analysis-campaign"
    assert decision["requires_human_confirmation"] is False
    assert decision["work_unit_fingerprint"] == "decision::methodology_reframe_route_decision"
    assert decision["next_work_unit"]["unit_id"] == "medical_prose_quality_analysis_source_documentation_repair"
    assert decision["next_work_unit"]["lane"] == "analysis-campaign"
    assert decision["next_work_unit"]["required_owner"] == "analysis_harmonization_owner"
    assert decision["next_work_unit"]["required_next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert execution["owner_result"]["selected_next_work_unit"]["unit_id"] == (
        "medical_prose_quality_analysis_source_documentation_repair"
    )
    assert decision["controller_actions"][0]["action_type"] == "ensure_study_runtime"
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_records_candidate_search_without_accepting_result_summary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    summary_path = (
        study_root
        / "experiments"
        / "analysis"
        / "clinical_transportability_attribution_analysis"
        / "RESULT.json"
    )
    _write_json(
        summary_path,
        {
            "schema_version": 1,
            "analysis_id": "clinical_transportability_attribution_analysis",
            "metric_rows": [{"metric": "c_index", "value": 0.5647}],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="recover_transport_model_provenance",
            owner="source_provenance_owner",
            required_output_surface=(
                "canonical transport model provenance bundle or "
                "typed blocker:transport_model_provenance_recovery_required"
            ),
            owner_route=_owner_route(
                study_id=study_id,
                action_type="recover_transport_model_provenance",
                owner="source_provenance_owner",
            ),
        ),
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    assert owner_result["status"] == "blocked"
    assert owner_result["transport_model_provenance_recovered"] is False
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] is None
    assert owner_result["provenance_search"]["searched"] is True
    assert owner_result["provenance_search"]["candidate_count"] == 1
    assert owner_result["provenance_search"]["accepted_bundle_ref"] is None
    assert owner_result["provenance_search"]["candidates"][0]["path"] == str(summary_path)
    assert owner_result["provenance_search"]["candidates"][0]["accepted"] is False
    assert "canonical_transport_model_provenance_bundle_missing" in owner_result["typed_blocker"][
        "blocking_reasons"
    ]
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_records_binary_candidates_without_crashing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    binary_path = study_root / "analysis" / "models" / "transport_cox_model.pkl"
    binary_path.parent.mkdir(parents=True, exist_ok=True)
    binary_path.write_bytes(b"\x80\x04\x95binary-model-candidate")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="recover_transport_model_provenance",
            owner="source_provenance_owner",
            required_output_surface=(
                "canonical transport model provenance bundle or "
                "typed blocker:transport_model_provenance_recovery_required"
            ),
            owner_route=_owner_route(
                study_id=study_id,
                action_type="recover_transport_model_provenance",
                owner="source_provenance_owner",
            ),
        ),
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    assert owner_result["status"] == "blocked"
    assert owner_result["transport_model_provenance_recovered"] is False
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] is None
    assert owner_result["provenance_search"]["candidate_count"] == 1
    assert owner_result["provenance_search"]["candidates"][0]["path"] == str(binary_path)
    assert owner_result["provenance_search"]["candidates"][0]["candidate_kind"] == "non_json_or_non_object_candidate"
    assert owner_result["provenance_search"]["candidates"][0]["accepted"] is False
    assert owner_result["provenance_search"]["result_summary_acceptance_allowed"] is False
    assert owner_result["provenance_search"]["substitute_refit_allowed"] is False
    assert "canonical_transport_model_provenance_bundle_missing" in owner_result["typed_blocker"][
        "blocking_reasons"
    ]
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_accepts_complete_canonical_transport_model_bundle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    bundle_path = (
        study_root
        / "artifacts"
        / "model_provenance"
        / "transport_model_provenance_bundle.json"
    )
    _write_json(
        bundle_path,
        {
            "surface": "canonical_transport_model_provenance_bundle",
            "schema_version": 1,
            "model_type": "penalized_cox_ph",
            "coefficients": {
                "age": 0.04,
                "sex_male": 0.2,
                "smoking_current": 0.3,
                "hba1c": 0.08,
                "hdl_c": -0.15,
                "sbp": 0.01,
                "dbp": 0.01,
            },
            "feature_order": ["age", "sex_male", "smoking_current", "hba1c", "hdl_c", "sbp", "dbp"],
            "feature_coding": {
                "sex_male": {"source": "sex", "reference": "female"},
                "smoking_current": {"source": "smoking", "reference": "not_current"},
            },
            "baseline_survival_at_5_years": 0.98,
            "penalty": {"type": "ridge", "lambda": 0.01, "selection": "cross_validation"},
            "standardization": {
                "center": {"age": 50.0},
                "scale": {"age": 10.0},
                "unit_conversions": {"hdl_c": "mmol/L"},
            },
            "original_result_artifact": "paper/analysis_groups/clinical_transportability_attribution_analysis/RESULT.json",
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="recover_transport_model_provenance",
            owner="source_provenance_owner",
            required_output_surface=(
                "canonical transport model provenance bundle or "
                "typed blocker:transport_model_provenance_recovery_required"
            ),
            owner_route=_owner_route(
                study_id=study_id,
                action_type="recover_transport_model_provenance",
                owner="source_provenance_owner",
            ),
        ),
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    assert owner_result["status"] == "completed"
    assert owner_result["blocked_reason"] is None
    assert owner_result["typed_blocker"] is None
    assert owner_result["transport_model_provenance_recovered"] is True
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] == str(bundle_path)
    assert owner_result["next_owner"] == "analysis_harmonization_owner"
    assert owner_result["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert owner_result["provenance_search"]["accepted_bundle_ref"] == str(bundle_path)
    assert owner_result["provenance_assessment"]["status"] == "completed"
    assert owner_result["publication_eval_written"] is False
    assert owner_result["controller_decision_written"] is False
    assert not (study_root / "paper").exists()
