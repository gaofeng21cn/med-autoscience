from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_export_projects_gate_clearing_default_executor_dispatch(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_gate_clearing_batch.json"
    )
    dispatch_path = workspace_root / dispatch_ref
    write_profile(profile_path, workspace_root=workspace_root)
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-dm003-gate-current",
        "runtime_health_epoch": "runtime-health-event-dm003-gate-current",
        "work_unit_fingerprint": "dm003::gate-clearing::current",
        "source_fingerprint": "truth-snapshot::dm003::gate-clearing",
        "route_epoch": "truth-event-dm003-gate-current",
        "current_owner": "mas_controller",
        "next_owner": "gate_clearing_batch",
        "owner_reason": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "allowed_actions": ["run_gate_clearing_batch"],
        "blocked_actions": ["run_quality_repair_batch", "return_to_ai_reviewer_workflow"],
        "source_refs": {
            "runtime_health_epoch": "runtime-health-event-dm003-gate-current",
            "study_truth_epoch": "truth-event-dm003-gate-current",
            "source_eval_id": "publication-eval::003::current",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "dm003::gate-clearing::current",
            "blocked_reason": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        },
        "idempotency_key": "owner-route::003::gate-clearing-current",
    }
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "domain_action_request_materializer_publication_owner_bridge",
            "next_executable_owner": "gate_clearing_batch",
            "executor_kind": "codex_cli_default",
            "consumer_mutation_scope": "executor_dispatch_request_only",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "owner_route": owner_route,
            "prompt_contract": {
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_gate_clearing_batch",
                "next_executable_owner": "gate_clearing_batch",
                "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                "owner_route": owner_route,
                "allowed_write_surfaces": [
                    "artifacts/supervision/consumer/latest.json",
                    "artifacts/supervision/consumer/history.jsonl",
                    "studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/*.json",
                    "studies/<study_id>/artifacts/supervision/requests/gate_clearing_batch/latest.json",
                ],
                "forbidden_surfaces": [
                    "paper/**",
                    "manuscript/**",
                    "current_package/**",
                    "paper/current_package/**",
                    "manuscript/current_package/**",
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
                "scan_latest": str(
                    workspace_root
                    / "artifacts"
                    / "supervision"
                    / "opl_current_control_state"
                    / "latest.json"
                ),
            },
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["study_id"] == study_id
    assert task["quest_id"] == study_id
    assert task["action_type"] == "run_gate_clearing_batch"
    assert task["domain_owner"] == "gate_clearing_batch"
    assert task["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert task["work_unit_fingerprint"] == "dm003::gate-clearing::current"
    assert task["payload"]["action_type"] == "run_gate_clearing_batch"
    assert task["payload"]["domain_owner"] == "gate_clearing_batch"
    assert task["payload"]["next_executable_owner"] == "gate_clearing_batch"
    assert task["payload"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert task["payload"]["dispatch_ref"] == dispatch_ref
    assert task["payload"]["completion_boundary"] == {
        "provider_completion": "typed_closeout_packet_observed",
        "domain_ready_verdict": "read_from_mas_publication_or_gate_surface",
        "provider_completion_is_domain_ready": False,
    }
    assert task["owner_route_attempt_envelope"]["domain_owner"] == "gate_clearing_batch"
    assert task["owner_route_attempt_envelope"]["dispatchable"] is True
