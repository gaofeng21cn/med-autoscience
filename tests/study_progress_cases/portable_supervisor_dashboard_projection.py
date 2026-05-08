from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_workspace_hourly_supervisor_dashboard_and_mcp_markdown(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    hourly_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        hourly_path,
        {
            "surface": "portable_supervisor_hourly_projection",
            "schema_version": 1,
            "generated_at": "2026-05-04T06:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {
                        "health_status": "escalated",
                        "runtime_liveness_status": "stale",
                    },
                    "artifact_delta": {
                        "status": "stale",
                        "summary": "No meaningful artifact delta since last tick.",
                    },
                    "gate_specificity": {
                        "status": "blocked",
                        "blocked_reason": "publication_gate_specificity_required",
                    },
                    "ai_reviewer_status": {
                        "status": "trace_missing",
                        "summary": "AI reviewer workflow must recheck the repaired package.",
                    },
                    "action_queue": [
                        {
                            "action_type": "publication_gate_specificity_required",
                            "summary": "Ask controller to specify the publication gate blocker.",
                            "fingerprint": "publication_gate_specificity_required::publication_gate_specificity_required",
                            "queue_age_hours": 6.0,
                            "owner_pickup": {
                                "state": "overdue",
                                "owner": "publication_gate",
                                "duration_hours": 6.0,
                                "pickup_overdue": True,
                            },
                            "consumption": {
                                "state": "attention_required",
                                "unconsumed_duration_hours": 6.0,
                                "developer_supervisor_attention_required": True,
                            },
                        },
                        {
                            "action_type": "return_to_ai_reviewer_workflow",
                            "summary": "Return the package to AI reviewer after gate specificity.",
                        },
                    ],
                    "queue_slo": {
                        "max_queue_age_hours": 6.0,
                        "owner_pickup_overdue_count": 1,
                        "developer_supervisor_attention_required_count": 1,
                    },
                    "owner_pickup_overdue": True,
                    "developer_supervisor_attention_required": True,
                    "why_not_applied": [
                        "runtime_recovery_retry_budget_exhausted",
                        "ai_reviewer_trace_missing",
                    ],
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                    "blocked_reason": "runtime_recovery_not_authorized",
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {"attempt_state": "escalated", "retry_budget_remaining": 0},
            "control_plane_snapshot": {"control_state": "blocked_runtime_escalation"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)

    dashboard = result["portable_supervisor_dashboard"]
    assert dashboard["source_path"] == str(hourly_path)
    assert dashboard["authority"] == "observability_only"
    assert dashboard["quest_status"] == "running"
    assert dashboard["active_run_id"] == "run-001"
    assert dashboard["runtime_health"]["health_status"] == "escalated"
    assert dashboard["artifact_delta"]["status"] == "stale"
    assert dashboard["gate_specificity"]["blocked_reason"] == "publication_gate_specificity_required"
    assert dashboard["ai_reviewer_status"]["status"] == "trace_missing"
    assert [item["action_type"] for item in dashboard["action_queue"]] == [
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert dashboard["queue_slo"]["max_queue_age_hours"] == 6.0
    assert dashboard["owner_pickup_overdue"] is True
    assert dashboard["developer_supervisor_attention_required"] is True
    assert dashboard["action_queue"][0]["fingerprint"] == (
        "publication_gate_specificity_required::publication_gate_specificity_required"
    )
    assert dashboard["action_queue"][0]["owner_pickup"]["state"] == "overdue"
    assert dashboard["action_queue"][0]["consumption"]["developer_supervisor_attention_required"] is True
    assert dashboard["why_not_applied"] == [
        "runtime_recovery_retry_budget_exhausted",
        "ai_reviewer_trace_missing",
    ]
    assert dashboard["next_owner"] == "external_supervisor"
    assert dashboard["external_supervisor_required"] is True
    assert result["refs"]["portable_supervisor_hourly_path"] == str(hourly_path)
    assert compact["portable_supervisor_dashboard"]["blocked_reason"] == "runtime_recovery_not_authorized"
    assert compact["portable_supervisor_dashboard"]["queue_slo"]["owner_pickup_overdue_count"] == 1
    assert compact["portable_supervisor_dashboard"]["action_queue"][0]["queue_age_hours"] == 6.0
    assert compact["portable_supervisor_dashboard"]["action_queue"][0]["action_type"] == (
        "publication_gate_specificity_required"
    )
    assert "Portable Supervisor Queue" in markdown
    assert "publication_gate_specificity_required" in markdown
    assert "owner_pickup: `overdue`" in markdown
    assert "developer_supervisor_attention_required: `True`" in markdown
    assert "runtime_recovery_retry_budget_exhausted" in markdown
