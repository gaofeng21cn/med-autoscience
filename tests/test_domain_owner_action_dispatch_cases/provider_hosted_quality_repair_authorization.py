from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_provider_hosted_quality_repair_dispatch_survives_own_running_provider_envelope(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "owner_reason": work_unit_id,
            "failure_signature": "run_quality_repair_batch",
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": work_unit_fingerprint,
            "idempotency_key": f"provider-admission::{study_id}::{work_unit_fingerprint}",
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-event-000032",
                    "runtime_health_epoch": "runtime-health-event-006603",
                    "source_eval_id": "publication-eval::dm003::current",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
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
    dispatch["prompt_contract"].pop("opl_execution_authorization", None)
    dispatch["prompt_contract"]["owner_route"] = route
    dispatch["prompt_contract"]["owner_route_currentness_basis"] = route["source_refs"][
        "owner_route_currentness_basis"
    ]
    dispatch["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "next_work_unit": {"unit_id": work_unit_id, "lane": "write"},
        "work_unit_fingerprint": work_unit_fingerprint,
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat-provider-hosted-quality-repair")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "opl://stage-attempts/sat-provider-hosted-quality-repair")
    monkeypatch.setenv(
        "OPL_ATTEMPT_LEASE_REF",
        "opl://stage-attempts/sat-provider-hosted-quality-repair/leases/frt-provider-hosted-quality-repair/active",
    )
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://stage-attempts/sat-provider-hosted-quality-repair/execution-authorizations/current",
    )
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", "run_quality_repair_batch")
    monkeypatch.setenv("OPL_WORK_UNIT_ID", work_unit_id)
    monkeypatch.setenv("OPL_TASK_ID", "frt-provider-hosted-quality-repair")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "active_run_id": "opl-stage-attempt://sat-provider-hosted-quality-repair",
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "one-person-lab",
                "next_work_unit": "sat-provider-hosted-quality-repair",
            },
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {"study_id": study_id, "quest_id": study_id, "quest_root": str(quest_root)},
    )
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

    assert result["executed_count"] == 1, result
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["owner_route_current"] is True
    assert called["authority_route_context"]["work_unit_id"] == work_unit_id
