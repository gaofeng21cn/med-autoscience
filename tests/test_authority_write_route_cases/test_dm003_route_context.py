from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_quality_repair_batch_prefers_current_upstream_eval_over_stale_bundle_route(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::003-dpcc::quest-003::medical-prose",
        "study_id": study_root.name,
        "quest_id": quest_id,
        "emitted_at": "2026-05-22T08:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": f"charter::{study_root.name}::v1",
            "publication_objective": "primary care phenotype treatment gap",
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
            "summary": "Current manuscript prose is not yet publication-ready.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-medical-prose",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "medical_prose_quality_blocked",
                "evidence_refs": [str(study_root / "paper" / "draft.md")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::medical-prose::latest",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Repair current manuscript prose through the write owner.",
                "route_target": "write",
                "route_key_question": "Which medical prose repair is still blocking?",
                "route_rationale": "Revise the canonical manuscript before replaying the gate.",
                "evidence_refs": [str(study_root / "paper" / "draft.md")],
                "requires_controller_decision": True,
                "work_unit_fingerprint": "publication-blockers::medical-prose",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair the current manuscript prose.",
                },
                "blocking_work_units": [
                    {
                        "unit_id": "medical_prose_write_repair",
                        "lane": "write",
                        "summary": "Repair the current manuscript prose.",
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::003-dpcc::medical-prose",
            "quality_closure_truth": {
                "state": "quality_repair_required",
                "route_target": "write",
                "current_required_action": "continue_write_stage",
            },
            "quality_execution_lane": {
                "lane_id": "general_quality_repair",
                "route_target": "write",
            },
        },
    )
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": ["medical_publication_surface_blocked", "medical_prose_quality_blocked"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
        "gate_fingerprint": "publication-gate::medical-prose",
        "bundle_tasks_downstream_only": True,
    }
    route_context = {
        "authority_snapshot": {
            "surface": "authority_snapshot",
            "control_state": "supervisor_gated",
            "canonical_next_action": "resume_same_study_line",
            "authority_refs": {
                "study_truth": {"epoch": "truth-1"},
                "runtime_health": {"epoch": "runtime-1"},
            },
            "dispatch_gate": {
                "state": "blocked",
                "blocking_reasons": [
                    "execution_owner_guard.supervisor_only",
                    "publication_supervisor_state.bundle_tasks_downstream_only",
                ],
            },
            "route_authorization": {
                "authorized": False,
                "paper_write_allowed": False,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
        },
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "submission_minimal_refresh",
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "publication-blockers::stale-submission",
        },
    }
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: object(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: gate_report,
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("gate_context", kwargs["authority_route_context"]),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=route_context,
    )

    assert result["authority_route_gate"]["allowed"] is True
    assert result["authority_route_gate"]["action"] == "paper_write"
    assert result["authority_route_gate"]["controller_route_gate"]["work_unit_id"] == (
        "medical_prose_write_repair"
    )
    gate_context = seen["gate_context"]
    assert isinstance(gate_context, dict)
    assert gate_context["controller_route_context"]["work_unit_id"] == "medical_prose_write_repair"
    assert gate_context["controller_route_context"]["work_unit_fingerprint"] == (
        "publication-blockers::medical-prose"
    )
