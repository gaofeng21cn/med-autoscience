from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
    write_scan_latest as _write_scan_latest,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_rejects_consumer_dispatch_disallowed_by_current_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    stale_route.update(
        {
            "work_unit_fingerprint": "truth-snapshot::stale-quality-repair",
            "source_fingerprint": "truth-source::stale-quality-repair",
            "idempotency_key": "owner-route::003::stale-quality-repair",
        }
    )
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="artifacts/supervision/quality_repair_batch/latest.json",
        owner_route=stale_route,
    )
    stale_dispatch["refs"] = {"dispatch_path": str(stale_dispatch_path)}
    _write_json(stale_dispatch_path, stale_dispatch)
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    current_route.update(
        {
            "work_unit_fingerprint": "truth-snapshot::current-gate-clearing",
            "source_fingerprint": "truth-source::current-gate-clearing",
            "idempotency_key": "owner-route::003::current-gate-clearing",
        }
    )
    _write_scan_latest(profile, study_id, current_route)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [stale_dispatch],
        },
    )

    def fail_quality_repair_batch(**kwargs) -> dict[str, object]:
        raise AssertionError("current route disallowed stale quality repair dispatch should not execute")

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fail_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executed_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    ).exists()


def test_execute_dispatch_rejects_unrouted_consumer_dispatch_when_current_control_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    current_route.update(
        {
            "work_unit_fingerprint": "truth-snapshot::current-gate-clearing",
            "source_fingerprint": "truth-source::current-gate-clearing",
            "idempotency_key": "owner-route::003::current-gate-clearing",
        }
    )
    _write_scan_latest(profile, study_id, current_route)
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    del stale_dispatch["owner_route"]
    del stale_dispatch["prompt_contract"]["owner_route"]
    del stale_dispatch["prompt_contract"]["idempotency_key"]
    stale_dispatch["refs"] = {"dispatch_path": str(stale_dispatch_path)}
    _write_json(stale_dispatch_path, stale_dispatch)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [stale_dispatch],
        },
    )

    def fail_ai_reviewer_workflow(**kwargs) -> dict[str, object]:
        raise AssertionError("unrouted legacy dispatch must not reach executor selection")

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fail_ai_reviewer_workflow)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executed_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    ).exists()


def test_execute_dispatch_rejects_unrouted_consumer_dispatch_when_current_work_unit_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    del stale_dispatch["owner_route"]
    del stale_dispatch["prompt_contract"]["owner_route"]
    del stale_dispatch["prompt_contract"]["idempotency_key"]
    stale_dispatch["refs"] = {"dispatch_path": str(stale_dispatch_path)}
    _write_json(stale_dispatch_path, stale_dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "truth-snapshot::current-gate-clearing",
                        "action_fingerprint": "truth-snapshot::current-gate-clearing",
                    },
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [stale_dispatch],
        },
    )

    def fail_ai_reviewer_workflow(**kwargs) -> dict[str, object]:
        raise AssertionError("unrouted legacy dispatch must not execute when current_work_unit exists")

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fail_ai_reviewer_workflow)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executed_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    ).exists()

    explicit_result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert explicit_result["execution_count"] == 0
    assert explicit_result["executed_count"] == 0
    assert explicit_result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    ).exists()
