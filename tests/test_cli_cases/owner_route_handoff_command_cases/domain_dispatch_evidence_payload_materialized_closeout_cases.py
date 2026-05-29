from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_materializes_stage_attempt_closeout_from_blocked_execution(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = "sat_e6f92e06019386999767fccc"
    stage_attempt_source = "mas_default_executor_source_31f624984b95141678c05395"
    domain_source = "7fb3d7989fa07608"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/immutable/run_quality_repair_batch/735ab53344e0c086e868219d.json"
    )
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        f"default_executor_execution/{stage_attempt_id}.closeout.json"
    )
    latest_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_execution/latest.json"
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
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "generated_at": "2026-05-29T01:00:03+00:00",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "generated_at": "2026-05-29T01:00:03+00:00",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "action_id": "supervisor-action::dm002::run_quality_repair_batch",
                    "execution_id": "execution::dm002::run_quality_repair_batch::2026-05-29T01:00:03+00:00",
                    "execution_status": "blocked",
                    "blocked_reason": "paper_progress_stall_fingerprint_stale",
                    "owner_callable_surface": None,
                    "dispatch_path": str(workspace_root / dispatch_ref),
                    "current_owner_route": {
                        "next_owner": "write",
                        "owner_reason": "quest_waiting_opl_runtime_owner_route",
                    },
                    "execution_observation": {
                        "execution_status": "blocked",
                        "blocked_reason": "paper_progress_stall_fingerprint_stale",
                    },
                }
            ],
            "execution_ledger": [],
            "blocked_count": 1,
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
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {"studies": [{"study_id": study_id}]}

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
    materialized_closeout_path = workspace_root / closeout_ref
    closeout = json.loads(materialized_closeout_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["status"] == "typed_blocker_payload_ready"
    assert_stable_blocker_reason(
        payload,
        blocker_class="stage_attempt_closeout_blocked",
        detail_reason="stage_attempt_closeout_typed_blocker_observed_for_default_executor_dispatch",
    )
    assert closeout["surface_kind"] == "stage_attempt_closeout_packet"
    assert closeout["stage_attempt_id"] == stage_attempt_id
    assert closeout["status"] == "blocked"
    assert closeout["blocked_reason"] == "paper_progress_stall_fingerprint_stale"
    assert closeout["provider_completion_is_domain_completion"] is False
    assert closeout["domain_blocker"]["surface_kind"] == "mas_domain_typed_blocker"
    assert closeout["domain_blocker"]["reason"] == "paper_progress_stall_fingerprint_stale"
    assert closeout["typed_blocker_ref"] == f"{closeout_ref}#domain_blocker"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"] == [closeout["typed_blocker_ref"]]
    assert closeout_ref in record_payload["evidence_refs"]
    assert latest_ref in record_payload["evidence_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:blocked_reason=paper_progress_stall_fingerprint_stale" in record_payload[
        "evidence_refs"
    ]
    assert payload["domain_dispatch_evidence_record_payload"]["domain_ready_claimed"] is False
    assert payload["domain_dispatch_evidence_record_payload"]["publication_ready_claimed"] is False


def test_domain_handler_dispatch_evidence_payload_materializes_stage_attempt_closeout_from_current_dispatch_binding(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = "sat_e6f92e06019386999767fccc"
    stage_attempt_source = "mas_default_executor_source_31f624984b95141678c05395"
    domain_source = "7fb3d7989fa07608"
    dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/immutable/run_quality_repair_batch/735ab53344e0c086e868219d.json"
    )
    latest_dispatch_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        f"default_executor_execution/{stage_attempt_id}.closeout.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    dispatch_packet = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "idempotency_key": (
            "owner-route::002-dm-china-us-mortality-attribution::truth-event-000024-daa5883571a64a07::"
            "write::quest_waiting_opl_runtime_owner_route::cafda975370666b3"
        ),
        "action_fingerprint": "paper_progress_stall:93efc669895ecdf9",
        "refs": {
            "dispatch_path": str(workspace_root / latest_dispatch_ref),
            "immutable_dispatch_path": str(workspace_root / dispatch_ref),
            "stage_packet_path": str(workspace_root / dispatch_ref),
        },
        "owner_route": {
            "next_owner": "write",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "source_fingerprint": "truth-snapshot::b59ccabc79e7f6773fd2e783",
        },
    }
    _write_json(workspace_root / dispatch_ref, dispatch_packet)
    _write_json(workspace_root / latest_dispatch_ref, dispatch_packet)
    _write_json(
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "generated_at": "2026-05-29T01:00:03+00:00",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "generated_at": "2026-05-29T01:00:03+00:00",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "action_id": "supervisor-action::dm002::run_quality_repair_batch",
                    "execution_id": "execution::dm002::run_quality_repair_batch::2026-05-29T01:00:03+00:00",
                    "execution_status": "blocked",
                    "blocked_reason": "paper_progress_stall_fingerprint_stale",
                    "owner_callable_surface": None,
                    "dispatch_path": str(workspace_root / latest_dispatch_ref),
                    "idempotency_key": dispatch_packet["idempotency_key"],
                    "action_fingerprint": dispatch_packet["action_fingerprint"],
                    "current_owner_route": {
                        "next_owner": "write",
                        "owner_reason": "quest_waiting_opl_runtime_owner_route",
                    },
                    "execution_observation": {
                        "execution_status": "blocked",
                        "blocked_reason": "paper_progress_stall_fingerprint_stale",
                    },
                }
            ],
            "execution_ledger": [],
            "blocked_count": 1,
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
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {"studies": [{"study_id": study_id}]}

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
    materialized_closeout_path = workspace_root / closeout_ref
    closeout = json.loads(materialized_closeout_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["status"] == "typed_blocker_payload_ready"
    assert closeout["stage_packet_ref"] == dispatch_ref
    assert closeout["blocked_reason"] == "paper_progress_stall_fingerprint_stale"
    assert closeout["typed_blocker_ref"] == f"{closeout_ref}#domain_blocker"
    assert latest_dispatch_ref in closeout["closeout_refs"]
    assert dispatch_ref in closeout["closeout_refs"]
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"] == [closeout["typed_blocker_ref"]]
    assert closeout_ref in record_payload["evidence_refs"]
    assert latest_dispatch_ref in record_payload["evidence_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]


def test_domain_handler_dispatch_evidence_payload_does_not_materialize_closeout_without_dispatch_binding(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    stage_attempt_id = "sat_e6f92e06019386999767fccc"
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        f"default_executor_execution/{stage_attempt_id}.closeout.json"
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
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "paper_progress_stall_fingerprint_stale",
                    "dispatch_path": (
                        str(
                            workspace_root
                            / "studies"
                            / study_id
                            / "artifacts"
                            / "supervision"
                            / "consumer"
                            / "default_executor_dispatches"
                            / "run_quality_repair_batch.json"
                        )
                    ),
                    "idempotency_key": "owner-route::dm002::current",
                    "action_fingerprint": "paper_progress_stall:current",
                }
            ],
            "execution_ledger": [],
            "blocked_count": 1,
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
                "source_fingerprint": "mas_default_executor_source_without_dispatch",
                "domain_source_fingerprint": "domain_source_without_dispatch",
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {"studies": [{"study_id": study_id}]}

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
    assert not (workspace_root / closeout_ref).exists()
