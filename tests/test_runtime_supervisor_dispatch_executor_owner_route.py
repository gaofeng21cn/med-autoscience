from __future__ import annotations

import importlib
import json
import sqlite3
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


def test_execute_dispatch_allows_external_engineering_agent_for_external_supervisor_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="external_supervisor",
    )
    route["owner_reason"] = "runtime_recovery_not_authorized"
    route["failure_signature"] = "runtime_recovery_not_authorized"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="external_engineering_agent",
        required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module,
        "_execute_runtime_platform_repair",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "runtime_supervisor_scan.supervisor_scan(apply_runtime_platform_repair=True)",
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("runtime_platform_repair",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None


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


def test_execute_dispatch_blocks_unsupported_executor_kind_fail_closed(
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
        action_type="runtime_platform_repair",
        owner="external_engineering_agent",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="external_engineering_agent",
        required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
        owner_route=route,
    )
    dispatch_payload["executor_kind"] = "hermes_agent"
    dispatch_payload["executor_name"] = "Hermes-Agent"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        module,
        "_execute_runtime_platform_repair",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "should_not_run_for_unsupported_executor_kind",
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("runtime_platform_repair",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["blocked_count"] == 1
    assert result["executed_count"] == 0
    assert result["codex_dispatch_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "unsupported_executor_kind"
    assert execution["dispatch_contract_valid"] is False
    assert execution["executor_boundary"] == {
        "adapter_owner": "med-autoscience",
        "executor_requirement_owner": "one-person-lab",
        "mas_executor_adapter_policy": "codex_cli_default_only",
        "supported_executor_kind": "codex_cli_default",
        "default_executor_kind": "codex_cli_default",
        "received_executor_kind": "hermes_agent",
        "unsupported_executor_policy": "fail_closed",
        "local_codex_cli_scope": "standalone_diagnostics_only",
        "external_executor_opt_in_owner": "one-person-lab",
        "external_executor_opt_in_policy": "typed_closeout_or_domain_task_receipt_only",
        "mas_owned_hermes_or_claude_executor": False,
    }


def test_execute_dispatch_suppresses_repeat_when_no_meaningful_artifact_delta_and_indexes_receipt(
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
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": route["route_epoch"],
            "runtime_health_epoch": "runtime-health-repeat",
            "work_unit_fingerprint": "publication-blockers::repeat-executor",
            "failure_signature": "ai_reviewer_assessment_required",
            "trace_id": "owner-route-trace::repeat-executor",
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["prompt_contract"].update(
        {
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": "artifacts/supervision/compact_evidence_packets/return_to_ai_reviewer_workflow.json",
            "do_not_repeat": True,
            "repeat_suppression_key": "publication-blockers::repeat-executor",
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
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
                }
            ],
        },
    )
    _write_json(
        _execution_latest_path := (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_execution"
            / "latest.json"
        ),
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_request_missing",
                    "owner_route": route,
                    "prompt_contract": dispatch_payload["prompt_contract"],
                    "repeat_suppression_key": "publication-blockers::repeat-executor",
                }
            ],
        },
    )
    assert _execution_latest_path.is_file()
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

    execution = result["executions"][0]
    assert result["executed_count"] == 0
    assert result["repeat_suppressed_count"] == 1
    assert execution["execution_status"] == "repeat_suppressed"
    assert execution["repeat_suppressed"] is True
    assert execution["why_not_applied"] == "repeat_suppressed"
    assert execution["owner_callable_surface"] is None
    assert execution["prompt_contract"]["repeat_suppression_key"] == "publication-blockers::repeat-executor"

    db_path = profile.workspace_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    assert db_path.is_file()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT status, idempotency_key, payload_json
            FROM dispatch_receipts
            WHERE study_id = ? AND action_type = ?
            """,
            (study_id, "return_to_ai_reviewer_workflow"),
        ).fetchone()
    assert row is not None
    assert row[0] == "repeat_suppressed"
    assert row[1] == route["idempotency_key"]
    assert json.loads(row[2])["why_not_applied"] == "repeat_suppressed"


def test_execute_dispatch_does_not_repeat_suppress_pending_ai_reviewer_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": route["route_epoch"],
            "runtime_health_epoch": "runtime-health-repeat",
            "work_unit_fingerprint": "publication-blockers::pending-ai-reviewer",
            "failure_signature": "ai_reviewer_assessment_required",
            "trace_id": "owner-route-trace::pending-ai-reviewer",
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["prompt_contract"].update(
        {
            "do_not_repeat": True,
            "repeat_suppression_key": "publication-blockers::pending-ai-reviewer",
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
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
                    "ai_reviewer_assessment": {"present": False, "missing": True, "owner": "mechanical_projection"},
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_request_missing",
                    "owner_route": route,
                    "prompt_contract": dispatch_payload["prompt_contract"],
                    "repeat_suppression_key": "publication-blockers::pending-ai-reviewer",
                }
            ],
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["repeat_suppressed_count"] == 0
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_request_missing"
    assert execution["repeat_suppression"]["repeat_suppressed"] is False


def test_execute_dispatch_runs_ai_reviewer_handoff_when_terminal_stall_marks_exhausted_analysis(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="write/ai_reviewer",
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-000004",
            "runtime_health_epoch": "runtime-health-event-002417",
            "work_unit_fingerprint": "truth-snapshot::handoff",
            "source_fingerprint": "truth-snapshot::handoff",
            "failure_signature": "controller_work_unit_owner_handoff_required",
            "owner_reason": "controller_work_unit_owner_handoff_required",
            "trace_id": "owner-route-trace::handoff",
        }
    )
    paper_progress_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "stall_reasons": [
            "same_fingerprint_loop",
            "runtime_recovery_retry_budget_exhausted",
        ],
        "action_fingerprint": "paper_progress_stall::handoff",
        "action_cost": {
            "surface_kind": "runtime_dispatch_cost_contract",
            "action_class": "observe_only",
            "will_start_llm": False,
            "reason": "paper_progress_stall_read_model",
            "llm_dispatch_allowed": False,
            "codex_worker_dispatch": False,
        },
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="write/ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["paper_progress_stall"] = paper_progress_stall
    dispatch_payload["prompt_contract"]["paper_progress_stall"] = paper_progress_stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": paper_progress_stall,
                    "ai_reviewer_assessment": {
                        "present": False,
                        "missing": True,
                        "owner": "write/ai_reviewer",
                    },
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    called: dict[str, object] = {}

    def fake_execute_ai_reviewer_workflow(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "owner_result": {"status": "materialized"},
        }

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fake_execute_ai_reviewer_workflow)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["action_class"] == "controller_apply"
    assert execution["will_start_llm"] is False
    assert called["study_id"] == study_id


def test_execute_dispatch_runs_runtime_platform_repair_when_terminal_stall_route_allows_repair(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="MAS/controller",
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-000002",
            "runtime_health_epoch": "runtime-health-event-003034",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "source_fingerprint": "truth-snapshot::runtime-controller-redrive",
            "failure_signature": "runtime_controller_redrive_required",
            "owner_reason": "runtime_controller_redrive_required",
            "trace_id": "owner-route-trace::runtime-controller-redrive",
            "next_owner": "MAS/controller",
            "allowed_actions": ["runtime_platform_repair"],
        }
    )
    route["idempotency_key"] = "owner-route::obesity::runtime-controller-redrive"
    paper_progress_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
        "action_fingerprint": "paper_progress_stall::runtime-controller-redrive",
        "action_cost": {
            "surface_kind": "runtime_dispatch_cost_contract",
            "action_class": "observe_only",
            "will_start_llm": False,
            "reason": "paper_progress_stall_read_model",
            "llm_dispatch_allowed": False,
            "codex_worker_dispatch": False,
        },
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="MAS/controller",
        required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
        owner_route=route,
    )
    dispatch_payload["paper_progress_stall"] = paper_progress_stall
    dispatch_payload["prompt_contract"]["paper_progress_stall"] = paper_progress_stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": paper_progress_stall,
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    called: dict[str, object] = {}

    def fake_execute_runtime_platform_repair(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "runtime_supervisor_scan.supervisor_scan(apply_runtime_platform_repair=True)",
            "owner_result": {"dispatch_status": "applied", "started": True, "active_run_id": "run-obesity"},
        }

    monkeypatch.setattr(module, "_execute_runtime_platform_repair", fake_execute_runtime_platform_repair)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("runtime_platform_repair",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert called["study_id"] == study_id
