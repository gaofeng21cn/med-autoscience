from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import write_text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _study_root(tmp_path: Path, study_id: str) -> Path:
    study_root = tmp_path / "studies" / study_id
    write_text(study_root / "paper" / "draft.md", "# Draft\n")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"items": []})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "blocked",
                    "summary": "Current manuscript needs route-back before publication gate replay.",
                }
            },
        },
    )
    return study_root


def test_medical_quality_regression_lane_covers_dm002_and_dm003_route_back_contracts(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    dm002 = _study_root(tmp_path, "002-dm-china-us-mortality-attribution")
    dm003 = _study_root(tmp_path, "003-dpcc-primary-care-phenotype-treatment-gap")
    _write_json(
        dm002 / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_intent": "reviewer_revision",
            "summary": "Need validation uncertainty, calibration, claim-evidence alignment, and prose repair.",
        },
    )
    _write_json(
        dm003 / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_intent": "reviewer_revision",
            "summary": (
                "Need phenotype derivation transparency, recorded treatment-gap terminology, "
                "BP/data quality reporting, baseline table, formal figures, and journal prose."
            ),
        },
    )

    suites = {
        "dm002": module.build_medical_manuscript_quality_agent_lab_suite(study_root=dm002),
        "dm003": module.build_medical_manuscript_quality_agent_lab_suite(study_root=dm003),
    }

    dm002_task = suites["dm002"]["tasks"][0]
    dm003_task = suites["dm003"]["tasks"][0]
    dm002_work_order = dm002_task["improvement_candidate"]["developer_patch_work_order"]
    dm003_work_order = dm003_task["improvement_candidate"]["developer_patch_work_order"]
    dm003_checklist = dm003_task["mechanism_evolution_inputs"]["first_draft_quality_route_back_checklist"]

    assert dm002_work_order["study_quality_target_family"] == "prediction_model_external_validation"
    assert dm003_work_order["study_quality_target_family"] == "observational_phenotype_treatment_gap"
    assert "first_draft_quality_route_back_regression" in dm002_work_order["required_patch_scopes"]
    assert "first_draft_quality_route_back_regression" in dm003_work_order["required_patch_scopes"]
    assert {
        "methods_reproducibility_floor_missing",
        "results_numeric_uncertainty_floor_missing",
        "formal_figure_table_quality_floor_missing",
        "runtime_language_purge_required",
        "claim_evidence_alignment_required",
    }.issubset({item["blocker"] for item in dm003_checklist["items"]})
    assert dm003_checklist["can_write_study_truth"] is False
    assert dm003_checklist["can_authorize_quality_verdict"] is False
    assert dm003_task["authority_boundary"]["can_mutate_domain_artifact"] is False


def test_medical_quality_regression_lane_keeps_platform_repair_out_of_paper_progress() -> None:
    projection = importlib.import_module("med_autoscience.controllers.study_progress_parts.progress_first_projection")

    result = projection.build_progress_first_projection(
        {
            "paper_progress_delta": {"count": 0, "token_usage_total": 0},
            "platform_repair_delta": {"count": 1, "token_usage_total": 2048},
        }
    )

    sprint_state = result["progress_first_sprint_state"]
    assert sprint_state["paper_progress_delta_counted"] is False
    assert sprint_state["platform_repair_delta_counted"] is True
    assert sprint_state["classification"] == "platform_repair"
    assert sprint_state["platform_only_is_paper_progress"] is False
    assert result["next_forced_delta"]["required_delta_kind"] == "paper_progress_delta_or_typed_blocker"
    assert result["next_forced_delta"]["reason"] == "platform_repair_does_not_count_as_paper_progress"


def test_progress_first_projection_exposes_current_owner_ticket_without_domain_authority() -> None:
    projection = importlib.import_module("med_autoscience.controllers.study_progress_parts.progress_first_projection")

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 1},
            "domain_transition": {
                "owner": "write",
                "route_target": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "summary": "Repair manuscript story surface from current eval.",
                },
                "guard_boundary": {
                    "required_owner_surface": "paper/draft.md plus claim-evidence map",
                },
                "source_refs": ["artifacts/publication_eval/latest.json"],
            },
            "current_blockers": ["platform_repair_only"],
        }
    )

    ticket = result["current_owner_ticket"]
    assert ticket["surface_kind"] == "mas_current_owner_ticket"
    assert ticket["owner"] == "write"
    assert ticket["allowed_action"] == "run_quality_repair_batch"
    assert ticket["work_unit"] == {
        "work_unit_id": "medical_prose_write_repair",
        "summary": "Repair manuscript story surface from current eval.",
    }
    assert ticket["required_input_refs"] == ["artifacts/publication_eval/latest.json"]
    assert ticket["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
    }
    assert ticket["acceptance_criteria"] == result["next_forced_delta"]["acceptance_refs"]
    assert ticket["forbidden_writes"] == [
        "study_truth",
        "memory_body",
        "artifact_body",
        "publication_verdict",
        "source_readiness_verdict",
        "current_package",
    ]
    assert ticket["expected_receipt_or_blocker"] == [
        "owner_receipt",
        "typed_blocker",
        "route_back_request",
        "human_gate_request",
        "stop_loss",
    ]
    assert ticket["no_loop_budget"] == {
        "platform_repair_is_not_deliverable_progress": True,
        "provider_completion_is_not_closeout": True,
        "repeat_same_work_unit_requires_typed_blocker_or_new_target_surface": True,
    }
    assert ticket["authority_boundary"] == {
        "ticket_authorizes_next_attempt_only": True,
        "ticket_authorizes_publication_quality": False,
        "ticket_authorizes_artifact_mutation": False,
        "ticket_authorizes_study_truth_write": False,
    }
    assert result["next_forced_delta"]["current_owner_ticket"] == ticket


def test_medical_quality_regression_lane_projects_runtime_closeout_only_as_route_back_checklist() -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_progress_state")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "quest-003",
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "medical_prose_currentness_recheck",
                "required_output_surface": "paper/build/review_manuscript.md",
            },
            "evidence_refs": {
                "publication_eval": "artifacts/publication_eval/latest.json",
            },
            "expected_repair_result": "paper-facing story delta or typed blocker",
        },
        "study_macro_state": {
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "details": {"package_delivered": False},
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "latest_terminal_stage_log": {
                "status": "handoff_ready",
                "action_type": "run_quality_repair_batch",
                "paper_stage_log": {
                    "current_owner": "write",
                    "progress_delta_classification": "platform_repair",
                    "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
                    "paper_progress_delta": {"count": 0, "token_usage_total": 0},
                    "platform_repair_delta": {"count": 1, "token_usage_total": 101},
                    "changed_paper_surfaces": [],
                    "changed_stage_surfaces": ["artifacts/runtime/closeout.json"],
                    "remaining_blockers": {
                        "typed_blocker": "manuscript_story_surface_delta_missing",
                    },
                    "evidence_refs": ["artifacts/controller/quality_repair_batch/latest.json"],
                },
            },
        },
        "progress_freshness": {
            "meaningful_artifact_delta_freshness": {"status": "missing"},
        },
    }

    state = module.build_paper_progress_state(payload)

    assert state["meaningful_artifact_delta"] is False
    assert state["why_not_progressing"] == "paper_facing_progress_delta_or_typed_blocker_missing"
    assert state["stage_closeout_progress"]["runtime_closeout_only"] is True
    assert state["stage_closeout_progress"]["paper_facing_delta_present"] is False
    checklist = state["route_back_checklist"]
    assert checklist["route_back_required"] is True
    assert checklist["owner"] == "write"
    assert checklist["blockers"] == ["manuscript_story_surface_delta_missing"]
