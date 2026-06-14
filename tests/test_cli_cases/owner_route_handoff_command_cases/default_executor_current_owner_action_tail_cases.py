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


def test_domain_handler_export_retire_writer_handoff_after_current_reviewer_record_routes_to_gate_replay(
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
        workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_ai_work_unit_id,
        work_unit_fingerprint="truth-snapshot::current-ai-reviewer-workflow",
        owner="ai_reviewer",
        source="opl_current_control_state.action_queue.canonical_current_work_unit",
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
    monkeypatch,
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
        workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="truth-snapshot::current",
        owner="ai_reviewer",
        source="opl_current_control_state.action_queue.canonical_current_work_unit",
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
        workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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


def test_domain_handler_export_exports_provider_admission_when_current_work_unit_renames_dispatch_unit(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)

    action_type = "run_quality_repair_batch"
    current_work_unit_id = "medical_prose_write_repair"
    current_fingerprint = "publication-blockers::0915410f804b3697"
    stale_stage_native_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason=action_type,
        action_type=action_type,
        work_unit_id=action_type,
        work_unit_fingerprint=(
            "stage-native-next-action::08-publication_package_handoff::"
            "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
        ),
        runtime_health_epoch=(
            "stage-native-next-action::003-dpcc-primary-care-phenotype-treatment-gap::"
            "08-publication_package_handoff"
        ),
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type=action_type,
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-14T08:02:57+00:00",
        owner_route=stale_stage_native_route,
        allowed_write_surfaces=[
            "studies/<study_id>/artifacts/supervision/requests/quality_repair_batch/latest.json",
            "studies/<study_id>/artifacts/controller/repair_execution_evidence/latest.json",
        ],
    )
    _write_json(
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat_old_writer.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "stage_id": "domain_owner/default-executor-dispatch",
            "status": "completed",
            "stage_attempt_id": "sat_old_writer",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": current_fingerprint,
            "action_fingerprint": current_fingerprint,
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "owner_route_currentness_basis": {
                "work_unit_id": current_work_unit_id,
                "work_unit_fingerprint": current_fingerprint,
                "truth_epoch": "truth-event-current",
                "runtime_health_epoch": "runtime-health-event-current",
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::current"
                ),
            },
            "owner_route": {
                **stale_stage_native_route,
                "next_owner": "write",
                "work_unit_fingerprint": current_fingerprint,
                "source_fingerprint": current_fingerprint,
                "source_refs": {
                    "work_unit_id": current_work_unit_id,
                    "work_unit_fingerprint": current_fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-current",
                    "owner_route_currentness_basis": {
                        "work_unit_id": current_work_unit_id,
                        "work_unit_fingerprint": current_fingerprint,
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-event-current",
                        "source_eval_id": (
                            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::current"
                        ),
                    },
                },
            },
            "owner_receipt": {"status": "executed", "owner": "write"},
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "changed_artifact_refs": [
                    {
                        "path": str(
                            workspace_root
                            / "studies"
                            / study_id
                            / "paper"
                            / "draft.md"
                        ),
                        "artifact_role": "canonical_manuscript_story_surface",
                    }
                ],
            },
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": current_work_unit_id,
                "problem_summary": "Old writer closeout for a previous admission cycle.",
                "stage_goal": "Repair medical prose.",
                "stage_work_done": ["recorded old delta"],
                "paper_work_done": ["recorded old delta"],
                "changed_stage_surfaces": ["paper/draft.md"],
                "changed_paper_surfaces": ["paper/draft.md"],
                "outcome": "deliverable_progress",
                "remaining_blockers": ["medical_publication_surface_blocked"],
                "duration": {"status": "missing", "value": None},
                "token_usage": {"status": "missing", "value": None, "total_tokens": None},
                "cost": {"status": "missing", "value": None, "total_cost": None},
                "usage_refs": [],
                "cost_refs": [],
                "progress_delta_classification": "deliverable_progress",
                "deliverable_progress_delta": {"count": 1, "token_usage_total": None},
                "paper_progress_delta": {"count": 1, "token_usage_total": None},
                "platform_repair_delta": {"count": 0, "token_usage_total": None},
                "next_forced_delta": {
                    "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                    "work_unit_id": current_work_unit_id,
                    "owner_action": {
                        "next_owner": "write",
                        "action_type": action_type,
                        "work_unit_id": current_work_unit_id,
                    },
                    "reason": "terminal_closeout_observed",
                },
                "evidence_refs": [],
            },
        },
    )

    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")

    def _read_study_progress(**_: object) -> dict[str, object]:
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
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": action_type,
                "work_unit_id": current_work_unit_id,
                "work_unit_fingerprint": current_fingerprint,
                "action_fingerprint": current_fingerprint,
                "currentness_basis": {
                    "work_unit_id": current_work_unit_id,
                    "work_unit_fingerprint": current_fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-current",
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                    "provider_admission_pending": True,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": current_work_unit_id,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "action_type": action_type,
                "work_unit_id": current_work_unit_id,
                "work_unit_fingerprint": current_fingerprint,
                "action_fingerprint": current_fingerprint,
                "allowed_actions": [action_type],
                "publication_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::current"
                ),
            },
            "provider_admission_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "provider_admission_pending",
                    "source": "opl_current_control_state.study_current_executable_owner_action",
                    "execution_ref": str(
                        workspace_root
                        / "runtime"
                        / "artifacts"
                        / "supervision"
                        / "opl_current_control_state"
                        / "latest.json"
                    ),
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": action_type,
                    "work_unit_id": current_work_unit_id,
                    "work_unit_fingerprint": current_fingerprint,
                    "action_fingerprint": current_fingerprint,
                    "dispatch_path": str(dispatch_path),
                    "next_executable_owner": "write",
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "currentness_basis": {
                        "work_unit_id": current_work_unit_id,
                        "work_unit_fingerprint": current_fingerprint,
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-event-current",
                        "source_eval_id": (
                            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::current"
                        ),
                    },
                    "source_refs": {
                        "dispatch_path": str(dispatch_path),
                        "stage_packet_ref": (
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                            "supervision/consumer/default_executor_dispatches/"
                            "run_quality_repair_batch.json"
                        ),
                        "route_identity_key": "provider-admission::dm003::medical-prose",
                        "attempt_idempotency_key": "provider-admission::dm003::medical-prose",
                    },
                }
            ],
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
    assert len(tasks) == 1
    task = tasks[0]
    assert task["study_id"] == study_id
    assert task["payload"]["action_type"] == action_type
    assert task["payload"]["work_unit_id"] == current_work_unit_id
    assert task["payload"]["work_unit_fingerprint"] == current_fingerprint
    assert task["payload"]["provider_admission_identity"]["work_unit_id"] == current_work_unit_id
    assert task["payload"]["provider_attempt_or_lease_required"] is True
