from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_stale_writer_supersession(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_2d2016c043571616bc488132"
    domain_source = "7e021b878296c1fc"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_e4d0fb9ccbcce9225b25f754",
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
        assert study_ids == (study_id,)
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "ai_reviewer_status": {
                        "status": "trace_missing",
                        "owner": "ai_reviewer",
                        "trace_complete": False,
                        "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                    },
                    "domain_transition": {
                        "decision_type": "ai_reviewer_re_eval",
                        "route_target": "review",
                        "owner": "ai_reviewer",
                        "controller_action": "return_to_ai_reviewer_workflow",
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
                        "next_owner": "ai_reviewer",
                        "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
                        "source_refs": {
                            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
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
        "stale_run_quality_repair_dispatch_superseded_by_ai_reviewer_currentness_route"
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=return_to_ai_reviewer_workflow" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:owner_route_next_owner=ai_reviewer" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_publication_gate_route_with_domain_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_fa9247a8faa6af24c39af2f1"
    domain_source = "8720c3edc2c8e258"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_e21cc5d7afb36b92cb6239bd:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_e21cc5d7afb36b92cb6239bd",
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
                    "blocked_reason": "runtime_recovery_not_authorized",
                    "domain_transition": {
                        "decision_type": "publication_gate_blocker",
                        "route_target": "review",
                        "owner": "publication_gate",
                        "controller_action": "run_gate_clearing_batch",
                        "source_refs": [
                            "artifacts/publication_eval/latest.json",
                            "artifacts/controller_decisions/latest.json",
                            "artifacts/controller/repair_execution_evidence/latest.json",
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
                        "next_owner": "one-person-lab",
                        "owner_reason": "runtime_recovery_not_authorized",
                        "source_fingerprint": "truth-snapshot::f0131cb0281c135e7390717f",
                        "idempotency_key": (
                            "owner-route::003-dpcc-primary-care-phenotype-treatment-gap::"
                            "truth-event-000010-e18716b017085fdf::one-person-lab::"
                            "runtime_recovery_not_authorized::80d5113e67d153da"
                        ),
                        "source_refs": {
                            "study_truth_epoch": "truth-event-000010-e18716b017085fdf",
                            "runtime_health_epoch": "runtime-health-event-006092-68bc2476344e7e8d",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": "truth-snapshot::f0131cb0281c135e7390717f",
                            "blocked_reason": "runtime_recovery_not_authorized",
                            "publication_eval_path": (
                                "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                                "artifacts/publication_eval/latest.json"
                            ),
                            "owner_route_currentness_basis": {
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": "truth-snapshot::f0131cb0281c135e7390717f",
                                "truth_epoch": "truth-event-000010-e18716b017085fdf",
                                "runtime_health_epoch": "runtime-health-event-006092-68bc2476344e7e8d",
                                "owner_reason": "runtime_recovery_not_authorized",
                            },
                        },
                        "owner_reason_contract": {
                            "registered": True,
                            "reason": "runtime_recovery_not_authorized",
                            "owner": "one-person-lab",
                            "allowed_actions": [],
                            "required_output": "OPL stage attempt admission or typed blocker",
                        },
                        "currentness_contract": {
                            "status": "currentness_basis_required",
                            "missing_required_fields": [],
                            "fail_closed_when_missing": True,
                        },
                        "owner_route_attempt_protocol": {
                            "version": "mas-owner-route-attempt-protocol.v1",
                            "dispatchable": False,
                            "runtime_completion_guard": {
                                "provider_completion_is_domain_completion": False,
                                "queue_succeeded_is_domain_completion": False,
                            },
                        },
                    },
                    "domain_authority_handoff": {
                        "surface_kind": "mas_domain_authority_handoff",
                        "status": "typed_blocker",
                        "typed_blocker": {
                            "surface_kind": "mas_domain_typed_blocker",
                            "blocker_kind": "owner_route_blocked",
                            "reason": "runtime_recovery_not_authorized",
                            "next_owner": "one-person-lab",
                            "source_fingerprint": "truth-snapshot::f0131cb0281c135e7390717f",
                            "idempotency_key": (
                                "owner-route::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "truth-event-000010-e18716b017085fdf::one-person-lab::"
                                "runtime_recovery_not_authorized::80d5113e67d153da"
                            ),
                            "provider_completion_is_domain_completion": False,
                        },
                        "opl_control_plane": {
                            "runtime_control_owner": "one-person-lab",
                            "hydrate_owner_route_refs": True,
                            "provider_completion_is_domain_completion": False,
                            "queue_succeeded_is_domain_completion": False,
                            "stage_attempt_state_owned_by_mas": False,
                        },
                        "authority": {
                            "kind": "domain_authority_refs_only_handoff",
                            "writes_runtime_attempt_state": False,
                            "owns_generic_queue": False,
                            "owns_retry_dead_letter": False,
                            "quality_ready_authorized": False,
                            "publication_ready_authorized": False,
                            "submission_ready_authorized": False,
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
        "stale_run_quality_repair_dispatch_superseded_by_publication_gate_route"
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=run_gate_clearing_batch" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:blocked_reason=runtime_recovery_not_authorized" in record_payload[
        "evidence_refs"
    ]
    assert "domain-authority-handoff:status=typed_blocker" in record_payload["evidence_refs"]
    assert (
        "domain-authority-handoff:typed_blocker_reason=runtime_recovery_not_authorized"
        in record_payload["evidence_refs"]
    )
    assert "domain-authority-handoff:owner_route_attempt_dispatchable=false" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
