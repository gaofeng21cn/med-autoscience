from __future__ import annotations

import json
import importlib
from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_nonconsumable_closeout,
    default_executor_execution_receipt_consumption,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_gate_replay_closeout_with_incomplete_stage_log_consumes_as_typed_blocker(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_incomplete"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{source_eval_id}"
    )
    owner_route = {
        "route_epoch": "truth-event-000032-097fe584ce2a78fb",
        "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
        "runtime_health_epoch": "runtime-health-event-006596-c5963ea7240e495b",
        "source_eval_id": source_eval_id,
        "work_unit_fingerprint": fingerprint,
        "next_owner": "gate_clearing_batch",
        "owner_reason": "publication gate replay after current AI reviewer record",
        "allowed_actions": ["run_gate_clearing_batch"],
        "idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
                "runtime_health_epoch": "runtime-health-event-006596-c5963ea7240e495b",
                "source_eval_id": source_eval_id,
                "work_unit_fingerprint": fingerprint,
                "work_unit_id": work_unit_id,
                "owner_reason": "publication gate replay after current AI reviewer record",
            },
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
        },
    }
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat_incomplete_stage_log.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_incomplete_stage_log",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "status": "completed",
            "execution_status": "executed",
            "owner_route_currentness": {
                "truth_epoch": owner_route["truth_epoch"],
                "runtime_health_epoch": owner_route["runtime_health_epoch"],
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "owner_reason": owner_route["owner_reason"],
            },
            "owner_receipt": {
                "owner": "gate_clearing_batch",
                "status": "executed",
                "publication_eval_latest_write_authorized": False,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "domain_execution": {
                "domain_owner": "gate_clearing_batch",
                "execution_status": "executed",
                "gate_replay_status": "blocked",
                "publication_work_unit_lifecycle_status": "blocked",
                "publication_gate_report_json": (
                    f"runtime/quests/{study_id}/artifacts/reports/publishability_gate/"
                    "2026-06-10T233125Z.json"
                ),
            },
            "paper_stage_log": {
                "outcome": "blocked_with_domain_typed_blocker",
                "next_forced_delta": {
                    "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                    "work_unit_id": work_unit_id,
                    "owner_action": {
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                    },
                },
            },
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/stage_attempt_closeouts/"
                "sat_incomplete_stage_log.json",
                f"runtime/quests/{study_id}/artifacts/reports/publishability_gate/"
                "2026-06-10T233125Z.json",
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_gate_clearing_batch"}],
    )
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_gate_clearing_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["action_type"] == "run_gate_clearing_batch"
    assert receipt["execution_status"] == "executed"
    assert receipt["outcome"] == "typed_blocker"
    assert receipt["blocked_reason"] == "domain_closeout_provided_incomplete_user_stage_log"
    assert receipt["typed_blocker"]["reason"] == "domain_closeout_provided_incomplete_user_stage_log"
    assert receipt["typed_blocker_ref"] == (
        "artifacts/supervision/consumer/stage_attempt_closeouts/sat_incomplete_stage_log.json"
    )
    assert receipt["work_unit_id"] == work_unit_id
    assert receipt["work_unit_fingerprint"] == fingerprint
    assert receipt["changed_artifact_ref_count"] == 0
    assert receipt["next_action"] == "honor_typed_blocker_without_redrive"
    assert redrive == {}


def test_quality_repair_stage_packet_currentness_closeout_consumes_as_typed_blocker(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
    owner_route = {
        "truth_epoch": "truth-event-000041-dm002",
        "route_epoch": "truth-event-000041-dm002",
        "runtime_health_epoch": "runtime-health-event-006950-dm002",
        "work_unit_fingerprint": fingerprint,
        "next_owner": "write",
        "allowed_actions": ["run_quality_repair_batch"],
        "idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000041-dm002",
                "runtime_health_epoch": "runtime-health-event-006950-dm002",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }
    closeout_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
        "sat_stage_packet_currentness.closeout.json"
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_stage_packet_currentness.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_stage_packet_currentness",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "outcome": "typed_blocker",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "schema_version": 1,
                "status": "blocked",
                "blocker_id": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                "blocker_type": "stage_packet_not_current_selected_dispatch",
                "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                "owner": "one-person-lab",
                "write_permitted": False,
            },
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "default-executor-dispatch:run_quality_repair_batch",
                "problem_summary": "The supplied quality repair stage packet was not current-selected.",
                "stage_goal": "Return an owner receipt or typed blocker for the selected quality repair packet.",
                "stage_work_done": ["Checked the current dispatch identity."],
                "paper_work_done": ["No paper surfaces were changed."],
                "changed_stage_surfaces": [closeout_ref],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker",
                "remaining_blockers": ["stage_packet_not_current_selected_dispatch"],
                "duration": {"status": "missing", "seconds": None},
                "token_usage": {"status": "missing", "total_tokens": None},
                "cost": {"status": "missing", "usd": None},
                "usage_refs": [],
                "cost_refs": [],
                "progress_delta_classification": "typed_blocker",
                "deliverable_progress_delta": {"count": 0, "refs": [], "token_usage_total": None},
                "paper_progress_delta": {"count": 0, "refs": [], "token_usage_total": None},
                "platform_repair_delta": {"count": 1, "refs": [closeout_ref], "token_usage_total": None},
                "next_forced_delta": {
                    "required_delta_kind": "owner_receipt_or_typed_blocker_selected_by_mas_domain_owner_dispatch",
                    "work_unit_id": work_unit_id,
                    "owner_action": {
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                    "reason": "typed_blocker::stage_packet_not_current_selected_dispatch",
                },
                "evidence_refs": [closeout_ref],
            },
            "closeout_refs": [closeout_ref],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["action_type"] == "run_quality_repair_batch"
    assert receipt["outcome"] == "typed_blocker"
    assert receipt["blocked_reason"] == "stage_packet_not_current_selected_dispatch"
    assert receipt["typed_blocker"]["blocker_type"] == "stage_packet_not_current_selected_dispatch"
    assert receipt["work_unit_id"] == work_unit_id
    assert receipt["work_unit_fingerprint"] == fingerprint
    assert receipt["changed_artifact_ref_count"] == 0
    assert receipt["next_action"] == "honor_typed_blocker_without_redrive"
    assert redrive == {}


def test_stage_log_workbench_projection_is_refs_only_body_free_read_model(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    closeout_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/stage_attempt_closeouts/"
        "sat_workbench_projection.json"
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "stage_attempt_closeouts" / "sat_workbench_projection.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-06-11T08:30:00+00:00",
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_workbench_projection",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "status": "completed",
            "duration": {
                "status": "missing",
                "seconds": None,
                "missing_duration_reason": "no_terminal_stage_duration_observed",
            },
            "token_usage": {
                "status": "missing",
                "total_tokens": None,
                "missing_token_usage_reason": "no_terminal_stage_token_usage_observed",
            },
            "cost": {
                "status": "missing",
                "usd": None,
                "missing_cost_reason": "no_terminal_stage_cost_observed",
            },
            "usage_refs": [f"{closeout_ref}#usage"],
            "cost_refs": [f"{closeout_ref}#cost"],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "publication gate replay",
                "current_owner": "gate_clearing_batch",
                "problem_summary": "Gate replay ended with a typed blocker.",
                "stage_goal": "Produce a gate replay owner receipt or typed blocker.",
                "stage_work_done": ["Recorded the replay closeout and blocker refs."],
                "paper_work_done": [],
                "changed_stage_surfaces": [
                    f"{closeout_ref}#stage-log",
                    f"{closeout_ref}#semantic-gap",
                ],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker",
                "remaining_blockers": ["domain_closeout_provided_incomplete_user_stage_log"],
                "duration": {
                    "status": "missing",
                    "seconds": None,
                    "missing_duration_reason": "no_terminal_stage_duration_observed",
                },
                "token_usage": {
                    "status": "missing",
                    "total_tokens": None,
                    "missing_token_usage_reason": "no_terminal_stage_token_usage_observed",
                },
                "cost": {
                    "status": "missing",
                    "usd": None,
                    "missing_cost_reason": "no_terminal_stage_cost_observed",
                },
                "usage_refs": [f"{closeout_ref}#usage"],
                "cost_refs": [f"{closeout_ref}#cost"],
                "progress_delta_classification": "platform_repair",
                "deliverable_progress_delta": {"count": 0, "token_usage_total": None},
                "paper_progress_delta": {"count": 0, "token_usage_total": None},
                "platform_repair_delta": {"count": 1, "token_usage_total": None},
                "next_forced_delta": {
                    "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                    "work_unit_id": work_unit_id,
                    "target_surface": {"surface_ref": "publication_gate/latest.json"},
                    "owner_action": {
                        "next_owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                    },
                    "acceptance_refs": ["owner_receipt_ref", "typed_blocker_ref"],
                    "reason": "typed_blocker::publication_gate_replay_blocked",
                },
                "evidence_refs": [closeout_ref],
            },
            "closeout_refs": [closeout_ref],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.managed_runtime_home / "quests" / study_id),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_health_snapshot": {"health_status": "blocked"},
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)

    terminal = result["opl_current_control_state_handoff"]["latest_terminal_stage_log"]
    summary = terminal["stage_log_workbench_summary"]
    assert summary["surface_kind"] == "mas_stage_log_workbench_summary"
    assert summary["read_model"] == "stage_log_minimum_viability_workbench_projection"
    assert summary["body_policy"] == "refs_only_body_free"
    assert summary["authority_boundary"] == {
        "refs_only": True,
        "body_free": True,
        "observability_only": True,
        "can_mark_domain_ready": False,
        "can_write_paper_truth": False,
        "can_authorize_quality_verdict": False,
        "can_block_provider_admission": False,
    }
    assert summary["stage_goal"] == {
        "field": "stage_goal",
        "status": "present",
        "item_count": 1,
        "refs": [closeout_ref],
        "body_included": False,
    }
    assert summary["actual_work"]["field"] == "stage_work_done"
    assert summary["actual_work"]["body_included"] is False
    assert summary["actual_work"]["item_count"] == 1
    assert summary["paper_delta"]["status"] == "present"
    assert summary["paper_delta"]["count"] == 0
    assert summary["deliverable_delta"]["status"] == "present"
    assert summary["platform_delta"]["count"] == 1
    assert summary["platform_delta"]["changed_surface_refs"] == [
        f"{closeout_ref}#stage-log",
        f"{closeout_ref}#semantic-gap",
    ]
    assert summary["observability"] == {
        "status": "missing",
        "duration": {
            "status": "missing",
            "missing_reason": "no_terminal_stage_duration_observed",
        },
        "token_usage": {
            "status": "missing",
            "missing_reason": "no_terminal_stage_token_usage_observed",
        },
        "cost": {
            "status": "missing",
            "missing_reason": "no_terminal_stage_cost_observed",
        },
        "missing_fields": ["duration", "token_usage", "cost"],
    }
    assert summary["evidence_refs"] == [closeout_ref]
    assert summary["usage_refs"] == [f"{closeout_ref}#usage"]
    assert summary["cost_refs"] == [f"{closeout_ref}#cost"]
    assert summary["next_forced_delta"] == {
        "required_delta_kind": "paper_progress_delta_or_typed_blocker",
        "reason": "typed_blocker::publication_gate_replay_blocked",
        "work_unit_id": work_unit_id,
        "target_surface": {"surface_ref": "publication_gate/latest.json"},
        "acceptance_refs": ["owner_receipt_ref", "typed_blocker_ref"],
        "owner_action": {
            "next_owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
        },
        "body_included": False,
    }
    assert "stage_work_done" not in summary
    assert "paper_work_done" not in summary
    assert compact["opl_current_control_state_handoff"]["latest_terminal_stage_log"][
        "stage_log_workbench_summary"
    ]["body_policy"] == "refs_only_body_free"
    assert "latest_terminal_stage_workbench_summary" in markdown
