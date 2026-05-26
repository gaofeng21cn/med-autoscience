from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_stage_attempt_closeout_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = "sat_9c4ab82e4e1fdef49b662c54"
    stage_attempt_source = "mas_default_executor_source_5e75b4fe5fdc3311bffba5c5"
    domain_source = "6dc238f98af6b118"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        f"default_executor_execution/{stage_attempt_id}.closeout.json"
    )
    typed_blocker_ref = (
        "artifacts/supervision/opl_current_control_state/latest.json#/studies/0/"
        "domain_authority_handoff/typed_blocker"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "status": "blocked",
            "blocked_reason": "owner_route_blocked",
            "domain_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "blocker_kind": "owner_route_blocked",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "next_owner": "external_supervisor",
                "provider_completion_is_domain_completion": False,
            },
            "execution_observation": {
                "execution_status": "blocked",
                "blocked_reason": "current_owner_route_missing",
                "owner_route_current": False,
            },
            "closeout_refs": [
                closeout_ref,
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/default_executor_execution/latest.json",
                dispatch_ref,
                "artifacts/supervision/opl_current_control_state/latest.json",
            ],
            "typed_blocker_ref": typed_blocker_ref,
            "owner_receipt_ref": None,
            "provider_completion_is_domain_completion": False,
        },
    )
    workorder_path = tmp_path / "opl-workorder.json"
    _write_json(
        workorder_path,
        {
            "action_id": f"domain_dispatch:medautoscience:{stage_attempt_id}:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": stage_attempt_id,
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "nfpitnet",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                        },
                    },
                    "owner_route": {
                        "next_owner": "external_supervisor",
                        "owner_reason": "quest_waiting_opl_runtime_owner_route",
                    },
                }
            ]
        }

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "domain-handler",
            "dispatch-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "typed_blocker_payload_ready"
    assert payload["payload_reason"] == (
        "stage_attempt_closeout_typed_blocker_observed_for_default_executor_dispatch"
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"] == [typed_blocker_ref]
    assert closeout_ref in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:blocked_reason=owner_route_blocked" in record_payload[
        "evidence_refs"
    ]
    assert "stage-attempt-closeout:execution_blocked_reason=current_owner_route_missing" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
