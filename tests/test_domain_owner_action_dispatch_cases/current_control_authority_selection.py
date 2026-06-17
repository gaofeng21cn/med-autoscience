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


def _accepted_owner_gate_quality_repair_dispatch(
    *,
    study_id: str,
    fingerprint: str = "publication-blockers::497d1260db522f01",
    work_unit_id: str = "analysis_claim_evidence_repair",
    source_ref: str = "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
) -> dict[str, object]:
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "truth_epoch": fingerprint,
            "runtime_health_epoch": fingerprint,
            "route_epoch": fingerprint,
            "work_unit_fingerprint": fingerprint,
            "source_fingerprint": fingerprint,
            "failure_signature": work_unit_id,
            "owner_reason": work_unit_id,
            "idempotency_key": (
                f"paper-recovery-owner-gate::{study_id}::run_quality_repair_batch::{fingerprint}"
            ),
            "source_refs": {
                "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
                "source_ref": source_ref,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "truth_epoch": fingerprint,
                    "runtime_health_epoch": fingerprint,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "currentness_contract": {
                "status": "currentness_basis_required",
                "basis": {
                    "truth_epoch": fingerprint,
                    "runtime_health_epoch": fingerprint,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
        }
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch.pop("opl_execution_authorization", None)
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract.pop("opl_execution_authorization", None)
    prompt_contract["owner_route_currentness_basis"] = route["source_refs"][
        "owner_route_currentness_basis"
    ]
    prompt_contract["request_packet_ref"] = "artifacts/supervision/requests/quality_repair_batch/latest.json"
    stall = {
        "kind": "owner_gate_route_back",
        "provider_admission_allowed": False,
        "route_back_evidence_ref": source_ref,
    }
    dispatch["paper_progress_stall"] = stall
    prompt_contract["paper_progress_stall"] = stall
    dispatch["action_fingerprint"] = fingerprint
    dispatch["repeat_suppression_key"] = fingerprint
    dispatch["source_action"] = {
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "action_type": "run_quality_repair_batch",
        "action_id": f"paper-recovery-owner-gate::{study_id}::run_quality_repair_batch",
        "authority": "paper_recovery_state.accepted_owner_gate_decision",
        "source_surface": "paper_recovery_state.accepted_owner_gate_decision",
        "source_ref": source_ref,
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "handoff_packet": {
            "request_owner": "write",
            "recommended_owner": "write",
            "next_executable_owner": "write",
            "source_ref": source_ref,
            "work_unit_fingerprint": fingerprint,
        },
    }
    return dispatch


def _write_owner_gate_quality_repair_request(
    study_root: Path,
    *,
    study_id: str,
    dispatch: dict[str, object],
) -> None:
    source_action = dispatch["source_action"]
    assert isinstance(source_action, dict)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "surface": "supervisor_request_handoff_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "authority": "paper_recovery_state.accepted_owner_gate_decision",
            "action_type": "run_quality_repair_batch",
            "request_kind": "run_quality_repair_batch",
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "work_unit_id": source_action["work_unit_id"],
            "work_unit_fingerprint": source_action["work_unit_fingerprint"],
            "source_ref": source_action["source_ref"],
            "owner_route": dispatch["owner_route"],
            "owner_pickup": {
                "state": "pending",
                "owner": "write",
                "owner_route": dispatch["owner_route"],
            },
        },
    )


def _patch_owner_gate_ready_progress(
    monkeypatch,
    *,
    study_id: str,
    fingerprint: str = "publication-blockers::497d1260db522f01",
    work_unit_id: str = "analysis_claim_evidence_repair",
    source_ref: str = "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
) -> None:
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        progress_module,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "active_run_id": None,
            "current_execution_envelope": {"state_kind": "parked"},
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "conditions": [{"condition": "accepted_owner_gate_decision"}],
                "next_safe_action": {
                    "kind": "route_back_to_owner_or_repair_materialization",
                    "accepted_owner_gate_decision": {
                        "decision": "route_back_to_mas_packet_materialization_bug",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "route_back_evidence_ref": source_ref,
                    },
                },
            },
        },
    )


def test_accepted_owner_gate_quality_repair_dispatch_supersedes_stale_gate_replay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _patch_owner_gate_ready_progress(monkeypatch, study_id=study_id)
    gate_route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    gate_route.update(
        {
            "owner_reason": "repair_progress_gate_replay_required",
            "work_unit_fingerprint": "sha256:old-gate-replay",
            "source_fingerprint": "truth-snapshot::old-gate-replay",
        }
    )
    gate_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    gate_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/supervision/gate_clearing_batch/latest.json",
        owner_route=gate_route,
    )
    gate_dispatch["refs"] = {"dispatch_path": str(gate_dispatch_path)}
    _write_json(gate_dispatch_path, gate_dispatch)
    quality_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    quality_dispatch = _accepted_owner_gate_quality_repair_dispatch(study_id=study_id)
    quality_dispatch["refs"] = {"dispatch_path": str(quality_dispatch_path)}
    _write_json(quality_dispatch_path, quality_dispatch)
    _write_owner_gate_quality_repair_request(
        study_root,
        study_id=study_id,
        dispatch=quality_dispatch,
    )
    _write_scan_latest(profile, study_id, gate_route)
    _write_json(
        profile.workspace_root / module.CONSUMER_LATEST_RELATIVE_PATH,
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [gate_dispatch, quality_dispatch],
        },
    )

    default_result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=False,
    )
    explicit_result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=False,
    )

    assert default_result["execution_count"] == 1
    assert default_result["executions"][0]["action_type"] == "run_quality_repair_batch"
    assert default_result["executions"][0]["dispatch_path"] == str(quality_dispatch_path)
    assert default_result["executions"][0]["owner_route_basis"] == "accepted_owner_gate_decision"
    assert default_result["executions"][0]["execution_status"] == "blocked"
    assert default_result["executions"][0]["blocked_reason"] == "opl_execution_authorization_required"
    assert default_result["executions"][0]["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert default_result["executions"][0]["owner_callable_surface"] is None
    assert explicit_result["execution_count"] == 1
    assert explicit_result["executions"][0]["action_type"] == "run_quality_repair_batch"
    assert explicit_result["executions"][0]["dispatch_path"] == str(quality_dispatch_path)
    assert explicit_result["executions"][0]["execution_status"] == "blocked"
    assert explicit_result["executions"][0]["blocked_reason"] == "opl_execution_authorization_required"
    assert explicit_result["executions"][0]["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert explicit_result["executions"][0]["owner_callable_surface"] is None


def test_dispatch_dry_run_materializes_current_owner_action_when_no_dispatch_is_persisted(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    write_study(profile.workspace_root, study_id, quest_id=study_id)
    _patch_owner_gate_ready_progress(monkeypatch, study_id=study_id)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id}],
            "action_queue": [],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "run_quality_repair_batch"
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert execution["owner_callable_surface"] is None
    assert execution["owner_route_basis"] == "accepted_owner_gate_decision"
    assert execution["dispatch_path"] == str(
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )


def test_accepted_owner_gate_quality_repair_apply_requires_opl_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _patch_owner_gate_ready_progress(monkeypatch, study_id=study_id)
    quality_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    quality_dispatch = _accepted_owner_gate_quality_repair_dispatch(study_id=study_id)
    quality_dispatch["refs"] = {"dispatch_path": str(quality_dispatch_path)}
    _write_json(quality_dispatch_path, quality_dispatch)
    _write_owner_gate_quality_repair_request(
        study_root,
        study_id=study_id,
        dispatch=quality_dispatch,
    )
    _write_json(
        profile.workspace_root / module.CONSUMER_LATEST_RELATIVE_PATH,
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [quality_dispatch],
        },
    )
    calls: list[dict[str, object]] = []

    def run_quality_repair_batch(**kwargs) -> dict[str, object]:
        calls.append(dict(kwargs))
        return {"ok": True, "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json")}

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert calls == []
    execution = result["executions"][0]
    assert execution["owner_route_basis"] == "accepted_owner_gate_decision"
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert execution["owner_callable_surface"] is None
    assert execution["provider_attempt_or_lease_required"] is False
    assert execution["provider_admission_requires_opl_runtime_result"] is True


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
            "owner_callable_adapter_count": 1,
            "owner_callable_adapters": [stale_dispatch],
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
            "owner_callable_adapter_count": 1,
            "owner_callable_adapters": [stale_dispatch],
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
            "owner_callable_adapter_count": 1,
            "owner_callable_adapters": [stale_dispatch],
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
