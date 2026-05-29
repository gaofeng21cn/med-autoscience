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
    assert_stable_blocker_reason(
        payload,
        blocker_class="dispatch_superseded_by_current_owner_route",
        detail_reason="stale_run_quality_repair_dispatch_superseded_by_ai_reviewer_currentness_route",
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


def test_domain_handler_dispatch_evidence_payload_projects_stale_writer_supervisor_only_currentness(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_source = "mas_default_executor_source_74e5e16f1fa98f17c8b4bc57"
    domain_source = "ef567840cec9a22a"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_d9ad53e32adb615176f082fe:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_d9ad53e32adb615176f082fe",
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
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
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
                        "next_owner": "supervisor_only/live_quality_repair",
                        "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
                        "source_refs": {
                            "work_unit_id": (
                                "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
                            ),
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
    assert_stable_blocker_reason(
        payload,
        blocker_class="dispatch_superseded_by_current_owner_route",
        detail_reason="stale_run_quality_repair_dispatch_superseded_by_ai_reviewer_currentness_route",
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:owner_route_next_owner=supervisor_only/live_quality_repair" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_writer_superseded_by_ai_reviewer_stage_admission(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_source = "mas_default_executor_source_74e5e16f1fa98f17c8b4bc57"
    domain_source = "ef567840cec9a22a"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_d9ad53e32adb615176f082fe:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_d9ad53e32adb615176f082fe",
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
                    "blocked_reason": "opl_stage_attempt_admission_required",
                    "domain_transition": {
                        "decision_type": "ai_reviewer_re_eval",
                        "route_target": "review",
                        "owner": "ai_reviewer",
                        "controller_action": "return_to_ai_reviewer_workflow",
                        "source_refs": [
                            "artifacts/publication_eval/latest.json",
                            "artifacts/controller_decisions/latest.json",
                            "artifacts/supervision/requests/ai_reviewer/latest.json",
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
                        "owner_reason": "opl_stage_attempt_admission_required",
                        "source_refs": {
                            "work_unit_id": (
                                "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
                            ),
                            "work_unit_fingerprint": "truth-snapshot::e367d4426f64cea0a4917de0",
                            "truth_epoch": "truth-event-000024-daa5883571a64a07",
                            "runtime_health_epoch": "runtime-health-event-006324-dd1ec9d786f62191",
                            "blocked_reason": "opl_stage_attempt_admission_required",
                        },
                        "owner_reason_contract": {
                            "registered": False,
                            "reason": "opl_stage_attempt_admission_required",
                            "owner": "one-person-lab",
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
        detail_reason="stale_run_quality_repair_dispatch_superseded_by_current_ai_reviewer_stage_admission",
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:route_target=review" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=return_to_ai_reviewer_workflow" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:owner_route_next_owner=one-person-lab" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


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
    assert_stable_blocker_reason(
        payload,
        blocker_class="publication_gate_supersession_blocked",
        detail_reason="stale_run_quality_repair_dispatch_superseded_by_publication_gate_route",
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


def test_domain_handler_dispatch_evidence_payload_projects_writer_dispatch_under_owner_authorized_gate_replay(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_ad2f96eb01cacc2be523c1a2"
    domain_source = "f81029cf9856d775"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_95ec3c7ef26d29ea7208715a:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_95ec3c7ef26d29ea7208715a",
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
                    "blocked_reason": "owner_authorized_publication_gate_replay",
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "finalize",
                        "owner": "finalize",
                        "controller_action": "request_opl_stage_attempt",
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
                        "next_owner": "external_supervisor",
                        "owner_reason": "owner_authorized_publication_gate_replay",
                        "allowed_actions": [],
                        "source_refs": {
                            "work_unit_id": "owner_authorized_publication_gate_replay",
                            "work_unit_fingerprint": "truth-snapshot::0207cd84d518447fa5e4e08c",
                            "truth_epoch": "truth-event-000008-907e7cfcb3ca1206",
                            "runtime_health_epoch": "runtime-health-event-006112-265d50ac109175b6",
                            "blocked_reason": "owner_authorized_publication_gate_replay",
                        },
                        "owner_reason_contract": {
                            "registered": True,
                            "reason": "owner_authorized_publication_gate_replay",
                            "owner": "gate_clearing_batch",
                            "allowed_actions": [
                                "run_gate_clearing_batch",
                            ],
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
                    "domain_authority_handoff": {
                        "surface_kind": "mas_domain_authority_handoff",
                        "status": "typed_blocker",
                        "typed_blocker": {
                            "surface_kind": "mas_domain_typed_blocker",
                            "blocker_kind": "owner_route_blocked",
                            "reason": "owner_authorized_publication_gate_replay",
                            "next_owner": "external_supervisor",
                            "source_fingerprint": "truth-snapshot::0207cd84d518447fa5e4e08c",
                            "idempotency_key": (
                                "owner-route::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "truth-event-000008-907e7cfcb3ca1206::external_supervisor::"
                                "owner_authorized_publication_gate_replay::a26fd6bb3b6d2240"
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
    assert_stable_blocker_reason(
        payload,
        blocker_class="publication_gate_supersession_blocked",
        detail_reason="owner_authorized_publication_gate_replay_stage_attempt_blocker",
    )
    assert payload["owner_route_next_owner"] == "external_supervisor"
    assert payload["owner_route_owner_reason"] == "owner_authorized_publication_gate_replay"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:route_target=finalize" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:blocked_reason=owner_authorized_publication_gate_replay" in record_payload[
        "evidence_refs"
    ]
    assert "domain-authority-handoff:status=typed_blocker" in record_payload["evidence_refs"]
    assert (
        "domain-authority-handoff:typed_blocker_reason=owner_authorized_publication_gate_replay"
        in record_payload["evidence_refs"]
    )
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_stale_reviewer_dispatch_under_publication_gate_route(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_fef44d912fde9f1941ba47b5"
    domain_source = "6a4b1a112aca4016"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/return_to_ai_reviewer_workflow.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_187a069929581c8796342e10:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_187a069929581c8796342e10",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "return_to_ai_reviewer_workflow",
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
                        "source_fingerprint": "truth-snapshot::f4109e60379e665074330a51",
                        "idempotency_key": (
                            "owner-route::003-dpcc-primary-care-phenotype-treatment-gap::"
                            "truth-event-000010-e18716b017085fdf::one-person-lab::"
                            "runtime_recovery_not_authorized::ceeb63a208e7892a"
                        ),
                        "source_refs": {
                            "study_truth_epoch": "truth-event-000010-e18716b017085fdf",
                            "runtime_health_epoch": "runtime-health-event-006102-eefb741d529ce7d5",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": "truth-snapshot::f4109e60379e665074330a51",
                            "blocked_reason": "runtime_recovery_not_authorized",
                            "publication_eval_path": (
                                "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                                "artifacts/publication_eval/latest.json"
                            ),
                            "owner_route_currentness_basis": {
                                "work_unit_id": "publication_gate_replay",
                                "work_unit_fingerprint": "truth-snapshot::f4109e60379e665074330a51",
                                "truth_epoch": "truth-event-000010-e18716b017085fdf",
                                "runtime_health_epoch": "runtime-health-event-006102-eefb741d529ce7d5",
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
                            "source_fingerprint": "truth-snapshot::f4109e60379e665074330a51",
                            "idempotency_key": (
                                "owner-route::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "truth-event-000010-e18716b017085fdf::one-person-lab::"
                                "runtime_recovery_not_authorized::ceeb63a208e7892a"
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
    assert_stable_blocker_reason(
        payload,
        blocker_class="publication_gate_supersession_blocked",
        detail_reason="stale_return_to_ai_reviewer_dispatch_superseded_by_publication_gate_route",
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
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
