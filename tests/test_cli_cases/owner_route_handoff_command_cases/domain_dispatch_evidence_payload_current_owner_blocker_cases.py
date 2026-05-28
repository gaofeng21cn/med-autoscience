from __future__ import annotations

from .shared import *  # noqa: F403,F401


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
    assert payload["status"] == "typed_blocker_payload_ready"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
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

    assert payload["payload_reason"] == "current_owner_route_typed_blocker_observed_for_default_executor_dispatch"
    assert payload["owner_route_next_owner"] == "external_supervisor"
    assert payload["owner_route_owner_reason"] == "paper_authority_clean_migration_required"


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

    assert payload["payload_reason"] == "current_owner_route_typed_blocker_observed_for_default_executor_dispatch"
    assert payload["owner_route_next_owner"] == "external_supervisor"
    assert payload["owner_route_owner_reason"] == "paper_authority_clean_migration_required"
