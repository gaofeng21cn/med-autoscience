from __future__ import annotations

import importlib
import os

from tests.mcp_opl_current_control_state_handoff_cases.shared import (
    append_jsonl as _append_jsonl,
    make_profile,
    opl_transition_readback,
    opl_transition_replay_audit_readback,
    write_json as _write_json,
)

def test_study_progress_opl_current_control_state_handoff_projects_latest_terminal_stage_log(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-05-27T20:32:10+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {"health_status": "awaiting_explicit_resume"},
                }
            ],
        },
    )
    closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-terminal.closeout_payload.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-05-27T19:46:34Z",
            "study_id": "001-risk",
            "stage_id": "stage_outcome/opl-handoff",
            "stage_attempt_id": "sat-terminal",
            "action_type": "run_quality_repair_batch",
            "status": "blocked_with_domain_owner_refs",
            "duration": {"seconds": 91.25, "source": "provider_attempt"},
            "token_usage": {"total_tokens": 12345, "input_tokens": 6789, "output_tokens": 5556},
            "cost": {"usd": 0.42, "currency": "USD"},
            "usage_refs": ["usage:provider-attempt:sat-terminal"],
            "cost_refs": ["cost:provider-attempt:sat-terminal"],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_name": "stage_outcome/opl-handoff",
                "problem_summary": "The repair owner could not write because authority route evidence was blocked.",
                "stage_goal": "Produce owner-authorized manuscript repair output or a typed blocker.",
                "stage_work_done": [
                    "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                ],
                "paper_work_done": [
                    "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                ],
                "changed_stage_surfaces": [],
                "changed_paper_surfaces": [],
                "progress_delta_classification": "platform_repair",
                "outcome": "blocked_with_domain_typed_blocker",
                "remaining_blockers": [
                    "authority_route_blocked",
                    "opl_current_control_state.handoff_required",
                ],
                "usage_refs": ["usage:provider-attempt:sat-terminal"],
                "cost_refs": ["cost:provider-attempt:sat-terminal"],
                "evidence_refs": [
                    "artifacts/supervision/consumer/owner_callable_adapters/run_quality_repair_batch.json",
                    "artifacts/publication_eval/latest.json",
                ],
            },
            "closeout_refs": [
                "artifacts/supervision/consumer/stage_attempt_closeouts/sat-terminal.closeout_payload.json"
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["active_run_id"] is None
    assert projection["stage_progress_log"] == {}
    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["surface_kind"] == "mas_latest_terminal_stage_log_projection"
    assert terminal_log["source_path"] == str(closeout_path)
    assert terminal_log["stage_attempt_id"] == "sat-terminal"
    assert terminal_log["action_type"] == "run_quality_repair_batch"
    assert terminal_log["status"] == "blocked_with_domain_owner_refs"
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["duration"] == {"seconds": 91.25, "source": "provider_attempt"}
    assert terminal_log["token_usage"] == {
        "total_tokens": 12345,
        "input_tokens": 6789,
        "output_tokens": 5556,
    }
    assert terminal_log["cost"] == {"usd": 0.42, "currency": "USD"}
    assert terminal_log["usage_refs"] == ["usage:provider-attempt:sat-terminal"]
    assert terminal_log["cost_refs"] == ["cost:provider-attempt:sat-terminal"]
    assert terminal_log["missing_observability_fields"] == []
    assert terminal_log["paper_stage_log"]["stage_work_done"] == [
        "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
    ]
    assert terminal_log["paper_stage_log"]["changed_stage_surfaces"] == []
    assert terminal_log["paper_stage_log"]["progress_delta_classification"] == "platform_repair"
    assert terminal_log["paper_stage_log"]["outcome"] == "blocked_with_domain_typed_blocker"
    assert terminal_log["paper_stage_log"]["remaining_blockers"] == [
        "authority_route_blocked",
        "opl_current_control_state.handoff_required",
    ]
    assert terminal_log["authority_boundary"]["observability_only"] is True
    assert terminal_log["authority_boundary"]["can_mark_live_run"] is False
    assert terminal_log["authority_boundary"]["can_authorize_quality_verdict"] is False


def test_study_progress_latest_terminal_stage_log_prefers_current_stage_closure_route_checkpoint_over_newer_stale_closeout(
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-07-05T03:50:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {"health_status": "awaiting_explicit_resume"},
                }
            ],
        },
    )
    stale_closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-stale.json"
    )
    _write_json(
        stale_closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-07-05T03:40:00Z",
            "study_id": "001-risk",
            "stage_id": "submission_milestone_candidate",
            "stage_attempt_id": "sat-stale",
            "status": "blocked_with_typed_closeout",
            "work_unit_id": "submission_milestone_candidate",
            "paper_stage_log": {
                "stage_name": "submission_milestone_candidate",
                "paper_work_done": ["Recorded an older submission checkpoint blocker."],
                "outcome": "typed_blocker",
                "remaining_blockers": ["opl_runtime_live_readback_missing"],
                "evidence_refs": ["ops/medautoscience/paper_mission_stage_attempts/sat-stale/stage_attempt_closeout_packet.json"],
            },
        },
    )
    current_closeout_path = (
        profile.workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-current"
        / "stage_attempt_closeout_packet.json"
    )
    _write_json(
        current_closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-07-05T03:35:00Z",
            "study_id": "001-risk",
            "stage_id": "review",
            "stage_attempt_id": "sat-current",
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "route_back_evidence_candidate",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            "paper_stage_log": {
                "stage_name": "review",
                "paper_work_done": ["Materialized the current route-back checkpoint packet."],
                "outcome": "route_back_evidence_candidate",
                "remaining_blockers": [],
                "evidence_refs": ["ops/medautoscience/paper_mission_stage_attempts/sat-current/stage_attempt_closeout_packet.json"],
            },
        },
    )
    os.utime(stale_closeout_path, (1_783_000_000, 1_783_000_000))
    os.utime(current_closeout_path, (1_782_999_900, 1_782_999_900))
    stage_closure_path = (
        profile.workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / "001-risk"
        / "stage_closure_decision.json"
    )
    _write_json(
        stage_closure_path,
        {
            "surface_kind": "mas_stage_closure_decision",
            "generated_at": "2026-07-05T03:49:00Z",
            "study_id": "001-risk",
            "stage_id": "review",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            "route_checkpoint_evidence_ref": "ops/medautoscience/paper_mission_stage_attempts/sat-current/stage_attempt_closeout_packet.json",
            "opl_closeout": {
                "stage_attempt_id": "sat-current",
                "status": "opl_runtime_terminal_readback_observed",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            },
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "route_checkpoint_evidence_ref": "ops/medautoscience/paper_mission_stage_attempts/sat-current/stage_attempt_closeout_packet.json",
            },
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["stage_attempt_id"] == "sat-current"
    assert terminal_log["source_path"] == str(current_closeout_path)
    assert terminal_log["action_type"] == "return_to_ai_reviewer_workflow"
    assert terminal_log["paper_stage_log"]["paper_work_done"] == [
        "Materialized the current route-back checkpoint packet."
    ]


def test_study_progress_latest_terminal_stage_log_prefers_direct_owner_execution(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-05-27T21:13:12+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {"health_status": "awaiting_explicit_resume"},
                }
            ],
        },
    )
    old_closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-old.closeout_payload.json"
    )
    _write_json(
        old_closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "generated_at": "2026-05-27T19:46:34Z",
            "study_id": "001-risk",
            "stage_attempt_id": "sat-old",
            "action_type": "run_quality_repair_batch",
            "status": "blocked_with_domain_owner_refs",
            "paper_stage_log": {
                "stage_name": "stage_outcome/opl-handoff",
                "paper_work_done": ["Recorded an older typed blocker."],
                "outcome": "blocked_with_domain_typed_blocker",
                "remaining_blockers": ["authority_route_blocked"],
                "evidence_refs": ["artifacts/publication_eval/latest.json"],
            },
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "legacy_surface_alias": "owner_callable_dispatch_execution_study_latest",
            "generated_at": "2026-05-27T21:12:39+00:00",
            "study_id": "001-risk",
            "owner_callable_receipt_projection": True,
            "projection_authority": False,
            "executions": [
                {
                    "surface": "owner_callable_adapter_receipt",
                    "legacy_surface_alias": "owner_callable_dispatch_execution",
                    "generated_at": "2026-05-27T21:12:39+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "duration_seconds": 18.0,
                    "usage": {
                        "input_tokens": 2100,
                        "output_tokens": 900,
                        "total_tokens": 3000,
                        "source_refs": ["usage:quality-repair-owner"],
                    },
                    "cost_usd": 0.17,
                    "cost_refs": ["cost:quality-repair-owner"],
                    "paper_stage_log": {
                        "stage_name": "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
                        "current_owner": "write",
                        "stage_work_done": [
                            "Updated claim-evidence and review ledgers through the quality repair owner."
                        ],
                        "paper_work_done": [
                            "Updated claim-evidence and review ledgers through the quality repair owner."
                        ],
                        "changed_stage_surfaces": [
                            "paper/claim_evidence_map.json",
                            "paper/evidence_ledger.json",
                        ],
                        "changed_paper_surfaces": [
                            "paper/claim_evidence_map.json",
                            "paper/evidence_ledger.json",
                        ],
                        "outcome": "executed",
                        "remaining_blockers": [],
                        "evidence_refs": [
                            "artifacts/controller/quality_repair_batch/latest.json",
                            "paper/evidence_ledger.json",
                        ],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert projection["active_run_id"] is None
    assert terminal_log["source_path"] == str(latest_execution_path)
    assert terminal_log["record_path"] == f"{latest_execution_path}#executions/0"
    assert terminal_log["action_type"] == "run_quality_repair_batch"
    assert terminal_log["status"] == "executed"
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["duration"] == {"seconds": 18.0}
    assert terminal_log["token_usage"] == {
        "input_tokens": 2100,
        "output_tokens": 900,
        "total_tokens": 3000,
        "source_refs": ["usage:quality-repair-owner"],
    }
    assert terminal_log["cost"] == {"usd": 0.17}
    assert terminal_log["usage_refs"] == ["usage:quality-repair-owner"]
    assert terminal_log["cost_refs"] == ["cost:quality-repair-owner"]
    assert terminal_log["missing_observability_fields"] == []
    assert terminal_log["paper_stage_log"]["outcome"] == "executed"
    assert terminal_log["paper_stage_log"]["stage_work_done"] == [
        "Updated claim-evidence and review ledgers through the quality repair owner."
    ]
    assert terminal_log["paper_stage_log"]["changed_stage_surfaces"] == [
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
    ]
    assert terminal_log["paper_stage_log"]["changed_paper_surfaces"] == [
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
    ]
    assert terminal_log["authority_boundary"]["can_mark_live_run"] is False


def test_handoff_projection_closes_running_flag_for_matching_terminal_attempt(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-08T17:18:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-live",
                    "active_stage_attempt_id": "sat-live",
                    "active_workflow_id": "wf-live",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "owner_callable_dispatch_execution_study_latest",
            "generated_at": "2026-06-08T17:19:37+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-06-08T17:19:37+00:00",
                    "study_id": "001-risk",
                    "stage_attempt_id": "sat-live",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "paper_stage_log": {
                        "stage_name": "return_to_ai_reviewer_workflow",
                        "problem_summary": "Owner callable failed closed with a typed blocker.",
                        "stage_goal": "Produce an AI reviewer record or typed blocker.",
                        "stage_work_done": ["Ran the owner callable."],
                        "paper_work_done": ["No publication eval was written."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "typed_blocker",
                        "outcome": "typed_blocker",
                        "remaining_blockers": ["medical_prose_review_request_rehydrate_required"],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert projection["active_workflow_id"] is None
    assert projection["active_stage_attempt_id"] == "sat-live"
    assert projection["runtime_health"]["health_status"] == "terminal"
    assert projection["runtime_health"]["runtime_liveness_status"] == "terminal"
    assert projection["latest_terminal_stage_log"]["stage_attempt_id"] == "sat-live"
    assert projection["latest_terminal_stage_log"]["status"] == "blocked"


def test_handoff_projection_fail_closed_when_terminal_closeout_lacks_owner_answer(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-10T12:00:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-no-answer",
                    "active_stage_attempt_id": "sat-no-answer",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "status": "ready",
                            "owner": "ai_reviewer",
                            "work_unit_id": "ai-reviewer-record",
                            "work_unit_fingerprint": "wu-fp-1",
                            "stage_attempt_id": "sat-no-answer",
                        }
                    ],
                }
            ],
        },
    )
    closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    _write_json(
        closeout_path,
        {
            "surface": "owner_callable_dispatch_execution_study_latest",
            "generated_at": "2026-06-10T12:01:00+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-06-10T12:01:00+00:00",
                    "study_id": "001-risk",
                    "stage_attempt_id": "sat-no-answer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "completed",
                    "paper_stage_log": {
                        "stage_name": "return_to_ai_reviewer_workflow",
                        "problem_summary": "Provider returned terminal closeout without owner answer.",
                        "stage_goal": "Produce an AI reviewer record or typed blocker.",
                        "stage_work_done": ["Inspected current inputs."],
                        "paper_work_done": ["No publication eval was written."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "platform_repair",
                        "outcome": "completed_without_owner_answer",
                        "remaining_blockers": [],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert projection["action_queue"] == []
    assert projection["typed_blocker"]["blocker_id"] == "typed_closeout_packet_required"
    assert projection["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"
    assert projection["typed_blocker"]["owner"] == "MedAutoScience"
    assert projection["typed_blocker"]["work_unit_id"] == "ai-reviewer-record"
    assert projection["consumed_action_queue"][0]["consumption"]["state"] == "consumed_by_terminal_stage_closeout"
    assert projection["blocked_reason"] == "typed_closeout_packet_required"
    assert projection["next_owner"] == "MedAutoScience"


def test_handoff_projection_accepts_terminal_closeout_owner_receipt_ref(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-10T12:00:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-owner-answer",
                    "active_stage_attempt_id": "sat-owner-answer",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "status": "ready",
                            "owner": "ai_reviewer",
                            "work_unit_id": "ai-reviewer-record",
                            "work_unit_fingerprint": "wu-fp-1",
                            "stage_attempt_id": "sat-owner-answer",
                        }
                    ],
                }
            ],
        },
    )
    closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    _write_json(
        closeout_path,
        {
            "surface": "owner_callable_dispatch_execution_study_latest",
            "generated_at": "2026-06-10T12:01:00+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-06-10T12:01:00+00:00",
                    "study_id": "001-risk",
                    "stage_attempt_id": "sat-owner-answer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "completed",
                    "status": "closed_with_domain_owner_refs",
                    "route_outcome": "owner_receipt",
                    "owner_receipt_ref": (
                        "studies/001-risk/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                        "sat-owner-answer.closeout.json#owner_receipt"
                    ),
                    "paper_stage_log": {
                        "stage_name": "return_to_ai_reviewer_workflow",
                        "problem_summary": "Provider returned record-only AI reviewer evidence.",
                        "stage_goal": "Produce an AI reviewer owner receipt.",
                        "stage_work_done": ["Materialized reviewer record."],
                        "paper_work_done": ["No publication latest surface was written."],
                        "changed_stage_surfaces": [
                            "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json"
                        ],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "deliverable_progress",
                        "outcome": "closed_with_domain_owner_refs",
                        "remaining_blockers": [],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert "typed_blocker" not in projection
    assert "typed_closeout_packet_required" not in projection.get("why_not_applied", [])


def test_handoff_projection_accepts_terminal_closeout_next_handoff_refs(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "generated_at": "2026-06-10T12:00:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "provider_admission_pending",
                    "active_run_id": "opl-stage-attempt://sat-next-handoff",
                    "active_stage_attempt_id": "sat-next-handoff",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                    "action_queue": [
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "status": "ready",
                            "owner": "ai_reviewer",
                            "work_unit_id": "ai-reviewer-record",
                            "work_unit_fingerprint": "wu-fp-1",
                            "stage_attempt_id": "sat-next-handoff",
                        }
                    ],
                }
            ],
        },
    )
    closeout_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-next-handoff.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "generated_at": "2026-06-10T12:01:00+00:00",
            "study_id": "001-risk",
            "stage_attempt_id": "sat-next-handoff",
            "stage_id": "stage_outcome/opl-handoff",
            "action_type": "return_to_ai_reviewer_workflow",
            "status": "closed_with_domain_owner_refs",
            "domain_owner_refs": {
                "publication_eval_record_ref": "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                "next_dispatch_ref": "studies/001-risk/artifacts/supervision/consumer/owner_callable_adapters/run_gate_clearing_batch.json",
                "next_request_ref": "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
            },
            "paper_stage_log": {
                "stage_name": "return_to_ai_reviewer_workflow",
                "problem_summary": "Provider produced current reviewer evidence and routed the next owner.",
                "stage_goal": "Produce reviewer record and next gate-clearing handoff.",
                "stage_work_done": [
                    "Materialized the reviewer record.",
                    "Routed the next owner to run_gate_clearing_batch.",
                ],
                "paper_work_done": ["Produced record-only reviewer evidence."],
                "changed_stage_surfaces": [
                    "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                    "studies/001-risk/artifacts/supervision/consumer/owner_callable_adapters/run_gate_clearing_batch.json",
                    "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
                ],
                "changed_paper_surfaces": [],
                "progress_delta_classification": "deliverable_progress",
                "outcome": "closed_with_domain_owner_refs",
                "remaining_blockers": ["Domain readiness remains owned by MAS gate surfaces."],
                "next_forced_delta": {
                    "required_delta_kind": "owner_route_replay_or_typed_blocker",
                    "reason": "domain_action_request_materialize_routed_next_owner_after_current_ai_reviewer_record",
                    "owner_action": {
                        "next_owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "current_package_freshness_required",
                    },
                    "target_surface": {
                        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                    },
                    "acceptance_refs": ["owner_receipt_ref", "typed_blocker_ref", "changed_surface_ref"],
                },
                "evidence_refs": [
                    "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                    "studies/001-risk/artifacts/supervision/consumer/owner_callable_adapters/run_gate_clearing_batch.json",
                    "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
                ],
            },
            "closeout_refs": [
                "studies/001-risk/artifacts/publication_eval/ai_reviewer_responses/record.json",
                "studies/001-risk/artifacts/supervision/consumer/owner_callable_adapters/run_gate_clearing_batch.json",
                "studies/001-risk/artifacts/supervision/requests/gate_clearing_batch/latest.json",
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    assert projection["running_provider_attempt"] is False
    assert projection["active_run_id"] is None
    assert "typed_blocker" not in projection
    assert projection["next_owner"] != "one-person-lab"
    assert "typed_closeout_packet_required" not in projection.get("why_not_applied", [])
    assert projection["latest_terminal_stage_log"]["next_forced_delta"]["owner_action"]["action_type"] == (
        "run_gate_clearing_batch"
    )
