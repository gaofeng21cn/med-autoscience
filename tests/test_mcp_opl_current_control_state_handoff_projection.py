from __future__ import annotations

import importlib
import json

from tests.study_runtime_test_helpers import make_profile


def _write_json(path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_study_progress_opl_current_control_state_handoff_projection_reads_developer_supervisor_mode(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
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

    assert projection["mode"] == "developer_apply_safe"
    assert projection["mode_label"] == "Developer Supervisor Mode"
    assert projection["scheduler_owner"] == "external_scheduler"
    assert projection["codex_app_heartbeat_required"] is False
    assert projection["safe_actions_enabled"] is True
    assert projection["repo_level_repair_authority"] is True
    assert projection["github_user_gate"] == {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None}


def test_study_progress_opl_current_control_state_handoff_projection_preserves_string_why_not_applied(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
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


def test_study_progress_opl_current_control_state_handoff_projects_latest_terminal_stage_log(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
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
            "stage_id": "domain_owner/default-executor-dispatch",
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
                "stage_name": "domain_owner/default-executor-dispatch",
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
                    "artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
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


def test_study_progress_latest_terminal_stage_log_prefers_direct_owner_execution(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
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
                "stage_name": "domain_owner/default-executor-dispatch",
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
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-05-27T21:12:39+00:00",
            "study_id": "001-risk",
            "executions": [
                {
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
            "surface": "portable_owner_route_reconcile",
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
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
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
            "surface": "portable_owner_route_reconcile",
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
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        closeout_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
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
    assert projection["typed_blocker"]["blocker_id"] == "terminal_closeout_owner_answer_required"
    assert projection["typed_blocker"]["owner"] == "one-person-lab"
    assert projection["typed_blocker"]["work_unit_id"] == "ai-reviewer-record"
    assert projection["consumed_action_queue"][0]["consumption"]["state"] == "blocked_by_terminal_closeout_missing_owner_answer"
    assert projection["blocked_reason"] == "terminal_closeout_owner_answer_required"
    assert projection["next_owner"] == "one-person-lab"


def test_handoff_projection_accepts_terminal_closeout_owner_receipt_ref(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
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
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        closeout_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
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
                        "studies/001-risk/artifacts/supervision/consumer/default_executor_execution/"
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
    assert "terminal_closeout_owner_answer_required" not in projection.get("why_not_applied", [])


def test_live_attempt_merge_replaces_stale_handoff_stage_attempt_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")

    merged = module.merge_live_attempt_observability_into_handoff(
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "study_id": "001-risk",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-previous-closeout",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": "sat-previous-closeout",
                "status": "blocked",
            },
        },
        live_attempt_handoff={
            "surface_kind": "opl_current_control_state_provider_attempt_handoff",
            "study_id": "001-risk",
            "active_run_id": "opl-stage-attempt://sat-current",
            "active_stage_attempt_id": "sat-current",
            "active_workflow_id": "wf-current",
            "running_provider_attempt": True,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    assert merged is not None
    assert merged["running_provider_attempt"] is True
    assert merged["active_run_id"] == "opl-stage-attempt://sat-current"
    assert merged["active_stage_attempt_id"] == "sat-current"
    assert merged["active_workflow_id"] == "wf-current"


def test_mcp_compacts_and_renders_opl_current_control_state_handoff_dashboard() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "current_stage": "publication_supervision",
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "read_model": "workspace_opl_current_control_state_handoff_projection",
            "authority": "observability_only",
            "source_path": "/tmp/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
            "study_id": "001-risk",
            "mode": "developer_apply_safe",
            "mode_label": "Developer Supervisor Mode",
            "scheduler_owner": "external_scheduler",
            "codex_app_heartbeat_required": False,
            "safe_actions_enabled": True,
            "repo_level_repair_authority": True,
            "github_user_gate": {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None},
            "quest_status": "blocked",
            "active_run_id": "run-001",
            "runtime_health": {"health_status": "external_supervisor_required"},
            "artifact_delta": {"status": "stale"},
            "gate_specificity": {
                "status": "blocked",
                "blocked_reason": "publication_gate_specificity_required",
            },
            "ai_reviewer_status": {"status": "trace_missing"},
            "action_queue": [
                {
                    "action_type": "publication_gate_specificity_required",
                    "summary": "Request gate specificity.",
                    "large": {"omit": True},
                }
            ],
            "why_not_applied": ["runtime_recovery_retry_budget_exhausted"],
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "blocked_reason": "runtime_recovery_not_authorized",
        },
    }

    compact = module.compact_study_progress_projection(payload)
    markdown = module.render_mcp_study_progress_markdown(payload)

    dashboard = compact["opl_current_control_state_handoff"]
    assert dashboard["authority"] == "observability_only"
    assert dashboard["mode"] == "developer_apply_safe"
    assert dashboard["mode_label"] == "Developer Supervisor Mode"
    assert dashboard["scheduler_owner"] == "external_scheduler"
    assert dashboard["codex_app_heartbeat_required"] is False
    assert dashboard["safe_actions_enabled"] is True
    assert dashboard["repo_level_repair_authority"] is True
    assert dashboard["github_user_gate"] == {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None}
    assert dashboard["action_queue"] == [
        {
            "action_type": "publication_gate_specificity_required",
            "summary": "Request gate specificity.",
        }
    ]
    assert dashboard["why_not_applied"] == ["runtime_recovery_retry_budget_exhausted"]
    assert "large" not in dashboard["action_queue"][0]
    assert "OPL Current Control State Handoff" in markdown
    assert "developer supervisor mode: `developer_apply_safe`" in markdown
    assert "Codex App heartbeat required: `False`" in markdown
    assert "publication_gate_specificity_required" in markdown
    assert "runtime_recovery_retry_budget_exhausted" in markdown


def test_mcp_compacts_string_why_not_applied_as_single_reason() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "authority": "observability_only",
            "why_not_applied": "repeat_suppressed",
        },
    }

    compact = module.compact_study_progress_projection(payload)
    markdown = module.render_mcp_study_progress_markdown(payload)

    assert compact["opl_current_control_state_handoff"]["why_not_applied"] == ["repeat_suppressed"]
    assert "`repeat_suppressed`" in markdown


def test_mcp_compacts_and_renders_latest_terminal_stage_log() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "authority": "observability_only",
            "active_run_id": None,
            "latest_terminal_stage_log": {
                "surface_kind": "mas_latest_terminal_stage_log_projection",
                "source_path": "/tmp/study/artifacts/supervision/consumer/stage_attempt_closeouts/sat-terminal.closeout_payload.json",
                "generated_at": "2026-05-27T19:46:34Z",
                "stage_attempt_id": "sat-terminal",
                "action_type": "run_quality_repair_batch",
                "status": "blocked_with_domain_owner_refs",
                "observability_status": "observed",
                "duration": {"seconds": 91.25, "source": "provider_attempt"},
                "token_usage": {"total_tokens": 12345, "input_tokens": 6789, "output_tokens": 5556},
                "cost": {"usd": 0.42, "currency": "USD"},
                "usage_refs": ["usage:provider-attempt:sat-terminal"],
                "cost_refs": ["cost:provider-attempt:sat-terminal"],
                "missing_observability_fields": [],
                "paper_stage_log": {
                    "stage_name": "domain_owner/default-executor-dispatch",
                    "stage_work_done": [
                        "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                    ],
                    "paper_work_done": [
                        "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                    ],
                    "outcome": "blocked_with_domain_typed_blocker",
                    "progress_delta_classification": "platform_repair",
                    "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
                    "paper_progress_delta": {"count": 0, "token_usage_total": 0},
                    "platform_repair_delta": {"count": 1, "token_usage_total": 12345},
                    "remaining_blockers": ["authority_route_blocked"],
                    "usage_refs": ["usage:provider-attempt:sat-terminal"],
                    "cost_refs": ["cost:provider-attempt:sat-terminal"],
                    "evidence_refs": ["artifacts/publication_eval/latest.json"],
                },
                "authority_boundary": {
                    "observability_only": True,
                    "can_mark_live_run": False,
                    "can_authorize_quality_verdict": False,
                },
            },
        },
    }

    compact = module.compact_study_progress_projection(payload)
    markdown = module.render_mcp_study_progress_markdown(payload)

    terminal_log = compact["opl_current_control_state_handoff"]["latest_terminal_stage_log"]
    assert terminal_log["stage_attempt_id"] == "sat-terminal"
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["duration"] == {"seconds": 91.25, "source": "provider_attempt"}
    assert terminal_log["token_usage"]["total_tokens"] == 12345
    assert terminal_log["cost"] == {"usd": 0.42, "currency": "USD"}
    assert terminal_log["usage_refs"] == ["usage:provider-attempt:sat-terminal"]
    assert terminal_log["cost_refs"] == ["cost:provider-attempt:sat-terminal"]
    assert terminal_log["paper_stage_log"]["stage_work_done"] == [
        "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
    ]
    assert terminal_log["paper_stage_log"]["outcome"] == "blocked_with_domain_typed_blocker"
    assert terminal_log["paper_stage_log"]["progress_delta_classification"] == "platform_repair"
    assert terminal_log["paper_stage_log"]["deliverable_progress_delta"] == {"count": 0, "token_usage_total": 0}
    assert terminal_log["paper_stage_log"]["paper_progress_delta"] == {"count": 0, "token_usage_total": 0}
    assert terminal_log["paper_stage_log"]["platform_repair_delta"] == {"count": 1, "token_usage_total": 12345}
    assert terminal_log["paper_stage_log"]["remaining_blockers"] == ["authority_route_blocked"]
    assert "latest_terminal_stage_log: action `run_quality_repair_batch`" in markdown
    assert "latest_terminal_stage_duration_seconds: `91.25`" in markdown
    assert "latest_terminal_stage_token_usage_total: `12345`" in markdown
    assert "latest_terminal_stage_cost_usd: `0.42`" in markdown
    assert "latest_terminal_stage_outcome: `blocked_with_domain_typed_blocker`" in markdown
    assert "authority_route_blocked" in markdown


def test_latest_terminal_stage_log_marks_missing_observability(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-28T03:44:00+00:00",
            "studies": [{"study_id": "001-risk", "quest_status": "active"}],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-05-28T03:45:25+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-05-28T03:45:25+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "paper_stage_log": {
                        "stage_name": "owner_authorized_publication_gate_replay",
                        "paper_work_done": ["Recorded gate replay receipt."],
                        "outcome": "executed",
                        "remaining_blockers": [],
                        "evidence_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["observability_status"] == "missing"
    assert terminal_log["missing_observability_fields"] == ["duration", "token_usage", "cost"]
    assert terminal_log["duration"] == {
        "status": "missing",
        "seconds": None,
        "missing_duration_reason": "no_terminal_stage_duration_observed",
    }
    assert terminal_log["token_usage"] == {
        "status": "missing",
        "total_tokens": None,
        "missing_token_usage_reason": "no_terminal_stage_token_usage_observed",
    }
    assert terminal_log["cost"] == {
        "status": "missing",
        "usd": None,
        "missing_cost_reason": "no_terminal_stage_cost_observed",
    }


def test_latest_terminal_stage_log_preserves_zero_observability_values(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff")
    profile = make_profile(tmp_path)
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "portable_owner_route_reconcile",
            "generated_at": "2026-05-28T03:44:00+00:00",
            "studies": [{"study_id": "001-risk", "quest_status": "active"}],
        },
    )
    latest_execution_path = (
        profile.studies_root
        / "001-risk"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    _write_json(
        latest_execution_path,
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "generated_at": "2026-05-28T03:45:25+00:00",
            "study_id": "001-risk",
            "executions": [
                {
                    "generated_at": "2026-05-28T03:45:25+00:00",
                    "study_id": "001-risk",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "duration_seconds": 0,
                    "token_usage": {"total_tokens": 0},
                    "cost_usd": 0,
                    "paper_stage_log": {
                        "stage_name": "owner_authorized_publication_gate_replay",
                        "paper_work_done": ["Recorded gate replay receipt."],
                        "outcome": "executed",
                    },
                }
            ],
        },
    )

    projection = module.opl_current_control_state_study_handoff_projection(profile=profile, study_id="001-risk")

    terminal_log = projection["latest_terminal_stage_log"]
    assert terminal_log["observability_status"] == "observed"
    assert terminal_log["missing_observability_fields"] == []
    assert terminal_log["duration"] == {"seconds": 0}
    assert terminal_log["token_usage"] == {"total_tokens": 0}
    assert terminal_log["cost"] == {"usd": 0}
