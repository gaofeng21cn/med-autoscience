from __future__ import annotations

from .shared import *  # noqa: F403,F401
from .default_executor_dispatch_export_cases import _write_default_executor_dispatch


def test_domain_handler_export_stops_repeated_nonconsumable_same_work_unit_closeout(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
    )
    owner_route = json.loads(dispatch_path.read_text(encoding="utf-8"))["prompt_contract"]["owner_route"]
    execution_base = {
        "surface": "default_executor_dispatch_execution",
        "schema_version": 1,
        "study_id": study_root.name,
        "quest_id": study_root.name,
        "action_type": "run_quality_repair_batch",
        "execution_status": "executed",
        "idempotency_key": owner_route["idempotency_key"],
        "current_owner_route": owner_route,
        "prompt_contract": {"owner_route": owner_route},
        "owner_result": {
            "status": "executed",
            "ok": True,
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                },
                "changed_artifact_refs": [{"path": str(study_root / "paper" / "claim_evidence_map.json")}],
            },
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "canonical_surface": "owner_callable_adapter_receipt_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "projection_authority": False,
            "owner_callable_receipt_projection": True,
            "execution_ledger_authority": False,
            "attempt_lifecycle_authority": False,
            "queue_authority": False,
            "executions": [],
            "execution_ledger": [
                {
                    **execution_base,
                    "surface": "owner_callable_adapter_receipt",
                    "canonical_surface": "owner_callable_adapter_receipt",
                    "execution_id": "execution::dm002::run_quality_repair_batch::first",
                },
                {
                    **execution_base,
                    "surface": "owner_callable_adapter_receipt",
                    "canonical_surface": "owner_callable_adapter_receipt",
                    "execution_id": "execution::dm002::run_quality_repair_batch::second",
                },
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []


def test_domain_handler_export_redrives_newer_nonconsumable_closeout_over_old_consumed_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
    )
    first_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    first_payload = json.loads(capsys.readouterr().out)
    assert first_exit_code == 0
    first_task = next(
        task
        for task in first_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    owner_route = dispatch["prompt_contract"]["owner_route"]
    owner_route_basis = {
        "truth_epoch": owner_route["truth_epoch"],
        "runtime_health_epoch": owner_route["runtime_health_epoch"],
        "source_eval_id": owner_route["source_refs"]["source_eval_id"],
        "work_unit_fingerprint": owner_route["work_unit_fingerprint"],
        "work_unit_id": owner_route["source_refs"]["work_unit_id"],
        "owner_reason": owner_route["owner_reason"],
    }
    closeout_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution"
    _write_json(
        closeout_root / "sat_001_old_consumed.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_001_old_consumed",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "action_type": "run_quality_repair_batch",
            "status": "completed",
            "route_outcome": "write_repair_delta_recorded",
            "owner_route_basis": owner_route_basis,
            "artifact_delta": {
                "status": "progress_delta_candidate",
                "story_surface_delta_present": True,
                "changed_artifact_refs": [
                    {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                ],
                "manuscript_surface_hygiene": {
                    "status": "clear",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "blockers": [],
                },
            },
            "closeout_refs": [
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/default_executor_execution/sat_001_old_consumed.closeout.json"
            ],
        },
    )
    _write_json(
        closeout_root / "sat_002_new_nonconsumable.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_002_new_nonconsumable",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_root.name,
            "quest_id": study_root.name,
            "action_type": "run_quality_repair_batch",
            "status": "completed",
            "route_outcome": "closed_with_domain_owner_refs",
            "owner_route_basis": owner_route_basis,
            "artifact_delta": {
                "status": "progress_delta_candidate",
                "story_surface_delta_present": False,
                "changed_artifact_refs": [
                    {"path": str(study_root / "paper" / "claim_evidence_map.json")},
                ],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "blockers": [],
                },
            },
            "closeout_refs": [
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/default_executor_execution/sat_002_new_nonconsumable.closeout.json"
            ],
        },
    )

    second_exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    second_payload = json.loads(capsys.readouterr().out)

    assert second_exit_code == 0
    second_task = next(
        task
        for task in second_payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )
    assert second_task["source_fingerprint"] != first_task["source_fingerprint"]
    assert second_task["payload"]["redrive_context"]["status"] == "non_consumable_closeout"
    assert second_task["payload"]["redrive_context"]["receipt_ref"] == (
        "artifacts/supervision/consumer/default_executor_execution/"
        "sat_002_new_nonconsumable.closeout.json"
    )
    assert second_task["payload"]["redrive_context"]["reason"] == "manuscript_story_surface_delta_missing"
