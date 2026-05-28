from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_export_skips_consumed_ai_reviewer_dispatch_after_publication_eval_written(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = workspace_root / "studies" / study_id
    dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "return_to_ai_reviewer_workflow.json"
    )
    dispatch_path = workspace_root / dispatch_ref
    eval_id = f"publication-eval::{study_id}::{study_id}::20260528T015915Z::ai-reviewer-record"
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "runtime_health_epoch": "runtime-health-event-006316-b5c4f3837a811a49",
        "work_unit_fingerprint": "truth-snapshot::5ff4a47789dba6ff6387506e",
        "source_fingerprint": "truth-snapshot::5ff4a47789dba6ff6387506e",
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "current_owner": "mas_controller",
        "next_owner": "ai_reviewer",
        "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "blocked_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "runtime_health_epoch": "runtime-health-event-006316-b5c4f3837a811a49",
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
        },
        "idempotency_key": (
            f"owner-route::{study_id}::truth-event-000024-daa5883571a64a07::"
            "ai_reviewer::ai_reviewer_record_stale_after_current_manuscript::0660d60a889373a4"
        ),
    }
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "next_executable_owner": "ai_reviewer",
            "executor_kind": "codex_cli_default",
            "consumer_mutation_scope": "executor_dispatch_request_only",
            "owner_route": owner_route,
            "prompt_contract": {
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "return_to_ai_reviewer_workflow",
                "next_executable_owner": "ai_reviewer",
                "owner_route": owner_route,
                "allowed_write_surfaces": [
                    "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
                ],
                "forbidden_surfaces": [
                    "paper/**",
                    "artifacts/publication_eval/latest.json",
                    "artifacts/controller_decisions/latest.json",
                ],
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_claim_authoring_allowed": False,
            },
            "refs": {
                "dispatch_path": str(dispatch_path),
                "source_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": eval_id,
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
            "reviewer_operating_system": {"contract_id": "medical_publication_ai_reviewer_os_v1"},
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "executed",
                    "execution_id": (
                        f"execution::{study_id}::return_to_ai_reviewer_workflow::"
                        "2026-05-28T02:02:18+00:00"
                    ),
                    "idempotency_key": owner_route["idempotency_key"],
                    "current_owner_route": owner_route,
                    "prompt_contract": {"owner_route": owner_route},
                    "owner_result": {
                        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "publication_eval_surface": "artifacts/publication_eval/latest.json",
                        "eval_id": eval_id,
                        "reviewer_operating_system": {
                            "contract_id": "medical_publication_ai_reviewer_os_v1",
                        },
                        "controller_decision_refresh": {
                            "refresh_status": "materialized",
                            "study_decision_ref": {
                                "artifact_path": str(
                                    study_root / "artifacts" / "controller_decisions" / "latest.json"
                                ),
                            },
                        },
                    },
                }
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
