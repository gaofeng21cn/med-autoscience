from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_routes_default_executor_transition_request_to_opl_runtime_intake(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    transition_request = {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "target_runtime_owner": "one-person-lab",
        "recommended_transition_kind": "StartProviderAttempt",
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_stage_run": False,
        "aggregate_identity": {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "work_unit_id": "unit-001",
            "work_unit_fingerprint": "fingerprint-001",
        },
    }
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "default-executor-transition-request",
            "domain_id": "medautoscience",
            "task_kind": "domain_owner/default-executor-dispatch",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": (
                    "studies/001-risk/artifacts/supervision/consumer/"
                    "default_executor_dispatches/run_quality_repair_batch.json"
                ),
                "next_executable_owner": "write",
                "authority_boundary": "mas_domain_progress_transition_request_only",
                "provider_admission_requires_opl_runtime_result": True,
                "opl_domain_progress_transition_request": transition_request,
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["opl_attempt_admission_requested"] is False
    assert payload["opl_attempt_admission_status"] == "not_requested"
    assert payload["opl_domain_progress_transition_runtime_intake_requested"] is True
    assert payload["opl_domain_progress_transition_runtime_intake_status"] == "requested"
    assert payload["dispatch"]["execution_policy"] == (
        "opl_domain_progress_transition_runtime_intake_required"
    )
    result = payload["dispatch"]["result"]
    assert result["surface"] == "default_executor_transition_request_intake"
    assert result["status"] == "opl_domain_progress_transition_runtime_intake_requested"
    assert result["authority_boundary"] == "mas_domain_progress_transition_request_only"
    assert result["provider_admission_requires_opl_runtime_result"] is True
    assert result["mas_can_authorize_provider_admission"] is False
    assert result["mas_can_create_opl_event"] is False
    assert result["mas_can_create_opl_outbox_record"] is False
    assert result["mas_can_create_opl_stage_run"] is False
    assert result["opl_domain_progress_transition_request"] == transition_request
    assert payload["authority_boundary"]["writes_domain_truth"] is False


def test_domain_handler_dispatch_blocks_default_executor_carrier_without_transition_request(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "default-executor-legacy-carrier",
            "domain_id": "medautoscience",
            "task_kind": "domain_owner/default-executor-dispatch",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": (
                    "studies/001-risk/artifacts/supervision/consumer/"
                    "default_executor_dispatches/run_quality_repair_batch.json"
                ),
                "next_executable_owner": "write",
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["opl_attempt_admission_requested"] is False
    assert payload["opl_attempt_admission_status"] == "not_requested"
    assert payload["dispatch"]["execution_policy"] == "guarded_domain_control_receipt_only"
    result = payload["dispatch"]["result"]
    assert result["surface"] == "default_executor_dispatch_request_blocker"
    assert result["status"] == "opl_domain_progress_transition_request_required"
    assert result["authority_boundary"] == "mas_default_executor_dispatch_request_only"
    assert result["provider_admission_requires_opl_runtime_result"] is True
    assert result["mas_can_authorize_provider_admission"] is False
