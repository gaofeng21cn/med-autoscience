from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_selects_same_tick_gate_clearing_owner_request_when_scan_lags(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    quest_root.mkdir(parents=True, exist_ok=True)
    current_route = _owner_route(study_id=study_id, action_type="return_to_ai_reviewer_workflow", owner="ai_reviewer")
    current_route.update(
        {
            "quest_id": study_id,
            "allowed_actions": [],
            "blocked_actions": ["run_gate_clearing_batch", "return_to_ai_reviewer_workflow"],
            "owner_reason": "domain_transition_ai_reviewer_re_eval",
            "failure_signature": "domain_transition_ai_reviewer_re_eval",
            "truth_epoch": "truth-event-000022",
            "runtime_health_epoch": "runtime-health-event-006275",
            "work_unit_fingerprint": "truth-snapshot::current-reviewer-record",
            "source_fingerprint": "truth-snapshot::current-reviewer-record",
            "idempotency_key": "owner-route::003::ai-reviewer-current",
        }
    )
    gate_route = _owner_route(study_id=study_id, action_type="run_gate_clearing_batch", owner="gate_clearing_batch")
    gate_refs = {
        "blocked_reason": "current_package_freshness_required",
        "bridge_authority": "domain_action_request_materializer_publication_owner_bridge",
        "bridged_from_owner_reason": "domain_transition_ai_reviewer_re_eval",
        "bridged_from_idempotency_key": current_route["idempotency_key"],
        "materialized_from_action_type": "return_to_ai_reviewer_workflow",
        "materialized_work_unit_id": "current_package_freshness_required",
        "runtime_health_epoch": "runtime-health-event-006275",
        "source_eval_id": "publication-eval::003::current",
        "truth_epoch": "truth-event-000022",
        "work_unit_fingerprint": "truth-snapshot::current-reviewer-record",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
    }
    gate_route.update(
        {
            "quest_id": study_id,
            "truth_epoch": "truth-event-000022",
            "runtime_health_epoch": "runtime-health-event-006275",
            "work_unit_fingerprint": "truth-snapshot::current-reviewer-record",
            "source_fingerprint": "truth-snapshot::current-reviewer-record",
            "owner_reason": "current_package_freshness_required",
            "failure_signature": "current_package_freshness_required",
            "idempotency_key": "owner-route::003::gate-clearing-same-tick",
            "source_refs": gate_refs,
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=gate_route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_gate_clearing_batch",
        "controller_work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "materialization_decision": "current_package_freshness_required",
        "source_eval_id": "publication-eval::003::current",
    }
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "gate_clearing_batch" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "run_gate_clearing_batch",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "gate_clearing_batch",
            "expected_owner": "gate_clearing_batch",
            "next_executable_owner": "gate_clearing_batch",
            "owner_route": gate_route,
        },
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": study_id, "owner_route": current_route}],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {"study_id": study_id, "quest_id": study_id, "quest_root": str(quest_root)},
    )
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_gate_clearing_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    summary = result["per_study_execution_summary"][0]
    assert summary["selected_dispatch_count"] == 1
    assert summary["zero_dispatch_reason"] is None
    execution = result["executions"][0]
    assert execution["owner_route_basis"] == "owner_request"
    assert execution["owner_route_current"] is True
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert called["study_id"] == study_id
