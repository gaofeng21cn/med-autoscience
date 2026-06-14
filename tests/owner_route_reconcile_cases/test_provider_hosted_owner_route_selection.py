from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile


def test_provider_hosted_stage_attempt_uses_bound_dispatch_owner_route_when_scan_lacks_route(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.owner_route_selection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_gate_clearing_batch/203c0b81fd948c1ceb0b990e.json"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
        "route_epoch": "truth-event-000035-39f0b8e96689a623",
        "runtime_health_epoch": "runtime-health-event-006850-e3a5043498d31d6b",
        "source_fingerprint": "truth-snapshot::c78cd0944ae1b634479109b1",
        "work_unit_fingerprint": "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9",
        "current_owner": "controller_stop",
        "next_owner": "gate_clearing_batch",
        "owner_reason": "repair_progress_gate_replay_required",
        "failure_signature": "repair_progress_gate_replay_required",
        "allowed_actions": ["run_gate_clearing_batch"],
        "blocked_actions": ["run_quality_repair_batch"],
        "idempotency_key": f"owner-route::{study_id}::gate_clearing_batch::repair_progress_gate_replay_required",
        "source_refs": {
            "study_truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006850-e3a5043498d31d6b",
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
            ),
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": (
                "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
            ),
            "blocked_reason": "repair_progress_gate_replay_required",
        },
        "owner_route_attempt_protocol": {
            "dispatchable": True,
        },
    }
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "next_executable_owner": "gate_clearing_batch",
        "dispatch_status": "ready",
        "executor_kind": "codex_cli_default",
        "owner_route": owner_route,
        "prompt_contract": {"owner_route": owner_route},
        "refs": {
            "stage_packet_path": str(tmp_path / stage_packet_ref),
            "immutable_dispatch_path": str(tmp_path / stage_packet_ref),
        },
    }
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat_bb3fa22e4d97294b86998d7f")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", stage_packet_ref)
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", "run_gate_clearing_batch")
    monkeypatch.setenv("OPL_WORK_UNIT_ID", "publication_gate_replay")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "temporal://attempt/sat_bb3fa22e4d97294b86998d7f")
    monkeypatch.setenv(
        "OPL_ATTEMPT_LEASE_REF",
        "opl://stage-attempts/sat_bb3fa22e4d97294b86998d7f/leases/frt_5fb72b39ce0347285ab6fc50/active",
    )
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://stage-attempts/sat_bb3fa22e4d97294b86998d7f/execution-authorizations/frt_5fb72b39ce0347285ab6fc50/wf_0cb2784befebf25b00adaa83",
    )

    selected_route, basis = module.execution_owner_route(
        profile=profile,
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        dispatch=dispatch,
        scan_payload={"studies": [{"study_id": study_id}]},
        fresh_progress={},
    )

    assert basis == "provider_hosted_stage_attempt_dispatch"
    assert selected_route["idempotency_key"] == owner_route["idempotency_key"]
    assert selected_route["allowed_actions"] == ["run_gate_clearing_batch"]
