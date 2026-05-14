from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_study_runtime_execution_control_intent_cases.helpers import (
    _base_status_payload,
    _write_controller_decision_authorization,
    _write_publication_eval_authority,
    _write_publication_eval_gate_replay_with_specificity_targets,
    _write_publication_eval_review_only_authority,
    _write_publication_eval_work_unit_authority,
    _write_runtime_state,
)

def test_controller_authorization_prefers_publication_work_unit_over_stale_route_text(tmp_path: Path) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(study_root)
    _write_publication_eval_work_unit_authority(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)

    assert authorization_context is not None
    assert authorization_context["work_unit_id"] == "analysis_claim_evidence_repair"
    assert authorization_context["work_unit_fingerprint"] == "publication-blockers::claim-story-figure"
    assert authorization_context["route_target"] == "analysis-campaign"
    assert authorization_context["route_key_question"].startswith("analysis_claim_evidence_repair:")
    assert authorization_context["source_route_key_question"] == (
        "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
    )
    assert authorization_context["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert authorization_context["blocking_work_units"][1]["unit_id"] == "submission_minimal_refresh"
    assert authorization_context["control_intent_identity"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert (
        authorization_context["control_intent_identity"]["blocker_authority_fingerprint"]
        == "publication-blockers::claim-story-figure"
    )

def test_controller_authorization_carries_publication_specificity_targets_for_current_decision(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        work_unit_fingerprint="publication-blockers::claim-story-figure",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
        },
    )
    _write_publication_eval_work_unit_authority(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    message = auth_module._controller_decision_authorization_message(
        authorization_context=authorization_context or {}
    )

    assert authorization_context is not None
    assert authorization_context["work_unit_id"] == "analysis_claim_evidence_repair"
    assert authorization_context["specificity_targets"][0]["target_kind"] == "claim"
    assert authorization_context["specificity_targets"][0]["source_path"].endswith("claim_evidence_map.json")
    assert "specificity_targets" in message

def test_controller_authorization_prefers_current_decision_work_unit_over_stale_publication_eval(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_gate_clearing_batch",
        work_unit_fingerprint="publication-blockers::current",
        next_work_unit={
            "unit_id": "submission_minimal_refresh",
            "lane": "finalize",
            "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
        },
        blocking_work_units=[
            {
                "unit_id": "manuscript_story_repair",
                "lane": "write",
                "summary": "Repair the paper story around the current evidence and claim boundary.",
            },
            {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
            },
        ],
    )
    _write_publication_eval_work_unit_authority(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)

    assert authorization_context is not None
    assert authorization_context["work_unit_id"] == "submission_minimal_refresh"
    assert authorization_context["work_unit_fingerprint"] == "publication-blockers::current"
    assert authorization_context["route_target"] == "finalize"
    assert authorization_context["next_work_unit"]["unit_id"] == "submission_minimal_refresh"
    assert authorization_context["blocking_work_units"][0]["unit_id"] == "manuscript_story_repair"
    assert authorization_context["control_intent_identity"]["work_unit_id"] == "submission_minimal_refresh"


def test_controller_authorization_projects_finalize_route_for_controller_owned_submission_unit(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(
        study_root,
        next_work_unit={
            "unit_id": "submission_authority_sync_closure",
            "lane": "controller",
            "summary": "Regenerate submission authority signatures, then replay the publication gate.",
            "control_surface": "gate_clearing_batch",
        },
        blocking_work_units=[
            {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "summary": "Regenerate submission authority signatures, then replay the publication gate.",
                "control_surface": "gate_clearing_batch",
            }
        ],
        work_unit_fingerprint="publication-blockers::bundle-ready",
    )
    _write_publication_eval_review_only_authority(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)

    assert authorization_context is not None
    assert authorization_context["route_target"] == "finalize"
    assert authorization_context["route_key_question"].startswith("submission_authority_sync_closure:")
    assert authorization_context["work_unit_id"] == "submission_authority_sync_closure"
    assert authorization_context["next_work_unit"]["unit_id"] == "submission_authority_sync_closure"
    assert authorization_context["control_intent_identity"]["route_target"] == "finalize"
    assert authorization_context["control_intent_identity"]["work_unit_id"] == "submission_authority_sync_closure"


def test_controller_authorization_keeps_record_route_over_review_only_publication_work_unit(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(
        study_root,
        decision_id="decision-dm002-reviewer-revision",
        emitted_at="2026-05-13T16:39:25+00:00",
    )
    _write_publication_eval_review_only_authority(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)

    assert authorization_context is not None
    assert authorization_context["decision_type"] == "bounded_analysis"
    assert authorization_context["route_target"] == "analysis-campaign"
    assert authorization_context["route_key_question"] == (
        "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
    )
    assert authorization_context["work_unit_id"] == (
        "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
    )
    assert authorization_context["source_route_key_question"] == authorization_context["route_key_question"]
    assert authorization_context["next_work_unit"] == {}
    assert authorization_context["blocking_work_units"] == []
    assert authorization_context["work_unit_fingerprint"] is None
    assert authorization_context["control_intent_identity"]["route_target"] == "analysis-campaign"
    assert authorization_context["control_intent_identity"]["work_unit_id"] != "publication_gate_blocker_review"


def test_controller_authorization_converts_gate_replay_targets_to_upstream_paper_repair(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(study_root)
    _write_publication_eval_gate_replay_with_specificity_targets(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)

    assert authorization_context is not None
    assert authorization_context["route_target"] == "analysis-campaign"
    assert authorization_context["work_unit_id"] == "analysis_claim_evidence_repair"
    assert authorization_context["next_work_unit"] == {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
    }
    assert [unit["unit_id"] for unit in authorization_context["blocking_work_units"]] == [
        "analysis_claim_evidence_repair",
        "figure_results_trace_repair",
    ]
    assert authorization_context["work_unit_fingerprint"] == "publication-blockers::replay-with-targets"
    assert {target["target_kind"] for target in authorization_context["specificity_targets"]} == {
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    }
    assert authorization_context["control_intent_identity"]["work_unit_id"] == "analysis_claim_evidence_repair"
