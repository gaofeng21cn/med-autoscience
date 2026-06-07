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
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
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
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": stale_route}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
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


def test_explicit_harmonization_dispatch_ignores_stale_consumer_tail_actions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    current_route = _owner_route(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
    )
    current_route.update(
        {
            "failure_signature": "unit_harmonized_rerun_required",
            "owner_reason": "unit_harmonized_rerun_required",
            "work_unit_fingerprint": "hard-methodology::unit_harmonized_external_validation_rerun::current",
            "source_fingerprint": "truth-snapshot::current-analysis-harmonization",
            "idempotency_key": "owner-route::dm002::analysis-harmonization::current",
        }
    )
    current_dispatch = _dispatch(
        study_id=study_id,
        action_type="unit_harmonized_external_validation_rerun",
        owner="analysis_harmonization_owner",
        required_output_surface=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        owner_route=current_route,
    )
    current_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "unit_harmonized_external_validation_rerun.json"
    )
    current_dispatch["refs"] = {"dispatch_path": str(current_dispatch_path)}
    _write_json(current_dispatch_path, current_dispatch)
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
            "owner_route": current_route,
            "idempotency_key": current_route["idempotency_key"],
        },
    )

    stale_decision_route = _owner_route(
        study_id=study_id,
        action_type="methodology_reframe_route_decision",
        owner="decision",
    )
    stale_decision_route.update(
        {
            "failure_signature": "methodology_reframe_required",
            "owner_reason": "methodology_reframe_required",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision::stale",
            "source_fingerprint": "truth-snapshot::stale-methodology-reframe",
            "idempotency_key": "owner-route::dm002::decision::methodology-reframe::stale",
        }
    )
    stale_decision_dispatch = _dispatch(
        study_id=study_id,
        action_type="methodology_reframe_route_decision",
        owner="decision",
        required_output_surface=(
            "controller route decision for a provenance-limited reframe, "
            "reproducible-model restart, stop-loss, or human gate"
        ),
        owner_route=stale_decision_route,
    )
    stale_decision_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "methodology_reframe_route_decision.json"
    )
    stale_decision_dispatch["refs"] = {"dispatch_path": str(stale_decision_path)}
    _write_json(stale_decision_path, stale_decision_dispatch)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "decision" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "request_kind": "methodology_reframe_route_decision",
            "request_owner": "decision",
            "status": "requested",
            "blocked_reason": "methodology_reframe_required",
            "next_owner": "decision",
            "next_work_unit": "methodology_reframe_route_decision",
            "owner_route": stale_decision_route,
            "idempotency_key": stale_decision_route["idempotency_key"],
        },
    )

    stale_ai_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    stale_ai_route.update(
        {
            "work_unit_fingerprint": "ai-reviewer::stale-record-production",
            "source_fingerprint": "truth-snapshot::stale-ai-reviewer",
            "idempotency_key": "owner-route::dm002::ai-reviewer::stale",
        }
    )
    stale_ai_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=stale_ai_route,
    )
    stale_ai_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_ai_dispatch["refs"] = {"dispatch_path": str(stale_ai_path)}
    _write_json(stale_ai_path, stale_ai_dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": current_route}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 3,
            "default_executor_dispatches": [
                current_dispatch,
                stale_decision_dispatch,
                stale_ai_dispatch,
            ],
        },
    )

    executed: list[str] = []

    def fake_harmonization_owner(**kwargs) -> dict[str, object]:
        executed.append("unit_harmonized_external_validation_rerun")
        request_path = (
            study_root / "artifacts" / "supervision" / "requests" / "analysis_harmonization" / "latest.json"
        )
        owner_result_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
        _write_json(
            owner_result_path,
            {
                "surface": "analysis_harmonization_owner_result",
                "study_id": study_id,
                "owner": "analysis_harmonization_owner",
                "work_unit": "unit_harmonized_external_validation_rerun",
                "status": "completed",
                "unit_harmonized_rerun_completed": True,
            },
        )
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": (
                "analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker"
            ),
            "request_path": str(request_path),
            "result_ref": str(owner_result_path),
            "surface": "analysis_harmonization_owner_result",
            "status": "completed",
            "work_unit": "unit_harmonized_external_validation_rerun",
        }

    def fail_stale_dispatch(**kwargs) -> dict[str, object]:
        raise AssertionError("stale consumer tail dispatch should not execute")

    monkeypatch.setattr(
        module.action_execution,
        "execute_unit_harmonized_external_validation_rerun",
        fake_harmonization_owner,
    )
    monkeypatch.setattr(module.action_execution, "execute_methodology_reframe_route_decision", fail_stale_dispatch)
    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fail_stale_dispatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(
            "unit_harmonized_external_validation_rerun",
            "methodology_reframe_route_decision",
            "return_to_ai_reviewer_workflow",
        ),
        mode="developer_apply_safe",
        apply=True,
    )

    assert executed == ["unit_harmonized_external_validation_rerun"]
    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["action_type"] == "unit_harmonized_external_validation_rerun"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] in {"scan_latest", "owner_request"}
    latest = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_execution"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert [item["action_type"] for item in latest["executions"]] == [
        "unit_harmonized_external_validation_rerun"
    ]


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
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
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
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
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
    assert decision["controller_actions"][0]["action_type"] == "request_opl_stage_attempt"
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
            "controller_actions": [{"action_type": "request_opl_stage_attempt", "payload_ref": str(decision_path)}],
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
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
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
