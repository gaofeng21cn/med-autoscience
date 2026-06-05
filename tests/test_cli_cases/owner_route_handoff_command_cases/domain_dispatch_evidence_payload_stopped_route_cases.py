from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_stopped_owner_route_blocks_stale_dispatch(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_source = "mas_default_executor_source_9de5a65c139c09d661417f1d"
    domain_source = "802a9fc19d285178"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/immutable/run_quality_repair_batch/c8d6ba3192e1b684c49f88fd.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_187bca513e83d3bd30ffd208:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_187bca513e83d3bd30ffd208",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_authority": "consumer_default_executor_dispatch",
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
                    "domain_transition": None,
                    "owner_route": {
                        "current_owner": "controller_stop",
                        "next_owner": None,
                        "owner_reason": None,
                        "allowed_actions": [],
                        "blocked_actions": [
                            "return_to_ai_reviewer_workflow",
                            "run_quality_repair_batch",
                            "run_gate_clearing_batch",
                        ],
                        "source_refs": {
                            "study_truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
                            "runtime_health_epoch": "runtime-health-event-006635-f57a202d5720ded3",
                            "work_unit_fingerprint": "truth-snapshot::68752759d1bae2ba81621424",
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
                            "runtime_completion_guard": {
                                "provider_completion_is_domain_completion": False,
                                "queue_succeeded_is_domain_completion": False,
                            },
                        },
                    },
                    "domain_authority_handoff": {
                        "surface_kind": "mas_domain_authority_handoff",
                        "status": "owner_route_ready",
                        "typed_blocker": None,
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
        detail_reason="stale_run_quality_repair_dispatch_blocked_by_stopped_current_owner_route",
    )
    assert payload["owner_route_next_owner"] is None
    assert payload["owner_route_owner_reason"] is None
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:current_owner=controller_stop" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:blocked_action=run_quality_repair_batch" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:owner_route_next_owner=None" not in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_gate_clearing_dispatch_under_publication_gate_route(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_f93aab8c22b31cdbc78ecbe3"
    domain_source = "d47147484d17a585"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/run_gate_clearing_batch/"
        "06d91f72ce7196481d348691.json"
    )
    receipt_ref = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
        "publication_eval/ai_reviewer_responses/20260605T080613Z_publication_eval_record.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_42941d4a0235b1e977e82672:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_42941d4a0235b1e977e82672",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "run_gate_clearing_batch",
                "dispatch_authority": "consumer_default_executor_dispatch",
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
                        ],
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": receipt_ref,
                            "reviewer_trace_ref": f"{receipt_ref}#reviewer_operating_system",
                        },
                    },
                    "owner_route": {
                        "current_owner": "controller_stop",
                        "next_owner": None,
                        "owner_reason": None,
                        "allowed_actions": [],
                        "blocked_actions": [
                            "return_to_ai_reviewer_workflow",
                            "run_quality_repair_batch",
                            "run_gate_clearing_batch",
                        ],
                        "source_refs": {
                            "source_eval_id": (
                                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "ai-reviewer-record::20260605T080529Z"
                            ),
                            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "work_unit_fingerprint": "truth-snapshot::4076096b79dd1629df61c406",
                            "truth_epoch": "truth-event-000027-22af45131c3e612e",
                            "runtime_health_epoch": "runtime-health-event-006429-ec7b7ee1bc2cf216",
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
        detail_reason="stale_run_gate_clearing_dispatch_superseded_by_publication_gate_route",
    )
    assert payload["owner_route_next_owner"] is None
    assert payload["owner_route_owner_reason"] is None
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert receipt_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:route_target=finalize" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=request_opl_stage_attempt" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:blocked_action=run_gate_clearing_batch" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_reviewer_dispatch_under_finalize_gate_replay(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_e33ede855775529204635536"
    domain_source = "4a2498cffc8ea01d"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/return_to_ai_reviewer_workflow/"
        "80a9f92c4c585cd3b5897d9b.json"
    )
    receipt_ref = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
        "publication_eval/ai_reviewer_responses/20260605T080613Z_publication_eval_record.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_bad4c817e26e9aff5f374c46:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_bad4c817e26e9aff5f374c46",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "return_to_ai_reviewer_workflow",
                "dispatch_authority": "consumer_default_executor_dispatch",
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
                        ],
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": receipt_ref,
                            "reviewer_trace_ref": f"{receipt_ref}#reviewer_operating_system",
                        },
                    },
                    "owner_route": {
                        "current_owner": "controller_stop",
                        "next_owner": None,
                        "owner_reason": None,
                        "allowed_actions": [],
                        "blocked_actions": [
                            "return_to_ai_reviewer_workflow",
                            "run_quality_repair_batch",
                            "run_gate_clearing_batch",
                        ],
                        "source_refs": {
                            "source_eval_id": (
                                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "ai-reviewer-record::20260605T080529Z"
                            ),
                            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "work_unit_fingerprint": "truth-snapshot::4076096b79dd1629df61c406",
                            "truth_epoch": "truth-event-000027-22af45131c3e612e",
                            "runtime_health_epoch": "runtime-health-event-006429-ec7b7ee1bc2cf216",
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
        detail_reason="stale_return_to_ai_reviewer_dispatch_superseded_by_publication_gate_route",
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert receipt_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:route_target=finalize" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=request_opl_stage_attempt" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:blocked_action=return_to_ai_reviewer_workflow" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
