from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_nonconsumable_closeout,
    default_executor_execution_receipt_consumption,
)
from tests.owner_route_reconcile_cases.test_default_executor_receipt_consumption import _write_json


def test_consumes_record_only_ai_reviewer_owner_receipt_closeout(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = tmp_path / "studies" / study_id
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    work_unit_fingerprint = "sha256:b5bf5db0b484262f915f6fa5e179e40062604f17a97f43403576490c3a3a78cf"
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
        "route_epoch": "truth-event-000032-097fe584ce2a78fb",
        "runtime_health_epoch": "runtime-health-event-006600-1273d3d3f4f7dcfa",
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "current_owner": "ai_reviewer",
        "next_owner": "ai_reviewer",
        "owner_reason": "repair_progress_ai_reviewer_recheck_required",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "idempotency_key": f"ai-reviewer-record::{study_id}::{work_unit_fingerprint}",
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
                "runtime_health_epoch": "runtime-health-event-006600-1273d3d3f4f7dcfa",
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "ai-reviewer-record::20260605T080529Z::sat_9a259b52215b12db0c760e07"
                ),
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "owner_reason": "repair_progress_ai_reviewer_recheck_required",
            },
            "study_truth_epoch": "truth-event-000032-097fe584ce2a78fb",
            "runtime_health_epoch": "runtime-health-event-006600-1273d3d3f4f7dcfa",
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                "ai-reviewer-record::20260605T080529Z::sat_9a259b52215b12db0c760e07"
            ),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "blocked_reason": "repair_progress_ai_reviewer_recheck_required",
        },
    }
    immutable_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/return_to_ai_reviewer_workflow/09033e09c7ea1e2b4aba6671.json"
    )
    _write_json(
        tmp_path / immutable_packet_ref,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "executor_kind": "codex_cli_default",
            "owner_route": owner_route,
            "prompt_contract": {"owner_route": owner_route},
        },
    )
    closeout_ref = (
        f"artifacts/supervision/consumer/default_executor_execution/"
        "sat_3961f4c4b2e9335879a17891.closeout.json"
    )
    _write_json(
        study_root / closeout_ref,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_3961f4c4b2e9335879a17891",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "stage_packet_ref": immutable_packet_ref,
            "status": "closed_with_domain_owner_refs",
            "route_outcome": "owner_receipt",
            "owner_route_currentness": owner_route["source_refs"]["owner_route_currentness_basis"],
            "owner_receipt_ref": f"studies/{study_id}/{closeout_ref}#owner_receipt",
            "owner_receipt": {
                "status": "closed_with_domain_owner_refs",
                "owner": "ai_reviewer",
                "owner_callable_surface": "publication materialize-ai-reviewer-record",
                "publication_eval_record_ref": (
                    f"studies/{study_id}/artifacts/publication_eval/ai_reviewer_responses/"
                    "20260611T003454Z_publication_eval_record.json"
                ),
                "record_only_surface": True,
                "publication_eval_surface": "not_written",
                "publication_eval_latest_write_authorized": False,
                "controller_decision_write_authorized": False,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
                "paper_package_mutation_allowed": False,
                "typed_blocker": None,
            },
            "domain_execution": {
                "owner_callable_command_status": "materialized",
                "record_only_publication_eval_surface": "not_written",
                "downstream_materialize_dry_run_status": (
                    "recognized_next_owner_route_but_apply_not_allowed"
                ),
                "downstream_apply_blocked_reason": "github_user_lookup_failed",
            },
            "artifact_delta": {
                "meaningful_artifact_delta": True,
                "changed_artifact_refs": [
                    (
                        f"studies/{study_id}/artifacts/publication_eval/"
                        "ai_reviewer_responses/20260611T003454Z_publication_eval_record.json"
                    )
                ],
            },
            "paper_stage_log": {
                "stage_name": work_unit_id,
                "problem_summary": "AI reviewer record was materialized as a record-only owner receipt.",
                "stage_goal": "Produce the current AI reviewer record without mutating publication authority.",
                "stage_work_done": [
                    "Materialized record-only AI reviewer publication evaluation evidence.",
                ],
                "paper_work_done": [
                    "Materialized record-only AI reviewer publication evaluation evidence.",
                ],
                "changed_stage_surfaces": [
                    (
                        f"studies/{study_id}/artifacts/publication_eval/"
                        "ai_reviewer_responses/20260611T003454Z_publication_eval_record.json"
                    )
                ],
                "changed_paper_surfaces": [
                    (
                        f"studies/{study_id}/artifacts/publication_eval/"
                        "ai_reviewer_responses/20260611T003454Z_publication_eval_record.json"
                    )
                ],
                "outcome": "closed_with_domain_owner_refs",
                "remaining_blockers": [],
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
                    "work_unit_id": "current_package_freshness_required",
                    "owner_action": {
                        "next_owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "current_package_freshness_required",
                    },
                },
                "evidence_refs": [
                    (
                        f"studies/{study_id}/artifacts/publication_eval/"
                        "ai_reviewer_responses/20260611T003454Z_publication_eval_record.json"
                    )
                ],
            },
            "closeout_refs": [
                f"studies/{study_id}/{closeout_ref}",
                (
                    f"studies/{study_id}/artifacts/publication_eval/ai_reviewer_responses/"
                    "20260611T003454Z_publication_eval_record.json"
                ),
                immutable_packet_ref,
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "return_to_ai_reviewer_workflow"}],
    )
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "return_to_ai_reviewer_workflow"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["receipt_ref"] == closeout_ref
    assert receipt["owner_result_status"] == "closed_with_domain_owner_refs"
    assert receipt["owner_receipt_ref"] == f"studies/{study_id}/{closeout_ref}#owner_receipt"
    assert receipt["work_unit_id"] == work_unit_id
    assert receipt["work_unit_fingerprint"] == work_unit_fingerprint
    assert receipt["next_action"] == "do_not_redrive_consumed_owner_route"
    assert redrive == {}
