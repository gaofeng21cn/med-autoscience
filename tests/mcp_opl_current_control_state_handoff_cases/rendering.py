from __future__ import annotations

import importlib


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
