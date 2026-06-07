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


def test_domain_handler_export_prefers_current_control_action_queue_over_stale_readiness_blocker(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id

    current_work_unit_id = "ai_reviewer_medical_prose_quality_review"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="domain_transition_ai_reviewer_re_eval",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="domain-transition::ai-reviewer-current",
        runtime_health_epoch="runtime-health-event-006663-current",
        blocked_actions=["complete_medical_paper_readiness_surface", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-06T23:49:15+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=ai_route,
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "surface": "controller_decision",
            "schema_version": 1,
            "decision_type": "medical_paper_readiness_owner_blocker",
            "generated_at": "2026-06-06T23:09:27Z",
            "readiness_next_action": {
                "action_id": "complete_medical_paper_readiness_surface",
                "surface_key": "authoring_runtime_authorization",
                "summary": "Old readiness blocker residue.",
            },
        },
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-06T23:50:00Z",
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
                                "owner_reason": "domain_transition_ai_reviewer_re_eval",
                                "runtime_health_epoch": "runtime-health-event-006663-current",
                                "truth_epoch": "truth-event-000040-current",
                                "work_unit_fingerprint": "domain-transition::ai-reviewer-current",
                                "work_unit_id": current_work_unit_id,
                            },
                            "missing_required_fields": [],
                            "required_fields": [
                                "work_unit_fingerprint",
                                "truth_epoch",
                                "runtime_health_epoch_or_source_eval_id",
                            ],
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": current_work_unit_id,
                        "owner": "ai_reviewer",
                    },
                    "consumption": {
                        "state": "unconsumed",
                        "first_seen_at": "2026-06-06T23:45:03Z",
                    },
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["current_owner_action"]["source"] == "opl_current_control_state_action_queue"
    assert study["current_owner_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert study["current_owner_action"]["work_unit_id"] == current_work_unit_id
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["work_unit_id"] == current_work_unit_id


def test_domain_handler_export_prefers_current_writer_handoff_over_stale_current_control_action(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    source_eval_id = "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::ai-reviewer-record::20260602T161258Z"
    publication_eval = {
        **_ai_reviewer_blocking_eval(study_root),
        "study_id": study_id,
        "quest_id": study_id,
        "eval_id": source_eval_id,
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})

    stale_ai_work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=stale_ai_work_unit_id,
        work_unit_fingerprint="dm003::ai-reviewer::stale-current-control",
        runtime_health_epoch="runtime-health-event-007001-ai",
        blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
    )
    writer_work_unit_id = "medical_prose_write_repair"
    write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        action_type="run_quality_repair_batch",
        work_unit_id=writer_work_unit_id,
        work_unit_fingerprint="dm003::writer::current-handoff",
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
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    writer_handoff = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "action_id": f"quality-repair-writer-handoff::{study_id}::{source_eval_id}",
        "dispatch_status": "ready",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "owner_route": write_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": write_route,
            "next_work_unit": {"unit_id": writer_work_unit_id, "owner": "write"},
            "allowed_write_surfaces": ["paper/draft.md", "paper/build/review_manuscript.md"],
            "forbidden_surfaces": [
                "paper/current_package/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": True,
        },
        "source_action": {
            "surface": "quality_repair_batch",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "source_eval_id": source_eval_id,
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "source_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "generated_at": "2026-06-02T09:52:05+00:00",
    }
    _write_json(dispatch_path, writer_handoff)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "surface_kind": "quality_repair_batch",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "status": "handoff_ready",
            "next_owner": "write",
            "source_eval_id": source_eval_id,
            "writer_worker_handoff": writer_handoff,
        },
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
                                "work_unit_fingerprint": "dm003::ai-reviewer::stale-current-control",
                                "work_unit_id": stale_ai_work_unit_id,
                            },
                            "missing_required_fields": [],
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": stale_ai_work_unit_id,
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
    assert study["current_owner_action"]["source"] == "quality_repair_batch_writer_handoff"
    assert study["current_owner_action"]["action_type"] == "run_quality_repair_batch"
    assert study["current_owner_action"]["work_unit_id"] == writer_work_unit_id
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == writer_work_unit_id
    assert tasks[0]["payload"]["next_executable_owner"] == "write"


def test_domain_handler_export_retire_writer_handoff_after_current_reviewer_record_routes_to_gate_replay(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    source_eval_id = "publication-eval::003::ai-reviewer-record::20260602T184032Z"
    publication_eval = {
        **_ai_reviewer_blocking_eval(study_root),
        "study_id": study_id,
        "quest_id": study_id,
        "eval_id": source_eval_id,
        "recommended_actions": [
            {
                "action_id": "route-current-ai-reviewer-record-to-publication-gate-replay",
                "action_type": "route_back_same_line",
                "route_target": "finalize",
                "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "finalize",
                    "summary": "Replay publication gate against the current AI reviewer record.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})

    writer_work_unit_id = "medical_prose_write_repair"
    stale_write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        action_type="run_quality_repair_batch",
        work_unit_id=writer_work_unit_id,
        work_unit_fingerprint="publication-blockers::stale-writer-handoff",
        runtime_health_epoch="runtime-health-event-007002-write",
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    writer_handoff = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "action_id": f"quality-repair-writer-handoff::{study_id}::{source_eval_id}",
        "dispatch_status": "ready",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "owner_route": stale_write_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route": stale_write_route,
            "next_work_unit": {"unit_id": writer_work_unit_id, "owner": "write"},
            "allowed_write_surfaces": ["paper/draft.md", "paper/build/review_manuscript.md"],
            "forbidden_surfaces": [
                "paper/current_package/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": True,
        },
        "source_action": {
            "surface": "quality_repair_batch",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "source_eval_id": source_eval_id,
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "source_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "generated_at": "2026-06-02T20:13:13+00:00",
    }
    _write_json(dispatch_path, writer_handoff)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "surface_kind": "quality_repair_batch",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "status": "handoff_ready",
            "next_owner": "write",
            "source_eval_id": source_eval_id,
            "writer_worker_handoff": writer_handoff,
            "repair_execution_evidence": {
                "status": "blocked",
                "review_finding": {"source_eval_id": source_eval_id},
                "repair_work_unit": {"unit_id": writer_work_unit_id},
                "blockers": ["manuscript_story_surface_delta_missing"],
                "manuscript_surface_hygiene": {
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
            },
        },
    )
    _write_json(
        study_root / "paper" / "review" / "domain_stage_closeout_sat_story_delta_20260602T202258Z.json",
        {
            "surface_kind": "domain_stage_closeout_packet",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "status": "completed_for_write_owner_delta",
            "route_outcome": "write_repair_delta_recorded",
            "stage_attempt_id": "sat_story_delta",
            "stage_packet_ref": f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
            "source_eval_id": source_eval_id,
            "work_unit_id": writer_work_unit_id,
            "work_unit_fingerprint": "publication-blockers::stale-writer-handoff",
            "owner_receipt": {
                "status": "executed",
                "owner": "write",
                "typed_blocker": None,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "artifact_delta": {
                "status": "materialized",
                "meaningful_artifact_delta": True,
                "story_surface_delta_present": True,
                "changed_artifact_refs": [
                    {"path": f"studies/{study_id}/paper/draft.md"},
                    {"path": f"studies/{study_id}/paper/build/review_manuscript.md"},
                ],
                "manuscript_surface_hygiene": {
                    "status": "clear",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "blockers": [],
                },
            },
            "closeout_refs": [
                f"studies/{study_id}/paper/review/domain_stage_closeout_sat_story_delta_20260602T202258Z.json",
                f"studies/{study_id}/paper/draft.md",
                f"studies/{study_id}/paper/build/review_manuscript.md",
            ],
        },
    )
    current_ai_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    ai_route = _owner_route(
        study_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_inputs",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_ai_work_unit_id,
        work_unit_fingerprint="truth-snapshot::current-ai-reviewer-workflow",
        runtime_health_epoch="runtime-health-event-007003-ai",
        blocked_actions=["run_quality_repair_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="return_to_ai_reviewer_workflow.json",
        action_type="return_to_ai_reviewer_workflow",
        next_owner="ai_reviewer",
        dispatch_authority="ai_reviewer_record_production_handoff",
        generated_at="2026-06-02T20:30:00+00:00",
        allowed_write_surfaces=[
            "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        ],
        owner_route=ai_route,
    )
    _write_json(
        workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-02T20:35:00Z",
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
                                "owner_reason": "ai_reviewer_record_stale_after_current_inputs",
                                "runtime_health_epoch": "runtime-health-event-007003-ai",
                                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                                "work_unit_fingerprint": "truth-snapshot::current-ai-reviewer-workflow",
                                "work_unit_id": current_ai_work_unit_id,
                            },
                            "missing_required_fields": [],
                        },
                    },
                    "controller_next_work_unit": {
                        "unit_id": current_ai_work_unit_id,
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
    assert study["current_owner_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["return_to_ai_reviewer_workflow"]
    assert tasks[0]["payload"]["work_unit_id"] == current_ai_work_unit_id


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
