from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_consumed_ai_reviewer_finalize_gate_replay(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_905e4f39202687eb5402610c"
    domain_source = "dpcc-current-ai-reviewer-finalize-gate-replay"
    receipt_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/publication_eval/"
        "ai_reviewer_responses/20260601T132728Z_publication_eval_record.json"
    )
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/"
        "default_executor_dispatches/immutable/run_quality_repair_batch/"
        "6eda3ebc7cf8086a654a4685.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_905e4f39202687eb5402610c:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_905e4f39202687eb5402610c",
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
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "finalize",
                        "owner": "finalize",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                        },
                        "source_refs": [
                            receipt_ref,
                            "artifacts/controller_decisions/latest.json",
                            "artifacts/controller/repair_execution_evidence/latest.json",
                        ],
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": receipt_ref,
                            "reviewer_trace_ref": f"{receipt_ref}#reviewer_operating_system",
                        },
                    },
                    "owner_route": {
                        "next_owner": None,
                        "owner_reason": None,
                        "currentness_contract": {
                            "status": "currentness_basis_required",
                            "missing_required_fields": [],
                        },
                        "owner_route_attempt_protocol": {
                            "version": "mas-owner-route-attempt-protocol.v1",
                            "dispatchable": False,
                        },
                    },
                    "domain_authority_handoff": {
                        "surface_kind": "mas_domain_authority_handoff",
                        "status": "owner_route_ready",
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
        blocker_class="publication_gate_supersession_blocked",
        detail_reason="stale_run_quality_repair_dispatch_superseded_by_publication_gate_route",
    )
    assert payload["owner_route_next_owner"] is None
    assert payload["owner_route_owner_reason"] is None
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert record_payload["no_regression_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:completion_receipt_consumption=consumed" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:route_target=finalize" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=request_opl_stage_attempt" in record_payload[
        "evidence_refs"
    ]
    assert "domain-authority-handoff:status=typed_blocker" not in record_payload["evidence_refs"]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
