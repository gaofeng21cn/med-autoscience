from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_json as _write_json,
    write_scan_latest as _write_scan_latest,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_blocks_dispatch_without_owner_route(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    route = dict(dispatch["owner_route"])
    del dispatch["owner_route"]
    del dispatch["prompt_contract"]["owner_route"]
    del dispatch["prompt_contract"]["idempotency_key"]
    _write_json(dispatch_path, dispatch)
    _write_scan_latest(profile, study_id, route)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "owner_route_missing"


def test_execute_dispatch_accepts_current_action_queue_owner_route(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner": "ai_reviewer",
                            "request_owner": "ai_reviewer",
                            "recommended_owner": "ai_reviewer",
                            "owner_route": dispatch["owner_route"],
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [dispatch],
        },
    )
    called: list[str] = []

    def fake_ai_reviewer_workflow(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_id"]))
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        }

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fake_ai_reviewer_workflow)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "scan_action_queue"
    assert execution["current_owner_route"]["idempotency_key"] == dispatch["owner_route"]["idempotency_key"]
    assert called == [study_id]


def test_execute_dispatch_uses_action_queue_route_when_scan_owner_route_is_not_dispatchable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    route = dict(dispatch["owner_route"])
    route.update(
        {
            "truth_epoch": "truth-event-current-manuscript",
            "runtime_health_epoch": "",
            "work_unit_fingerprint": (
                "domain-transition::ai_reviewer_re_eval::"
                "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
            ),
            "source_fingerprint": "truth-snapshot::current-manuscript",
            "route_epoch": "truth-event-current-manuscript",
            "failure_signature": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "owner_reason": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
                ),
            },
            "idempotency_key": "owner-route::003::ai-reviewer::current-manuscript",
        }
    )
    dispatch["owner_route"] = route
    dispatch["prompt_contract"]["owner_route"] = route
    dispatch["prompt_contract"]["idempotency_key"] = route["idempotency_key"]
    dispatch["prompt_contract"]["repeat_suppression_key"] = route["work_unit_fingerprint"]
    dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch)
    stale_scan_route = {
        **route,
        "next_owner": None,
        "allowed_actions": [],
        "blocked_actions": ["return_to_ai_reviewer_workflow"],
        "work_unit_fingerprint": "truth-snapshot::8545ef2695c45d2372522362",
        "source_fingerprint": "truth-snapshot::8545ef2695c45d2372522362",
        "idempotency_key": "owner-route::003::stale-scan-route",
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": stale_scan_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner": "ai_reviewer",
                            "request_owner": "ai_reviewer",
                            "recommended_owner": "ai_reviewer",
                            "owner_route": route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [dispatch],
        },
    )
    called: list[str] = []

    def fake_ai_reviewer_workflow(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_id"]))
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        }

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fake_ai_reviewer_workflow)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "scan_action_queue"
    assert execution["current_owner_route"]["idempotency_key"] == route["idempotency_key"]
    assert called == [study_id]
