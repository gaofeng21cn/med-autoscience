from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
    runtime_health_epoch: str | None = "runtime-health-current",
) -> dict[str, object]:
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
    }
    if runtime_health_epoch is not None:
        route["runtime_health_epoch"] = runtime_health_epoch
        route["source_refs"] = {
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": route["source_fingerprint"],
        }
    return route


def test_materialize_domain_action_requests_consumes_completed_analysis_ai_reviewer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="analysis_harmonization_completed_ai_reviewer_review_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "analysis_harmonization_completed_ai_reviewer_review_required",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": route,
        "required_currentness_refs": [
            str(study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"),
            str(
                study_root
                / "artifacts"
                / "controller"
                / "analysis_harmonization"
                / "unit_harmonized_external_validation_rerun.json"
            ),
        ],
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "action_queue": [action],
                    "ai_reviewer_assessment": {
                        "present": True,
                        "missing": True,
                        "blocked_reason": "ai_reviewer_record_stale_after_unit_harmonized_rerun",
                    },
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["domain_progress_transition_request_count"] == 1
    task = result["request_tasks"][0]
    dispatch = result["domain_progress_transition_requests"][0]
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["request_owner"] == "ai_reviewer"
    assert task["owner_route_current"] is True
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    assert dispatch["repeat_suppressed"] is False
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    assert result["written_files"] == []
    assert result["apply_writes_disabled_reason"] == "opl_domain_progress_transition_runtime_owns_durable_carrier"
    assert result["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert not packet_path.exists()
    assert not dispatch_path.exists()
    assert task["handoff_packet"]["request_owner"] == "ai_reviewer"
    assert task["handoff_packet"]["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert task["handoff_packet"]["dispatch_status"] == "transition_request_pending"
    assert task["handoff_packet"]["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["owner_route"]["currentness_contract"]["missing_required_fields"] == []
    assert dispatch["owner_route_attempt_envelope"]["dispatchable"] is True
    assert dispatch["prompt_contract_ref"]["request_packet_ref"] == (
        "artifacts/supervision/requests/ai_reviewer/latest.json"
    )
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == (
        "DomainProgressTransitionRuntime"
    )


def test_materialize_domain_transition_ai_reviewer_re_eval_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="domain_transition_ai_reviewer_re_eval",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": "ai_reviewer_medical_prose_quality_review",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "action_queue": [action],
                    "ai_reviewer_assessment": {
                        "present": True,
                        "missing": False,
                    },
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["domain_progress_transition_request_count"] == 1
    task = result["request_tasks"][0]
    dispatch = result["domain_progress_transition_requests"][0]
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["request_owner"] == "ai_reviewer"
    assert task["owner_route_current"] is True
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    assert result["written_files"] == []
    assert result["apply_writes_disabled_reason"] == "opl_domain_progress_transition_runtime_owns_durable_carrier"
    assert result["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert not dispatch_path.exists()
    assert dispatch["owner_route"]["owner_reason_contract"]["registered"] is True
    assert dispatch["owner_route"]["owner_reason_contract"]["reason"] == (
        "domain_transition_ai_reviewer_re_eval"
    )
    assert "return_to_ai_reviewer_workflow" in dispatch["owner_route"]["allowed_actions"]
    assert dispatch["owner_route"]["currentness_contract"]["missing_required_fields"] == []
    assert dispatch["owner_route_attempt_envelope"]["dispatchable"] is True
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == (
        "DomainProgressTransitionRuntime"
    )


def test_current_write_domain_transition_supersedes_stale_ai_reviewer_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_manuscript",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    stale_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "ai_reviewer_record_stale_after_current_manuscript",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": stale_route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": stale_route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "domain_transition": {
                        "study_id": study_id,
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": "dm002_same_line_display_table_package_repair",
                            "lane": "write",
                            "summary": (
                                "Reconcile Table 2, figures, display registry, claim-map boundaries, "
                                "and package freshness."
                            ),
                        },
                        "guard_boundary": {"opl_generic_runner_may_resume": False},
                    },
                    "action_queue": [stale_action],
                }
            ],
            "action_queue": [stale_action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["domain_progress_transition_request_count"] == 1
    task = result["request_tasks"][0]
    dispatch = result["domain_progress_transition_requests"][0]
    assert task["action_type"] == "run_quality_repair_batch"
    assert task["request_owner"] == "write"
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["owner_route"]["next_owner"] == "write"
    assert dispatch["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert any(
        ignored["action_type"] == "return_to_ai_reviewer_workflow"
        and ignored["reason"] == "superseded_by_current_domain_transition"
        for ignored in result["ignored_actions"]
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == (
        "DomainProgressTransitionRuntime"
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    ).exists()


def test_empty_per_study_queue_prevents_stale_top_level_redrive_without_current_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="domain_transition_ai_reviewer_re_eval",
        allowed_actions=[],
        runtime_health_epoch="runtime-health-current",
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="domain_transition_ai_reviewer_re_eval",
        allowed_actions=["return_to_ai_reviewer_workflow"],
        runtime_health_epoch="runtime-health-stale",
    )
    stale_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "owner_route": stale_route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": stale_route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [],
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "owner": "med-autoscience",
                        "typed_blocker": {
                            "blocker_type": "current_execution_unresolved",
                            "owner": "med-autoscience",
                        },
                    },
                }
            ],
            "action_queue": [stale_action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert any(
        ignored["action_type"] == "return_to_ai_reviewer_workflow"
        and ignored["reason"] == "superseded_by_current_work_unit_typed_blocker"
        for ignored in result["ignored_actions"]
    )


def test_consumed_ai_reviewer_transition_uses_current_owner_route_basis_for_dispatchable_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner=None,
        owner_reason=None,
        allowed_actions=[],
        runtime_health_epoch="runtime-health-current",
    )
    current_route.update(
        {
            "truth_epoch": "truth-event-current",
            "route_epoch": "truth-event-current",
            "source_fingerprint": "truth-snapshot::current",
            "work_unit_fingerprint": "truth-snapshot::current",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "truth-snapshot::current",
                "study_truth_epoch": "truth-event-current",
                "runtime_health_epoch": "runtime-health-current",
            },
        }
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [],
                    "domain_transition": {
                        "study_id": study_id,
                        "decision_type": "ai_reviewer_re_eval",
                        "route_target": "review",
                        "owner": "ai_reviewer",
                        "controller_action": "return_to_ai_reviewer_workflow",
                        "next_work_unit": {
                            "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "lane": "review",
                            "summary": "Produce current AI reviewer publication-eval record.",
                        },
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": (
                                "artifacts/publication_eval/ai_reviewer_responses/current.json"
                            ),
                        },
                    },
                }
            ],
            "action_queue": [],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["domain_progress_transition_request_count"] == 1
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["owner_route"]["currentness_contract"]["missing_required_fields"] == []
    assert dispatch["owner_route"]["source_refs"]["runtime_health_epoch"] == "runtime-health-current"
    assert dispatch["owner_route_attempt_envelope"]["dispatchable"] is True
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()


def test_action_queue_dispatch_inherits_complete_owner_route_currentness_basis(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    expected_basis = {
        "runtime_health_epoch": "runtime-health-event-dm003-current",
        "source_eval_id": "publication-eval::dm003::current",
        "truth_epoch": "truth-event-dm003-current",
        "work_unit_fingerprint": "truth-snapshot::dm003-current",
        "work_unit_id": work_unit_id,
    }
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_manuscript",
        allowed_actions=["return_to_ai_reviewer_workflow"],
        runtime_health_epoch=expected_basis["runtime_health_epoch"],
    )
    current_route.update(
        {
            "truth_epoch": expected_basis["truth_epoch"],
            "route_epoch": expected_basis["truth_epoch"],
            "source_fingerprint": expected_basis["work_unit_fingerprint"],
            "work_unit_fingerprint": expected_basis["work_unit_fingerprint"],
            "source_refs": {
                "source_eval_id": expected_basis["source_eval_id"],
                "study_truth_epoch": expected_basis["truth_epoch"],
                "runtime_health_epoch": expected_basis["runtime_health_epoch"],
                "work_unit_id": expected_basis["work_unit_id"],
                "work_unit_fingerprint": expected_basis["work_unit_fingerprint"],
                "owner_route_currentness_basis": expected_basis,
            },
        }
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "ai_reviewer_record_stale_after_current_manuscript",
        "controller_work_unit_id": work_unit_id,
        "executable_work_unit": work_unit_id,
        "next_work_unit": work_unit_id,
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "owner_route": current_route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": current_route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["domain_progress_transition_request_count"] == 1
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    for key, value in expected_basis.items():
        assert dispatch["owner_route"]["source_refs"]["owner_route_currentness_basis"][key] == value
        assert dispatch["prompt_contract_ref"]["owner_route_currentness_basis"][key] == value
        assert dispatch["owner_route_attempt_envelope"]["owner_route_currentness_basis"][key] == value
    assert dispatch["owner_route_attempt_envelope"]["dispatchable"] is True
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_kind"] == "DomainProgressTransitionRuntime"
