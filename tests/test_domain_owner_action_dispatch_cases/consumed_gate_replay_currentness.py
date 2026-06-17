from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


DM003_GATE_REPLAY_WORK_UNIT = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
DM003_GATE_REPLAY_SOURCE_FINGERPRINT = "owner-route-source::c09d46113d9004aaa469c2ad"
DM003_GATE_REPLAY_SOURCE_EVAL_ID = (
    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
    "sat_cc2c6c6cf90bbe4444a4d388"
)
DM003_AI_REVIEWER_REEVAL_WORK_UNIT = "produce_ai_reviewer_publication_eval_record_against_current_manuscript"


def _dm003_gate_replay_fingerprint() -> str:
    return f"domain-transition::route_back_same_line::{DM003_GATE_REPLAY_WORK_UNIT}"


def _dm003_ai_reviewer_reeval_fingerprint() -> str:
    return f"domain-transition::ai_reviewer_re_eval::{DM003_AI_REVIEWER_REEVAL_WORK_UNIT}"


def _dm003_gate_replay_route(
    *,
    study_id: str,
    quest_root: Path,
    source_fingerprint: str,
    source_eval_id: str | None = DM003_GATE_REPLAY_SOURCE_EVAL_ID,
) -> dict[str, object]:
    route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    route.update(
        {
            "quest_id": study_id,
            "truth_epoch": study_id,
            "route_epoch": study_id,
            "runtime_health_epoch": None,
            "work_unit_fingerprint": _dm003_gate_replay_fingerprint(),
            "source_fingerprint": source_fingerprint,
            "failure_signature": DM003_GATE_REPLAY_WORK_UNIT,
            "owner_reason": DM003_GATE_REPLAY_WORK_UNIT,
            "idempotency_key": (
                f"owner-route::{study_id}::{study_id}::gate_clearing_batch::"
                f"{DM003_GATE_REPLAY_WORK_UNIT}::aca38ea2c451332a"
            ),
            "source_refs": {
                "work_unit_id": DM003_GATE_REPLAY_WORK_UNIT,
                "work_unit_fingerprint": _dm003_gate_replay_fingerprint(),
                "blocked_reason": DM003_GATE_REPLAY_WORK_UNIT,
                "quest_root": str(quest_root),
                "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                "source_eval_id": source_eval_id,
                "runtime_health_epoch": None,
                "owner_route_currentness_basis": {
                    "truth_epoch": study_id,
                    "work_unit_fingerprint": _dm003_gate_replay_fingerprint(),
                    "work_unit_id": DM003_GATE_REPLAY_WORK_UNIT,
                    **({"source_eval_id": source_eval_id} if source_eval_id is not None else {}),
                },
            },
        }
    )
    return route


def _dm003_null_owner_route(*, study_id: str) -> dict[str, object]:
    truth_epoch = "truth-event-000022-212df8cd1d3b2842"
    runtime_health_epoch = "runtime-health-event-006271-aeaf343e896ba07b"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": "truth-snapshot::29680cbf64184e3f9943256c",
        "source_fingerprint": "truth-snapshot::29680cbf64184e3f9943256c",
        "current_owner": "mas_controller",
        "next_owner": None,
        "owner_reason": None,
        "failure_signature": None,
        "allowed_actions": [],
        "blocked_actions": [
            "publication_gate_specificity_required",
            "current_package_freshness_required",
            "artifact_display_surface_materialization_required",
            "return_to_ai_reviewer_workflow",
            "canonical_paper_inputs_rehydrate_required",
            "run_quality_repair_batch",
            "run_gate_clearing_batch",
        ],
        "idempotency_key": f"owner-route::{study_id}::{truth_epoch}::none::none::814f5abd5d6d157d",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": DM003_GATE_REPLAY_WORK_UNIT,
            "work_unit_fingerprint": "truth-snapshot::29680cbf64184e3f9943256c",
            "owner_route_currentness_basis": {
                "truth_epoch": truth_epoch,
                "runtime_health_epoch": runtime_health_epoch,
                "work_unit_fingerprint": "truth-snapshot::29680cbf64184e3f9943256c",
                "work_unit_id": DM003_GATE_REPLAY_WORK_UNIT,
            },
        },
    }


def _dm003_ai_reviewer_null_owner_route(*, study_id: str) -> dict[str, object]:
    truth_epoch = "truth-event-000022-212df8cd1d3b2842"
    runtime_health_epoch = "runtime-health-event-006348-b093abc70f3a3d8d"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": "truth-snapshot::8545ef2695c45d2372522362",
        "source_fingerprint": "truth-snapshot::8545ef2695c45d2372522362",
        "current_owner": "mas_controller",
        "next_owner": None,
        "owner_reason": None,
        "failure_signature": None,
        "allowed_actions": [],
        "blocked_actions": [
            "publication_gate_specificity_required",
            "current_package_freshness_required",
            "artifact_display_surface_materialization_required",
            "return_to_ai_reviewer_workflow",
            "canonical_paper_inputs_rehydrate_required",
            "run_quality_repair_batch",
            "run_gate_clearing_batch",
        ],
        "idempotency_key": f"owner-route::{study_id}::{truth_epoch}::none::none::37c8829f7dc12315",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                "ai-reviewer-record::20260602T184032Z"
            ),
            "work_unit_id": DM003_AI_REVIEWER_REEVAL_WORK_UNIT,
            "work_unit_fingerprint": "truth-snapshot::8545ef2695c45d2372522362",
            "owner_route_currentness_basis": {
                "truth_epoch": truth_epoch,
                "runtime_health_epoch": runtime_health_epoch,
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "ai-reviewer-record::20260602T184032Z"
                ),
                "work_unit_id": DM003_AI_REVIEWER_REEVAL_WORK_UNIT,
                "work_unit_fingerprint": "truth-snapshot::8545ef2695c45d2372522362",
            },
        },
    }


def _dm003_consumed_gate_replay_study(
    *,
    study_id: str,
    quest_root: Path,
    owner_route: dict[str, object] | None = None,
    completion_eval_id: str = DM003_GATE_REPLAY_SOURCE_EVAL_ID,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "study_id": study_id,
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "controller_action": "request_opl_stage_attempt",
            "work_unit_fingerprint": _dm003_gate_replay_fingerprint(),
            "next_work_unit": {
                "unit_id": DM003_GATE_REPLAY_WORK_UNIT,
                "lane": "publication_gate",
                "summary": "MAS publication-gate/currentness replay after current AI reviewer archive.",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "eval_id": completion_eval_id,
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
            },
        },
    }
    if owner_route is not None:
        payload["owner_route"] = owner_route
    return payload


def _dm003_consumed_ai_reviewer_reeval_study(
    *,
    study_id: str,
    quest_root: Path,
    owner_route: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "study_id": study_id,
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "current_stage": "publication_supervision",
        "paper_stage": "review",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": DM003_AI_REVIEWER_REEVAL_WORK_UNIT,
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record before dispatching the publication-eval workflow.",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "ai-reviewer-record::20260602T184032Z"
                ),
                "next_action": "honor_ai_reviewer_publication_eval_authority",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "work_unit_id": DM003_GATE_REPLAY_WORK_UNIT,
                "work_unit_fingerprint": "truth-snapshot::5bf8654ba006ca61f52ee21e",
            },
        },
    }
    if owner_route is not None:
        payload["owner_route"] = owner_route
    return payload


def _dm003_gate_replay_dispatch(
    profile,
    study_root: Path,
    *,
    source_fingerprint: str,
    source_eval_id: str | None = DM003_GATE_REPLAY_SOURCE_EVAL_ID,
) -> dict[str, object]:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_root = profile.runtime_root / study_id
    dispatch_route = _dm003_gate_replay_route(
        study_id=study_id,
        quest_root=quest_root,
        source_fingerprint=source_fingerprint,
        source_eval_id=source_eval_id,
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=dispatch_route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    return dispatch_payload


def _dm003_ai_reviewer_dispatch(profile, study_root: Path) -> dict[str, object]:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "quest_id": study_id,
            "truth_epoch": "truth-event-000022-212df8cd1d3b2842",
            "route_epoch": "truth-event-000022-212df8cd1d3b2842",
            "runtime_health_epoch": "runtime-health-event-006348-b093abc70f3a3d8d",
            "work_unit_fingerprint": _dm003_ai_reviewer_reeval_fingerprint(),
            "source_fingerprint": "truth-snapshot::8545ef2695c45d2372522362",
            "failure_signature": DM003_AI_REVIEWER_REEVAL_WORK_UNIT,
            "owner_reason": DM003_AI_REVIEWER_REEVAL_WORK_UNIT,
            "idempotency_key": f"owner-route::{study_id}::truth-event-000022::ai_reviewer::{DM003_AI_REVIEWER_REEVAL_WORK_UNIT}",
            "source_refs": {
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "ai-reviewer-record::20260602T184032Z"
                ),
                "work_unit_id": DM003_AI_REVIEWER_REEVAL_WORK_UNIT,
                "work_unit_fingerprint": _dm003_ai_reviewer_reeval_fingerprint(),
                "runtime_health_epoch": "runtime-health-event-006348-b093abc70f3a3d8d",
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-event-000022-212df8cd1d3b2842",
                    "runtime_health_epoch": "runtime-health-event-006348-b093abc70f3a3d8d",
                    "source_eval_id": (
                        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                        "ai-reviewer-record::20260602T184032Z"
                    ),
                    "work_unit_id": DM003_AI_REVIEWER_REEVAL_WORK_UNIT,
                    "work_unit_fingerprint": _dm003_ai_reviewer_reeval_fingerprint(),
                },
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["prompt_contract"]["owner_route"] = route
    dispatch_payload["prompt_contract"]["idempotency_key"] = route["idempotency_key"]
    dispatch_payload["prompt_contract"]["repeat_suppression_key"] = route["work_unit_fingerprint"]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    return dispatch_payload


def _write_consumer_latest(profile, dispatch_payload: dict[str, object]) -> None:
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapter_count": 1,
            "owner_callable_adapters": [dispatch_payload],
        },
    )


def _write_consumer_latest_dispatches(profile, dispatch_payloads: list[dict[str, object]]) -> None:
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapter_count": len(dispatch_payloads),
            "owner_callable_adapters": dispatch_payloads,
        },
    )


def _install_gate_clearing_stub(module, monkeypatch) -> list[str]:
    called: list[str] = []

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_root"]))
        return {
            "ok": True,
            "status": "executed",
            "owner_callable_surface": "gate_clearing_batch.run_gate_clearing_batch",
        }

    monkeypatch.setattr(
        module.action_execution.publication_gate_actions.gate_clearing_batch,
        "run_gate_clearing_batch",
        fake_run_gate_clearing_batch,
    )
    return called


def _install_ai_reviewer_stub(module, monkeypatch) -> list[str]:
    called: list[str] = []

    def fake_ai_reviewer_workflow(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_id"]))
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        }

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fake_ai_reviewer_workflow)
    return called


def test_execute_dispatch_selects_current_gate_replay_after_consumed_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    dispatch_payload = _dm003_gate_replay_dispatch(
        profile,
        study_root,
        source_fingerprint=DM003_GATE_REPLAY_SOURCE_FINGERPRINT,
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                _dm003_consumed_gate_replay_study(
                    study_id=study_id,
                    quest_root=quest_root,
                )
            ],
        },
    )
    _write_consumer_latest(profile, dispatch_payload)
    called = _install_gate_clearing_stub(module, monkeypatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "run_gate_clearing_batch"
    assert execution["owner_route_current"] is True
    assert execution["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert execution["execution_status"] == "executed"
    assert called == [str(study_root)]


def test_execute_dispatch_rejects_stale_quality_repair_when_current_route_allows_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
            "stage_index_ref": "control/stage_index.json",
            "next_work_unit": "medical_publication_surface_blocked_write_repair",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
        },
    )
    gate_route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    gate_route.update(
        {
            "quest_id": study_id,
            "truth_epoch": study_id,
            "route_epoch": study_id,
            "runtime_health_epoch": None,
            "work_unit_fingerprint": "work-unit::dm002::publication_gate_replay",
            "source_fingerprint": "owner-route-source::dm002-gate-replay",
            "failure_signature": "publication_gate_replay",
            "owner_reason": "publication_gate_replay",
            "source_refs": {
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "work-unit::dm002::publication_gate_replay",
                "quest_root": str(quest_root),
                "owner_route_currentness_basis": {
                    "truth_epoch": study_id,
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "work-unit::dm002::publication_gate_replay",
                },
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
    gate_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    gate_dispatch["refs"] = {"dispatch_path": str(gate_dispatch_path)}
    _write_json(gate_dispatch_path, gate_dispatch)
    stale_repair_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    stale_repair_route.update(
        {
            "work_unit_fingerprint": "work-unit::dm002::stale-quality-repair",
            "source_fingerprint": "owner-route-source::dm002-stale-quality-repair",
        }
    )
    stale_repair_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="artifacts/controller/quality_repair_batch/latest.json",
        owner_route=stale_repair_route,
    )
    stale_repair_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stale_repair_dispatch["refs"] = {"dispatch_path": str(stale_repair_dispatch_path)}
    _write_json(stale_repair_dispatch_path, stale_repair_dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "quest_root": str(quest_root),
                    "owner_route": gate_route,
                    "action_queue": [
                        {
                            "action_type": "run_gate_clearing_batch",
                            "owner_route": gate_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_consumer_latest_dispatches(profile, [stale_repair_dispatch, gate_dispatch])
    called = _install_gate_clearing_stub(module, monkeypatch)

    def fail_quality_repair_batch(**kwargs) -> dict[str, object]:
        raise AssertionError("stale quality repair dispatch should not execute")

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

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "run_gate_clearing_batch"
    assert execution["owner_route_current"] is True
    assert execution["execution_status"] == "executed"
    assert called == [str(study_root)]


def test_execute_dispatch_selects_materialized_gate_replay_when_top_level_route_is_null_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    dispatch_payload = _dm003_gate_replay_dispatch(
        profile,
        study_root,
        source_fingerprint=DM003_GATE_REPLAY_SOURCE_FINGERPRINT,
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                _dm003_consumed_gate_replay_study(
                    study_id=study_id,
                    quest_root=quest_root,
                    owner_route=_dm003_null_owner_route(study_id=study_id),
                )
            ],
        },
    )
    _write_consumer_latest(profile, dispatch_payload)
    called = _install_gate_clearing_stub(module, monkeypatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "run_gate_clearing_batch"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "consumed_transition_gate_replay"
    assert execution["owner_route"]["source_fingerprint"] == DM003_GATE_REPLAY_SOURCE_FINGERPRINT
    assert execution["execution_status"] == "executed"
    assert called == [str(study_root)]


def test_execute_dispatch_selects_ai_reviewer_after_consumed_transition_when_action_queue_is_empty(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    dispatch_payload = _dm003_ai_reviewer_dispatch(profile, study_root)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                _dm003_consumed_ai_reviewer_reeval_study(
                    study_id=study_id,
                    quest_root=quest_root,
                    owner_route=_dm003_ai_reviewer_null_owner_route(study_id=study_id),
                )
            ],
        },
    )
    _write_consumer_latest(profile, dispatch_payload)
    called = _install_ai_reviewer_stub(module, monkeypatch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "return_to_ai_reviewer_workflow"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "consumed_transition_owner_action"
    assert execution["execution_status"] == "executed"
    assert called == [study_id]


def test_execute_dispatch_rejects_stale_materialized_gate_replay_after_consumed_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    dispatch_payload = _dm003_gate_replay_dispatch(
        profile,
        study_root,
        source_fingerprint="owner-route-source::stale-dispatch",
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                _dm003_consumed_gate_replay_study(
                    study_id=study_id,
                    quest_root=quest_root,
                    owner_route=_dm003_null_owner_route(study_id=study_id),
                )
            ],
        },
    )
    _write_consumer_latest(profile, dispatch_payload)

    def fail_gate_clearing_batch(**kwargs) -> dict[str, object]:
        raise AssertionError("stale gate replay dispatch should not execute")

    monkeypatch.setattr(
        module.action_execution.publication_gate_actions.gate_clearing_batch,
        "run_gate_clearing_batch",
        fail_gate_clearing_batch,
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


def test_execute_dispatch_rejects_gate_replay_when_current_route_has_source_eval_but_dispatch_does_not(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    dispatch_payload = _dm003_gate_replay_dispatch(
        profile,
        study_root,
        source_fingerprint=DM003_GATE_REPLAY_SOURCE_FINGERPRINT,
    )
    current_route = _dm003_gate_replay_route(
        study_id=study_id,
        quest_root=quest_root,
        source_fingerprint=DM003_GATE_REPLAY_SOURCE_FINGERPRINT,
    )
    current_route["source_refs"] = {
        **current_route["source_refs"],
        "source_eval_id": "publication-eval::003::current",
        "owner_route_currentness_basis": {
            **current_route["source_refs"]["owner_route_currentness_basis"],
            "source_eval_id": "publication-eval::003::current",
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                _dm003_consumed_gate_replay_study(
                    study_id=study_id,
                    quest_root=quest_root,
                    owner_route=current_route,
                    completion_eval_id="publication-eval::003::current",
                )
            ],
        },
    )
    _write_consumer_latest(profile, dispatch_payload)

    def fail_gate_clearing_batch(**kwargs) -> dict[str, object]:
        raise AssertionError("source-eval-incomplete gate replay dispatch should not execute")

    monkeypatch.setattr(
        module.action_execution.publication_gate_actions.gate_clearing_batch,
        "run_gate_clearing_batch",
        fail_gate_clearing_batch,
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
