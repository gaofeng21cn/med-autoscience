from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_nonconsumable_closeout,
    default_executor_execution_receipt_consumption,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _current_write_route() -> dict[str, object]:
    return {
        "idempotency_key": "owner-route::dm002::methods-reporting",
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "source_fingerprint": "truth-snapshot::current-methods-reporting",
        "runtime_health_epoch": "runtime-health-event-006254-fresh",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
        ),
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006254-fresh",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
                ),
                "work_unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
            },
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-006254-fresh",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
            ),
            "work_unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
        },
    }


def test_default_executor_receipt_consumes_prior_execution_from_ledger_after_later_action(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    current_route = _current_write_route()
    later_reviewer_route = {
        **current_route,
        "idempotency_key": "owner-route::dm002::later-ai-reviewer",
        "next_owner": "ai_reviewer",
        "owner_reason": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "work_unit_fingerprint": "sha256:later-ai-reviewer",
        "source_refs": {
            "owner_route_currentness_basis": {
                "owner_reason": "return_to_ai_reviewer_workflow",
                "truth_epoch": "paper-repair::later-ai-reviewer",
                "work_unit_fingerprint": "sha256:later-ai-reviewer",
                "work_unit_id": "quality_dimension_novelty_positioning::ai_reviewer_recheck",
            },
            "work_unit_id": "quality_dimension_novelty_positioning::ai_reviewer_recheck",
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::return_to_ai_reviewer_workflow::later",
                    "idempotency_key": later_reviewer_route["idempotency_key"],
                    "current_owner_route": later_reviewer_route,
                    "prompt_contract": {"owner_route": later_reviewer_route},
                    "owner_result": {"status": "executed", "ok": True},
                }
            ],
            "execution_ledger": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::methods-reporting",
                    "idempotency_key": current_route["idempotency_key"],
                    "current_owner_route": current_route,
                    "prompt_contract": {"owner_route": current_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
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
    assert receipt["execution_id"] == "execution::dm002::run_quality_repair_batch::methods-reporting"
    assert receipt["receipt_ref"] == "artifacts/supervision/consumer/default_executor_execution/latest.json#execution_ledger"


def test_default_executor_closeout_with_recovered_stage_packet_currentness_redrives(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = _current_write_route()
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::return_to_ai_reviewer_workflow::latest",
                    "owner_result": {"status": "executed", "ok": True},
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_story_delta.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_story_delta",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": (
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/default_executor_dispatches/run_quality_repair_batch.json"
            ),
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "closeout_id": "stage-attempt-closeout::sat_story_delta",
            "domain_execution": {
                "action_type": "run_quality_repair_batch",
                "execution_status": "blocked",
                "blocked_reason": "quality_repair_batch_current_manuscript_digest_mismatch",
                "domain_owner": "write",
            },
            "owner_receipt": {
                "status": "blocked",
                "typed_blocker": "quality_repair_batch_current_manuscript_digest_mismatch",
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "status": "closed_with_typed_domain_blocker",
            "route_outcome": "write_repair_delta_recorded",
            "artifact_delta": {
                "status": "progress_delta_candidate",
                "meaningful_artifact_delta": True,
                "story_surface_delta_present": True,
                "changed_artifact_refs": [
                    {"path": str(study_root / "paper" / "draft.md")},
                    {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                ],
            },
            "domain_completion_boundary": {
                "provider_completion_is_domain_completion": False,
                "domain_ready_verdict": "read_from_mas_publication_or_gate_surface",
            },
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json",
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "executor_kind": "codex_cli_default",
            "owner_route": owner_route,
            "prompt_contract": {"owner_route": owner_route},
        },
    )

    assert (
        default_executor_execution_receipt_consumption(
            study_root=study_root,
            owner_route=owner_route,
            actions=[{"action_type": "run_quality_repair_batch"}],
        )
        == {}
    )
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert redrive["status"] == "non_consumable_closeout"
    assert redrive["execution_id"] == "stage-attempt-closeout::sat_story_delta"
    assert redrive["receipt_ref"] == (
        "artifacts/supervision/consumer/default_executor_execution/sat_story_delta.closeout.json"
    )
    assert redrive["reason"] == "quality_repair_batch_current_manuscript_digest_mismatch"
