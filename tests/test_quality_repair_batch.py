from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_blocked_publication_eval(study_root: Path, *, quest_id: str) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_root.name}::{quest_id}::2026-04-22T08:00:00+00:00",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-04-22T08:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Current paper needs deterministic quality repair before the gate can be trusted.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "claim_evidence_map_missing_or_incomplete",
                "evidence_refs": [str(study_root / "paper")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::quality-repair::2026-04-22T08:00:00+00:00",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Return to the same paper line for deterministic quality repair.",
                "route_target": "review",
                "route_key_question": "Which deterministic quality repair is still blocking publishability?",
                "route_rationale": "Structured quality blockers remain before publishability gate replay.",
                "evidence_refs": [str(study_root / "paper")],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_quality_summary(study_root: Path) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "summary_id": f"evaluation-summary::{study_root.name}::2026-04-22T08:01:00+00:00",
        "study_id": study_root.name,
        "quest_id": "quest-001",
        "emitted_at": "2026-04-22T08:01:00+00:00",
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "summary": "Hard publication-quality blockers remain open.",
            "current_required_action": "return_to_publishability_gate",
            "route_target": "review",
        },
        "quality_execution_lane": {
            "lane_id": "general_quality_repair",
            "lane_label": "General quality repair",
            "repair_mode": "deterministic_batch",
            "route_target": "review",
            "route_key_question": "Which deterministic claim-evidence/display repair is still blocking publishability?",
            "summary": "Run deterministic repair units, then replay the publishability gate.",
            "why_now": "The paper gate is blocked by structured quality surfaces.",
        },
    }
    _write_json(study_root / "artifacts" / "evaluation_summary" / "latest.json", payload)
    return payload


def test_build_quality_repair_batch_action_for_general_quality_repair_lane(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    _write_quality_summary(study_root)
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_map_missing_or_incomplete",
            "table_catalog_missing_or_incomplete",
        ],
        "bundle_tasks_downstream_only": False,
    }

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["route_target"] == "review"
    assert action["controller_action_type"] == "run_quality_repair_batch"
    assert action["quality_repair_batch_reason"] == (
        "quality_closure_truth requires deterministic repair; "
        "paper-facing display/reporting blockers are deterministic repair candidates"
    )


def test_run_quality_repair_batch_wraps_gate_clearing_and_writes_record(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    quality_summary = _write_quality_summary(study_root)
    gate_result = {
        "ok": True,
        "status": "executed",
        "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        "gate_replay": {
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        },
        "unit_results": [{"unit_id": "materialize_display_surface", "status": "updated"}],
    }
    seen: dict[str, object] = {}
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (seen.setdefault("kwargs", kwargs), gate_result)[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    assert seen["kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert result["source_summary_id"] == quality_summary["summary_id"]
    assert result["gate_clearing_batch"]["gate_replay"]["status"] == "blocked"
    record = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert record["quality_closure_state"] == "quality_repair_required"
    assert record["quality_execution_lane_id"] == "general_quality_repair"


def test_study_outer_loop_executes_quality_repair_batch_controller_action(monkeypatch, tmp_path: Path) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    runtime_protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "controller" / "study_charter.json",
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        outer_loop.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-22T08:00:00+00:00",
                "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
        },
    )
    monkeypatch.setattr(
        outer_loop,
        "_resolve_runtime_escalation_record",
        lambda **_: (
            runtime_protocol.RuntimeEscalationRecordRef(
                record_id="runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-22T08:00:00+00:00",
                artifact_path=str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            ),
            None,
        ),
    )
    monkeypatch.setattr(
        outer_loop.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **kwargs: (
            seen.setdefault("batch_kwargs", kwargs),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = outer_loop.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref={
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        publication_eval_ref={
            "eval_id": publication_eval_payload["eval_id"],
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        decision_type="route_back_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Quality repair batch should run before resuming the same paper line.",
        source="test-source",
        recorded_at="2026-04-22T08:02:00+00:00",
    )

    assert seen["batch_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert result["executed_controller_action"]["action_type"] == "run_quality_repair_batch"
    assert result["executed_controller_action"]["result"] == {"ok": True, "status": "executed"}
