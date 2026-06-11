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
