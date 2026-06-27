from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import *  # noqa: F403,F401

from .default_executor_current_owner_action_shared import (
    _owner_route,
    _patch_canonical_current_work_unit,
    _write_dispatch,
)


def test_domain_handler_export_projects_current_control_transition_request_to_opl_task(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        work_unit_fingerprint="publication-blockers::0915410f804b3697",
        owner="write",
        source="opl_current_control_state.study_current_executable_owner_action",
    )
    stale_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="medical_prose_write_repair",
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        work_unit_fingerprint="publication-blockers::0915410f804b3697",
        runtime_health_epoch="runtime-health-event-stale-dispatch",
        blocked_actions=[],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-17T00:00:00+00:00",
        owner_route=stale_route,
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
    assert task["reason"] == "current_control_transition_request_pending"
    assert task["payload"]["authority_boundary"] == "mas_domain_progress_transition_request_only"
    assert task["dispatch_owner"] == "one-person-lab"
    assert task["domain_truth_owner"] == "med-autoscience"
    assert task["queue_owner"] == "one-person-lab"
    assert task["provider_admission_pending"] is False
    assert task["provider_admission_requires_opl_runtime_result"] is True
    transition_request = task["payload"]["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["recommended_transition_kind"] == "StartProviderAttempt"
    assert transition_request["mas_can_create_opl_event"] is False
    assert transition_request["mas_can_create_opl_outbox_record"] is False
    assert transition_request["mas_can_create_opl_stage_run"] is False
    assert task["payload"]["authority_boundary"] == "mas_domain_progress_transition_request_only"
    assert task["payload"]["provider_admission_pending"] is False
    assert task["payload"]["provider_admission_requires_opl_runtime_result"] is True
    assert task["payload"]["current_control_action"]["status"] == "transition_request_pending"
    assert task["payload"]["current_control_action"]["opl_domain_progress_transition_request"] == (
        transition_request
    )
    assert "runtime-health-event-stale-dispatch" not in json.dumps(task, sort_keys=True)


def test_domain_handler_export_consumes_transition_request_after_owner_receipt(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "publication-blockers::0915410f804b3697"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    stale_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason=work_unit_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        runtime_health_epoch="runtime-health-event-stale-dispatch",
        blocked_actions=[],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=f"{action_type}.json",
        action_type=action_type,
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-17T00:00:00+00:00",
        owner_route=stale_route,
    )

    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")

    def _read_study_progress(**_: object) -> dict[str, object]:
        transition_request = {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
            "recommended_transition_kind": "StartProviderAttempt",
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_stage_run": False,
            "currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-canonical-test",
            },
        }
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "owner_receipt_recorded",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
                "currentness_basis": transition_request["currentness_basis"],
            },
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "transition_request_pending",
                "source": "opl_current_control_state.study_current_executable_owner_action",
                "next_owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_fingerprint": work_unit_fingerprint,
                "owner_route_currentness_basis": transition_request["currentness_basis"],
                "opl_domain_progress_transition_request": transition_request,
                "paper_progress_policy_result": {
                    "policy_result_id": "paper-policy::dm003-owner-receipt",
                    "opl_domain_progress_transition_request": transition_request,
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert not [
        task
        for task in payload["pending_family_tasks"]
        if task.get("reason") == "current_control_transition_request_pending"
        and task.get("payload", {}).get("study_id") == study_id
        and task.get("payload", {}).get("work_unit_id") == work_unit_id
    ]


def test_domain_handler_export_consumes_transition_request_from_current_control_handoff_terminal_surface(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "publication-blockers::0915410f804b3697"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    stale_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason=work_unit_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        runtime_health_epoch="runtime-health-event-stale-dispatch",
        blocked_actions=[],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=f"{action_type}.json",
        action_type=action_type,
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-17T00:00:00+00:00",
        owner_route=stale_route,
    )

    transition_request = {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_owner": "one-person-lab",
        "recommended_transition_kind": "StartProviderAttempt",
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_stage_run": False,
        "currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-canonical-test",
        },
    }
    terminal_current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "owner_receipt_recorded",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "write",
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "owner_receipt_ref": (
            "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
            "artifacts/controller/repair_execution_receipts/latest.json"
        ),
        "currentness_basis": transition_request["currentness_basis"],
    }

    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "transition_request_pending",
                "source": "opl_current_control_state.study_current_executable_owner_action",
                "next_owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source_fingerprint": work_unit_fingerprint,
                "owner_route_currentness_basis": transition_request["currentness_basis"],
                "opl_domain_progress_transition_request": transition_request,
                "paper_progress_policy_result": {
                    "policy_result_id": "paper-policy::dm003-owner-receipt",
                    "opl_domain_progress_transition_request": transition_request,
                },
            },
            "opl_current_control_state_handoff": {
                "transition_request_pending_count": 0,
                "transition_request_candidates": [],
                "provider_admission_terminal_closeout_consumed": {
                    "surface_kind": "provider_admission_terminal_closeout_consumed",
                    "stage_attempt_id": "sat-terminal",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "owner_receipt_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/controller/repair_execution_receipts/latest.json"
                    ),
                },
                "current_work_unit": terminal_current_work_unit,
                "current_execution_envelope": {
                    "state_kind": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert not [
        task
        for task in payload["pending_family_tasks"]
        if task.get("reason") == "current_control_transition_request_pending"
        and task.get("payload", {}).get("study_id") == study_id
        and task.get("payload", {}).get("work_unit_id") == work_unit_id
    ]


def test_domain_handler_export_suppresses_stale_transition_request_when_current_owner_action_changed(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stale_action_type = "run_quality_repair_batch"
    stale_work_unit_id = "medical_prose_write_repair"
    stale_fingerprint = "publication-blockers::0915410f804b3697"
    current_action_type = "return_to_ai_reviewer_workflow"
    current_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    current_fingerprint = "sha256:current-ai-reviewer-followup"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    (study_root / "study.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    stale_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason=stale_work_unit_id,
        action_type=stale_action_type,
        work_unit_id=stale_work_unit_id,
        work_unit_fingerprint=stale_fingerprint,
        runtime_health_epoch="runtime-health-event-stale-dispatch",
        blocked_actions=[],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=f"{stale_action_type}.json",
        action_type=stale_action_type,
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-17T00:00:00+00:00",
        owner_route=stale_route,
    )
    current_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason=current_work_unit_id,
        action_type=current_action_type,
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint=current_fingerprint,
        runtime_health_epoch=current_fingerprint,
        blocked_actions=[stale_action_type],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=f"{current_action_type}.json",
        action_type=current_action_type,
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-17T00:05:00+00:00",
        owner_route=current_route,
    )

    transition_request = {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_owner": "one-person-lab",
        "recommended_transition_kind": "StartProviderAttempt",
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_stage_run": False,
        "currentness_basis": {
            "work_unit_id": stale_work_unit_id,
            "work_unit_fingerprint": stale_fingerprint,
            "truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-canonical-test",
        },
    }

    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "transition_request_pending",
                "source": "opl_current_control_state.study_current_executable_owner_action",
                "next_owner": "write",
                "action_type": stale_action_type,
                "work_unit_id": stale_work_unit_id,
                "work_unit_fingerprint": stale_fingerprint,
                "source_fingerprint": stale_fingerprint,
                "owner_route_currentness_basis": transition_request["currentness_basis"],
                "opl_domain_progress_transition_request": transition_request,
                "paper_progress_policy_result": {
                    "policy_result_id": "paper-policy::stale-writer",
                    "opl_domain_progress_transition_request": transition_request,
                },
            },
        }

    domain_handler_export = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.domain_handler_export"
    )
    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)
    monkeypatch.setattr(
        domain_handler_export,
        "_export_current_owner_action",
        lambda **_: {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "action_type": current_action_type,
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": current_fingerprint,
            "action_fingerprint": current_fingerprint,
            "allowed_actions": [current_action_type],
            "owner_route_currentness_basis": {
                "work_unit_id": current_work_unit_id,
                "work_unit_fingerprint": current_fingerprint,
            },
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    default_executor_tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [
        task
        for task in default_executor_tasks
        if task.get("reason") == "current_control_transition_request_pending"
        and task.get("payload", {}).get("work_unit_id") == stale_work_unit_id
    ] == []
    assert [task["payload"]["action_type"] for task in default_executor_tasks] == [
        current_action_type
    ]
    assert default_executor_tasks[0]["payload"]["work_unit_id"] == current_work_unit_id
