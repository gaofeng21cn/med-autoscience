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
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Ask the publication gate to identify concrete blocker targets.",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "claim_evidence_map",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "blocking_reason": "missing_publication_anchor",
                    },
                    {
                        "target_kind": "figure",
                        "target_id": "figure_catalog",
                        "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                        "blocking_reason": "missing_publication_anchor",
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
            },
            "quality_execution_lane": {
                "lane_id": "general_quality_repair",
                "route_target": "review",
                "summary": "Run deterministic repair units, then replay the publishability gate.",
            },
        },
    )


def _analysis_claim_evidence_repair_route_context() -> dict[str, Any]:
    return {
        "authority_snapshot": {
            "surface": "authority_snapshot",
            "control_state": "supervisor_gated",
            "canonical_next_action": "resume_same_study_line",
            "authority_refs": {"study_truth": {"epoch": "truth-1"}, "runtime_health": {"epoch": "runtime-1"}},
            "dispatch_gate": {
                "state": "blocked",
                "blocking_reasons": ["publication_supervisor_state.bundle_tasks_downstream_only"],
            },
            "route_authorization": {
                "paper_write_allowed": True,
                "bundle_build_allowed": False,
                "runtime_recovery_allowed": True,
            },
        },
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
            "requires_human_confirmation": False,
            "source_eval_id": "publication-eval::test",
            "gate_fingerprint": "publication-gate::test",
            "work_unit_fingerprint": "publication-blockers::test",
        },
    }


def test_quality_repair_batch_repairs_missing_display_registry_for_existing_paper_root(
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
    quest_id = "quest-001"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    _write_json(paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    (paper_root / "draft.md").write_text("# Draft\n\nExisting owner shell.\n", encoding="utf-8")
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _write_json(
        paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "paper_root": str(paper_root),
            "surface_owner": "study_canonical_paper_owner_surface",
        },
    )
    _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(study_root)

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=_analysis_claim_evidence_repair_route_context(),
    )

    display_registry = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))
    assert result["paper_owner_surface_prepare"]["status"] == "repaired_existing"
    assert result["status"] != "blocked_no_paper_root"
    assert display_registry == {
        "schema_version": 1,
        "status": "owner_surface_initialized",
        "displays": [],
    }
