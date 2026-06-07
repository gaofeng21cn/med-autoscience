from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_uses_pending_ai_reviewer_request_when_scan_route_loses_owner_reason(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
            "truth_epoch": "truth-event-000010",
            "route_epoch": "truth-event-000010",
            "runtime_health_epoch": "runtime-health-event-005991-old",
            "work_unit_fingerprint": "truth-snapshot::9f2bb69281c7a1139cadf9c7",
            "source_fingerprint": "truth-snapshot::9f2bb69281c7a1139cadf9c7",
            "failure_signature": "ai_reviewer_assessment_required",
            "owner_reason": "ai_reviewer_assessment_required",
            "trace_id": "owner-route-trace::ai-reviewer-request",
        }
    )
    route["idempotency_key"] = (
        "owner-route::003::truth-event-000010::ai_reviewer::"
        "ai_reviewer_assessment_required::62865bff6e21564f"
    )
    dispatch_payload = _dispatch(
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
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "ai_reviewer_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested"},
        },
    )
    stale_scan_route = {
        **route,
        "runtime_health_epoch": "runtime-health-event-005991-new",
        "failure_signature": None,
        "owner_reason": None,
        "next_owner": None,
        "allowed_actions": [],
        "blocked_actions": ["return_to_ai_reviewer_workflow", "run_quality_repair_batch"],
        "idempotency_key": "owner-route::003::truth-event-000010::none::none::ce59b7999efe6df2",
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
                    "ai_reviewer_assessment": {
                        "present": False,
                        "missing": True,
                        "request_state": "requested",
                    },
                    "paper_progress_stall": {
                        "surface_kind": "paper_progress_stall",
                        "stalled": True,
                        "terminal": True,
                        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
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
        }

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fake_execute_ai_reviewer_workflow)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "owner_request"
    assert called["study_id"] == study_id
