from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_default_dispatch_ignores_persisted_dispatch_with_applied_owner_request(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "status": "applied",
            "study_id": study_id,
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "action_queue": []}],
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executed_count"] == 0


def test_default_dispatch_ignores_owner_request_superseded_by_current_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    stale_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    stale_route["source_refs"] = {
        "work_unit_id": "medical_prose_write_repair",
        "source_eval_id": "publication-eval::003::old",
    }
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="typed blocker:manuscript_story_surface_delta_missing",
        owner_route=stale_route,
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json",
        stale_dispatch,
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "write",
            "owner_route": stale_route,
        },
    )
    current_work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    current_eval_id = "publication-eval::003::current"
    gate_route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    gate_route.update(
        {
            "owner_reason": current_work_unit,
            "failure_signature": current_work_unit,
            "work_unit_fingerprint": f"domain-transition::route_back_same_line::{current_work_unit}",
            "source_refs": {
                "work_unit_id": current_work_unit,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{current_work_unit}",
                "source_eval_id": current_eval_id,
            },
        }
    )
    gate_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=gate_route,
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json",
        gate_dispatch,
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "gate_clearing_batch" / "latest.json",
        {
            "request_kind": "run_gate_clearing_batch",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "gate_clearing_batch",
            "owner_route": gate_route,
        },
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "finalize",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": current_work_unit,
                            "lane": "publication_gate",
                        },
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "eval_id": current_eval_id,
                            "receipt_kind": "ai_reviewer_publication_eval",
                        },
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.action_execution.publication_gate_actions.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "should_not_run",
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["executions"][0]["action_type"] == "run_gate_clearing_batch"
    assert result["executions"][0]["owner_route_basis"] in {
        "owner_request",
        "consumed_transition_gate_replay",
    }


def test_default_dispatch_current_stage_handoff_supersedes_consumed_transition_gate_replay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    gate_work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    gate_route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    gate_route.update(
        {
            "owner_reason": gate_work_unit,
            "failure_signature": gate_work_unit,
            "work_unit_fingerprint": f"domain-transition::route_back_same_line::{gate_work_unit}",
            "source_refs": {
                "work_unit_id": gate_work_unit,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{gate_work_unit}",
                "source_eval_id": "publication-eval::003::current",
            },
        }
    )
    gate_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=gate_route,
    )
    handoff_route = _owner_route(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
    )
    handoff_route["source_refs"] = {
        "work_unit_id": "publication_handoff_owner_gate",
        "work_unit_fingerprint": handoff_route["work_unit_fingerprint"],
        "owner_route_currentness_basis": {
            "truth_epoch": handoff_route["truth_epoch"],
            "runtime_health_epoch": handoff_route["runtime_health_epoch"],
            "work_unit_id": "publication_handoff_owner_gate",
            "work_unit_fingerprint": handoff_route["work_unit_fingerprint"],
        },
    }
    handoff_dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
        required_output_surface=(
            "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json "
            "or artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
        ),
        owner_route=handoff_route,
    )
    gate_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    handoff_path = gate_path.parent / "publication_handoff_owner_gate.json"
    _write_json(gate_path, gate_dispatch)
    _write_json(handoff_path, handoff_dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": handoff_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "publication_handoff_owner_gate",
                            "owner": "publication_gate_owner",
                            "owner_route": handoff_route,
                        }
                    ],
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_artifact_index.next_owner_action",
                        "allowed_actions": ["publication_handoff_owner_gate"],
                        "next_owner": "publication_gate_owner",
                        "work_unit_id": "publication_handoff_owner_gate",
                    },
                    "stage_artifact_index": {
                        "surface_kind": "stage_artifact_index",
                        "next_owner_action": {
                            "action_type": "publication_handoff_owner_gate",
                            "allowed_actions": ["publication_handoff_owner_gate"],
                            "next_owner": "publication_gate_owner",
                            "work_unit_id": "publication_handoff_owner_gate",
                        },
                    },
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "finalize",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {"unit_id": gate_work_unit},
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "eval_id": "publication-eval::003::current",
                            "receipt_kind": "ai_reviewer_publication_eval",
                        },
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
            "owner_callable_adapters": [
                {**gate_dispatch, "refs": {"dispatch_path": str(gate_path)}},
                {**handoff_dispatch, "refs": {"dispatch_path": str(handoff_path)}},
            ],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [execution["action_type"] for execution in result["executions"]] == [
        "publication_handoff_owner_gate"
    ]


def test_default_dispatch_executes_active_owner_request_when_scan_route_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    request_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    persisted_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="artifacts/controller/repair_execution_evidence/latest.json",
        owner_route=request_route,
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json",
        persisted_dispatch,
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "request_kind": "run_quality_repair_batch",
            "study_id": study_id,
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "owner_pickup": {"state": "pending"},
            "owner_route": request_route,
        },
    )
    stale_scan_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": stale_scan_route}],
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "should_not_run",
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 1
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] is None
    execution = result["executions"][0]
    assert execution["action_type"] == "run_quality_repair_batch"
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_route_basis"] == "owner_request"
    assert execution["owner_route_current"] is True
