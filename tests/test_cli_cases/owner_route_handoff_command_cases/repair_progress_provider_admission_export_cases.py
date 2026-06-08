from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import *  # noqa: F403,F401
from .default_executor_current_owner_action_shared import _owner_route, _write_dispatch


def test_domain_handler_export_prefers_repair_progress_provider_admission_identity_over_stage_native_next_action(
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
    old_stage_route = _owner_route(
        study_id=study_id,
        next_owner="write",
        owner_reason="run_quality_repair_batch",
        action_type="run_quality_repair_batch",
        work_unit_id="run_quality_repair_batch",
        work_unit_fingerprint=(
            "stage-native-next-action::08-publication_package_handoff::"
            "run_quality_repair_batch::artifacts/reports/medical_publication_surface/latest.json"
        ),
        runtime_health_epoch=(
            "stage-native-next-action::002-dm-china-us-mortality-attribution::"
            "08-publication_package_handoff"
        ),
        blocked_actions=["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
    )
    _write_dispatch(
        workspace_root=workspace_root,
        study_id=study_id,
        filename="run_quality_repair_batch.json",
        action_type="run_quality_repair_batch",
        next_owner="write",
        dispatch_authority="stage_native_workspace_next_action",
        generated_at="2026-06-08T02:24:04+00:00",
        owner_route=old_stage_route,
        allowed_write_surfaces=["paper/draft.md", "paper/claim_evidence_map.json"],
    )

    draft = study_root / "paper" / "draft.md"
    evidence_ledger = study_root / "paper" / "evidence_ledger.json"
    for path in (draft, evidence_ledger):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    repair_evidence = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    repair_receipt = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    ai_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    gate_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    _write_json(
        repair_evidence,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "repair-progress-current-source",
            "repair_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "source_eval_id": "publication-eval::dm002::current",
            },
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                ],
            },
            "changed_artifact_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "ai_reviewer_recheck_request_ref": str(ai_request),
            "gate_replay_refs": [str(gate_request)],
        },
    )
    _write_json(
        repair_receipt,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "medical_prose_write_repair",
            "execution_status": "progress_delta_candidate",
            "canonical_artifact_delta_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "repair_execution_evidence_ref": str(repair_evidence),
            "ai_reviewer_recheck_request_ref": str(ai_request),
            "gate_replay_request_ref": str(gate_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )

    current_work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    current_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs::"
        "return_to_ai_reviewer_workflow"
    )
    current_basis = {
        "runtime_health_epoch": "runtime-health-event-current",
        "source_eval_id": "publication-eval::dm002::current",
        "truth_epoch": "truth-event-current",
        "work_unit_fingerprint": current_fingerprint,
        "work_unit_id": current_work_unit_id,
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "write",
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "dispatch_path": str(dispatch_path),
                    "dispatch_authority": "quality_repair_batch_writer_handoff",
                    "action_fingerprint": current_fingerprint,
                    "owner_route": {
                        "surface": "domain_route_owner_route",
                        "schema_version": 2,
                        "study_id": study_id,
                        "quest_id": study_id,
                        "truth_epoch": "truth-event-current",
                        "runtime_health_epoch": "runtime-health-event-current",
                        "work_unit_fingerprint": current_fingerprint,
                        "source_fingerprint": current_fingerprint,
                        "current_owner": "mas_controller",
                        "next_owner": "write",
                        "owner_reason": current_work_unit_id,
                        "allowed_actions": ["run_quality_repair_batch"],
                        "blocked_actions": ["return_to_ai_reviewer_workflow"],
                        "source_refs": {
                            "work_unit_id": current_work_unit_id,
                            "work_unit_fingerprint": current_fingerprint,
                            "blocked_reason": "manuscript_story_surface_delta_missing",
                            "owner_route_currentness_basis": current_basis,
                        },
                    },
                }
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    action = study["current_owner_action"]
    assert action["source"] == "default_executor_execution.provider_admission_identity"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == current_work_unit_id
    for key, value in current_basis.items():
        assert action["owner_route_currentness_basis"][key] == value
    tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ]
    assert [task["payload"]["action_type"] for task in tasks] == ["run_quality_repair_batch"]
    assert tasks[0]["payload"]["work_unit_id"] == current_work_unit_id
    assert tasks[0]["payload"]["provider_admission_identity"]["action_fingerprint"] == current_fingerprint
    assert tasks[0]["source_fingerprint"] == current_fingerprint
