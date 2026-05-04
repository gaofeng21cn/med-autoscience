from __future__ import annotations

import importlib


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
    assert dashboard["action_queue"] == [
        {
            "action_type": "publication_gate_specificity_required",
            "summary": "Request gate specificity.",
        }
    ]
    assert dashboard["why_not_applied"] == ["runtime_recovery_retry_budget_exhausted"]
    assert "large" not in dashboard["action_queue"][0]
    assert "Portable Supervisor Queue" in markdown
    assert "publication_gate_specificity_required" in markdown
    assert "runtime_recovery_retry_budget_exhausted" in markdown
