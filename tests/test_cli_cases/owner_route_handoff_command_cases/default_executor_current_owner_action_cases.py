from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import *  # noqa: F403,F401


def _owner_route(
    *,
    study_id: str,
    next_owner: str,
    owner_reason: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    runtime_health_epoch: str,
    blocked_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "allowed_actions": [action_type],
        "blocked_actions": blocked_actions,
        "source_refs": {
            "runtime_health_epoch": runtime_health_epoch,
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "work_unit_id": work_unit_id,
            "blocked_reason": owner_reason,
        },
        "idempotency_key": f"owner-route::{study_id}::{work_unit_fingerprint}",
    }


def _write_dispatch(
    *,
    workspace_root: Path,
    study_id: str,
    filename: str,
    action_type: str,
    next_owner: str,
    dispatch_authority: str,
    owner_route: dict[str, object],
    generated_at: str,
    allowed_write_surfaces: list[str] | None = None,
) -> None:
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / filename
    )
    _write_json(
        dispatch_path,
        {
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
                "allowed_write_surfaces": allowed_write_surfaces or ["paper/draft.md"],
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
                    workspace_root
                    / "studies"
                    / study_id
                    / "artifacts"
                    / "publication_eval"
                    / "latest.json"
                ),
            },
            "generated_at": generated_at,
        },
    )


def test_domain_handler_export_prefers_current_control_action_queue_over_later_dispatch(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})

    current_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="dm003::ai-reviewer::current-control",
        runtime_health_epoch="runtime-health-event-007001-ai",
        blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
    )
    write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        work_unit_fingerprint="dm003::writer::later-dispatch",
        runtime_health_epoch="runtime-health-event-007002-write",
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-02T09:15:18+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=ai_route,
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-02T09:52:05+00:00",
        owner_route=write_route,
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-02T10:00:00Z",
            "studies": [],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner_route": {
                        **ai_route,
                        "currentness_contract": {
                            "basis": {
                                "owner_reason": "ai_reviewer_assessment_required",
                                "runtime_health_epoch": "runtime-health-event-007001-ai",
                                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                                "work_unit_fingerprint": "dm003::ai-reviewer::current-control",
                            },
                            "missing_required_fields": [],
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": current_work_unit_id,
                        "owner": "ai_reviewer",
                    },
                    "consumption": {
                        "state": "unconsumed",
                        "first_seen_at": "2026-06-02T09:15:18Z",
                    },
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["current_owner_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert study["current_owner_action"]["work_unit_id"] == current_work_unit_id
    assert study["paper_autonomy_loop"]["status"] == "superseded_by_opl_current_owner_route"
    assert study["publication_aftercare"]["currentness_status"] == "superseded_by_opl_current_owner_route"
    task_kinds = [task["task_kind"] for task in payload["pending_family_tasks"]]
    assert "paper_autonomy/repair-recheck" not in task_kinds
    assert "publication_aftercare/analysis-queue-progress" not in task_kinds
    assert "publication_aftercare/reviewer-refresh" not in task_kinds
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["work_unit_id"] == current_work_unit_id
    assert tasks[0]["payload"]["next_executable_owner"] == "ai_reviewer"


def test_domain_handler_export_accepts_required_fields_currentness_basis_without_owner_reason(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)

    current_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_inputs",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="truth-snapshot::current",
        runtime_health_epoch="runtime-health-event-006313-92d173350337cee0",
        blocked_actions=["run_quality_repair_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-02T09:15:18+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=ai_route,
    )
    currentness_basis = {
        "runtime_health_epoch": "runtime-health-event-006313-92d173350337cee0",
        "source_eval_id": (
            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
            "ai-reviewer-record::20260602T091913Z"
        ),
        "truth_epoch": "truth-event-000022-212df8cd1d3b2842",
        "work_unit_fingerprint": "truth-snapshot::current",
        "work_unit_id": current_work_unit_id,
    }
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-02T10:00:00Z",
            "studies": [],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner": "ai_reviewer",
                    "owner_route": {
                        **ai_route,
                        "owner_reason": None,
                        "currentness_contract": {
                            "basis": currentness_basis,
                            "missing_required_fields": [],
                            "required_fields": [
                                "work_unit_fingerprint",
                                "truth_epoch",
                                "runtime_health_epoch_or_source_eval_id",
                            ],
                        },
                        "source_refs": {
                            "owner_route_currentness_basis": currentness_basis,
                            "work_unit_id": current_work_unit_id,
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": current_work_unit_id,
                        "owner": "ai_reviewer",
                    },
                    "consumption": {"state": "unconsumed"},
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["current_owner_action"]["owner_route_currentness_basis"] == currentness_basis
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["work_unit_id"] == current_work_unit_id


def test_domain_handler_export_does_not_fall_back_when_current_control_action_has_no_dispatch(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)

    current_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="dm003::ai-reviewer::current-control",
        runtime_health_epoch="runtime-health-event-007001-ai",
        blocked_actions=["run_quality_repair_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-02T09:52:05+00:00",
        owner_route=_owner_route(
            study_id=study_id,
            next_owner="write",
            owner_reason="manuscript_story_surface_delta_missing",
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_write_repair",
            work_unit_fingerprint="dm003::writer::later-dispatch",
            runtime_health_epoch="runtime-health-event-007002-write",
            blocked_actions=["return_to_ai_reviewer_workflow"],
        ),
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-02T10:00:00Z",
            "studies": [],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner_route": {
                        **ai_route,
                        "currentness_contract": {
                            "basis": {
                                "owner_reason": "ai_reviewer_assessment_required",
                                "runtime_health_epoch": "runtime-health-event-007001-ai",
                                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                                "work_unit_fingerprint": "dm003::ai-reviewer::current-control",
                            },
                            "missing_required_fields": [],
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": current_work_unit_id,
                        "owner": "ai_reviewer",
                    },
                    "consumption": {"state": "unconsumed"},
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
    assert tasks == []
