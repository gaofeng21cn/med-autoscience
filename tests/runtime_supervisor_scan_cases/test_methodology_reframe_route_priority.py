from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study, write_text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _set_mtime(path: Path, timestamp: int) -> None:
    os.utime(path, (timestamp, timestamp))


def test_scan_prefers_materialized_methodology_decision_over_analysis_source_blockers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    write_text(quest_root / "quest.yaml", f"quest_id: {quest_id}\nstudy_id: {study_id}\n")
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::methodology-reframe-with-analysis-source",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
        "recommended_actions": [],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    analysis_result_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    source_result_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(analysis_result_path, _analysis_blocker(study_id=study_id))
    _write_json(source_result_path, _legacy_source_blocker(study_id=study_id))
    _write_json(decision_path, _materialized_decision(study_id=study_id, quest_id=quest_id, decision_path=decision_path))
    _set_mtime(analysis_result_path, 1_000)
    _set_mtime(source_result_path, 2_000)
    _set_mtime(decision_path, 3_000)
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "current_stage": "publication_supervision",
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-methodology-reframe",
            "source_signature": "truth-source-dm002-methodology-reframe",
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == [
        "provenance_limited_harmonization_audit"
    ]
    assert [action["action_type"] for action in result["action_queue"]] == [
        "provenance_limited_harmonization_audit"
    ]
    assert study["blocked_reason"] == "provenance_limited_harmonization_audit_required"
    assert study["next_owner"] == "provenance_limited_harmonization_owner"
    assert study["owner_route"]["allowed_actions"] == ["provenance_limited_harmonization_audit"]


def test_scan_routes_authorized_provenance_limited_rebuild_to_analysis_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    write_text(quest_root / "quest.yaml", f"quest_id: {quest_id}\nstudy_id: {study_id}\n")
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::authorized-rebuild",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    analysis_result_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    source_result_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    provenance_result_path = (
        study_root / "artifacts" / "controller" / "provenance_limited_harmonization" / "latest.json"
    )
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(analysis_result_path, _analysis_blocker(study_id=study_id))
    source_blocker = _legacy_source_blocker(study_id=study_id)
    source_blocker["provenance_search"] = {
        "searched": True,
        "accepted_bundle_ref": None,
        "result_summary_acceptance_allowed": False,
        "substitute_refit_allowed": False,
    }
    _write_json(source_result_path, source_blocker)
    _write_json(decision_path, _materialized_decision(study_id=study_id, quest_id=quest_id, decision_path=decision_path))
    _write_json(provenance_result_path, _authorized_provenance_limited_result(study_id=study_id))
    _set_mtime(analysis_result_path, 1_000)
    _set_mtime(source_result_path, 2_000)
    _set_mtime(decision_path, 3_000)
    _set_mtime(provenance_result_path, 4_000)
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "current_stage": "publication_supervision",
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-authorized-rebuild",
            "source_signature": "truth-source-dm002-authorized-rebuild",
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
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
    action = study["action_queue"][0]
    assert action["owner"] == "analysis_harmonization_owner"
    assert action["reason"] == "unit_harmonized_rerun_required"
    assert action["source_ref"] == str(provenance_result_path)
    assert action["rebuild_authorization_consumed"] is True
    assert study["blocked_reason"] == "unit_harmonized_rerun_required"
    assert study["next_owner"] == "analysis_harmonization_owner"
    assert study["owner_route"]["allowed_actions"] == ["unit_harmonized_external_validation_rerun"]


def _analysis_blocker(*, study_id: str) -> dict:
    return {
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
            "blocking_reasons": [
                "hdl_unit_scale_mismatch",
                "cox_model_application_provenance_insufficient_for_rerun",
            ],
        },
        "blocking_owner_route": {
            "blocked_reason": "transport_model_provenance_recovery_required",
            "next_owner": "source_provenance_owner",
            "next_work_unit": "recover_transport_model_provenance",
        },
        "unit_harmonized_rerun_completed": False,
    }


def _legacy_source_blocker(*, study_id: str) -> dict:
    return {
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
    }


def _materialized_decision(*, study_id: str, quest_id: str, decision_path: Path) -> dict:
    return {
        "schema_version": 1,
        "decision_id": "study-decision::dm002::methodology-reframe-with-analysis-source",
        "study_id": study_id,
        "quest_id": quest_id,
        "decision_type": "bounded_analysis",
        "requires_human_confirmation": False,
        "controller_actions": [{"action_type": "ensure_study_runtime", "payload_ref": str(decision_path)}],
        "route_target": "analysis-campaign",
        "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
        "next_work_unit": {
            "unit_id": "provenance_limited_harmonization_audit",
            "lane": "analysis-campaign",
            "hard_methodology": True,
            "selected_route_option": "provenance_limited_harmonization_audit",
            "terminal_source_provenance_blocker_consumed": True,
            "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    }


def _authorized_provenance_limited_result(*, study_id: str) -> dict:
    return {
        "surface": "provenance_limited_harmonization_owner_result",
        "schema_version": 1,
        "generated_at": "2026-05-19T07:41:00+00:00",
        "study_id": study_id,
        "owner": "provenance_limited_harmonization_owner",
        "work_unit": "provenance_limited_harmonization_audit",
        "status": "blocked",
        "blocked_reason": "unit_harmonized_rerun_required",
        "typed_blocker_owner": "provenance_limited_harmonization_owner",
        "typed_blocker": {"blocker_id": "unit_harmonized_rerun_required"},
        "provenance_limited_audit_completed": True,
        "terminal_source_provenance_blocker_consumed": True,
        "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
        "rebuild_authorization_consumed": True,
        "recommended_next_route": "rebuild_reproducible_model_route",
        "next_owner": "analysis_harmonization_owner",
        "next_work_unit": "unit_harmonized_external_validation_rerun",
    }
