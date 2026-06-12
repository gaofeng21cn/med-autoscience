from __future__ import annotations

import os

from .shared import *  # noqa: F403,F401
from .default_executor_dispatch_readiness_cases import (
    test_domain_handler_export_carries_stage_current_provider_admission_identity,
    test_readiness_surface_key_changes_default_executor_source_identity,
)


def test_domain_handler_export_uses_current_owner_action_fingerprint_when_current_work_unit_lacks_one(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    action_type = "return_to_ai_reviewer_workflow"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    work_unit_fingerprint = "sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type=action_type,
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-10T09:05:58+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="repair_progress_ai_reviewer_recheck_required",
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            runtime_health_epoch="runtime-health-event-006758-0ac91a25224dc45c",
            blocked_actions=["run_quality_repair_batch"],
        ),
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "ai_reviewer",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
                    "runtime_health_epoch": "runtime-health-event-006760-d897d9ca5c5e348f",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "ai_reviewer",
                "next_work_unit": work_unit_id,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "action_type": action_type,
                "allowed_actions": [action_type],
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == [action_type]
    assert tasks[0]["payload"]["work_unit_id"] == work_unit_id
    assert tasks[0]["payload"]["work_unit_fingerprint"] == work_unit_fingerprint


def test_domain_handler_export_suppresses_stale_dispatch_blocked_by_current_owner_route(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_record_stale_after_current_manuscript",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            work_unit_fingerprint="truth-snapshot::old-ai-reviewer",
            runtime_health_epoch="runtime-health-event-006306-2365a556e7176a6b",
            blocked_actions=["run_quality_repair_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            work_unit_fingerprint="domain-transition::current-write",
            runtime_health_epoch="runtime-health-event-006315-6046777ae24dd127",
            blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["owner_route_currentness_basis"]["runtime_health_epoch"] == (
        "runtime-health-event-006315-6046777ae24dd127"
    )


def test_domain_handler_export_suppresses_stale_dispatch_blocked_by_current_route_when_work_unit_changed(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="consumer_default_executor_dispatch",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_record_stale_after_current_manuscript",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            work_unit_fingerprint="truth-snapshot::old-ai-reviewer-record",
            runtime_health_epoch="runtime-health-event-006325-ff1404193e350d0c",
            blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T06:07:53+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            work_unit_fingerprint=(
                "domain-transition::route_back_same_line::"
                "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
            ),
            runtime_health_epoch="runtime-health-event-006327-307bbee727d9e286",
            blocked_actions=[
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
            ],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == (
        "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    )


def test_domain_handler_export_uses_mtime_for_legacy_dispatch_without_generated_at(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    dispatch_dir = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    ai_reviewer_dispatch = dispatch_dir / "return_to_ai_reviewer_workflow.json"
    write_dispatch = dispatch_dir / "run_quality_repair_batch.json"

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=ai_reviewer_dispatch.name,
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-05-31T15:54:37+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_record_stale_after_current_manuscript",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            work_unit_fingerprint="dm003::ai-reviewer::older",
            runtime_health_epoch="runtime-health-event-006227-ai",
            blocked_actions=["run_quality_repair_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename=write_dispatch.name,
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="consumer_default_executor_dispatch",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="quest_waiting_opl_runtime_owner_route",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_currentness_recheck",
            work_unit_fingerprint="dm003::write::current",
            runtime_health_epoch="runtime-health-event-006237-write",
            blocked_actions=[
                "publication_gate_specificity_required",
                "current_package_freshness_required",
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
            ],
        ),
    )
    write_payload = json.loads(write_dispatch.read_text(encoding="utf-8"))
    write_payload.pop("generated_at", None)
    _write_json(write_dispatch, write_payload)
    os.utime(ai_reviewer_dispatch, (1_780_000_000, 1_780_000_000))
    os.utime(write_dispatch, (1_780_000_600, 1_780_000_600))

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == "medical_prose_currentness_recheck"
    assert tasks[0]["payload"]["next_executable_owner"] == "write"


def test_domain_handler_export_keeps_new_ai_reviewer_handoff_when_older_write_route_has_later_runtime_epoch(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T00:24:22+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id=work_unit_id,
            work_unit_fingerprint="domain-transition::current-write",
            runtime_health_epoch="runtime-health-event-006315-6046777ae24dd127",
            blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-05-28T01:01:03+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_assessment_required",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id=work_unit_id,
            work_unit_fingerprint="truth-snapshot::current-ai-reviewer",
            runtime_health_epoch="runtime-health-event-006306-2365a556e7176a6b",
            blocked_actions=[
                "publication_gate_specificity_required",
                "current_package_freshness_required",
                "artifact_display_surface_materialization_required",
                "canonical_paper_inputs_rehydrate_required",
                "run_quality_repair_batch",
                "run_gate_clearing_batch",
            ],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert tasks[0]["payload"]["next_executable_owner"] == "ai_reviewer"
    assert tasks[0]["payload"]["allowed_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]


def test_domain_handler_export_hydrates_only_one_current_default_executor_action_per_study(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)

    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T01:00:00+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_write_repair",
            work_unit_fingerprint="dm003::write::old",
            runtime_health_epoch="runtime-health-event-001",
            blocked_actions=[],
        ),
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-05-28T01:05:00+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="ai_reviewer",
            owner_reason="ai_reviewer_assessment_required",
            action_type="return_to_ai_reviewer_workflow",
            work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            work_unit_fingerprint="dm003::ai-reviewer::current",
            runtime_health_epoch="runtime-health-event-002",
            blocked_actions=[],
        ),
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )


def test_domain_handler_export_falls_through_consumed_newer_dispatch_to_pending_owner_action(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        work_unit_fingerprint="truth-snapshot::current-ai-reviewer-record",
        runtime_health_epoch="runtime-health-event-006265-ai",
        blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
    )
    write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        action_type="run_quality_repair_batch",
        work_unit_id="dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        work_unit_fingerprint=(
            "domain-transition::route_back_same_line::"
            "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
        ),
        runtime_health_epoch="runtime-health-event-006251-write",
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-31T23:02:05+00:00",
        owner_route=write_route,
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-01T01:53:26+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=ai_route,
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
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
                    "execution_id": f"execution::{study_id}::return_to_ai_reviewer_workflow::current",
                    "idempotency_key": ai_route["idempotency_key"],
                    "current_owner_route": ai_route,
                    "prompt_contract": {"owner_route": ai_route},
                    "owner_result": {
                        "status": "materialized",
                        "eval_id": f"publication-eval::{study_id}::current-ai-reviewer",
                        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "publication_eval_surface": "artifacts/publication_eval/latest.json",
                        "reviewer_operating_system": {
                            "contract_id": "medical_publication_ai_reviewer_os_v1",
                        },
                        "controller_decision_refresh": {
                            "refresh_status": "materialized",
                        },
                    },
                }
            ],
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
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert tasks[0]["payload"]["next_executable_owner"] == "write"


def test_domain_handler_export_uses_immutable_packet_ref_when_latest_slot_is_overwritten(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    dispatch_dir = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    latest_path = dispatch_dir / "run_quality_repair_batch.json"
    immutable_path = (
        dispatch_dir
        / "immutable"
        / "run_quality_repair_batch"
        / "medical-prose-write-repair.json"
    )

    current_dispatch = _dispatch_payload(
        workspace_root=workspace_root,
        study_id=study_id,
        dispatch_path=latest_path,
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T18:00:05+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_write_repair",
            work_unit_fingerprint="dm003::medical-prose-write-repair",
            runtime_health_epoch="runtime-health-event-medical-prose",
            blocked_actions=[],
        ),
    )
    current_dispatch["refs"]["immutable_dispatch_path"] = str(immutable_path)
    current_dispatch["refs"]["stage_packet_path"] = str(immutable_path)
    _write_json(immutable_path, current_dispatch)

    overwritten_latest = _dispatch_payload(
        workspace_root=workspace_root,
        study_id=study_id,
        dispatch_path=latest_path,
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-05-28T18:00:29+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="manuscript_story_repair",
            work_unit_fingerprint="dm003::manuscript-story-repair",
            runtime_health_epoch="runtime-health-event-story-repair",
            blocked_actions=[],
        ),
    )
    _write_json(latest_path, overwritten_latest)

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["work_unit_id"] for task in tasks] == ["manuscript_story_repair"]

    _write_json(latest_path, current_dispatch)
    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    task = next(
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    )

    expected_ref = str(immutable_path.relative_to(workspace_root))
    latest_ref = str(latest_path.relative_to(workspace_root))
    assert task["payload"]["work_unit_id"] == "medical_prose_write_repair"
    assert task["payload"]["dispatch_ref"] == expected_ref
    assert task["payload"]["dispatch_ref"] != latest_ref
    assert task["source_fingerprint"] in task["dedupe_key"]
    source_refs_by_role = {ref["role"]: ref for ref in task["source_refs"]}
    assert source_refs_by_role["default_executor_stage_packet"]["ref"] == expected_ref
    assert source_refs_by_role["default_executor_dispatch_request"]["ref"] == expected_ref
    assert source_refs_by_role["default_executor_latest_dispatch_request"]["ref"] == latest_ref
    assert source_refs_by_role["default_executor_immutable_dispatch_path"]["ref"] == expected_ref


def _dispatch_payload(
    *,
    workspace_root: Path,
    study_id: str,
    dispatch_path: Path,
    action_type: str,
    next_owner: str,
    dispatch_authority: str,
    owner_route: dict[str, object],
    generated_at: str,
) -> dict[str, object]:
    payload = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "dispatch_status": "ready",
        "dispatch_authority": dispatch_authority,
        "next_executable_owner": next_owner,
        "executor_kind": "codex_cli_default",
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "owner_route": owner_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "next_executable_owner": next_owner,
            "owner_route": owner_route,
            "allowed_write_surfaces": ["paper/draft.md"],
            "forbidden_surfaces": [
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
            "source_eval_path": str(
                workspace_root / "studies" / study_id / "artifacts" / "publication_eval" / "latest.json"
            ),
        },
        "generated_at": generated_at,
    }
    return payload
