from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _set_mtime(path: Path, timestamp: int) -> None:
    os.utime(path, (timestamp, timestamp))


def test_scan_reopens_hard_methodology_handoff_when_newer_quality_batch_supersedes_downstream_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::newer-hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    analysis_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    source_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    quality_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    _write_json(
        analysis_path,
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {
                "blocker_id": "unit_harmonized_rerun_required",
                "blocking_reasons": ["cox_model_application_provenance_insufficient_for_rerun"],
            },
            "unit_harmonized_rerun_completed": False,
        },
    )
    _write_json(
        source_path,
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {"blocker_id": "transport_model_provenance_recovery_required"},
            "transport_model_provenance_recovered": False,
            "provenance_search": {
                "searched": True,
                "accepted_bundle_ref": None,
                "result_summary_acceptance_allowed": False,
                "substitute_refit_allowed": False,
            },
        },
    )
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_id": "study-decision::dm002::methodology-reframe",
            "study_id": study_id,
            "quest_id": quest_id,
            "decision_type": "route_back_same_line",
            "route_target": "analysis-campaign",
            "route_key_question": "Can DM002 continue without original transported model provenance?",
            "route_rationale": "Route back for methodology reframe before manuscript work.",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {
                "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                "lane": "analysis-campaign",
                "summary": "Reframe the invalid transported-model claim.",
            },
            "controller_actions": [{"action_type": "ensure_study_runtime", "payload_ref": str(decision_path)}],
        },
    )
    _write_json(
        quality_path,
        {
            "schema_version": 1,
            "status": "blocked",
            "ok": False,
            "study_id": study_id,
            "quest_id": quest_id,
            "blocked_reason": "unit_harmonized_rerun_required",
            "next_owner": "analysis_harmonization_owner",
            "next_work_unit": "unit_harmonized_external_validation_rerun",
            "hard_methodology_target": {
                "target_id": "hdl_unit_standardized_sensitivity",
                "required_owner": "analysis_harmonization_owner",
                "required_next_work_unit": "unit_harmonized_external_validation_rerun",
                "typed_blocker": "unit_harmonized_rerun_required",
            },
            "quality_gate_relaxation_allowed": False,
            "current_package_write_allowed": False,
        },
    )
    for path, timestamp in (
        (analysis_path, 100),
        (source_path, 200),
        (decision_path, 300),
        (quality_path, 400),
    ):
        _set_mtime(path, timestamp)
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "ai_repair_lifecycle": {"state": "blocked", "blocked_reason": "domain_transition_ai_reviewer_re_eval"},
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == [
        "unit_harmonized_external_validation_rerun"
    ]
    assert [action["action_type"] for action in result["action_queue"]] == [
        "unit_harmonized_external_validation_rerun"
    ]
    assert study["blocked_reason"] == "unit_harmonized_rerun_required"
    assert study["next_owner"] == "analysis_harmonization_owner"
    assert study["owner_route"]["allowed_actions"] == ["unit_harmonized_external_validation_rerun"]
