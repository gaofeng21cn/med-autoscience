from __future__ import annotations

from .shared import *  # noqa: F403,F401


def _assert_refs_only_current_owner_route_blocker_contract(
    payload: dict[str, object],
    *,
    expected_action_type: str,
    expected_next_owner: str,
    expected_owner_reason: str,
    expected_dispatch_ref: str,
) -> None:
    assert payload["status"] == "typed_blocker_payload_ready"
    assert payload["owner_route_next_owner"] == expected_next_owner
    assert payload["owner_route_owner_reason"] == expected_owner_reason
    assert payload["dispatch_identity_fields"]["action_type"] == expected_action_type

    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["mode"] == "refs_only_domain_owned_typed_blocker_payload"
    assert evidence_payload["body_included"] is False
    assert evidence_payload["domain_ready_claimed"] is False
    assert evidence_payload["publication_ready_claimed"] is False
    assert evidence_payload["artifact_mutation_authorized"] is False
    assert evidence_payload["current_package_mutation_authorized"] is False

    record_payload = evidence_payload["opl_runtime_action_execute_payload"]
    assert record_payload["typed_blocker_refs"]
    assert record_payload["domain_owner_receipt_refs"] == []
    assert expected_dispatch_ref in record_payload["evidence_refs"]
    assert f"owner-route-reconcile:owner_route_next_owner={expected_next_owner}" in record_payload[
        "evidence_refs"
    ]
    assert "domain-authority-handoff:status=typed_blocker" in record_payload["evidence_refs"]
    assert record_payload["no_regression_evidence_refs"]
    assert any(
        ref.startswith("mas-no-forbidden-write-proof:medautoscience:")
        for ref in record_payload["no_regression_evidence_refs"]
    )


def _current_owner_route_blocker_scan(study_id: str) -> dict[str, object]:
    return {
        "studies": [
            {
                "study_id": study_id,
                "blocked_reason": "paper_authority_clean_migration_required",
                "owner_route": {
                    "next_owner": "external_supervisor",
                    "owner_reason": "paper_authority_clean_migration_required",
                    "source_fingerprint": "truth-snapshot::b7326f0cf5e2b63a802ebce9",
                    "idempotency_key": (
                        f"owner-route::{study_id}::truth-event-000024-daa5883571a64a07::"
                        "external_supervisor::paper_authority_clean_migration_required::fb048165aef89ab4"
                    ),
                    "source_refs": {
                        "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
                        "runtime_health_epoch": "runtime-health-event-006329-2e2c7afb26004270",
                        "work_unit_fingerprint": "truth-snapshot::b7326f0cf5e2b63a802ebce9",
                        "blocked_reason": "paper_authority_clean_migration_required",
                        "publication_eval_path": (
                            "/workspace/studies/002-dm-china-us-mortality-attribution/"
                            "artifacts/publication_eval/latest.json"
                        ),
                    },
                    "owner_reason_contract": {
                        "registered": True,
                        "reason": "paper_authority_clean_migration_required",
                        "owner": "ai_reviewer",
                        "allowed_actions": ["return_to_ai_reviewer_workflow"],
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
                        "reason": "paper_authority_clean_migration_required",
                        "next_owner": "external_supervisor",
                        "source_fingerprint": "truth-snapshot::b7326f0cf5e2b63a802ebce9",
                        "idempotency_key": (
                            f"owner-route::{study_id}::truth-event-000024-daa5883571a64a07::"
                            "external_supervisor::paper_authority_clean_migration_required::fb048165aef89ab4"
                        ),
                        "provider_completion_is_domain_completion": False,
                    },
                },
            }
        ]
    }


def _readiness_owner_route_blocker_scan(study_id: str) -> dict[str, object]:
    return {
        "studies": [
            {
                "study_id": study_id,
                "blocked_reason": "medical_paper_readiness_not_ready",
                "owner_route": {
                    "next_owner": "MedAutoScience",
                    "owner_reason": "medical_paper_readiness_not_ready",
                    "source_fingerprint": "truth-snapshot::dpcc-readiness-current",
                    "idempotency_key": (
                        f"owner-route::{study_id}::truth-event-000041-dpcc::"
                        "MedAutoScience::medical_paper_readiness_not_ready::a2f1ce9d"
                    ),
                    "source_refs": {
                        "study_truth_epoch": "truth-event-000041-dpcc",
                        "runtime_health_epoch": "runtime-health-event-readiness-041",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "work_unit_fingerprint": "truth-snapshot::dpcc-readiness-current",
                        "blocked_reason": "medical_paper_readiness_not_ready",
                        "publication_eval_path": (
                            "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                            "artifacts/publication_eval/latest.json"
                        ),
                    },
                    "owner_reason_contract": {
                        "registered": True,
                        "reason": "medical_paper_readiness_not_ready",
                        "owner": "MedAutoScience",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
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
                        "reason": "medical_paper_readiness_not_ready",
                        "next_owner": "MedAutoScience",
                        "source_fingerprint": "truth-snapshot::dpcc-readiness-current",
                        "idempotency_key": (
                            f"owner-route::{study_id}::truth-event-000041-dpcc::"
                            "MedAutoScience::medical_paper_readiness_not_ready::a2f1ce9d"
                        ),
                        "provider_completion_is_domain_completion": False,
                    },
                },
            }
        ]
    }


def _write_current_owner_workorder(
    *,
    path: Path,
    study_id: str,
    action_type: str,
    stage_attempt_id: str,
    stage_attempt_source: str,
    domain_source: str,
    dispatch_ref: str,
) -> None:
    _write_json(
        path,
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
                "stage_run_id": "app-stage-run:medautoscience:domain-owner-default-executor-dispatch",
                "stage_manifest_ref": "opl://stage-manifests/domain_owner%2Fdefault-executor-dispatch",
                "current_pointer_ref": (
                    "opl://stage-runs/app-stage-run%3Amedautoscience%3A"
                    "domain-owner-default-executor-dispatch/current"
                ),
                "idempotency_key": f"idem_{stage_attempt_id}",
                "provider_attempt_ref": f"temporal://attempt/{stage_attempt_id}",
                "attempt_lease_ref": f"opl://stage-attempts/{stage_attempt_id}/leases/frt-current/active",
                "execution_authorization_decision_ref": (
                    f"opl://stage-attempts/{stage_attempt_id}/execution-authorizations/"
                    "frt-current/wf-current"
                ),
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": action_type,
                "dispatch_ref": dispatch_ref,
            },
        },
    )


def _run_payload_export(monkeypatch, tmp_path: Path, capsys, *, action_type: str) -> dict[str, object]:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = (
        "sat_ced76f140623875b809b58ac"
        if action_type == "return_to_ai_reviewer_workflow"
        else "sat_9f6a6b0f243ba239aef0ad4d"
    )
    stage_attempt_source = (
        "mas_default_executor_source_7cfa7c0f20db52f3cd694d77"
        if action_type == "return_to_ai_reviewer_workflow"
        else "mas_default_executor_source_928d16572b36cc749119b385"
    )
    domain_source = (
        "66d2907a15cfd228"
        if action_type == "return_to_ai_reviewer_workflow"
        else "ddc04b6cf4f67a95"
    )
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        f"default_executor_dispatches/{action_type}.json"
    )
    workorder_path = tmp_path / f"{stage_attempt_id}.workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_current_owner_workorder(
        path=workorder_path,
        study_id=study_id,
        action_type=action_type,
        stage_attempt_id=stage_attempt_id,
        stage_attempt_source=stage_attempt_source,
        domain_source=domain_source,
        dispatch_ref=dispatch_ref,
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        assert study_ids == (study_id,)
        return _current_owner_route_blocker_scan(study_id)

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
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["owner_delta_result"]["closeout_binding"]["source_fingerprint"] == stage_attempt_source
    assert record_payload["owner_delta_result"]["closeout_binding"]["provider_attempt_ref"] == (
        f"temporal://attempt/{stage_attempt_id}"
    )
    assert record_payload["typed_blocker_refs"]
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert (
        "owner-route-reconcile:blocked_reason=paper_authority_clean_migration_required"
        in record_payload["evidence_refs"]
    )
    assert "owner-route-reconcile:owner_route_next_owner=external_supervisor" in record_payload[
        "evidence_refs"
    ]
    assert "domain-authority-handoff:status=typed_blocker" in record_payload["evidence_refs"]
    assert (
        "domain-authority-handoff:typed_blocker_reason=paper_authority_clean_migration_required"
        in record_payload["evidence_refs"]
    )
    assert "owner-route-reconcile:completion_receipt_consumption=consumed" not in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:route_target=None" not in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=None" not in record_payload["evidence_refs"]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False
    return payload


def test_domain_handler_dispatch_evidence_payload_projects_readiness_current_owner_route_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_id = "sat_05313b31327f1b145eeea680"
    stage_attempt_source = "mas_default_executor_source_0be125f91ef430f09f900c73"
    domain_source = "c6fc80c7adf241f7"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/complete_medical_paper_readiness_surface/"
        "ee9be6b2a20e61bffc19efde.json"
    )
    workorder_path = tmp_path / f"{stage_attempt_id}.workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_current_owner_workorder(
        path=workorder_path,
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        stage_attempt_id=stage_attempt_id,
        stage_attempt_source=stage_attempt_source,
        domain_source=domain_source,
        dispatch_ref=dispatch_ref,
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        assert study_ids == (study_id,)
        return _readiness_owner_route_blocker_scan(study_id)

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
    assert_stable_blocker_reason(
        payload,
        blocker_class="current_owner_route_blocked",
        detail_reason="current_owner_route_typed_blocker_observed_for_default_executor_dispatch",
    )
    _assert_refs_only_current_owner_route_blocker_contract(
        payload,
        expected_action_type="complete_medical_paper_readiness_surface",
        expected_next_owner="MedAutoScience",
        expected_owner_reason="medical_paper_readiness_not_ready",
        expected_dispatch_ref=dispatch_ref,
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert "owner-route-reconcile:blocked_reason=medical_paper_readiness_not_ready" in record_payload[
        "evidence_refs"
    ]


def test_domain_handler_dispatch_evidence_payload_projects_reviewer_dispatch_current_owner_route_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    payload = _run_payload_export(
        monkeypatch,
        tmp_path,
        capsys,
        action_type="return_to_ai_reviewer_workflow",
    )

    assert_stable_blocker_reason(
        payload,
        blocker_class="current_owner_route_blocked",
        detail_reason="current_owner_route_typed_blocker_observed_for_default_executor_dispatch",
    )
    _assert_refs_only_current_owner_route_blocker_contract(
        payload,
        expected_action_type="return_to_ai_reviewer_workflow",
        expected_next_owner="external_supervisor",
        expected_owner_reason="paper_authority_clean_migration_required",
        expected_dispatch_ref=(
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
            "default_executor_dispatches/return_to_ai_reviewer_workflow.json"
        ),
    )


def test_domain_handler_dispatch_evidence_payload_projects_writer_dispatch_current_owner_route_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    payload = _run_payload_export(
        monkeypatch,
        tmp_path,
        capsys,
        action_type="run_quality_repair_batch",
    )

    assert_stable_blocker_reason(
        payload,
        blocker_class="current_owner_route_blocked",
        detail_reason="current_owner_route_typed_blocker_observed_for_default_executor_dispatch",
    )
    _assert_refs_only_current_owner_route_blocker_contract(
        payload,
        expected_action_type="run_quality_repair_batch",
        expected_next_owner="external_supervisor",
        expected_owner_reason="paper_authority_clean_migration_required",
        expected_dispatch_ref=(
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
            "default_executor_dispatches/run_quality_repair_batch.json"
        ),
    )


def test_domain_handler_dispatch_evidence_payload_projects_dpcc_gate_clearing_blocker_for_stale_writer_dispatch(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_id = "sat_3b5b062ba800c1f81e0c18df"
    stage_attempt_source = "mas_default_executor_source_3e3cd74d7475b77eb8372a9f"
    domain_source = "899b0362d9b68d3e"
    owner_reason = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/consumer/"
        "default_executor_dispatches/immutable/run_quality_repair_batch/3684d9b4f9b031adf43c280b.json"
    )
    workorder_path = tmp_path / f"{stage_attempt_id}.workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_current_owner_workorder(
        path=workorder_path,
        study_id=study_id,
        action_type="run_quality_repair_batch",
        stage_attempt_id=stage_attempt_id,
        stage_attempt_source=stage_attempt_source,
        domain_source=domain_source,
        dispatch_ref=dispatch_ref,
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        assert study_ids == (study_id,)
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": owner_reason,
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": owner_reason,
                            "lane": "publication_gate",
                            "summary": (
                                "MAS publication-gate/currentness replay after current "
                                "AI reviewer archive."
                            ),
                        },
                        "source_refs": [
                            "artifacts/publication_eval/ai_reviewer_responses/current.json",
                            "artifacts/controller/gate_clearing_batch/latest.json",
                        ],
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                            "reviewer_trace_ref": (
                                "artifacts/publication_eval/ai_reviewer_responses/"
                                "current.json#reviewer_operating_system"
                            ),
                            "next_action": "honor_ai_reviewer_publication_eval_authority",
                        },
                    },
                    "owner_route": {
                        "next_owner": "external_supervisor",
                        "owner_reason": owner_reason,
                        "source_fingerprint": "truth-snapshot::dpcc-current-gate-clearing",
                        "idempotency_key": (
                            f"owner-route::{study_id}::truth-event-000031-dpcc::"
                            f"external_supervisor::{owner_reason}::b32a9ab86aa"
                        ),
                        "source_refs": {
                            "study_truth_epoch": "truth-event-000031-dpcc",
                            "source_eval_id": (
                                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "sat_cc2c6c6cf90bbe4444a4d388"
                            ),
                            "work_unit_id": owner_reason,
                            "work_unit_fingerprint": "truth-snapshot::dpcc-current-gate-clearing",
                            "blocked_reason": owner_reason,
                            "publication_eval_path": (
                                "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                                "artifacts/publication_eval/ai_reviewer_responses/current.json"
                            ),
                        },
                        "owner_reason_contract": {
                            "registered": True,
                            "reason": owner_reason,
                            "owner": "gate_clearing_batch",
                            "allowed_actions": ["run_gate_clearing_batch"],
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
                            "reason": owner_reason,
                            "detail_reason": owner_reason,
                            "next_owner": "external_supervisor",
                            "source_fingerprint": "truth-snapshot::dpcc-current-gate-clearing",
                            "idempotency_key": (
                                f"owner-route::{study_id}::truth-event-000031-dpcc::"
                                f"external_supervisor::{owner_reason}::b32a9ab86aa"
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
    _assert_refs_only_current_owner_route_blocker_contract(
        payload,
        expected_action_type="run_quality_repair_batch",
        expected_next_owner="external_supervisor",
        expected_owner_reason=owner_reason,
        expected_dispatch_ref=dispatch_ref,
    )
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert stage_attempt_source in record_payload["typed_blocker_refs"][0]
    assert "owner-route-reconcile:completion_receipt_consumption=consumed" in record_payload[
        "evidence_refs"
    ]
    assert "owner-route-reconcile:route_target=write" in record_payload["evidence_refs"]
    assert "owner-route-reconcile:controller_action=request_opl_stage_attempt" in record_payload[
        "evidence_refs"
    ]
    assert f"owner-route-reconcile:blocked_reason={owner_reason}" in record_payload["evidence_refs"]
    assert f"domain-authority-handoff:typed_blocker_reason={owner_reason}" in record_payload[
        "evidence_refs"
    ]
