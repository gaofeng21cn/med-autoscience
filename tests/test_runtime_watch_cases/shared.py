from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_quest(tmp_path: Path, name: str, status: str = "running") -> Path:
    quest_root = tmp_path / "runtime" / "quests" / name
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": name,
            "status": status,
            "active_run_id": "run-1" if status in {"running", "active"} else None,
        },
    )
    return quest_root


def make_study_runtime_status_payload(
    *,
    study_id: str = "001-risk",
    decision: str = "create_and_start",
    reason: str = "quest_missing",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": f"/tmp/studies/{study_id}",
        "entry_mode": "full_research",
        "execution": {"quest_id": study_id, "auto_resume": True},
        "quest_id": study_id,
        "quest_root": f"/tmp/runtime/quests/{study_id}",
        "quest_exists": True,
        "quest_status": "created",
        "runtime_binding_path": f"/tmp/studies/{study_id}/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": decision,
        "reason": reason,
    }


def _write_runtime_escalation_record(quest_root: Path, study_root: Path) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    dump_json(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        {
            "recorded_at": "2026-04-05T05:54:00+00:00",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
        },
    )
    record = protocol.RuntimeEscalationRecord(
        schema_version=1,
        record_id="runtime-escalation::001-risk::quest-001::quest_stopped_requires_explicit_rerun::2026-04-05T05:55:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T05:55:00+00:00",
        trigger=protocol.RuntimeEscalationTrigger(
            trigger_id="quest_stopped_requires_explicit_rerun",
            source="runtime_watch",
        ),
        scope="quest",
        severity="quest",
        reason="quest_stopped_requires_explicit_rerun",
        recommended_actions=("controller_review_required",),
        evidence_refs=(str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),),
        runtime_context_refs={"launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json")},
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
    )
    return protocol.write_runtime_escalation_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_runtime_event_record(
    quest_root: Path,
    study_root: Path,
    *,
    runtime_escalation_ref: dict[str, str],
) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    record = protocol.RuntimeEventRecord(
        schema_version=1,
        event_id="runtime-event::001-risk::quest-001::status_observed::2026-04-05T05:56:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T05:56:00+00:00",
        event_source="study_runtime_status",
        event_kind="status_observed",
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        status_snapshot={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "active_run_id": None,
            "runtime_liveness_status": "none",
            "worker_running": False,
            "continuation_policy": None,
            "continuation_reason": None,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
        outer_loop_input={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "active_run_id": None,
            "runtime_liveness_status": "none",
            "worker_running": False,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    return protocol.write_runtime_event_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_charter(study_root: Path) -> dict[str, str]:
    payload = {
        "schema_version": 1,
        "charter_id": "charter::001-risk::v1",
        "study_id": "001-risk",
        "publication_objective": "risk stratification external validation",
    }
    dump_json(study_root / "artifacts" / "controller" / "study_charter.json", payload)
    return {
        "charter_id": payload["charter_id"],
        "artifact_path": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
    }


def _write_publication_eval(
    study_root: Path,
    quest_root: Path,
    *,
    action_type: str = "continue_same_line",
    reason: str = "Controller should continue the same study line.",
) -> dict[str, str]:
    if action_type == "bounded_analysis":
        route_target = "analysis-campaign"
        route_key_question = "What is the narrowest supplementary analysis still required before the paper line can continue?"
        route_rationale = "The current line is clear enough to continue after one bounded supplementary analysis pass."
    elif action_type == "continue_same_line":
        route_target = "write"
        route_key_question = "What is the narrowest same-line manuscript repair or continuation step required now?"
        route_rationale = "The publication gate is clear and the current paper line can continue through same-line manuscript work."
    else:
        route_target = None
        route_key_question = None
        route_rationale = None
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::001-risk::quest-001::{action_type}::2026-04-05T05:58:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T05:58:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(
                (quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json").resolve()
            ),
            "main_result_ref": str((quest_root / "artifacts" / "results" / "main_result.json").resolve()),
        },
        "delivery_context_refs": {
            "paper_root_ref": str((study_root / "paper").resolve()),
            "submission_minimal_ref": str((study_root / "paper" / "submission_minimal" / "submission_manifest.json").resolve()),
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
                "evidence_refs": [str((quest_root / "artifacts" / "results" / "main_result.json").resolve())],
            }
        ],
        "recommended_actions": [
            {
                "action_id": f"action::{action_type}",
                "action_type": action_type,
                "priority": "now",
                "reason": reason,
                **(
                    {
                        "route_target": route_target,
                        "route_key_question": route_key_question,
                        "route_rationale": route_rationale,
                    }
                    if route_target is not None
                    else {}
                ),
                "evidence_refs": [str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve())],
                "requires_controller_decision": True,
            }
        ],
    }
    dump_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return {
        "eval_id": payload["eval_id"],
        "artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
    }















































































































