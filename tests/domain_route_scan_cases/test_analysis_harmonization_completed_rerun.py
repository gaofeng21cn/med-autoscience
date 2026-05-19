from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_consumes_completed_unit_harmonized_rerun_without_requeue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_type": "bounded_analysis",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {
                "unit_id": "unit_harmonized_external_validation_rerun",
                "selected_route_option": "rebuild_reproducible_model_route",
                "terminal_source_provenance_blocker_consumed": True,
                "clean_reproducible_model_rebuild_authorized": True,
                "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
            },
        },
    )
    evidence_ref = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_json(
        evidence_ref,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "schema_version": 1,
            "status": "completed",
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "blocked_reason": None,
            "typed_blocker_owner": None,
            "typed_blocker": None,
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(evidence_ref),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-hard-methodology",
            "source_signature": "truth-source-dm002-hard-methodology",
        },
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    queued_actions = [action["action_type"] for action in study["action_queue"]]
    assert "unit_harmonized_external_validation_rerun" not in queued_actions
    assert "recover_transport_model_provenance" not in queued_actions


def test_completed_unit_harmonized_rerun_clears_prior_provenance_limited_rerun_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::completed-rerun",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::ai-reviewer-re-eval",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
                ),
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
            }
        ],
    }
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_type": "bounded_analysis",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "next_work_unit": {
                "unit_id": "unit_harmonized_external_validation_rerun",
                "hard_methodology": True,
                "selected_route_option": "rebuild_reproducible_model_route",
                "terminal_source_provenance_blocker_consumed": True,
                "clean_reproducible_model_rebuild_authorized": True,
                "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
            },
        },
    )
    provenance_limited_path = (
        study_root / "artifacts" / "controller" / "provenance_limited_harmonization" / "latest.json"
    )
    _write_json(
        provenance_limited_path,
        {
            "surface": "provenance_limited_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "provenance_limited_harmonization_owner",
            "work_unit": "provenance_limited_harmonization_audit",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "next_owner": "analysis_harmonization_owner",
            "next_work_unit": "unit_harmonized_external_validation_rerun",
            "typed_blocker_owner": "provenance_limited_harmonization_owner",
            "typed_blocker": {"blocker_id": "unit_harmonized_rerun_required"},
            "provenance_limited_audit_completed": False,
        },
    )
    evidence_ref = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_json(
        evidence_ref,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "schema_version": 1,
            "status": "completed",
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    )
    analysis_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    _write_json(
        analysis_path,
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "blocked_reason": None,
            "typed_blocker_owner": None,
            "typed_blocker": None,
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(evidence_ref),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    decision_mtime = 900
    provenance_mtime = 1_000
    analysis_mtime = 2_000
    decision_path.touch()
    provenance_limited_path.touch()
    analysis_path.touch()
    evidence_ref.touch()
    import os

    os.utime(decision_path, (decision_mtime, decision_mtime))
    os.utime(provenance_limited_path, (provenance_mtime, provenance_mtime))
    os.utime(analysis_path, (analysis_mtime, analysis_mtime))
    os.utime(evidence_ref, (analysis_mtime, analysis_mtime))
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {"unit_id": "ai_reviewer_medical_prose_quality_review"},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-completed-rerun",
            "source_signature": "truth-source-dm002-completed-rerun",
        },
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert "unit_harmonized_external_validation_rerun" not in [
        action["action_type"] for action in study["action_queue"]
    ]
    assert study["why_not_applied"] != "unit_harmonized_rerun_required"
    assert study["blocked_reason"] != "unit_harmonized_rerun_required"
    assert study["next_owner"] != "analysis_harmonization_owner"
    assert study["owner_route"]["owner_reason"] != "unit_harmonized_rerun_required"


def test_completed_unit_harmonized_rerun_supersedes_old_source_provenance_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::completed-rerun",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    source_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
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
    evidence_ref = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_json(
        evidence_ref,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "schema_version": 1,
            "status": "completed",
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "blocked_reason": None,
            "typed_blocker_owner": None,
            "typed_blocker": None,
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(evidence_ref),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-completed-rerun",
            "source_signature": "truth-source-dm002-completed-rerun",
        },
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

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    queued_actions = [action["action_type"] for action in study["action_queue"]]
    assert "methodology_reframe_route_decision" not in queued_actions
    assert "recover_transport_model_provenance" not in queued_actions


def test_scan_requeues_analysis_owner_when_clean_rebuild_decision_supersedes_legacy_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_type": "bounded_analysis",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {
                "unit_id": "unit_harmonized_external_validation_rerun",
                "selected_route_option": "rebuild_reproducible_model_route",
                "terminal_source_provenance_blocker_consumed": True,
                "clean_reproducible_model_rebuild_authorized": True,
                "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
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
                "blocking_reasons": [
                    "hdl_unit_scale_mismatch",
                    "nhanes_hdl_mapping_uses_raw_mg_dl_field_without_si_conversion_surface",
                    "cox_model_application_provenance_insufficient_for_rerun",
                ],
            },
            "blocking_owner_route": {
                "blocked_reason": "transport_model_provenance_recovery_required",
                "next_owner": "source_provenance_owner",
                "next_work_unit": "recover_transport_model_provenance",
            },
            "unit_harmonized_rerun_completed": False,
            "rerun_evidence_ref": None,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-clean-rebuild",
            "source_signature": "truth-source-dm002-clean-rebuild",
        },
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
    assert study["action_queue"][0]["owner"] == "analysis_harmonization_owner"
    assert study["blocked_reason"] == "unit_harmonized_rerun_required"
    assert study["next_owner"] == "analysis_harmonization_owner"
