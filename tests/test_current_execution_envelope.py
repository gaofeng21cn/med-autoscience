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
            "allowed_state_kinds": ["parked", "executable_owner_action", "typed_blocker"],
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
