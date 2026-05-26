from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_consumed_ai_reviewer_supersession(
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
                "dispatch_authority": "ai_reviewer_medical_prose_review_production_handoff",
                "dispatch_ref": dispatch_ref,
            },
            "required_evidence_refs": [
                "domain_dispatch:medautoscience:sat_7848b377174e9983fac31212:"
                "owner_receipt_or_typed_blocker"
            ],
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        assert profile.name == "nfpitnet"
        assert study_ids == (study_id,)
        assert apply_safe_actions is False
        assert developer_supervisor_mode is None
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": "opl_stage_attempt_admission_required",
                    "ai_reviewer_status": {
                        "status": "present",
                        "owner": "ai_reviewer",
                        "trace_complete": True,
                    },
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
                                "artifacts/publication_eval/latest.json#reviewer_trace"
                            ),
                            "next_action": "honor_ai_reviewer_publication_eval_authority",
                        },
                    },
                    "owner_route": {
                        "next_owner": "one-person-lab",
                        "owner_reason": "opl_stage_attempt_admission_required",
                        "source_refs": {
                            "work_unit_id": "dm002_current_manuscript_write_pass",
                            "blocked_reason": "opl_stage_attempt_admission_required",
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
    assert payload["surface_kind"] == "mas_domain_dispatch_evidence_payload_export"
    assert payload["status"] == "typed_blocker_payload_ready"
    assert payload["payload_reason"] == (
        "stale_return_to_ai_reviewer_dispatch_superseded_by_consumed_ai_reviewer_routeback"
    )
    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
    assert evidence_payload["mode"] == "refs_only_domain_owned_typed_blocker_payload"
    record_payload = evidence_payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["stage_attempt_source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"]
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "artifacts/publication_eval/latest.json" in record_payload["evidence_refs"]
    assert "artifacts/publication_eval/latest.json#reviewer_trace" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:completion_receipt_consumption=consumed" in record_payload[
        "evidence_refs"
    ]
    assert evidence_payload["body_included"] is False
    assert evidence_payload["domain_ready_claimed"] is False
    assert evidence_payload["publication_ready_claimed"] is False
    assert evidence_payload["artifact_mutation_authorized"] is False
    assert "publication_verdict_body" in evidence_payload["forbidden_payload_fields"]


def test_domain_handler_dispatch_evidence_payload_fails_closed_without_consumed_ai_reviewer_receipt(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    workorder_path = tmp_path / "opl-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_attempt_id": "sat_7848b377174e9983fac31212",
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": "mas_default_executor_source_d42d6161d143c0c4f0e0c1c3",
                "domain_source_fingerprint": "30ec9749a9ca699f",
                "profile_name": "nfpitnet",
            },
            "dispatch_identity_fields": {
                "action_type": "return_to_ai_reviewer_workflow",
                "dispatch_ref": (
                    "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                    "consumer/default_executor_dispatches/return_to_ai_reviewer_workflow.json"
                ),
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "domain_transition": {
                        "completion_receipt_consumption": {"status": "missing"},
                    },
                    "owner_route": {"next_owner": "ai_reviewer"},
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

    assert exit_code == 1
    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "consumed_ai_reviewer_routeback_not_observed"
    assert "domain_dispatch_evidence_record_payload" not in payload


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
