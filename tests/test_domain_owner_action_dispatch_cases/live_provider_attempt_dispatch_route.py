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


def test_execute_quality_repair_batch_uses_live_provider_attempt_dispatch_route_when_scan_queue_is_empty(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
            ),
            "idempotency_key": "owner-route::dm002::live-provider-current-write-pass",
            "source_refs": {
                "work_unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
                ),
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "next_work_unit": {
            "unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
            "lane": "write",
        },
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
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": {
                        **route,
                        "next_owner": "external_supervisor",
                        "allowed_actions": [],
                        "idempotency_key": "owner-route::dm002::scan-after-provider-admission",
                    },
                    "action_queue": [],
                    "running_provider_attempt": True,
                    "opl_provider_attempt": {
                        "running_provider_attempt": True,
                        "runtime_owner": "one-person-lab",
                        "provider_attempt_owner": "one-person-lab",
                        "queue_owner": "one-person-lab",
                        "executor_kind": "codex_cli",
                        "active_run_id": "opl-stage-attempt://sat-live",
                        "active_stage_attempt_id": "sat-live",
                        "active_workflow_id": "wf-live",
                        "attempt_lease_ref": "opl://stage-attempts/sat-live/leases/current",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
                        "dispatch_ref": (
                            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                            "consumer/default_executor_dispatches/run_quality_repair_batch.json"
                        ),
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "live_provider_attempt_dispatch"
    assert execution["current_owner_route"]["idempotency_key"] == route["idempotency_key"]
    assert called["authority_route_context"]["work_unit_id"] == (
        "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
    )
