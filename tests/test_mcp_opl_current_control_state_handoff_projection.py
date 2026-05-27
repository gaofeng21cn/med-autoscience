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
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
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
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_name": "domain_owner/default-executor-dispatch",
                "problem_summary": "The repair owner could not write because authority route evidence was blocked.",
                "stage_goal": "Produce owner-authorized manuscript repair output or a typed blocker.",
                "paper_work_done": [
                    "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                ],
                "changed_paper_surfaces": [],
                "outcome": "blocked_with_domain_typed_blocker",
                "remaining_blockers": [
                    "authority_route_blocked",
                    "opl_current_control_state.handoff_required",
                ],
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
    assert terminal_log["paper_stage_log"]["outcome"] == "blocked_with_domain_typed_blocker"
    assert terminal_log["paper_stage_log"]["remaining_blockers"] == [
        "authority_route_blocked",
        "opl_current_control_state.handoff_required",
    ]
    assert terminal_log["authority_boundary"]["observability_only"] is True
    assert terminal_log["authority_boundary"]["can_mark_live_run"] is False
    assert terminal_log["authority_boundary"]["can_authorize_quality_verdict"] is False


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
            "source_path": "/tmp/workspace/artifacts/supervision/opl_current_control_state/latest.json",
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
                "paper_stage_log": {
                    "stage_name": "domain_owner/default-executor-dispatch",
                    "paper_work_done": [
                        "Read the stage packet, repair request, current publication evaluation, and OPL handoff."
                    ],
                    "outcome": "blocked_with_domain_typed_blocker",
                    "remaining_blockers": ["authority_route_blocked"],
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
    assert terminal_log["paper_stage_log"]["outcome"] == "blocked_with_domain_typed_blocker"
    assert terminal_log["paper_stage_log"]["remaining_blockers"] == ["authority_route_blocked"]
    assert "latest_terminal_stage_log: action `run_quality_repair_batch`" in markdown
    assert "latest_terminal_stage_outcome: `blocked_with_domain_typed_blocker`" in markdown
    assert "authority_route_blocked" in markdown
