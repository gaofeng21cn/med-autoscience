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
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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


def test_study_progress_does_not_project_closed_handoff_attempt_as_live(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-08T04:14:26+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-closed",
                    "active_stage_attempt_id": "sat-closed",
                    "active_workflow_id": "wf-closed",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "latest_terminal_stage_log": {
                        "stage_attempt_id": "sat-closed",
                        "status": "closed_with_domain_owner_refs",
                        "source_path": (
                            "studies/002-dm-china-us-mortality-attribution/"
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat-closed.closeout.json"
                        ),
                    },
                    "action_queue": [
                        {
                            "action_type": "complete_medical_paper_readiness_surface",
                            "owner": "MedAutoScience",
                            "next_work_unit": "complete_medical_paper_readiness_surface",
                        }
                    ],
                    "next_owner": "MedAutoScience",
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
            "reason": "quest_marked_running_but_no_live_session",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-closed",
                "runtime_liveness_status": "unknown",
                "attempt_state": "queued",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    assert result["opl_current_control_state_handoff"]["running_provider_attempt"] is True
    assert result["active_run_id"] is None
    assert result["opl_runtime_refs"]["active_run_id"] is None
    assert result["opl_runtime_refs"]["strict_live"] is not True
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["current_execution_envelope"]["owner"] == "MedAutoScience"
    assert result["progress_first_monitoring_summary"]["running_provider_attempt"] is False
    assert (
        result["progress_first_monitoring_summary"]["owner_action_admission"][
            "provider_attempt_running_proven"
        ]
        is False
    )
    assert result["user_visible_projection"]["actual_write_active"] is False


def test_study_progress_envelope_prefers_live_attempt_over_readiness_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "sat-live"
    assert envelope["typed_blocker"] is None


def test_study_progress_projects_provider_admission_identity_queue_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-08T05:53:27+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "running_provider_attempt": False,
                    "provider_admission_pending_count": 1,
                    "runtime_health": {
                        "health_status": "recover_runtime",
                        "runtime_liveness_status": "ready",
                    },
                    "action_queue": [
                        {
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "next_owner": "write",
                            "next_work_unit": (
                                "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                            ),
                            "work_unit_id": (
                                "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                            ),
                            "authority": "mas_provider_admission_identity",
                            "action_id": "provider-admission::002-dm::run_quality_repair_batch",
                            "action_fingerprint": (
                                "study-progress-current-owner-ticket::002-dm::"
                                "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                            ),
                            "work_unit_fingerprint": (
                                "study-progress-current-owner-ticket::002-dm::"
                                "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                            ),
                        }
                    ],
                    "blocked_reason": "provider_admission_current_control_state_required",
                    "next_owner": "write",
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
                "runtime_health_epoch": "runtime-health-event-current-provider-admission",
                "runtime_liveness_status": "ready",
                "attempt_state": "queued",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    action = result["opl_current_control_state_handoff"]["action_queue"][0]
    assert action["authority"] == "mas_provider_admission_identity"
    assert action["action_id"] == "provider-admission::002-dm::run_quality_repair_batch"
    assert action["action_fingerprint"].startswith("study-progress-current-owner-ticket::002-dm::")
    assert action["work_unit_fingerprint"].startswith("study-progress-current-owner-ticket::002-dm::")
    assert result["current_execution_evidence"]["action_queue"][0]["authority"] == (
        "mas_provider_admission_identity"
    )


def test_study_progress_envelope_preserves_latest_default_executor_typed_closeout_over_stale_action_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-07T00:36:14+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-old",
                    "running_provider_attempt": False,
                    "runtime_health": {},
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner": "ai_reviewer",
                            "next_work_unit": "ai_reviewer_medical_prose_quality_review",
                        }
                    ],
                    "next_owner": "ai_reviewer",
                    "blocked_reason": "domain_transition_ai_reviewer_re_eval",
                }
            ],
        },
    )
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat-rehydrate.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "generated_at": "2026-06-07T01:04:47+00:00",
            "study_id": study_id,
            "quest_id": quest_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat-rehydrate",
            "closeout_id": "stage-attempt-closeout::sat-rehydrate::medical_prose_review_request_rehydrate_required",
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "blocked_with_typed_closeout",
            "blocked_reason": "medical_prose_review_request_rehydrate_required",
            "stage_packet_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
                "immutable/return_to_ai_reviewer_workflow/packet.json"
            ),
            "domain_execution": {
                "action_type": "return_to_ai_reviewer_workflow",
                "execution_status": "blocked",
                "blocked_reason": "medical_prose_review_request_rehydrate_required",
                "domain_owner": "ai_reviewer",
                "execution_id": "execution::002::return_to_ai_reviewer_workflow::2026-06-07T01:04:47+00:00",
            },
            "typed_blocker": {
                "blocked_reason": "medical_prose_review_request_rehydrate_required",
                "next_owner": "ai_reviewer",
                "write_permitted": False,
            },
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "ai_reviewer_medical_prose_quality_review",
                "current_owner": "ai_reviewer",
                "problem_summary": "request rehydrate required",
                "stage_goal": "Produce current AI reviewer medical prose review.",
                "stage_work_done": ["Recorded typed owner blocker."],
                "paper_work_done": ["Recorded typed owner blocker."],
                "changed_stage_surfaces": [],
                "changed_paper_surfaces": [],
                "outcome": "blocked_with_domain_typed_blocker",
                "remaining_blockers": [
                    "medical_prose_review_request_rehydrate_required",
                    "medical_prose_review_request_manuscript_ref_mismatch",
                ],
                "progress_delta_classification": "typed_blocker",
            },
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/sat-rehydrate.closeout.json",
                "typed-blocker:medical_prose_review_request_rehydrate_required",
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
                "runtime_health_epoch": "runtime-health-event-after-closeout",
                "runtime_liveness_status": "none",
                "attempt_state": "blocked",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    envelope = result["current_execution_envelope"]
    assert handoff["blocked_reason"] == "medical_prose_review_request_rehydrate_required"
    assert handoff["latest_typed_default_executor_closeout"]["receipt_ref"].endswith(
        "sat-rehydrate.closeout.json"
    )
    assert result["current_execution_evidence"]["action_queue"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "medical_prose_review_request_rehydrate_required"


def test_study_progress_envelope_treats_handoff_owner_reason_as_running_context(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-06T10:30:00+00:00",
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
                            "action_type": "run_gate_clearing_batch",
                            "owner": "gate_clearing_batch",
                            "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                        }
                    ],
                    "next_owner": "gate_clearing_batch",
                    "blocked_reason": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
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
    assert envelope["owner"] == "gate_clearing_batch"
    assert envelope["next_work_unit"] == "sat-live"
    assert envelope["typed_blocker"] is None


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


def test_envelope_preserves_rehydrate_typed_closeout_over_stale_ai_reviewer_action() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "ai_reviewer_medical_prose_quality_review",
            }
        ],
        blocked_reason="medical_prose_review_request_rehydrate_required",
        next_owner="ai_reviewer",
    )

    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "medical_prose_review_request_rehydrate_required"


def test_envelope_domain_transition_supersedes_readiness_blocker_after_paper_delta() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        progress={
            "progress_first_sprint_state": {
                "paper_progress_delta_counted": True,
            },
            "paper_progress_delta": {"count": 1},
        },
        actions=[
            {
                "action_type": "request_opl_stage_attempt",
                "owner": "finalize",
                "recommended_owner": "finalize",
                "next_owner": "finalize",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["request_opl_stage_attempt"],
                "source_surface": "domain_transition",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "finalize"
    assert envelope["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert envelope["typed_blocker"] is None


def test_envelope_does_not_let_stale_waiting_user_decision_hide_executable_route() -> None:
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
                "canonical_runtime_action": "continue_owner_route",
                "runtime_liveness_status": "idle",
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
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            }
        ],
        blocked_reason="domain_transition_publication_gate_blocker",
        next_owner="gate_clearing_batch",
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "gate_clearing_batch"
    assert envelope["next_work_unit"] == "publication_gate_replay"
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None


def test_envelope_treats_non_human_waiting_user_decision_as_stale_when_owner_action_exists() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        status={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "waiting_user_decision",
                "parked_owner": "user",
                "awaiting_explicit_wakeup": True,
                "auto_execution_complete": False,
                "source_reason": "quest_waiting_for_user",
                "runtime_failure_classification": {
                    "requires_human_gate": False,
                    "auto_recovery_allowed": True,
                    "blocker_class": "none",
                },
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "runtime_liveness_status": "idle",
            },
        },
        progress={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "waiting_user_decision",
                "parked_owner": "user",
                "awaiting_explicit_wakeup": True,
                "auto_execution_complete": False,
                "runtime_failure_classification": {
                    "requires_human_gate": False,
                    "auto_recovery_allowed": True,
                    "blocker_class": "none",
                },
            },
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
        },
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None


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


def test_envelope_prefers_running_provider_attempt_over_readiness_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": "complete_medical_paper_readiness_surface",
            "work_unit_id": "complete_medical_paper_readiness_surface",
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

from tests.test_current_execution_envelope_cases.repair_progress_and_provider_admission import *  # noqa: F403,F401,E402
