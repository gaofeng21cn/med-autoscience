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


def test_domain_handler_export_normalizes_current_control_transition_request_identity(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    transition_request = {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "target_runtime_owner": "one-person-lab",
        "recommended_transition_kind": "StartProviderAttempt",
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_stage_run": False,
        "aggregate_identity": {
            "study_id": study_id,
            "quest_id": "quest-001",
            "work_unit_id": "current-work-unit",
            "work_unit_fingerprint": "current-fingerprint",
        },
        "currentness_basis": {
            "source_eval_id": None,
            "source_fingerprint": "request-source",
            "work_unit_id": "request-work-unit",
            "work_unit_fingerprint": None,
            "route_epoch": "route-request",
        },
    }
    owner_route_currentness_basis = {
        "source_eval_id": "publication-eval::owner-route",
        "source_fingerprint": "owner-route-source",
        "work_unit_id": "owner-route-work-unit",
        "work_unit_fingerprint": "owner-route-fingerprint",
        "truth_epoch": "truth-owner-route",
    }

    def _fresh_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": "quest-001",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "current-work-unit",
                "work_unit_fingerprint": "current-fingerprint",
                "currentness_basis": {
                    "source_eval_id": None,
                    "runtime_health_epoch": "runtime-owner-route",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "current-work-unit",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "transition_request_pending",
                "source": "opl_current_control_state.study_current_executable_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "current-work-unit",
                "work_unit_fingerprint": "current-fingerprint",
                "source_fingerprint": "candidate-source",
                "owner_route_currentness_basis": owner_route_currentness_basis,
                "opl_domain_progress_transition_request": transition_request,
                "paper_progress_policy_result": {
                    "policy_result_id": "paper-policy::001",
                    "opl_domain_progress_transition_request": transition_request,
                },
            },
        }

    domain_handler_export = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export"
    )
    monkeypatch.setattr(domain_handler_export, "_fresh_study_progress", _fresh_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    task = next(
        item
        for item in payload["pending_family_tasks"]
        if item["reason"] == "current_control_transition_request_pending"
    )
    task_payload = task["payload"]
    expected_basis = {
        "source_fingerprint": "candidate-source",
        "work_unit_id": "current-work-unit",
        "work_unit_fingerprint": "current-fingerprint",
        "truth_epoch": "truth-owner-route",
        "runtime_health_epoch": "runtime-owner-route",
        "route_epoch": "route-request",
    }
    assert task_payload["owner_route_currentness_basis"] == expected_basis
    assert (
        task_payload["opl_domain_progress_transition_request"]["currentness_basis"]
        == expected_basis
    )
    assert (
        task_payload["current_control_action"]["opl_domain_progress_transition_request"]
        == task_payload["opl_domain_progress_transition_request"]
    )
    assert (
        task_payload["current_control_action"]["owner_route"]["source_refs"][
            "owner_route_currentness_basis"
        ]
        == expected_basis
    )
    assert "source_eval_id" not in task_payload["current_control_action"]
    assert task_payload["current_control_action"]["source_fingerprint"] == "candidate-source"
    assert task_payload["current_control_action"]["work_unit_id"] == "current-work-unit"
    assert task_payload["current_control_action"]["work_unit_fingerprint"] == "current-fingerprint"
