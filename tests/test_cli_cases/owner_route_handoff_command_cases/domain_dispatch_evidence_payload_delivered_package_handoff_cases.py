from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_delivered_package_handoff_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_bd88c01254ce30cfe8976f62"
    domain_source = "c7833476a5245c3b"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/"
        "default_executor_dispatches/return_to_ai_reviewer_workflow.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_33404ec000e39379b748d6e4:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_33404ec000e39379b748d6e4",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "return_to_ai_reviewer_workflow",
                "dispatch_authority": "ai_reviewer_record_production_handoff",
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
                    "blocked_reason": "publication_gate_route_back_write_required",
                    "domain_transition": {
                        "decision_type": "delivered_package_handoff",
                        "route_target": "human_gate",
                        "owner": "med-autoscience",
                        "controller_action": "wait_for_human_gate",
                        "source_refs": [
                            "artifacts/publication_eval/latest.json",
                            "artifacts/controller_decisions/latest.json",
                            "artifacts/controller/repair_execution_evidence/latest.json",
                            "artifacts/controller/publication_work_unit_lifecycle/latest.json",
                            "progress_projection",
                            "study_macro_state",
                        ],
                        "typed_blocker": {
                            "blocker_id": "package_delivered_not_publication_authority",
                            "blocker_type": "artifact_authority",
                            "required_owner_surface": "artifact_rebuild_proof",
                            "write_permitted": False,
                        },
                    },
                    "owner_route": {
                        "next_owner": "external_supervisor",
                        "owner_reason": "publication_gate_route_back_write_required",
                        "source_refs": {
                            "work_unit_id": "package_review_handoff",
                            "work_unit_fingerprint": "truth-snapshot::7e654645f2ff5942b1b9e07f",
                            "truth_epoch": "truth-event-000008-907e7cfcb3ca1206",
                            "runtime_health_epoch": "runtime-health-event-006165-5c76075864969e4e",
                            "blocked_reason": "publication_gate_route_back_write_required",
                        },
                        "owner_reason_contract": {
                            "registered": True,
                            "reason": "publication_gate_route_back_write_required",
                            "owner": "write",
                            "allowed_actions": ["run_quality_repair_batch"],
                        },
                        "currentness_contract": {
                            "status": "currentness_basis_required",
                            "missing_required_fields": [],
                        },
                        "owner_route_attempt_protocol": {
                            "dispatchable": False,
                        },
                    },
                    "domain_authority_handoff": {
                        "status": "typed_blocker",
                        "typed_blocker": {
                            "surface_kind": "mas_domain_typed_blocker",
                            "blocker_kind": "owner_route_blocked",
                            "reason": "publication_gate_route_back_write_required",
                            "next_owner": "external_supervisor",
                            "source_fingerprint": "truth-snapshot::7e654645f2ff5942b1b9e07f",
                            "idempotency_key": (
                                f"owner-route::{study_id}::truth-event-000008-907e7cfcb3ca1206::"
                                "external_supervisor::publication_gate_route_back_write_required::88da22"
                            ),
                            "provider_completion_is_domain_completion": False,
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
    assert payload["payload_reason"] == (
        "delivered_package_handoff_typed_blocker_observed_for_default_executor_dispatch"
    )
    assert payload["owner_route_next_owner"] == "external_supervisor"
    assert payload["owner_route_owner_reason"] == "publication_gate_route_back_write_required"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:route_target=human_gate" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=wait_for_human_gate" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:blocked_reason=publication_gate_route_back_write_required" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:owner_route_next_owner=external_supervisor" in record_payload[
        "evidence_refs"
    ]
    assert "domain-authority-handoff:status=typed_blocker" in record_payload["evidence_refs"]
    assert "domain-authority-handoff:typed_blocker_reason=publication_gate_route_back_write_required" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:completion_receipt_consumption=consumed" not in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
