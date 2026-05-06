from __future__ import annotations

import importlib
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_materializes_display_contract_stubs_before_gate_clearing(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    paper_root = study_root / "paper"
    _write_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "display_registry_required": True,
            "display_shell_plan": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                }
            ],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "artifact_display_surface_materialization_required.json"
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="artifact_display_surface_materialization_required",
        owner="artifact_os",
        required_output_surface="paper/display_registry.json",
    )
    route = dict(dispatch_payload["owner_route"])
    route["owner_reason"] = "display_surface_materialization_failed"
    dispatch_payload["owner_route"] = route
    dispatch_payload["prompt_contract"]["owner_route"] = route
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        assert (paper_root / "display_registry.json").exists()
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        }

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("artifact_display_surface_materialization_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == (
        "quest_hydration.materialize_display_contract_stubs+gate_clearing_batch.run_gate_clearing_batch"
    )
    stub_result = execution["owner_result"]["display_contract_stubs"]
    assert stub_result["display_registry_path"] == str(paper_root / "display_registry.json")
    assert str(paper_root / "display_registry.json") in stub_result["written_files"]
    assert called["study_id"] == study_id


def test_execute_dispatch_blocks_action_that_is_not_current_owner_route_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "return_to_ai_reviewer_workflow",
        "reason": "ai_reviewer_assessment_required",
        "owner": "ai_reviewer",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "owner_route_next_owner_mismatch"
    assert execution["owner_route_current"] is False


def test_execute_dispatch_allows_action_type_when_route_reason_is_concrete_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="artifact_display_surface_materialization_required",
        owner="artifact_os",
    )
    route["owner_reason"] = "display_surface_materialization_failed"
    route["idempotency_key"] = (
        "owner-route::002-dm-china-us-mortality-attribution::truth-epoch::artifact_os::"
        "display_surface_materialization_failed"
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="artifact_display_surface_materialization_required",
        owner="artifact_os",
        required_output_surface="paper/display_registry.json",
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "artifact_display_surface_materialization_required.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module,
        "_execute_artifact_display_materialization",
        lambda **_: {
            "execution_status": "blocked",
            "blocked_reason": "owner_callable_surface_missing",
            "owner_callable_surface": None,
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("artifact_display_surface_materialization_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["blocked_reason"] == "owner_callable_surface_missing"


def test_execute_dispatch_ignores_blocked_consumer_dispatches_by_default(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    ready_route = _owner_route(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
    )
    ready_dispatch = _dispatch(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=ready_route,
    )
    blocked_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=ready_route,
    )
    blocked_dispatch["dispatch_status"] = "blocked"
    blocked_dispatch["blocked_reason"] = "owner_route_next_owner_mismatch"
    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    ready_path = dispatch_dir / "current_package_freshness_required.json"
    blocked_path = dispatch_dir / "return_to_ai_reviewer_workflow.json"
    _write_json(ready_path, ready_dispatch)
    _write_json(blocked_path, blocked_dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": ready_route}],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "schema_version": 1,
            "default_executor_dispatches": [
                {**ready_dispatch, "refs": {"dispatch_path": str(ready_path)}},
                {**blocked_dispatch, "refs": {"dispatch_path": str(blocked_path)}},
            ],
        },
    )
    monkeypatch.setattr(
        module,
        "_execute_current_package_freshness",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["executions"][0]["action_type"] == "current_package_freshness_required"


def test_execute_dispatch_action_type_requires_current_consumer_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(dispatch_path, stale_dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )
    monkeypatch.setattr(
        module,
        "_execute_ai_reviewer_workflow",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "should_not_run",
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executed_count"] == 0
