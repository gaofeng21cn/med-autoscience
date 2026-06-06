from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_provider_hosted_stage_attempt_identity_authorizes_gate_clearing_batch_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    route = _owner_route(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
    )
    route.update(
        {
            "owner_reason": "publication_gate_replay_after_clean_migration",
            "failure_signature": "publication_gate_replay_after_clean_migration",
            "source_refs": {
                "work_unit_id": "publication_gate_replay_after_clean_migration",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::publication_gate_replay_after_clean_migration",
                "study_truth_epoch": "truth-event-dm002",
                "runtime_health_epoch": "runtime-health-event-dm002",
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-event-dm002",
                    "runtime_health_epoch": "runtime-health-event-dm002",
                    "source_eval_id": "publication-eval::dm002::current",
                    "work_unit_id": "publication_gate_replay_after_clean_migration",
                    "work_unit_fingerprint": "domain-transition::route_back_same_line::publication_gate_replay_after_clean_migration",
                },
            },
        }
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch.pop("opl_execution_authorization", None)
    dispatch["prompt_contract"].pop("opl_execution_authorization", None)
    dispatch["prompt_contract"]["owner_route"] = route
    dispatch["prompt_contract"]["owner_route_currentness_basis"] = route["source_refs"][
        "owner_route_currentness_basis"
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "immutable"
        / "run_gate_clearing_batch"
        / "provider-hosted.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat-provider-hosted-gate-clearing")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "opl://stage-attempts/sat-provider-hosted-gate-clearing")
    monkeypatch.setenv(
        "OPL_ATTEMPT_LEASE_REF",
        "opl://stage-attempts/sat-provider-hosted-gate-clearing/leases/frt-provider-hosted-gate-clearing/active",
    )
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://stage-attempts/sat-provider-hosted-gate-clearing/execution-authorizations/frt-provider-hosted-gate-clearing/current",
    )
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(dispatch_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", "run_gate_clearing_batch")
    monkeypatch.setenv("OPL_WORK_UNIT_ID", "publication_gate_replay_after_clean_migration")
    monkeypatch.setenv("OPL_TASK_ID", "frt-provider-hosted-gate-clearing")
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
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        }

    monkeypatch.setattr(module.action_execution.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_gate_clearing_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1, result
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "gate_clearing_batch.run_gate_clearing_batch"
    assert execution["owner_route_basis"] == "scan_latest"
    assert called["study_id"] == study_id
    route_context = called["authority_route_context"]["controller_route_context"]
    assert route_context["work_unit_id"] == "publication_gate_replay_after_clean_migration"
