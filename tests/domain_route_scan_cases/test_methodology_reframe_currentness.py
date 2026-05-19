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


def test_scan_requeues_methodology_reframe_when_source_blocker_newer_than_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    write_text(quest_root / "quest.yaml", f"quest_id: {quest_id}\nstudy_id: {study_id}\n")
    publication_eval = _publication_eval(study_id=study_id, quest_id=quest_id, eval_suffix="newer-source-blocker")
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    source_result_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    _write_json(source_result_path, _source_provenance_blocker(study_id=study_id))
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(decision_path, _materialized_methodology_decision(study_id=study_id, quest_id=quest_id))
    _set_mtime(decision_path, 1_000)
    _set_mtime(source_result_path, 2_000)
    _patch_projection_inputs(
        monkeypatch,
        module,
        study_id=study_id,
        quest_id=quest_id,
        quest_root=quest_root,
        study_root=study_root,
        publication_eval=publication_eval,
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    _assert_methodology_reframe_queued(result)


def test_scan_requeues_methodology_reframe_when_analysis_blocker_newer_than_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    write_text(quest_root / "quest.yaml", f"quest_id: {quest_id}\nstudy_id: {study_id}\n")
    publication_eval = _publication_eval(study_id=study_id, quest_id=quest_id, eval_suffix="newer-analysis-blocker")
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    source_result_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    _write_json(source_result_path, _source_provenance_blocker(study_id=study_id))
    analysis_result_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    _write_json(analysis_result_path, _analysis_harmonization_blocker(study_id=study_id))
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(decision_path, _materialized_methodology_decision(study_id=study_id, quest_id=quest_id))
    _set_mtime(source_result_path, 1_000)
    _set_mtime(decision_path, 2_000)
    _set_mtime(analysis_result_path, 3_000)
    _patch_projection_inputs(
        monkeypatch,
        module,
        study_id=study_id,
        quest_id=quest_id,
        quest_root=quest_root,
        study_root=study_root,
        publication_eval=publication_eval,
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    _assert_source_provenance_queued(result)


def test_methodology_reframe_decision_exposes_current_controller_runtime_route(tmp_path: Path) -> None:
    route_module = importlib.import_module(
        "med_autoscience.controllers.domain_route_scan_parts.current_truth_owner"
    )
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision = _materialized_methodology_decision(study_id=study_id, quest_id=quest_id)
    decision["controller_actions"] = [{"action_type": "ensure_study_runtime", "payload_ref": str(decision_path)}]
    decision["next_work_unit"].update(
        {
            "hard_methodology": True,
            "selected_route_option": "provenance_limited_harmonization_audit",
            "terminal_source_provenance_blocker_consumed": True,
            "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
        }
    )
    _write_json(decision_path, decision)

    route = route_module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=_publication_eval(
            study_id=study_id,
            quest_id=quest_id,
            eval_suffix="methodology-reframe-redrive",
        ),
    )

    assert route is not None
    assert route["work_unit_id"] == "provenance_limited_harmonization_audit"
    assert route["work_unit_fingerprint"] == "decision::methodology_reframe_route_decision"
    assert route["controller_actions"] == ["ensure_study_runtime"]


def test_clean_rebuild_methodology_decision_exposes_current_controller_runtime_route(tmp_path: Path) -> None:
    route_module = importlib.import_module(
        "med_autoscience.controllers.runtime_supervisor_scan_parts.current_truth_owner"
    )
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision = _materialized_methodology_decision(study_id=study_id, quest_id=quest_id)
    decision["controller_actions"] = [{"action_type": "ensure_study_runtime", "payload_ref": str(decision_path)}]
    decision["next_work_unit"] = {
        "unit_id": "unit_harmonized_external_validation_rerun",
        "lane": "analysis-campaign",
        "hard_methodology": True,
        "selected_route_option": "rebuild_reproducible_model_route",
        "terminal_source_provenance_blocker_consumed": True,
        "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
        "clean_reproducible_model_rebuild_authorized": True,
        "required_owner": "analysis_harmonization_owner",
        "required_next_work_unit": "unit_harmonized_external_validation_rerun",
        "typed_blocker": "unit_harmonized_rerun_required",
    }
    _write_json(decision_path, decision)

    route = route_module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=_publication_eval(
            study_id=study_id,
            quest_id=quest_id,
            eval_suffix="methodology-reframe-clean-rebuild-redrive",
        ),
    )

    assert route is not None
    assert route["work_unit_id"] == "unit_harmonized_external_validation_rerun"
    assert route["work_unit_fingerprint"] == "decision::methodology_reframe_route_decision"
    assert route["controller_actions"] == ["ensure_study_runtime"]


def test_platform_repair_prefers_methodology_reframe_route_over_stale_gate_specificity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repair_module = importlib.import_module("med_autoscience.controllers.domain_route_scan_parts.platform_repair")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    _write_json(
        runtime_state_path,
        {
            "status": "waiting_for_user",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "turn_closeout",
            "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            "last_controller_decision_authorization": {"decision_id": "old-ai-reviewer-route"},
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "status": "blocked",
            "blockers": ["stale_submission_minimal_authority"],
            "current_required_action": "return_to_publishability_gate",
            "supervisor_phase": "publishability_gate_blocked",
        },
    )
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision = _materialized_methodology_decision(study_id=study_id, quest_id=quest_id)
    decision["controller_actions"] = [{"action_type": "ensure_study_runtime", "payload_ref": str(decision_path)}]
    decision["next_work_unit"].update(
        {
            "hard_methodology": True,
            "selected_route_option": "provenance_limited_harmonization_audit",
            "terminal_source_provenance_blocker_consumed": True,
            "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
        }
    )
    _write_json(decision_path, decision)
    monkeypatch.setattr(
        repair_module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {
            "decision": "resume",
            "runtime_liveness_audit": {"active_run_id": "run-methodology-redrive"},
        },
    )

    result = repair_module.apply_runtime_platform_repair(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status={
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "quest_status": "waiting_for_user",
        },
        progress={"quest_root": str(quest_root), "quest_id": quest_id},
        publication_eval_payload=_publication_eval(
            study_id=study_id,
            quest_id=quest_id,
            eval_suffix="methodology-reframe-platform-redrive",
        ),
        developer_mode=_developer_mode(),
        enabled=True,
        repair_required=True,
    )

    assert result is not None
    assert result["dispatch_status"] == "applied"
    assert result["reason"] == "runtime_controller_redrive_required"
    assert result["repair_kind"] == "current_controller_runtime_route_redrive"
    assert result["current_controller_authorization_written"] is True
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["continuation_reason"] == "controller_work_unit_pending"
    assert runtime_state["last_controller_decision_authorization"]["decision_id"] == decision["decision_id"]
    assert runtime_state["last_controller_decision_authorization"]["work_unit_fingerprint"] == (
        "decision::methodology_reframe_route_decision"
    )


def _publication_eval(*, study_id: str, quest_id: str, eval_suffix: str) -> dict:
    return {
        "schema_version": 1,
        "eval_id": f"publication-eval::dm002::{eval_suffix}",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
        "recommended_actions": [],
    }


def _source_provenance_blocker(*, study_id: str) -> dict:
    return {
        "surface": "source_provenance_owner_result",
        "schema_version": 1,
        "study_id": study_id,
        "owner": "source_provenance_owner",
        "work_unit": "recover_transport_model_provenance",
        "status": "blocked",
        "blocked_reason": "transport_model_provenance_recovery_required",
        "typed_blocker_owner": "source_provenance_owner",
        "typed_blocker": {
            "blocker_id": "transport_model_provenance_recovery_required",
            "blocking_reasons": [
                "cox_model_coefficients_missing",
                "canonical_transport_model_provenance_bundle_missing",
            ],
        },
        "transport_model_provenance_recovered": False,
        "provenance_search": {
            "searched": True,
            "accepted_bundle_ref": None,
            "result_summary_acceptance_allowed": False,
            "substitute_refit_allowed": False,
        },
    }


def _analysis_harmonization_blocker(*, study_id: str) -> dict:
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


def _materialized_methodology_decision(*, study_id: str, quest_id: str) -> dict:
    return {
        "schema_version": 1,
        "decision_id": "study-decision::dm002::stale-materialized-methodology-reframe",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-18T23:13:18+00:00",
        "decision_type": "bounded_analysis",
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


def _patch_projection_inputs(
    monkeypatch,
    module,
    *,
    study_id: str,
    quest_id: str,
    quest_root: Path,
    study_root: Path,
    publication_eval: dict,
) -> None:
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "current_stage": "publication_supervision",
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


def _assert_methodology_reframe_queued(result: dict) -> None:
    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["methodology_reframe_route_decision"]
    assert [action["action_type"] for action in result["action_queue"]] == ["methodology_reframe_route_decision"]
    assert study["blocked_reason"] == "methodology_reframe_required"
    assert study["next_owner"] == "decision"
    assert study["owner_route"]["allowed_actions"] == ["methodology_reframe_route_decision"]


def _assert_source_provenance_queued(result: dict) -> None:
    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["recover_transport_model_provenance"]
    assert [action["action_type"] for action in result["action_queue"]] == ["recover_transport_model_provenance"]
    assert study["blocked_reason"] == "transport_model_provenance_recovery_required"
    assert study["next_owner"] == "source_provenance_owner"
    assert study["owner_route"]["allowed_actions"] == ["recover_transport_model_provenance"]


def _developer_mode():
    return type("DeveloperMode", (), {"safe_actions_enabled": True})()
