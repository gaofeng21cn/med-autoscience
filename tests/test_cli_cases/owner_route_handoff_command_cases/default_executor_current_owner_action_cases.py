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


def test_domain_handler_export_prefers_current_control_action_queue_over_later_dispatch(
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
                    "consumption": {
                        "state": "unconsumed",
                        "first_seen_at": "2026-06-02T09:15:18Z",
                    },
                }
            ],
        },
    )
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="dm003::ai-reviewer::current-control",
        owner="ai_reviewer",
        source="opl_current_control_state.action_queue.canonical_current_work_unit",
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
    monkeypatch,
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
        workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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
    _patch_canonical_current_work_unit(
        monkeypatch,
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id=current_work_unit_id,
        work_unit_fingerprint="domain-transition::ai-reviewer-current",
        owner="ai_reviewer",
        source="opl_current_control_state.action_queue.canonical_current_work_unit",
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


def test_domain_handler_export_projects_readiness_blocker_derived_repair_from_reconcile_study_queue(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id

    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "surface": "controller_decision",
            "schema_version": 1,
            "decision_type": "medical_paper_readiness_owner_blocker",
            "generated_at": "2026-06-07T15:00:00Z",
            "readiness_next_action": {
                "action_id": "complete_medical_paper_readiness_surface",
                "surface_key": "authoring_runtime_authorization",
            },
        },
    )

    repair_work_unit_id = "readiness_blocker_publication_repair"
    repair_fingerprint = (
        "readiness-blocker-repair::publication-eval::dm002::"
        "medical_publication_surface_blocked+reviewer_first_concerns_unresolved"
    )
    repair_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="medical_paper_readiness_repair_required",
        action_type="run_quality_repair_batch",
        work_unit_id=repair_work_unit_id,
        work_unit_fingerprint=repair_fingerprint,
        runtime_health_epoch="runtime-health-event-readiness-repair",
        blocked_actions=["complete_medical_paper_readiness_surface", "run_gate_clearing_batch"],
    )
    repair_route["source_refs"] = {
        **repair_route["source_refs"],
        "source_eval_id": "publication-eval::dm002::readiness-blocker-gaps",
        "source_ref": (
            "artifacts/stage_outputs/08-publication_package_handoff/"
            "receipts/typed_blocker.json"
        ),
        "owner_route_currentness_basis": {
            "truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-readiness-repair",
            "work_unit_id": repair_work_unit_id,
            "work_unit_fingerprint": repair_fingerprint,
        },
    }
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="domain_action_request_materializer_readiness_blocker_repair",
        generated_at="2026-06-07T15:28:33+00:00",
        owner_route=repair_route,
    )

    readiness_route = _owner_route(
        study_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        action_type="complete_medical_paper_readiness_surface",
        work_unit_id="complete_medical_paper_readiness_surface",
        work_unit_fingerprint="readiness-residue::authoring-runtime-authorization",
        runtime_health_epoch="runtime-health-event-readiness-residue",
        blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
    )
    _write_json(
        workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-07T15:29:00Z",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "owner": "MedAutoScience",
                    "reason": "medical_paper_readiness_missing",
                    "owner_route": readiness_route,
                    "consumption": {"state": "unconsumed"},
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": repair_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "next_owner": "write",
                        "work_unit_id": repair_work_unit_id,
                        "allowed_actions": ["run_quality_repair_batch"],
                        "source_ref": (
                            "artifacts/stage_outputs/08-publication_package_handoff/"
                            "receipts/typed_blocker.json"
                        ),
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "complete_medical_paper_readiness_surface",
                            "owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "surface_key": "authoring_runtime_authorization",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                        },
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "authority": "observability_only",
                            "owner": "write",
                            "reason": "medical_paper_readiness_repair_required",
                            "required_output_surface": (
                                "canonical manuscript story-surface delta, claim-evidence semantic delta, "
                                "reviewer/gate delta, or typed blocker:readiness_blocker_publication_repair_required"
                            ),
                            "controller_work_unit_id": repair_work_unit_id,
                            "work_unit_fingerprint": repair_fingerprint,
                            "source_ref": (
                                "artifacts/stage_outputs/08-publication_package_handoff/"
                                "receipts/typed_blocker.json"
                            ),
                            "readiness_blocker_followup_superseded": (
                                "complete_medical_paper_readiness_surface"
                            ),
                            "source_eval_id": "publication-eval::dm002::readiness-blocker-gaps",
                            "publication_eval_gap_ids": [
                                "medical_publication_surface_blocked",
                                "reviewer_first_concerns_unresolved",
                            ],
                            "owner_route": repair_route,
                            "consumption": {"state": "unconsumed"},
                        },
                    ],
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    action = study["current_owner_action"]
    assert action["source"] == "owner_route_reconcile_readiness_blocker_repair"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == repair_work_unit_id
    assert action["next_owner"] == "write"
    assert action["readiness_blocker_followup_superseded"] == "complete_medical_paper_readiness_surface"
    assert action["publication_eval_gap_ids"] == [
        "medical_publication_surface_blocked",
        "reviewer_first_concerns_unresolved",
    ]
    assert action["owner_route_currentness_basis"]["work_unit_fingerprint"] == repair_fingerprint
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == repair_work_unit_id
    assert tasks[0]["payload"]["next_executable_owner"] == "write"


def test_domain_handler_export_prefers_stage_native_write_repair_over_stale_readiness_current_control(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id

    _write_json(
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "stage_index_ref": "control/stage_index.json",
            "current_stage_id": "08-publication_package_handoff",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
        },
    )
    _write_json(
        study_root / "control" / "stage_index.json",
        {
            "schema_version": "mas.study_stage_index.v1",
            "study_id": study_id,
            "current_stage_id": "08-publication_package_handoff",
            "stages": [
                {
                    "stage_id": "08-publication_package_handoff",
                    "manifest_present": True,
                    "status": "typed_blocked",
                    "typed_blocker_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                }
            ],
        },
    )

    readiness_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        "authoring_runtime_authorization::"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    readiness_route = _owner_route(
        study_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        action_type="complete_medical_paper_readiness_surface",
        work_unit_id="complete_medical_paper_readiness_surface",
        work_unit_fingerprint=readiness_fingerprint,
        runtime_health_epoch="runtime-health-event-readiness",
        blocked_actions=["run_quality_repair_batch", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="complete_medical_paper_readiness_surface.json",
        action_type="complete_medical_paper_readiness_surface",
        next_owner="MedAutoScience",
        dispatch_authority="consumer_default_executor_dispatch",
        generated_at="2026-06-07T15:28:33+00:00",
        owner_route=readiness_route,
    )
    _write_json(
        workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface_kind": "opl_current_control_state",
            "schema_version": 1,
            "generated_at": "2026-06-07T15:28:33Z",
            "studies": [],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "owner_route": {
                        **readiness_route,
                        "currentness_contract": {
                            "basis": {
                                "owner_reason": "medical_paper_readiness_missing",
                                "runtime_health_epoch": "runtime-health-event-readiness",
                                "truth_epoch": "truth-event-readiness",
                                "work_unit_fingerprint": readiness_fingerprint,
                                "work_unit_id": "complete_medical_paper_readiness_surface",
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
                        "unit_id": "complete_medical_paper_readiness_surface",
                        "owner": "MedAutoScience",
                    },
                    "consumption": {
                        "state": "unconsumed",
                        "first_seen_at": "2026-06-07T15:28:33Z",
                    },
                }
            ],
        },
    )

    stage_route_fingerprint = (
        "stage-native-next-action::08-publication_package_handoff::"
        "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
    )
    write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="run_quality_repair_batch",
        action_type="run_quality_repair_batch",
        work_unit_id="run_quality_repair_batch",
        work_unit_fingerprint=stage_route_fingerprint,
        runtime_health_epoch=(
            "stage-native-next-action::002-dm-china-us-mortality-attribution::"
            "08-publication_package_handoff"
        ),
        blocked_actions=["complete_medical_paper_readiness_surface", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="stage_native_workspace_next_action",
        generated_at="2026-06-08T02:24:04+00:00",
        owner_route=write_route,
        allowed_write_surfaces=["paper/draft.md", "paper/claim_evidence_map.json", "paper/review/**"],
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["current_owner_action"]["source"] == "stage_native_workspace_next_action"
    assert study["current_owner_action"]["action_type"] == "run_quality_repair_batch"
    assert study["current_owner_action"]["work_unit_id"] == "run_quality_repair_batch"
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == "run_quality_repair_batch"
    assert tasks[0]["payload"]["next_executable_owner"] == "write"
    assert "complete_medical_paper_readiness_surface" not in {
        task["payload"]["action_type"] for task in tasks
    }


def test_domain_handler_export_materializes_stage_native_identity_over_stale_writer_handoff_dispatch(
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
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "stage_index_ref": "control/stage_index.json",
            "current_stage_id": "08-publication_package_handoff",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
        },
    )
    stale_writer_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        work_unit_fingerprint="publication-blockers::stale-writer-handoff",
        runtime_health_epoch="runtime-health-event-stale-writer-handoff",
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="quality_repair_batch_writer_handoff",
        generated_at="2026-06-07T12:31:00+00:00",
        owner_route=stale_writer_route,
        allowed_write_surfaces=["paper/draft.md", "paper/claim_evidence_map.json", "paper/review/**"],
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["current_owner_action"]["source"] == "stage_native_workspace_next_action"
    assert study["current_owner_action"]["action_type"] == "run_quality_repair_batch"
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == "run_quality_repair_batch"
    assert tasks[0]["payload"]["dispatch_authority"] == "stage_native_workspace_next_action"
    basis = tasks[0]["payload"]["owner_route_currentness_basis"]
    assert basis["work_unit_id"] == "run_quality_repair_batch"
    assert basis["truth_epoch"] == (
        f"stage-native-next-action::{study_id}::08-publication_package_handoff"
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


def test_domain_handler_export_carries_stage_packet_for_recovery_successor_transition_request(
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
    _write_json(study_root / "study.yaml", {"study_id": study_id})
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    stage_packet_path = workspace_root / stage_packet_ref
    route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason=work_unit_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
        runtime_health_epoch=fingerprint,
        blocked_actions=[],
    )
    route["source_refs"] = {
        **route["source_refs"],
        "owner_route_currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-current",
        },
    }
    _write_json(stage_packet_path, {"surface": "default_executor_dispatch_request", "immutable": True})
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "dispatch_status": "ready",
            "dispatch_authority": None,
            "next_executable_owner": "write",
            "owner_route": route,
            "refs": {
                "dispatch_path": str(dispatch_path),
                "immutable_dispatch_path": str(stage_packet_path),
                "stage_packet_path": str(stage_packet_path),
            },
            "generated_at": "2026-06-16T04:54:52+00:00",
        },
    )

    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
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
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                    "runtime_health_epoch": "runtime-health-event-006980-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
                "next_work_unit": None,
            },
            "current_executable_owner_action": None,
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "current_authority": {
                    "obligation": {
                        "currentness_basis": {
                            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                            "runtime_health_epoch": "runtime-health-event-006980-current",
                        }
                    }
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": action_type,
                        "owner": "write",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_ref": str(
                            study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                        ),
                    },
                },
            },
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    [task] = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert task["reason"] == "current_control_transition_request_pending"
    assert task["stage_packet_ref"] == stage_packet_ref
    assert task["stage_packet_refs"] == [stage_packet_ref]
    assert task["payload"]["stage_packet_ref"] == stage_packet_ref
    assert task["payload"]["stage_packet_refs"] == [stage_packet_ref]
    assert task["payload"]["current_control_action"]["stage_packet_ref"] == stage_packet_ref
    assert task["payload"]["current_control_action"]["stage_packet_refs"] == [stage_packet_ref]
    assert task["payload"]["dispatch_ref"] == (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "run_quality_repair_batch.json"
    )
    assert task["payload"]["current_control_action"]["dispatch_ref"] == task["payload"]["dispatch_ref"]
    assert task["payload"]["provider_admission_pending"] is False
    assert task["payload"]["provider_admission_requires_opl_runtime_result"] is True
    assert "current_control_command_outbox_record" not in task["payload"]
    assert "stage_run_identity" not in task["payload"]


def test_domain_handler_export_keeps_consumed_owner_receipt_successor_transition_request(
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
    _write_json(study_root / "study.yaml", {"study_id": study_id})
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason=work_unit_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
        runtime_health_epoch=fingerprint,
        blocked_actions=[],
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
            "next_executable_owner": "write",
            "owner_route": route,
            "refs": {"dispatch_path": str(dispatch_path)},
            "generated_at": "2026-06-16T04:54:52+00:00",
        },
    )

    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                },
                "currentness_basis": {
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                    "runtime_health_epoch": "runtime-health-event-006980-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
                "action_type": action_type,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": action_type,
                "allowed_actions": [action_type],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "paper_recovery_state": {
                "phase": "owner_action_ready",
                "conditions": [
                    {
                        "condition": "consumed_owner_receipt_routeback_successor",
                        "source_condition": "current_work_unit_owner_receipt_recorded",
                    }
                ],
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": action_type,
                        "owner": "write",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_ref": str(
                            study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                        ),
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "identity_match": True,
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "provider_admission_terminal_closeout_consumed": {
                    "surface_kind": "provider_admission_terminal_closeout_consumed",
                    "stage_attempt_id": "sat_f22f2e9d25d336fa2a2a4306",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "owner_receipt_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                        "controller/repair_execution_receipts/latest.json"
                    ),
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": (
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                            "controller/repair_execution_receipts/latest.json"
                        ),
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "owner_receipt_recorded",
                    "owner": "write",
                },
            },
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    [task] = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert task["reason"] == "current_control_transition_request_pending"
    assert task["payload"]["current_control_action"]["status"] == "transition_request_pending"
    assert task["payload"]["provider_admission_requires_opl_runtime_result"] is True


def test_domain_handler_export_does_not_treat_nonconsumable_redrive_budget_as_domain_closeout(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / study_id
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "stage_index_ref": "control/stage_index.json",
            "current_stage_id": "08-publication_package_handoff",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
        },
    )
    route_fingerprint = (
        "stage-native-next-action::08-publication_package_handoff::"
        "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
    )
    write_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="run_quality_repair_batch",
        action_type="run_quality_repair_batch",
        work_unit_id="run_quality_repair_batch",
        work_unit_fingerprint=route_fingerprint,
        runtime_health_epoch=f"stage-native-next-action::{study_id}::08-publication_package_handoff",
        blocked_actions=["complete_medical_paper_readiness_surface", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="stage_native_workspace_next_action",
        generated_at="2026-06-08T02:24:04+00:00",
        owner_route=write_route,
        allowed_write_surfaces=["paper/draft.md", "paper/claim_evidence_map.json", "paper/review/**"],
    )
    executions = []
    for index in range(2):
        executions.append(
            {
                "surface": "default_executor_dispatch_execution",
                "schema_version": 1,
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_quality_repair_batch",
                "execution_status": "executed",
                "execution_id": f"execution::{study_id}::run_quality_repair_batch::ledger-only::{index}",
                "idempotency_key": write_route["idempotency_key"],
                "repeat_suppression_key": write_route["source_fingerprint"],
                "current_owner_route": write_route,
                "prompt_contract": {"owner_route": write_route},
                "owner_result": {
                    "status": "executed",
                    "ok": True,
                    "repair_execution_evidence": {
                        "status": "pending",
                        "blockers": ["evidence_ledger_update_missing"],
                        "changed_artifact_refs": [
                            {"path": str(study_root / "paper" / "claim_evidence_map.json")},
                            {"path": str(study_root / "paper" / "review" / "review_ledger.json")},
                        ],
                        "manuscript_surface_hygiene": {
                            "status": "clear",
                            "story_surface_delta_required": False,
                            "story_surface_delta_present": False,
                            "story_surface_delta_refs": [],
                            "blockers": [],
                        },
                    },
                    "quality_authorized": False,
                    "submission_authorized": False,
                    "current_package_write_authorized": False,
                },
            }
        )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": len(executions),
            "blocked_count": 0,
            "executions": executions,
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
    assert tasks[0]["payload"]["redrive_context"]["status"] == "non_consumable_closeout"
    assert tasks[0]["payload"]["redrive_context"]["next_action"] == "redrive_owner_route_with_closeout_context"


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

from .repair_progress_provider_admission_export_cases import *  # noqa: F403,F401,E402
