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


def test_default_executor_blocked_closeout_supersedes_older_executed_closeout(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = _current_write_route()
    dispatch_ref = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(
        dispatch_ref,
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
    closeout_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution"
    _write_json(
        closeout_root / "sat_f6_latest.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_f6_latest",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": (
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/default_executor_dispatches/run_quality_repair_batch.json"
            ),
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "closeout_id": "stage-attempt-closeout::sat_f6_latest::manuscript_story_surface_delta_missing",
            "domain_execution": {
                "action_type": "run_quality_repair_batch",
                "execution_status": "blocked",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "domain_owner": "write",
            },
            "owner_receipt": {
                "status": "blocked",
                "typed_blocker": "manuscript_story_surface_delta_missing",
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "status": "blocked_with_domain_owner_refs",
            "artifact_delta": {
                "status": "blocked",
                "meaningful_artifact_delta": False,
                "story_surface_delta_present": False,
                "changed_artifact_refs": [],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
            },
        },
    )
    _write_json(
        closeout_root / "sat_ef_old.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_ef_old",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": (
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/default_executor_dispatches/run_quality_repair_batch.json"
            ),
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "closeout_id": "stage-attempt-closeout::sat_ef_old::previous",
            "domain_execution": {
                "action_type": "run_quality_repair_batch",
                "execution_status": "executed",
                "domain_owner": "write",
            },
            "owner_receipt": {
                "status": "closed_with_domain_owner_refs",
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "status": "closed_with_domain_owner_refs",
            "artifact_delta": {
                "status": "closed_with_domain_owner_refs",
                "meaningful_artifact_delta": False,
                "story_surface_delta_present": False,
                "changed_artifact_refs": [],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
            },
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
    assert redrive["execution_id"] == "stage-attempt-closeout::sat_f6_latest::manuscript_story_surface_delta_missing"
    assert redrive["receipt_ref"] == (
        "artifacts/supervision/consumer/default_executor_execution/sat_f6_latest.closeout.json"
    )
    assert redrive["execution_status"] == "blocked"
    assert redrive["reason"] == "manuscript_story_surface_delta_missing"


def test_default_executor_stage_closeout_embedded_currentness_consumes_story_surface_typed_blocker(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    owner_route = {
        **_current_write_route(),
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
        ),
        "source_refs": {
            "owner_route_currentness_basis": {
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
                ),
                "work_unit_id": "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
            },
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
            ),
            "work_unit_id": "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
        },
    }
    closeout_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution"
    _write_json(
        closeout_root / "sat_dm002_live.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": "sat_dm002_live",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": (
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/default_executor_dispatches/run_quality_repair_batch.json"
            ),
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "closeout_id": (
                "stage-attempt-closeout::sat_dm002_live::"
                "manuscript_story_surface_delta_missing"
            ),
            "owner_route_basis": {
                "work_unit_id": "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
                ),
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006285-1c4dfb5879325bcc",
            },
            "domain_execution": {
                "action_type": "run_quality_repair_batch",
                "execution_status": "blocked",
                "blocked_reason": "domain_owner_action_dispatch_execution_count_zero",
                "domain_owner": "write",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
            },
            "owner_receipt": {
                "status": "blocked",
                "typed_blocker": "manuscript_story_surface_delta_missing",
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "status": "blocked_with_domain_owner_refs",
            "blocked_reason": "domain_owner_action_dispatch_execution_count_zero",
            "artifact_delta": {
                "status": "blocked",
                "meaningful_artifact_delta": False,
                "story_surface_delta_present": False,
                "changed_artifact_refs": [],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
            },
            "closeout_refs": [
                "artifacts/supervision/consumer/default_executor_execution/sat_dm002_live.closeout.json",
                "artifacts/publication_eval/latest.json",
            ],
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

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["execution_status"] == "blocked"
    assert receipt["owner_result_status"] == "blocked"
    assert receipt["repair_execution_evidence_status"] == "blocked"
    assert receipt["next_action"] == "do_not_redrive_consumed_owner_route"
    assert default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    ) == {}
