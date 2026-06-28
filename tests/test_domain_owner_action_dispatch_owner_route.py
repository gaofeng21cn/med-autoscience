from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    transition_request_consumer_latest as _transition_request_consumer_latest,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_materializes_display_contract_stubs_before_gate_clearing(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
        module.domain_status_projection,
        "progress_projection",
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

    monkeypatch.setattr(module.action_execution.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.dispatch_domain_owner_actions(
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


def test_execute_dispatch_filters_action_that_is_not_current_owner_route_action(
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["blocked_count"] == 0
    assert result["executions"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_current_materialized_dispatches_do_not_select_successor_for_explicit_requested_action(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.current_dispatch_materialization"
    )
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    successor_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="canonical manuscript story-surface delta",
    )
    successor_dispatch["source_action_ref"] = {
        "materialized_from_action_type": "return_to_ai_reviewer_workflow",
    }
    successor_dispatch["owner_route_ref"] = {
        "source_refs": {
            "materialized_from_action_type": "return_to_ai_reviewer_workflow",
        }
    }

    def fake_transition_request_projection_producer(**_: object) -> dict[str, object]:
        return _transition_request_consumer_latest(successor_dispatch)

    dispatches = module.current_materialized_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=False,
        transition_request_projection_producer=fake_transition_request_projection_producer,
        text=lambda value: str(value).strip() if str(value or "").strip() else None,
    )

    assert dispatches == []


def test_current_materialized_dispatches_skip_transition_projection_for_current_mas_owner_callable(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.current_dispatch_materialization"
    )
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::f11710a114497b27"
    stale_projection_source = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="analysis-campaign",
        required_output_surface="canonical manuscript story-surface delta",
    )
    stale_projection_source.update(
        {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        }
    )
    stale_projection_source["owner_route"] = {
        **stale_projection_source["owner_route"],
        "next_owner": "analysis-campaign",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "owner_route_currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
    }
    fresh_progress = {
        "study_id": study_id,
        "paper_recovery_state": {
            "phase": "owner_action_ready",
            "next_safe_action": {"kind": "run_mas_owner_callable"},
        },
        "current_work_unit": {
            "status": "executable_owner_action",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "provider_admission_pending": False,
                "transition_request_pending": False,
                "provider_attempt_or_lease_required": False,
                "provider_admission_requires_opl_runtime_result": False,
                "opl_transition_runtime_required": False,
            },
        },
        "current_executable_owner_action": {
            "status": "ready",
            "action_type": "run_quality_repair_batch",
            "next_owner": "analysis-campaign",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "provider_admission_pending": False,
            "transition_request_pending": False,
            "provider_attempt_or_lease_required": False,
            "provider_admission_requires_opl_runtime_result": False,
            "opl_transition_runtime_required": False,
            "target_surface": {
                "ref_kind": "mas_owner_callable",
                "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            },
        },
    }

    def fake_transition_request_projection_producer(**_: object) -> dict[str, object]:
        return _transition_request_consumer_latest(stale_projection_source)

    dispatches = module.current_materialized_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=False,
        fresh_progress=fresh_progress,
        transition_request_projection_producer=fake_transition_request_projection_producer,
        text=lambda value: str(value).strip() if str(value or "").strip() else None,
    )

    assert dispatches == []


def test_execute_dispatch_allows_action_type_when_route_reason_is_concrete_blocker(
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
        module.action_execution,
        "execute_artifact_display_materialization",
        lambda **_: {
            "execution_status": "blocked",
            "blocked_reason": "owner_callable_surface_missing",
            "owner_callable_surface": None,
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("artifact_display_surface_materialization_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "scan_latest"
    assert result["executed_count"] == 0
    assert execution["blocked_reason"] == "owner_callable_surface_missing"


def test_execute_dispatch_rejects_dispatch_owner_route_when_scan_lacks_study_route(
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
        action_type="run_quality_repair_batch",
        owner="write",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="typed blocker:manuscript_story_surface_delta_missing",
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        _transition_request_consumer_latest({**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}),
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "blocked",
            "blocked_reason": "owner_callable_surface_missing",
            "owner_callable_surface": None,
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["owner_route_current"] is False
    assert execution["owner_route_basis"] == "scan_latest"
    assert execution["current_owner_route"] is None
    assert execution["blocked_reason"] == "current_owner_route_missing"


def test_execute_dispatch_authorization_ignores_diagnostic_owner_reason_drift(
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
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route.update(
        {
            "owner_reason": "opl_stage_attempt_admission_required",
            "failure_signature": "opl_stage_attempt_admission_required",
            "source_refs": {
                "owner_route_currentness_basis": {
                    "truth_epoch": route["truth_epoch"],
                    "runtime_health_epoch": route["runtime_health_epoch"],
                    "work_unit_fingerprint": route["work_unit_fingerprint"],
                    "work_unit_id": "current_manuscript_repair",
                    "owner_reason": "opl_stage_attempt_admission_required",
                },
                "study_macro_state": {
                    "writer_state": "queued",
                    "user_next": "repair",
                    "reason": "quality",
                    "source_fingerprint": "study-macro-state::quality",
                },
            },
        }
    )
    current_route = {
        **route,
        "owner_reason": "manuscript_story_surface_delta_missing",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "source_refs": {
            **route["source_refs"],
            "owner_route_currentness_basis": {
                **route["source_refs"]["owner_route_currentness_basis"],
                "owner_reason": "manuscript_story_surface_delta_missing",
            },
        },
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="typed blocker:manuscript_story_surface_delta_missing",
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
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
        _transition_request_consumer_latest({**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}),
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "blocked",
            "blocked_reason": "owner_callable_surface_missing",
            "owner_callable_surface": None,
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["blocked_reason"] == "owner_callable_surface_missing"


def test_execute_dispatch_filters_when_current_macro_state_drifted(
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
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["source_refs"] = {
        "owner_route_currentness_basis": {
            "truth_epoch": route["truth_epoch"],
            "runtime_health_epoch": route["runtime_health_epoch"],
            "work_unit_fingerprint": route["work_unit_fingerprint"],
            "work_unit_id": "current_manuscript_repair",
        },
        "study_macro_state": {
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "source_fingerprint": "study-macro-state::old",
        },
    }
    current_route = {
        **route,
        "source_refs": {
            **route["source_refs"],
            "study_macro_state": {
                "writer_state": "parked",
                "user_next": "none",
                "reason": "stop_loss",
                "source_fingerprint": "study-macro-state::current",
            },
        },
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="typed blocker:manuscript_story_surface_delta_missing",
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
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
        _transition_request_consumer_latest({**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executed_count"] == 0
    assert result["blocked_count"] == 0
    assert result["executions"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "manuscript" / "current_package").exists()

from tests.test_domain_owner_action_dispatch_owner_route_cases.consumer_dispatch_and_ai_reviewer_cases import *  # noqa: F403,F401
