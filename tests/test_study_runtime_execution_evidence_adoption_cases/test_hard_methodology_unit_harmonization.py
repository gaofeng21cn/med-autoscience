from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_study_runtime_execution_control_intent import (
    _write_controller_decision_authorization,
    _write_publication_eval_work_unit_authority,
    _write_runtime_state,
)


def test_rejects_completed_receipt_for_hard_unit_harmonization_target(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "002-dm"
    quest_root = tmp_path / "runtime" / "quest-002"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        emitted_at="2026-05-18T14:38:44+00:00",
        work_unit_fingerprint="publication-blockers::hdl-unit",
        next_work_unit={
            "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
            "lane": "analysis-campaign",
            "summary": "Close or type-block HDL harmonization and model reproducibility gaps.",
        },
        blocking_work_units=[
            {
                "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                "lane": "analysis-campaign",
                "summary": "Close or type-block HDL harmonization and model reproducibility gaps.",
            }
        ],
    )
    _write_publication_eval_work_unit_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    authorization_context["specificity_targets"] = [
        {
            "target_kind": "metric",
            "target_id": "hdl_unit_standardized_sensitivity",
            "source_path": str(quest_root / "artifacts" / "analysis" / "harmonization_route_back" / "latest.md"),
            "blocking_reason": "unit_standardized_model_application_or_sensitivity",
        }
    ]
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-analysis-repair", "active_run_id": "run-002"},
        recorded_at="2026-05-18T14:39:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta", "active_run_id": "run-002"},
        recorded_at="2026-05-18T14:45:00+00:00",
    )
    report_path = (
        quest_root
        / ".ds"
        / "cold_archive"
        / "report_history"
        / "artifacts"
        / "reports"
        / "report-hdl.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "analysis_claim_evidence_repair",
                "created_at": "2026-05-18T14:50:00+00:00",
                "updated_at": "2026-05-18T14:50:00+00:00",
                "status": "completed",
                "controller": {
                    "active_work_unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                    "work_unit_fingerprint": "publication-blockers::hdl-unit",
                    "controller_actions": "run_quality_repair_batch",
                    "route_target": "analysis-campaign",
                },
                "repair_counts": {
                    "changed_files_count": 1,
                    "unresolved_local_defect_count": 0,
                    "gate_owned_or_nonlocal_defect_count": 0,
                },
                "recommended_next_route": "return_to_publication_gate_recheck",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": None, "pending_user_message_count": 0})

    adoption_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.work_unit_evidence_adoption"
    )
    adoption = adoption_module.adopt_controller_work_unit_evidence_if_present(
        study_root=study_root,
        quest_root=quest_root,
        authorization_context=authorization_context,
        identity=identity,
        active_run_id=None,
        source="medautosci-test",
    )

    assert adoption is None
    assert [event["event_type"] for event in control_intent.read_events(study_root=study_root)] == [
        "delivered",
        "skipped_duplicate",
    ]


def test_adopts_hard_unit_harmonization_owner_handoff(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "002-dm"
    quest_root = tmp_path / "runtime" / "quest-002"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        emitted_at="2026-05-18T14:38:44+00:00",
        work_unit_fingerprint="publication-blockers::hdl-unit",
        next_work_unit={
            "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
            "lane": "analysis-campaign",
            "summary": "Close or type-block HDL harmonization and model reproducibility gaps.",
        },
        blocking_work_units=[
            {
                "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                "lane": "analysis-campaign",
                "summary": "Close or type-block HDL harmonization and model reproducibility gaps.",
            }
        ],
    )
    _write_publication_eval_work_unit_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    authorization_context["specificity_targets"] = [
        {
            "target_kind": "metric",
            "target_id": "hdl_unit_standardized_sensitivity",
            "source_path": str(quest_root / "artifacts" / "analysis" / "harmonization_route_back" / "latest.md"),
            "blocking_reason": "unit_standardized_model_application_or_sensitivity",
        }
    ]
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"message_id": "msg-analysis-repair", "active_run_id": "run-002"},
        recorded_at="2026-05-18T14:39:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta", "active_run_id": "run-002"},
        recorded_at="2026-05-18T14:45:00+00:00",
    )
    handoff_path = quest_root / "artifacts" / "supervision" / "controller_consumption" / "latest.json"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "surface": "controller_consumption_receipt_latest",
                "study_id": "002-dm",
                "quest_id": "quest-002",
                "updated_at": "2026-05-18T14:50:00Z",
                "work_unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                "work_unit_fingerprint": "publication-blockers::hdl-unit",
                "repair_packet_type": "analysis_claim_evidence_current_run_handoff",
                "analysis_lane_status": "exhausted_for_current_fingerprint",
                "meaningful_artifact_delta": True,
                "next_owner": "analysis_harmonization_owner",
                "next_work_unit": "unit_harmonized_external_validation_rerun",
                "blocked_reason": "unit_harmonized_rerun_required",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    adoption_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.work_unit_evidence_adoption"
    )
    adoption = adoption_module.adopt_controller_work_unit_evidence_if_present(
        study_root=study_root,
        quest_root=quest_root,
        authorization_context=authorization_context,
        identity=identity,
        active_run_id=None,
        source="medautosci-test",
    )

    assert adoption is not None
    assert adoption["recommended_next_route"] == "handoff_to_next_owner"
    assert adoption["next_owner"] == "analysis_harmonization_owner"
    assert adoption["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert adoption["blocked_reason"] == "unit_harmonized_rerun_required"
    assert [event["event_type"] for event in control_intent.read_events(study_root=study_root)] == [
        "delivered",
        "skipped_duplicate",
        "artifact_written",
        "owner_handoff",
    ]
