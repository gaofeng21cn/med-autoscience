from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_writer_superseded_by_live_opl_attempt(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_7dcbfcba3dc2f3125396f843"
    domain_source = "eb9b8583e212202d"
    active_stage_attempt_id = "sat_89a010952de78ebc8abb3ed2"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/run_quality_repair_batch/"
        "66c1b9e8b47f5b8b2e286752.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_f3fd1e7d225e41af1c84c24d:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_f3fd1e7d225e41af1c84c24d",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        assert study_ids == (study_id,)
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": None,
                    "active_stage_attempt_id": active_stage_attempt_id,
                    "running_provider_attempt": True,
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "source_refs": [
                            "artifacts/publication_eval/latest.json",
                            "artifacts/controller_decisions/latest.json",
                        ],
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": "artifacts/publication_eval/latest.json",
                            "reviewer_trace_ref": (
                                "artifacts/publication_eval/latest.json#reviewer_operating_system"
                            ),
                        },
                    },
                    "owner_route": {
                        "current_owner": "mas_controller",
                        "next_owner": None,
                        "owner_reason": None,
                        "source_refs": {
                            "work_unit_id": "medical_prose_currentness_recheck",
                            "work_unit_fingerprint": "truth-snapshot::6b6e137d06954def841a8839",
                            "truth_epoch": "truth-event-000020-aad9bf065035c134",
                            "runtime_health_epoch": "runtime-health-event-006219-72570b0468728033",
                        },
                        "owner_reason_contract": {
                            "registered": False,
                            "reason": None,
                            "owner": None,
                            "allowed_actions": [],
                        },
                        "currentness_contract": {
                            "status": "currentness_basis_required",
                            "missing_required_fields": [],
                        },
                        "owner_route_attempt_protocol": {
                            "version": "mas-owner-route-attempt-protocol.v1",
                            "dispatchable": False,
                        },
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
    assert_stable_blocker_reason(
        payload,
        blocker_class="dispatch_superseded_by_current_owner_route",
        detail_reason="stale_run_quality_repair_dispatch_superseded_by_consumed_ai_reviewer_routeback",
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert f"opl-provider-attempt:active_stage_attempt_id={active_stage_attempt_id}" in record_payload[
        "evidence_refs"
    ]
    assert "opl-provider-attempt:running_provider_attempt=true" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=request_opl_stage_attempt" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
