from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_receipt_consumption,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_default_executor_receipt_rejects_same_handoff_key_when_source_eval_advances(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    current_eval_id = "publication-eval::dm003::current-manuscript::20260528T125118Z"
    old_eval_id = "publication-eval::dm003::medical-prose-routeback::sha256-old"
    handoff_key = (
        "quality-repair-writer-handoff::003-dpcc-primary-care-phenotype-treatment-gap::"
        "domain-transition::route_back_same_line::medical_prose_write_repair"
    )
    current_route = {
        "idempotency_key": handoff_key,
        "route_epoch": current_eval_id,
        "truth_epoch": current_eval_id,
        "source_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "source_eval_id": current_eval_id,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            "study_truth_epoch": current_eval_id,
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "owner_route_currentness_basis": {
                "source_eval_id": current_eval_id,
                "truth_epoch": current_eval_id,
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "work_unit_id": "medical_prose_write_repair",
                "owner_reason": "manuscript_story_surface_delta_missing",
            },
        },
    }
    old_route = {
        **current_route,
        "truth_epoch": old_eval_id,
        "route_epoch": old_eval_id,
        "source_refs": {
            **current_route["source_refs"],
            "source_eval_id": old_eval_id,
            "study_truth_epoch": old_eval_id,
            "owner_route_currentness_basis": {
                **current_route["source_refs"]["owner_route_currentness_basis"],
                "source_eval_id": old_eval_id,
                "truth_epoch": old_eval_id,
            },
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_root.name,
                    "quest_id": study_root.name,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm003::run_quality_repair_batch::old-eval",
                    "idempotency_key": handoff_key,
                    "current_owner_route": old_route,
                    "prompt_contract": {"owner_route": old_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "manuscript_story_surface_delta_present",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "draft.md")},
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=current_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt == {}


def test_default_executor_receipt_consumes_when_only_diagnostic_owner_reason_changes(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    current_eval_id = "publication-eval::dm003::current-manuscript::20260528T125118Z"
    current_route = {
        "idempotency_key": "owner-route::dm003::current-writer-route",
        "route_epoch": current_eval_id,
        "truth_epoch": current_eval_id,
        "source_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "source_eval_id": current_eval_id,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            "study_truth_epoch": current_eval_id,
            "owner_route_currentness_basis": {
                "source_eval_id": current_eval_id,
                "truth_epoch": current_eval_id,
                "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                "work_unit_id": "medical_prose_write_repair",
                "owner_reason": "manuscript_story_surface_delta_missing",
            },
        },
    }
    execution_route = {
        **current_route,
        "idempotency_key": "owner-route::dm003::old-reason-key",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "failure_signature": "quest_waiting_opl_runtime_owner_route",
        "source_refs": {
            **current_route["source_refs"],
            "owner_route_currentness_basis": {
                **current_route["source_refs"]["owner_route_currentness_basis"],
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
            },
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_root.name,
                    "quest_id": study_root.name,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm003::run_quality_repair_batch::reason-drift",
                    "idempotency_key": execution_route["idempotency_key"],
                    "current_owner_route": execution_route,
                    "prompt_contract": {"owner_route": execution_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "manuscript_story_surface_delta_present",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "draft.md")},
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=current_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["execution_id"] == "execution::dm003::run_quality_repair_batch::reason-drift"
