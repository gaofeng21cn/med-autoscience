from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_owner_route_envelope_prefers_explicit_resume_pending_over_ai_reviewer_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-cvd-mortality-risk"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "request_opl_stage_attempt",
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "requires_human_confirmation": False,
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "lane": "review",
                "summary": "Re-run AI reviewer against current inputs.",
            },
        },
    )
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "completed_parked_auto_continue_no_new_message",
        "active_run_id": None,
        "auto_runtime_parked": {
            "surface_kind": "auto_runtime_parked",
            "schema_version": 1,
            "parked": True,
            "parked_state": "explicit_resume_pending",
            "parked_owner": "user",
            "awaiting_explicit_wakeup": True,
            "source_reason": "completed_parked_auto_continue_no_new_message",
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-event-dm002-parked",
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "parked",
        },
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "lane": "review",
            },
        },
        "publication_eval": publication_eval,
    }
    progress_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "active_run_id": None,
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "parked_state": "explicit_resume_pending",
        "parked_owner": "user",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {
            "publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "controller_decision_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
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
    envelope = study["current_execution_envelope"]
    assert envelope == {
        "state_kind": "parked",
        "owner": "user",
        "next_work_unit": None,
        "typed_blocker": None,
        "parked_state": "explicit_resume_pending",
        "source_refs": [
            str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        ],
        "conflict_suppression_refs": ["runtime_health:await_explicit_resume"],
        "authority_boundary": {
            "surface_kind": "current_execution_envelope",
            "authority": "read_model_projection",
            "top_level_truth": "state_kind",
            "allowed_state_kinds": [
                "parked",
                "executable_owner_action",
                "running_provider_attempt",
                "typed_blocker",
            ],
            "evidence_only_surfaces": ["action_queue", "runtime_health", "no_op"],
        },
    }
    assert [action["action_type"] for action in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["current_execution_evidence"]["action_queue"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["current_execution_envelopes"][study_id] == envelope


def test_study_progress_envelope_treats_opl_queue_as_evidence_under_explicit_resume(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-cvd-mortality-risk"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-28T01:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_run_id": None,
                    "runtime_health": {"health_status": "parked", "runtime_liveness_status": "parked"},
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner": "ai_reviewer",
                            "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                        }
                    ],
                    "blocked_reason": "domain_transition_ai_reviewer_re_eval",
                    "next_owner": "ai_reviewer",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "completed_parked_auto_continue_no_new_message",
            "active_run_id": None,
            "auto_runtime_parked": {
                "surface_kind": "auto_runtime_parked",
                "schema_version": 1,
                "parked": True,
                "parked_state": "explicit_resume_pending",
                "parked_owner": "user",
                "awaiting_explicit_wakeup": True,
                "source_reason": "completed_parked_auto_continue_no_new_message",
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-dm002-parked",
                "canonical_runtime_action": "await_explicit_resume",
                "attempt_state": "parked",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    envelope = result["current_execution_envelope"]
    assert envelope["state_kind"] == "parked"
    assert envelope["owner"] == "user"
    assert envelope["parked_state"] == "explicit_resume_pending"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"] is None
    assert "runtime_health:await_explicit_resume" in envelope["conflict_suppression_refs"]
    assert result["current_execution_evidence"]["action_queue"][0]["action_type"] == "return_to_ai_reviewer_workflow"


def test_study_progress_envelope_prefers_live_opl_attempt_over_handoff_action_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-06T10:20:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-live",
                    "active_stage_attempt_id": "sat-live",
                    "active_workflow_id": "wf-live",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                        "summary": "OPL provider attempt is running.",
                    },
                    "action_queue": [
                        {
                            "action_type": "complete_medical_paper_readiness_surface",
                            "owner": "MedAutoScience",
                            "next_work_unit": "complete_medical_paper_readiness_surface",
                        }
                    ],
                    "next_owner": "MedAutoScience",
                    "blocked_reason": None,
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "publication_handoff_owner_gate",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-before-live-attempt",
                "runtime_liveness_status": "queued",
                "attempt_state": "queued",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    envelope = result["current_execution_envelope"]
    assert result["opl_current_control_state_handoff"]["running_provider_attempt"] is True
    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "sat-live"
    assert envelope["typed_blocker"] is None
    assert result["current_execution_evidence"]["action_queue"][0]["action_type"] == (
        "complete_medical_paper_readiness_surface"
    )


def test_study_progress_envelope_preserves_non_superseded_handoff_blocker_over_live_attempt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-06T10:25:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-live",
                    "active_stage_attempt_id": "sat-live",
                    "active_workflow_id": "wf-live",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "complete_medical_paper_readiness_surface",
                            "owner": "MedAutoScience",
                            "next_work_unit": "complete_medical_paper_readiness_surface",
                        }
                    ],
                    "next_owner": "MedAutoScience",
                    "blocked_reason": "medical_paper_readiness_not_ready",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "publication_handoff_owner_gate",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-before-live-attempt",
                "runtime_liveness_status": "queued",
                "attempt_state": "queued",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    envelope = result["current_execution_envelope"]
    assert result["opl_current_control_state_handoff"]["running_provider_attempt"] is True
    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "medical_paper_readiness_not_ready"


def test_envelope_prefers_executable_action_over_reason_only_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            }
        ],
        blocked_reason="domain_transition_ai_reviewer_re_eval",
        next_owner="ai_reviewer",
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert envelope["typed_blocker"] is None


def test_envelope_prefers_running_provider_attempt_over_stale_action_queue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        blocked_reason=None,
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": "complete_medical_paper_readiness_surface",
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "runtime_health": {
                "runtime_liveness_status": "live",
                "provider_status": "running",
            },
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
            "work_unit_id": "complete_medical_paper_readiness_surface",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert envelope["typed_blocker"] is None


def test_envelope_preserves_non_superseded_blocker_over_running_provider_attempt() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        blocked_reason="typed_closeout_packet_required",
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": "complete_medical_paper_readiness_surface",
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
        },
    )

    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"


def test_envelope_does_not_borrow_next_work_unit_from_stale_action_queue_for_running_attempt() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            }
        ],
        blocked_reason=None,
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "sat-live"


def test_envelope_prefers_running_provider_attempt_over_stale_parked_projection() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        status={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "waiting_user_decision",
                "parked_owner": "user",
                "source_reason": "quest_waiting_for_user",
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "runtime_liveness_status": "live",
            },
        },
        progress={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "waiting_user_decision",
                "parked_owner": "user",
            },
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
        },
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
        runtime_health={
            "canonical_runtime_action": "continue_supervising_runtime",
            "runtime_liveness_status": "live",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "sat-live"
    assert envelope["parked_state"] is None


def test_envelope_preserves_explicit_typed_blocker_over_action_queue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_work_unit": "manuscript_story_repair",
            }
        ],
        blocked_reason="typed_closeout_packet_required",
        next_owner="one-person-lab",
        typed_blocker={
            "blocker_type": "typed_closeout_packet_required",
            "owner": "one-person-lab",
        },
    )

    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "one-person-lab"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"
