from __future__ import annotations

import importlib

from tests.mcp_opl_current_control_state_handoff_cases.shared import (
    append_jsonl as _append_jsonl,
    make_profile,
    opl_transition_readback,
    opl_transition_replay_audit_readback,
    write_json as _write_json,
)

def test_study_progress_opl_current_control_state_handoff_does_not_copy_private_execution_policy(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-05-04T06:00:00+00:00",
            "developer_supervisor_mode": {
                "mode": "developer_apply_safe",
                "mode_label": "Developer Supervisor Mode",
                "scheduler_owner": "external_scheduler",
                "codex_app_heartbeat_required": False,
                "safe_actions_enabled": True,
                "repo_level_repair_authority": True,
                "github_user_gate": {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None},
            },
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "blocked",
                    "active_run_id": "run-001",
                    "external_supervisor_required": True,
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["study_id"] == "001-risk"
    for key in (
        "mode",
        "mode_label",
        "scheduler_owner",
        "codex_app_heartbeat_required",
        "safe_actions_enabled",
        "repo_level_repair_authority",
        "github_user_gate",
    ):
        assert key not in projection


def test_study_progress_opl_current_control_state_handoff_projection_preserves_string_why_not_applied(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-05-09T08:54:24+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "why_not_applied": "repeat_suppressed",
                    "blocked_reason": "repeat_suppressed",
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["why_not_applied"] == ["repeat_suppressed"]


def test_study_progress_opl_current_control_state_handoff_rejects_incomplete_top_level_provider_admission_candidate(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-17T02:51:08+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "study_id": "001-risk",
                    "quest_id": "001-risk",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::abc",
                    "provider_admission_identity": {
                        "stage_packet_ref": "studies/001-risk/artifacts/packet.json",
                        "route_identity_key": "paper-policy-request:abc",
                    },
                    "domain_progress_transition_runtime": {
                        "transition_event": {"event_id": "evt-001"},
                        "transactional_outbox_item": {"outbox_item_id": "outbox-001"},
                        "identity": {"stage_run_identity": {"stage_run_id": "sr-001"}},
                    },
                }
            ],
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "blocked",
                    "blocked_reason": "stage_outcome_authority_apply_selected_zero_dispatch",
                    "typed_blocker": {
                        "blocker_type": "stage_outcome_authority_apply_selected_zero_dispatch",
                    },
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "publication-blockers::abc",
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["provider_admission_pending_count"] == 0
    assert projection["provider_admission_candidates"] == []
    assert projection["blocked_reason"] == "stage_outcome_authority_apply_selected_zero_dispatch"
    assert projection["typed_blocker"]["blocker_type"] == (
        "stage_outcome_authority_apply_selected_zero_dispatch"
    )


def test_study_progress_opl_current_control_state_handoff_merges_complete_top_level_provider_admission_readback(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::abc"
    route_key = "paper-policy-request:abc"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id="sr-001",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-17T02:51:08+00:00",
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "route_identity_key": route_key,
                    "attempt_idempotency_key": route_key,
                    "provider_admission_identity": {
                        "stage_packet_ref": f"studies/{study_id}/artifacts/packet.json",
                        "route_identity_key": route_key,
                        "attempt_idempotency_key": route_key,
                        "opl_domain_progress_transition_runtime_live_readback": readback,
                    },
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "blocked",
                    "blocked_reason": "stage_outcome_authority_apply_selected_zero_dispatch",
                    "typed_blocker": {
                        "blocker_type": "stage_outcome_authority_apply_selected_zero_dispatch",
                    },
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["provider_admission_pending_count"] == 1
    assert projection["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert projection["provider_admission_candidates"][0][
        "opl_domain_progress_transition_runtime_live_readback"
    ]["runtime_readback_status"] == "complete_transaction"
    assert projection["action_type"] == "run_quality_repair_batch"
    assert projection["work_unit_id"] == work_unit_id
    assert projection["blocked_reason"] is None
    assert "typed_blocker" not in projection


def test_study_progress_opl_current_control_state_handoff_binds_root_readback_to_action_queue(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
    )
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-20T17:45:32+00:00",
            "provider_admission_pending_count": 1,
            "transition_request_pending_count": 0,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "provider_admission_pending",
                    "provider_admission_pending_count": 1,
                    "transition_request_pending_count": 0,
                    "running_provider_attempt": False,
                    "provider_admission_identity": {
                        "study_id": study_id,
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "route_identity_key": route_key,
                        "attempt_idempotency_key": route_key,
                        "request_idempotency_key": route_key,
                        "opl_domain_progress_transition_runtime_live_readback": readback,
                    },
                    "action_queue": [
                        {
                            "status": "queued",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "request_opl_stage_attempt",
                            "owner": "write",
                            "next_executable_owner": "write",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "route_identity_key": route_key,
                            "attempt_idempotency_key": route_key,
                            "idempotency_key": route_key,
                        }
                    ],
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)

    assert projection["quest_status"] == "provider_admission_pending"
    assert projection["provider_admission_pending_count"] == 1
    assert projection["transition_request_pending_count"] == 0
    assert len(projection["provider_admission_candidates"]) == 1
    candidate = projection["provider_admission_candidates"][0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["source"] == "opl_current_control_state_action_queue"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["route_identity_key"] == route_key
    assert candidate["attempt_idempotency_key"] == route_key
    assert candidate["opl_domain_progress_transition_runtime_live_readback"] == readback
    assert projection["blocked_reason"] is None
