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
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Return to the same paper line for deterministic quality repair.",
                "evidence_refs": [str(study_root / "paper")],
                "work_unit_fingerprint": "publication-blockers::generic",
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Ask the publication gate to identify concrete blocker targets.",
                },
                "blocking_work_units": [
                    {
                        "unit_id": "gate_needs_specificity",
                        "lane": "controller",
                        "summary": "Ask the publication gate to identify concrete blocker targets.",
                    }
                ],
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                    {
                        "target_kind": "metric",
                        "target_id": "main_result_metrics",
                        "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                    {
                        "target_kind": "table",
                        "target_id": "submission_table_or_manifest",
                        "source_path": str(
                            study_root / "paper" / "submission_minimal" / "audit" / "submission_manifest.json"
                        ),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                    {
                        "target_kind": "source_path",
                        "target_id": "publication_gate_source_path",
                        "source_path": str(
                            study_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
                        ),
                        "blocking_reason": "medical_publication_surface_blocked",
                    },
                ],
                "requires_controller_decision": True,
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return payload


def _write_quality_summary(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": f"evaluation-summary::{study_root.name}::2026-04-22T08:01:00+00:00",
            "study_id": study_root.name,
            "quest_id": "quest-001",
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
        },
    )


def test_build_quality_repair_batch_action_uses_publication_eval_specificity_targets_for_generic_gate_blocker(
    tmp_path: Path,
) -> None:
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
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
    }

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_quality_repair_batch"
    assert action["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert action["specificity_targets"] == publication_eval_payload["recommended_actions"][0]["specificity_targets"]
    assert "non_executable_reason" not in action["next_work_unit"]
