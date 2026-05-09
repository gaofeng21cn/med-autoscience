from __future__ import annotations

import importlib
import json

from tests.study_runtime_test_helpers import make_profile


def _write_json(path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_study_progress_portable_supervisor_projection_reads_developer_supervisor_mode(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.supervisor_projection")
    profile = make_profile(tmp_path)
    hourly_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        hourly_path,
        {
            "surface": "portable_runtime_supervisor_scan",
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

    projection = module.portable_supervisor_study_projection(profile=profile, study_id="001-risk")

    assert projection["mode"] == "developer_apply_safe"
    assert projection["mode_label"] == "Developer Supervisor Mode"
    assert projection["scheduler_owner"] == "external_scheduler"
    assert projection["codex_app_heartbeat_required"] is False
    assert projection["safe_actions_enabled"] is True
    assert projection["repo_level_repair_authority"] is True
    assert projection["github_user_gate"] == {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None}


def test_study_progress_portable_supervisor_projection_preserves_string_why_not_applied(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.supervisor_projection")
    profile = make_profile(tmp_path)
    hourly_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        hourly_path,
        {
            "surface": "portable_runtime_supervisor_scan",
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

    projection = module.portable_supervisor_study_projection(profile=profile, study_id="001-risk")

    assert projection["why_not_applied"] == ["repeat_suppressed"]


def test_mcp_compacts_and_renders_portable_supervisor_queue_dashboard() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "current_stage": "publication_supervision",
        "portable_supervisor_dashboard": {
            "surface_kind": "portable_supervisor_study_queue_dashboard",
            "read_model": "workspace_hourly_supervision_projection",
            "authority": "observability_only",
            "source_path": "/tmp/workspace/artifacts/supervision/hourly/latest.json",
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

    dashboard = compact["portable_supervisor_dashboard"]
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
    assert "Portable Supervisor Queue" in markdown
    assert "developer supervisor mode: `developer_apply_safe`" in markdown
    assert "Codex App heartbeat required: `False`" in markdown
    assert "publication_gate_specificity_required" in markdown
    assert "runtime_recovery_retry_budget_exhausted" in markdown


def test_mcp_compacts_string_why_not_applied_as_single_reason() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "portable_supervisor_dashboard": {
            "surface_kind": "portable_supervisor_study_queue_dashboard",
            "authority": "observability_only",
            "why_not_applied": "repeat_suppressed",
        },
    }

    compact = module.compact_study_progress_projection(payload)
    markdown = module.render_mcp_study_progress_markdown(payload)

    assert compact["portable_supervisor_dashboard"]["why_not_applied"] == ["repeat_suppressed"]
    assert "`repeat_suppressed`" in markdown
