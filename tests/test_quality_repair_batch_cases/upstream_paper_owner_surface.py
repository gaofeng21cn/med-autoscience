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


def _write_quality_summary(study_root: Path, *, relative_path: Path | None = None) -> dict[str, Any]:
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
    _write_json(study_root / (relative_path or Path("artifacts/evaluation_summary/latest.json")), payload)
    return payload

def _mark_publication_eval_as_specific_upstream_repair(
    study_root: Path,
    publication_eval_payload: dict[str, Any],
) -> dict[str, Any]:
    action = publication_eval_payload["recommended_actions"][0]
    action["action_type"] = "return_to_controller"
    action.pop("route_target", None)
    action.pop("route_key_question", None)
    action.pop("route_rationale", None)
    action["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    action["specificity_targets"] = [
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
        {
            "target_kind": "table",
            "target_id": "table_catalog",
            "source_path": str(study_root / "paper" / "tables" / "table_catalog.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "source_path",
            "target_id": "publishability_gate",
            "source_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "blocking_reason": "missing_publication_anchor",
        },
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    return publication_eval_payload


def _paper_write_supervisor_route_context() -> dict[str, Any]:
    return {
        "control_plane_snapshot": {
            "surface": "control_plane_snapshot",
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
        }
    }

def test_run_quality_repair_batch_materializes_canonical_paper_owner_surface_for_upstream_repair(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    publication_gate = importlib.import_module("med_autoscience.controllers.publication_gate")
    paper_artifacts = importlib.import_module("med_autoscience.runtime_protocol.paper_artifacts")
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
    (quest_root / "paper" / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "draft.md").write_text("# Draft\n\nRuntime projected draft shell.\n", encoding="utf-8")
    _write_json(quest_root / "paper" / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(quest_root / "paper" / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(quest_root / "paper" / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(quest_root / "paper" / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(quest_root / "paper" / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(quest_root / "paper" / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(quest_root / "paper" / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    publication_eval_payload = _mark_publication_eval_as_specific_upstream_repair(
        study_root,
        _write_blocked_publication_eval(study_root, quest_id=quest_id),
    )
    _write_quality_summary(study_root)

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    canonical_paper_root = study_root / "paper"
    assert result["status"] != "blocked_no_paper_root"
    assert result["paper_owner_surface_prepare"]["status"] == "materialized"
    assert canonical_paper_root.is_dir()
    assert paper_artifacts.resolve_latest_paper_root(quest_root) == canonical_paper_root.resolve()
    gate_state = publication_gate.build_gate_state(quest_root)
    assert gate_state.paper_root == canonical_paper_root.resolve()
    assert (canonical_paper_root / "paper_bundle_manifest.json").is_file()
    assert (canonical_paper_root / "paper_line_state.json").is_file()
    assert (canonical_paper_root / "claim_evidence_map.json").is_file()
    assert (canonical_paper_root / "figures" / "figure_catalog.json").is_file()
    assert not (canonical_paper_root / "submission_minimal" / "submission_manifest.json").exists()


def test_run_quality_repair_batch_does_not_materialize_paper_owner_surface_without_projection(
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
    publication_eval_payload = _mark_publication_eval_as_specific_upstream_repair(
        study_root,
        _write_blocked_publication_eval(study_root, quest_id=quest_id),
    )
    _write_quality_summary(study_root)

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert result["status"] == "blocked_no_paper_root"
    assert result["paper_owner_surface_prepare"]["status"] == "blocked_missing_projection"
    assert not (study_root / "paper").exists()


def test_run_quality_repair_batch_materializes_owner_surface_from_hydration_projection_inputs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    publication_gate = importlib.import_module("med_autoscience.controllers.publication_gate")
    paper_artifacts = importlib.import_module("med_autoscience.runtime_protocol.paper_artifacts")
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
    _write_json(quest_root / "paper" / "medical_analysis_contract.json", {"schema_version": 1})
    _write_json(quest_root / "paper" / "medical_reporting_contract.json", {"schema_version": 1})
    _write_json(quest_root / "paper" / "display_registry.json", {"schema_version": 1, "displays": []})
    _write_json(quest_root / "paper" / "figures" / "cohort_flow.shell.json", {"schema_version": 1})
    _write_json(quest_root / "paper" / "tables" / "baseline_characteristics.shell.json", {"schema_version": 1})
    _write_json(
        quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json",
        {
            "schema_version": 1,
            "status": "hydrated",
            "written_files": [
                str(quest_root / "paper" / "medical_analysis_contract.json"),
                str(quest_root / "paper" / "medical_reporting_contract.json"),
                str(quest_root / "paper" / "display_registry.json"),
            ],
        },
    )
    publication_eval_payload = _mark_publication_eval_as_specific_upstream_repair(
        study_root,
        _write_blocked_publication_eval(study_root, quest_id=quest_id),
    )
    _write_quality_summary(study_root)

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        control_plane_route_context=_paper_write_supervisor_route_context(),
    )

    canonical_paper_root = study_root / "paper"
    assert result["source_eval_id"] == publication_eval_payload["eval_id"]
    assert result["status"] != "blocked_no_paper_root"
    assert result["paper_owner_surface_prepare"]["status"] == "materialized"
    assert result["paper_owner_surface_prepare"]["projection_input_status"] == "hydration_projection_present"
    assert paper_artifacts.resolve_latest_paper_root(quest_root) == canonical_paper_root.resolve()
    gate_state = publication_gate.build_gate_state(quest_root)
    assert gate_state.paper_root == canonical_paper_root.resolve()
    assert (canonical_paper_root / "paper_bundle_manifest.json").is_file()
    assert (canonical_paper_root / "paper_line_state.json").is_file()
    assert (canonical_paper_root / "display_registry.json").is_file()
    assert (canonical_paper_root / "claim_evidence_map.json").is_file()
    assert (canonical_paper_root / "figures" / "figure_catalog.json").is_file()
    assert not (canonical_paper_root / "submission_minimal" / "submission_manifest.json").exists()
