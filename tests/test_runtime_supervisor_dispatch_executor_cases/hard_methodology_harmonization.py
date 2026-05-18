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
