from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_runtime_escalation_record(module: object, quest_root: Path, study_root: Path) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    record = protocol.RuntimeEscalationRecord(
        schema_version=1,
        record_id="runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T05:55:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T05:55:00+00:00",
        trigger=protocol.RuntimeEscalationTrigger(
            trigger_id="startup_boundary_not_ready_for_resume",
            source="startup_boundary_gate",
        ),
        scope="quest",
        severity="quest",
        reason="startup_boundary_not_ready_for_resume",
        recommended_actions=("refresh_startup_hydration", "controller_review_required"),
        evidence_refs=(str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),),
        runtime_context_refs={"launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json")},
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
    )
    return protocol.write_runtime_escalation_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_runtime_event_record(
    quest_root: Path,
    study_root: Path,
    *,
    quest_id: str = "quest-001",
    quest_status: str = "paused",
    decision: str = "blocked",
    reason: str = "startup_boundary_not_ready_for_resume",
    active_run_id: str | None = None,
    runtime_liveness_status: str | None = "none",
    worker_running: bool | None = False,
    supervisor_tick_status: str | None = "fresh",
    runtime_escalation_ref: dict[str, str] | None = None,
) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    record = protocol.RuntimeEventRecord(
        schema_version=1,
        event_id=f"runtime-event::001-risk::{quest_id}::status_observed::2026-04-05T05:56:00+00:00",
        study_id="001-risk",
        quest_id=quest_id,
        emitted_at="2026-04-05T05:56:00+00:00",
        event_source="study_runtime_status",
        event_kind="status_observed",
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        status_snapshot={
            "quest_status": quest_status,
            "decision": decision,
            "reason": reason,
            "active_run_id": active_run_id,
            "runtime_liveness_status": runtime_liveness_status,
            "worker_running": worker_running,
            "continuation_policy": None,
            "continuation_reason": None,
            "supervisor_tick_status": supervisor_tick_status,
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
        outer_loop_input={
            "quest_status": quest_status,
            "decision": decision,
            "reason": reason,
            "active_run_id": active_run_id,
            "runtime_liveness_status": runtime_liveness_status,
            "worker_running": worker_running,
            "supervisor_tick_status": supervisor_tick_status,
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    return protocol.write_runtime_event_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_charter(study_root: Path) -> dict[str, str]:
    payload = {
        "charter_id": "charter::001-risk::v1",
        "publication_objective": "risk stratification external validation",
    }
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", payload)
    return {
        "charter_id": payload["charter_id"],
        "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
    }


def _write_publication_eval(study_root: Path, quest_root: Path) -> dict[str, str]:
    payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T05:58:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "summary": "Primary claim is ready to continue on the same line.",
            "stop_loss_pressure": "none",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "important",
                "summary": "External validation can still improve robustness.",
                "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "continue_same_line",
                "priority": "now",
                "reason": "Controller should continue the same study line.",
                "route_target": "write",
                "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                "route_rationale": "The publication gate is clear and the current paper line can continue through same-line manuscript work.",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return {
        "eval_id": payload["eval_id"],
        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
























































