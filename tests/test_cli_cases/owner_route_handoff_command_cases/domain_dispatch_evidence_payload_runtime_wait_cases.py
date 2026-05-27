from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_consumed_ai_reviewer_runtime_wait(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_source = "mas_default_executor_source_d42d6161d143c0c4f0e0c1c3"
    domain_source = "30ec9749a9ca699f"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/return_to_ai_reviewer_workflow.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_7848b377174e9983fac31212:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_7848b377174e9983fac31212",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "nfpitnet",
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
                    "blocked_reason": "quest_waiting_opl_runtime_owner_route",
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
                        "next_owner": "external_supervisor",
                        "owner_reason": "quest_waiting_opl_runtime_owner_route",
                        "allowed_actions": [],
                        "source_refs": {
                            "work_unit_id": (
                                "dm002_current_manuscript_methods_model_reporting_and_package_"
                                "currentness_write_pass"
                            ),
                            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                        },
                        "owner_reason_contract": {
                            "registered": True,
                            "reason": "quest_waiting_opl_runtime_owner_route",
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
        "stale_return_to_ai_reviewer_dispatch_superseded_by_consumed_ai_reviewer_routeback"
    )
    assert payload["owner_route_next_owner"] == "external_supervisor"
    assert payload["owner_route_owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:blocked_reason=quest_waiting_opl_runtime_owner_route" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:owner_route_next_owner=external_supervisor" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_consumed_ai_reviewer_runtime_recovery_guard(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_source = "mas_default_executor_source_8969eb5a7c12f5b3030ba8be"
    domain_source = "3ce2d30996698cb0"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_2cd1d3b6a0c82b8ffddb2066:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_2cd1d3b6a0c82b8ffddb2066",
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
                        "next_owner": "one-person-lab",
                        "owner_reason": "runtime_recovery_not_authorized",
                        "source_refs": {
                            "work_unit_id": (
                                "dm002_current_manuscript_methods_model_reporting_and_package_"
                                "currentness_write_pass"
                            ),
                            "blocked_reason": "runtime_recovery_not_authorized",
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
        "stale_run_quality_repair_dispatch_superseded_by_consumed_ai_reviewer_routeback"
    )
    assert payload["owner_route_next_owner"] == "one-person-lab"
    assert payload["owner_route_owner_reason"] == "runtime_recovery_not_authorized"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:blocked_reason=runtime_recovery_not_authorized" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:owner_route_next_owner=one-person-lab" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_projects_retry_budget_terminal_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_source = "mas_default_executor_source_af944506d7db657a6d560a38"
    domain_source = "3ee722ea3a948ff1"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workorder_path,
        {
            "action_id": "domain_dispatch:medautoscience:sat_7bcf15ad580603c51ed82179:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": "sat_7bcf15ad580603c51ed82179",
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
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
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
                        "next_owner": "one-person-lab",
                        "owner_reason": "runtime_recovery_retry_budget_exhausted",
                        "allowed_actions": [],
                        "source_refs": {
                            "work_unit_id": "current_manuscript_claim_evidence_alignment_repair",
                            "work_unit_fingerprint": "truth-snapshot::b0eaf95e18d325f1048873d4",
                            "truth_epoch": "truth-event-000010-e18716b017085fdf",
                            "runtime_health_epoch": "runtime-health-event-006080-e8cc11fd41f690f9",
                            "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                        },
                        "owner_reason_contract": {
                            "registered": True,
                            "reason": "runtime_recovery_retry_budget_exhausted",
                            "owner": "one-person-lab",
                            "allowed_actions": [],
                        },
                        "currentness_contract": {
                            "status": "currentness_basis_required",
                            "missing_required_fields": [],
                        },
                        "owner_route_attempt_protocol": {
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
    assert payload["payload_reason"] == "runtime_recovery_retry_budget_terminal_blocker"
    assert payload["owner_route_next_owner"] == "one-person-lab"
    assert payload["owner_route_owner_reason"] == "runtime_recovery_retry_budget_exhausted"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "owner-route-reconcile:blocked_reason=runtime_recovery_retry_budget_exhausted" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:owner_route_next_owner=one-person-lab" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
