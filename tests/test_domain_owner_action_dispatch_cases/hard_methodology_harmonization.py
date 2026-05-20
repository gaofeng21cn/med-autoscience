from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
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
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
            "surface": "portable_domain_route_scan",
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

    result = module.dispatch_domain_owner_actions(
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
    assert execution["owner_result"]["next_owner"] == "source_provenance_owner"
    assert execution["owner_result"]["next_work_unit"] == "recover_transport_model_provenance"
    assert execution["next_owner"] == "source_provenance_owner"
    assert execution["next_work_unit"] == "recover_transport_model_provenance"
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
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
            "surface": "domain_action_request",
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
            "surface": "portable_domain_route_scan",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": stale_route}],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 0,
            "default_executor_dispatches": [],
        },
    )

    result = module.dispatch_domain_owner_actions(
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
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
            "surface": "portable_domain_route_scan",
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

    result = module.dispatch_domain_owner_actions(
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
    assert execution["owner_result"]["next_owner"] == "decision"
    assert execution["owner_result"]["next_work_unit"] == "methodology_reframe_route_decision"
    assert execution["owner_result"]["terminal_source_provenance_blocker"] is True
    assert execution["next_owner"] == "decision"
    assert execution["next_work_unit"] == "methodology_reframe_route_decision"
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
    assert owner_result["next_owner"] == "decision"
    assert owner_result["next_work_unit"] == "methodology_reframe_route_decision"
    assert owner_result["terminal_source_provenance_blocker"] is True
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_routes_terminal_source_provenance_blocker_to_decision_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
            "surface": "portable_domain_route_scan",
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

    result = module.dispatch_domain_owner_actions(
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
    assert decision["decision_type"] == "bounded_analysis"
    assert decision["route_target"] == "analysis-campaign"
    assert decision["requires_human_confirmation"] is False
    assert decision["work_unit_fingerprint"] == "decision::methodology_reframe_route_decision"
    assert decision["next_work_unit"]["unit_id"] == "provenance_limited_harmonization_audit"
    assert decision["next_work_unit"]["lane"] == "analysis-campaign"
    assert decision["next_work_unit"]["selected_route_option"] == "provenance_limited_harmonization_audit"
    assert decision["next_work_unit"]["terminal_source_provenance_blocker_consumed"] is True
    assert decision["next_work_unit"]["current_transport_claim_must_not_be_used_as_medical_conclusion"] is True
    assert execution["owner_result"]["route_decision"] == "bounded_analysis"
    assert execution["owner_result"]["selected_route_option"] == "provenance_limited_harmonization_audit"
    assert execution["owner_result"]["selected_next_work_unit"]["unit_id"] == "provenance_limited_harmonization_audit"
    assert decision["controller_actions"][0]["action_type"] == "ensure_study_runtime"
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_materializes_provenance_limited_harmonization_audit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {"blocker_id": "unit_harmonized_rerun_required"},
            "unit_harmonized_rerun_completed": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "source_provenance" / "latest.json",
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {"blocker_id": "transport_model_provenance_recovery_required"},
            "transport_model_provenance_recovered": False,
            "provenance_search": {
                "searched": True,
                "accepted_bundle_ref": None,
                "result_summary_acceptance_allowed": False,
                "substitute_refit_allowed": False,
            },
        },
    )
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_id": "study-decision::dm002::methodology-reframe",
            "study_id": study_id,
            "quest_id": study_id,
            "decision_type": "bounded_analysis",
            "requires_human_confirmation": False,
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "controller_actions": [{"action_type": "ensure_study_runtime", "payload_ref": str(decision_path)}],
            "next_work_unit": {
                "unit_id": "provenance_limited_harmonization_audit",
                "lane": "analysis-campaign",
                "hard_methodology": True,
                "selected_route_option": "provenance_limited_harmonization_audit",
                "terminal_source_provenance_blocker_consumed": True,
                "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
            },
        },
    )
    route = _owner_route(
        study_id=study_id,
        action_type="provenance_limited_harmonization_audit",
        owner="provenance_limited_harmonization_owner",
    )
    route.update(
        {
            "failure_signature": "provenance_limited_harmonization_audit_required",
            "owner_reason": "provenance_limited_harmonization_audit_required",
            "work_unit_fingerprint": "provenance-limited-harmonization::audit",
            "source_fingerprint": "truth-snapshot::methodology-reframe-decision",
            "idempotency_key": "owner-route::dm002::provenance-limited-harmonization::audit",
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::provenance-limited-audit",
        "stall_reasons": ["owner_callable_surface_missing"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="provenance_limited_harmonization_audit",
        owner="provenance_limited_harmonization_owner",
        required_output_surface=(
            "provenance-limited harmonization audit or "
            "typed blocker:provenance_limited_harmonization_audit_required"
        ),
        owner_route=route,
    )
    dispatch["source_action"] = {
        "action_type": "provenance_limited_harmonization_audit",
        "source_ref": str(decision_path),
        "selected_route_option": "provenance_limited_harmonization_audit",
    }
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch["prompt_contract"][
        "request_packet_ref"
    ] = "artifacts/supervision/requests/provenance_limited_harmonization/latest.json"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "provenance_limited_harmonization_audit.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_domain_route_scan",
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("provenance_limited_harmonization_audit",),
        mode="developer_apply_safe",
        apply=True,
    )

    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "provenance_limited_harmonization"
        / "latest.json"
    )
    owner_result_path = study_root / "artifacts" / "controller" / "provenance_limited_harmonization" / "latest.json"
    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["dispatch_contract_valid"] is True
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["owner_callable_surface"] == (
        "provenance_limited_harmonization_owner."
        "provenance_limited_harmonization_audit_or_typed_blocker"
    )
    assert execution["owner_result"]["request_path"] == str(request_path)
    assert execution["owner_result"]["result_ref"] == str(owner_result_path)
    assert execution["owner_result"]["surface"] == "provenance_limited_harmonization_owner_result"
    assert execution["owner_result"]["status"] == "blocked"
    assert execution["owner_result"]["blocked_reason"] == "rebuild_reproducible_model_route_required"
    assert execution["owner_result"]["next_owner"] == "human_gate"
    assert execution["owner_result"]["work_unit"] == "provenance_limited_harmonization_audit"
    assert execution["owner_result"]["provenance_limited_audit_completed"] is True
    assert execution["owner_result"]["terminal_source_provenance_blocker_consumed"] is True
    assert execution["owner_result"]["current_transport_claim_must_not_be_used_as_medical_conclusion"] is True
    assert "medical_transportability_conclusion" in execution["owner_result"][
        "raw_transported_score_results_disallowed_uses"
    ]
    assert execution["owner_result"]["paper_package_mutation_allowed"] is False
    assert execution["owner_result"]["quality_gate_relaxation_allowed"] is False
    assert execution["owner_result"]["medical_claim_authoring_allowed"] is False
    assert execution["owner_result"]["publication_eval_written"] is False
    assert execution["owner_result"]["controller_decision_written"] is False
    assert request_path.is_file()
    assert owner_result_path.is_file()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    owner_result = json.loads(owner_result_path.read_text(encoding="utf-8"))
    assert request["request_kind"] == "provenance_limited_harmonization_audit"
    assert request["request_owner"] == "provenance_limited_harmonization_owner"
    assert request["blocked_reason"] == "provenance_limited_harmonization_audit_required"
    assert request["next_work_unit"] == "provenance_limited_harmonization_audit"
    assert request["paper_package_mutation_allowed"] is False
    assert request["quality_gate_relaxation_allowed"] is False
    assert request["medical_claim_authoring_allowed"] is False
    assert owner_result["request_ref"]["path"] == str(request_path)
    assert owner_result["typed_blocker"]["blocker_id"] == "rebuild_reproducible_model_route_required"
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_records_candidate_search_without_accepting_result_summary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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

    result = module.dispatch_domain_owner_actions(
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
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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

    result = module.dispatch_domain_owner_actions(
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


def test_source_provenance_owner_uses_bounded_search_for_deep_legacy_archive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    legacy_root = profile.workspace_root / "runtime" / "archives" / "legacy_mds"
    deep_bundle_path = (
        legacy_root
        / "snapshot"
        / "runtime"
        / "quest"
        / "generated"
        / "nested"
        / "paper"
        / "analysis"
        / "models"
        / "transport_model_provenance_bundle.json"
    )
    _write_json(
        deep_bundle_path,
        {
            "surface": "canonical_transport_model_provenance_bundle",
            "schema_version": 1,
            "model_type": "penalized_cox_ph",
            "coefficients": {"age": 0.04},
            "feature_order": ["age"],
            "feature_coding": {"age": {"type": "continuous"}},
            "baseline_survival_at_5_years": 0.98,
            "penalty": {"type": "ridge", "lambda": 0.01},
            "standardization": {"center": {"age": 50.0}, "scale": {"age": 10.0}},
            "original_result_artifact": "legacy/RESULT.json",
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("recover_transport_model_provenance",),
        mode="developer_apply_safe",
        apply=True,
    )

    owner_result = result["executions"][0]["owner_result"]
    search = owner_result["provenance_search"]
    legacy_summary = next(
        summary for summary in search["root_scan_summaries"] if summary["root_kind"] == "legacy_archive"
    )
    assert owner_result["status"] == "blocked"
    assert owner_result["transport_model_provenance_recovered"] is False
    assert owner_result["canonical_transport_model_provenance_bundle_ref"] is None
    assert search["searched"] is True
    assert search["bounded_search"] is True
    assert str(deep_bundle_path) not in {candidate["path"] for candidate in search["candidates"]}
    assert legacy_summary["bounded"] is True
    assert legacy_summary["max_depth"] < len(deep_bundle_path.relative_to(legacy_root).parts) - 1
    assert "canonical_transport_model_provenance_bundle_missing" in owner_result["typed_blocker"][
        "blocking_reasons"
    ]
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_source_provenance_owner_accepts_complete_canonical_transport_model_bundle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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

    result = module.dispatch_domain_owner_actions(
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
