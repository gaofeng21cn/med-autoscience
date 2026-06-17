from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _install_gate_clearing_executor(module, monkeypatch) -> dict[str, object]:
    called: dict[str, object] = {}

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "ready",
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
            "controller_action_type": "run_gate_clearing_batch",
        }

    monkeypatch.setattr(
        module.action_execution.publication_gate_actions.gate_clearing_batch,
        "run_gate_clearing_batch",
        fake_run_gate_clearing_batch,
    )
    return called


def _install_quality_repair_executor(module, monkeypatch) -> dict[str, object]:
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )
    return called


def test_execute_dispatch_accepts_story_surface_materialization_bridge_owner_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    work_unit_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    materialized_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    source_refs = dict(materialized_route.get("source_refs") or {})
    source_refs.update(
        {
            "source_eval_id": "publication-eval::003::ai-reviewer-record::current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "bridge_authority": "domain_action_request_materializer_story_surface_bridge",
            "bridged_from_owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "materialized_from_action_type": "return_to_ai_reviewer_workflow",
            "materialized_work_unit_id": "medical_prose_write_repair",
            "owner_route_currentness_basis": {
                "source_eval_id": "publication-eval::003::ai-reviewer-record::current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006348",
            },
        }
    )
    materialized_route.update(
        {
            "truth_epoch": "truth-event-000022",
            "route_epoch": "truth-event-000022",
            "runtime_health_epoch": "runtime-health-event-006348",
            "source_fingerprint": "truth-snapshot::dm003-current",
            "work_unit_fingerprint": work_unit_fingerprint,
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "source_refs": source_refs,
            "idempotency_key": "owner-route::dm003::write-story-surface-bridge",
        }
    )
    materialized_route = module.owner_route_part.ensure_owner_route_v2(materialized_route)
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=materialized_route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "controller_work_unit_id": work_unit_id,
        "executable_work_unit": work_unit_id,
        "materialization_decision": "story_surface_delta_or_typed_blocker_required",
        "source_eval_id": "publication-eval::003::ai-reviewer-record::current",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [
                {
                    **dispatch_payload,
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
        },
    )
    called = _install_quality_repair_executor(module, monkeypatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "dispatch_owner_route_bridge"
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    route_context = called["authority_route_context"]["controller_route_context"]
    assert route_context["source_eval_id"] == "publication-eval::003::ai-reviewer-record::current"


def test_execute_dispatch_accepts_publication_owner_materialization_bridge(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    current_route.update(
        {
            "quest_id": quest_id,
            "truth_epoch": "truth-event-000024",
            "route_epoch": "truth-event-000024",
            "runtime_health_epoch": "runtime-health-event-006315",
            "source_fingerprint": "truth-snapshot::dm002-current",
            "work_unit_fingerprint": work_unit_fingerprint,
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "idempotency_key": "owner-route::dm002::write-current",
            "source_refs": {
                "study_truth_epoch": "truth-event-000024",
                "runtime_health_epoch": "runtime-health-event-006315",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_eval_id": "publication-eval::dm002::current",
            },
        }
    )
    materialized_route = dict(current_route)
    materialized_refs = dict(current_route["source_refs"])
    materialized_refs.update(
        {
            "blocked_reason": "current_package_freshness_required",
            "bridge_authority": "domain_action_request_materializer_publication_owner_bridge",
            "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
            "bridged_from_idempotency_key": current_route["idempotency_key"],
            "materialized_from_action_type": "run_quality_repair_batch",
            "materialized_work_unit_id": "current_package_freshness_required",
        }
    )
    materialized_route.update(
        {
            "next_owner": "gate_clearing_batch",
            "owner_reason": "current_package_freshness_required",
            "failure_signature": "current_package_freshness_required",
            "allowed_actions": ["run_gate_clearing_batch"],
            "blocked_actions": ["run_quality_repair_batch"],
            "source_refs": materialized_refs,
            "idempotency_key": "owner-route::dm002::publication-owner-materialized",
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=materialized_route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_gate_clearing_batch",
        "controller_work_unit_id": work_unit_id,
        "executable_work_unit": work_unit_id,
        "materialization_decision": "current_package_freshness_required",
        "source_eval_id": "publication-eval::dm002::current",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    scan_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        scan_path,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": current_route}],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
        },
    )
    called = _install_gate_clearing_executor(module, monkeypatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_gate_clearing_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "bridged_publication_owner_materialization"
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    route_context = called["authority_route_context"]["controller_route_context"]
    assert route_context["controller_action_type"] == "run_gate_clearing_batch"
    assert route_context["work_unit_id"] == "submission_minimal_refresh"


def test_terminal_stall_accepts_current_publication_owner_materialization_bridge(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    stall = {
        "schema_version": 1,
        "surface_kind": "paper_progress_stall",
        "terminal": True,
        "stalled": True,
        "stall_reasons": ["same_fingerprint_loop", "runtime_recovery_retry_budget_exhausted"],
        "action_fingerprint": "paper_progress_stall:dm002-publication-owner-bridge",
    }
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    current_route.update(
        {
            "quest_id": quest_id,
            "truth_epoch": "truth-event-000024",
            "route_epoch": "truth-event-000024",
            "runtime_health_epoch": "runtime-health-event-006315",
            "source_fingerprint": "truth-snapshot::dm002-current",
            "work_unit_fingerprint": work_unit_fingerprint,
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "idempotency_key": "owner-route::dm002::write-current",
            "source_refs": {
                "study_truth_epoch": "truth-event-000024",
                "runtime_health_epoch": "runtime-health-event-006315",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_eval_id": None,
            },
        }
    )
    materialized_route = dict(current_route)
    materialized_refs = dict(current_route["source_refs"])
    materialized_refs.update(
        {
            "blocked_reason": "current_package_freshness_required",
            "bridge_authority": "domain_action_request_materializer_publication_owner_bridge",
            "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
            "bridged_from_idempotency_key": current_route["idempotency_key"],
            "materialized_from_action_type": "run_quality_repair_batch",
            "materialized_work_unit_id": "current_package_freshness_required",
            "owner_route_currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "truth_epoch": "truth-event-000024",
                "runtime_health_epoch": "runtime-health-event-006315",
                "owner_reason": "current_package_freshness_required",
            },
        }
    )
    materialized_route.update(
        {
            "next_owner": "gate_clearing_batch",
            "owner_reason": "current_package_freshness_required",
            "failure_signature": "current_package_freshness_required",
            "allowed_actions": ["run_gate_clearing_batch"],
            "blocked_actions": ["run_quality_repair_batch"],
            "source_refs": materialized_refs,
            "idempotency_key": "owner-route::dm002::publication-owner-materialized",
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=materialized_route,
    )
    dispatch_payload["paper_progress_stall"] = dict(stall)
    dispatch_payload["prompt_contract"]["paper_progress_stall"] = dict(stall)
    dispatch_payload["source_action"] = {
        "action_type": "run_gate_clearing_batch",
        "controller_work_unit_id": work_unit_id,
        "executable_work_unit": work_unit_id,
        "materialization_decision": "current_package_freshness_required",
        "source_eval_id": None,
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "action_type": "run_quality_repair_batch",
                            "owner_route": current_route,
                            "paper_progress_stall": stall,
                        }
                    ],
                    "paper_progress_stall": stall,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
        },
    )
    called = _install_gate_clearing_executor(module, monkeypatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_gate_clearing_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "bridged_publication_owner_materialization"
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    route_context = called["authority_route_context"]["controller_route_context"]
    assert route_context["work_unit_id"] == "submission_minimal_refresh"


def test_terminal_stall_rejects_gate_clearing_without_publication_owner_bridge(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    current_route.update(
        {
            "quest_id": quest_id,
            "truth_epoch": "truth-event-000024",
            "route_epoch": "truth-event-000024",
            "runtime_health_epoch": "runtime-health-event-006315",
            "source_fingerprint": "truth-snapshot::dm002-current",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::write-repair",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "idempotency_key": "owner-route::dm002::write-current",
            "source_refs": {
                "study_truth_epoch": "truth-event-000024",
                "runtime_health_epoch": "runtime-health-event-006315",
                "work_unit_id": "write-repair",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::write-repair",
            },
        }
    )
    gate_route = dict(current_route)
    gate_refs = dict(current_route["source_refs"])
    gate_route.update(
        {
            "next_owner": "gate_clearing_batch",
            "owner_reason": "current_package_freshness_required",
            "failure_signature": "current_package_freshness_required",
            "allowed_actions": ["run_gate_clearing_batch"],
            "blocked_actions": ["run_quality_repair_batch"],
            "source_refs": gate_refs,
            "idempotency_key": "owner-route::dm002::unbridged-gate-clearing",
        }
    )
    stall = {
        "schema_version": 1,
        "surface_kind": "paper_progress_stall",
        "terminal": True,
        "stalled": True,
        "stall_reasons": ["same_fingerprint_loop", "runtime_recovery_retry_budget_exhausted"],
        "action_fingerprint": "paper_progress_stall:dm002-unbridged",
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=gate_route,
    )
    dispatch_payload["paper_progress_stall"] = dict(stall)
    dispatch_payload["prompt_contract"]["paper_progress_stall"] = dict(stall)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": gate_route,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_gate_clearing_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["paper_progress_stall_handoff_allowed"] is False
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "paper_progress_stall_terminal"


def test_execute_dispatch_accepts_publication_gate_replay_materialization_bridge(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    current_route.update(
        {
            "quest_id": quest_id,
            "truth_epoch": "truth-event-000024",
            "route_epoch": "truth-event-000024",
            "runtime_health_epoch": "runtime-health-event-006315",
            "source_fingerprint": "truth-snapshot::dm002-current",
            "work_unit_fingerprint": work_unit_fingerprint,
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "idempotency_key": "owner-route::dm002::write-current",
            "source_refs": {
                "study_truth_epoch": "truth-event-000024",
                "runtime_health_epoch": "runtime-health-event-006315",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_eval_id": "publication-eval::dm002::current",
            },
        }
    )
    materialized_route = dict(current_route)
    materialized_refs = dict(current_route["source_refs"])
    materialized_refs.update(
        {
            "blocked_reason": "publication_owner_materialization_required",
            "bridge_authority": "domain_action_request_materializer_publication_owner_bridge",
            "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
            "bridged_from_idempotency_key": current_route["idempotency_key"],
            "materialized_from_action_type": "run_quality_repair_batch",
            "materialized_work_unit_id": "publication_gate_replay",
        }
    )
    materialized_route.update(
        {
            "next_owner": "gate_clearing_batch",
            "owner_reason": "publication_owner_materialization_required",
            "failure_signature": "publication_owner_materialization_required",
            "allowed_actions": ["run_gate_clearing_batch"],
            "blocked_actions": ["run_quality_repair_batch"],
            "source_refs": materialized_refs,
            "idempotency_key": "owner-route::dm002::publication-gate-replay-materialized",
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=materialized_route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_gate_clearing_batch",
        "controller_work_unit_id": work_unit_id,
        "executable_work_unit": work_unit_id,
        "materialization_decision": "publication_gate_replay",
        "source_eval_id": "publication-eval::dm002::current",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": current_route}],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
        },
    )
    called = _install_gate_clearing_executor(module, monkeypatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_gate_clearing_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "bridged_publication_owner_materialization"
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    route_context = called["authority_route_context"]["controller_route_context"]
    assert route_context["controller_action_type"] == "run_gate_clearing_batch"
    assert route_context["work_unit_id"] == "publication_gate_replay"
