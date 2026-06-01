from __future__ import annotations

import importlib
from pathlib import Path

from .shared import _write_json, make_profile, write_study


def test_study_progress_merges_live_stage_log_when_handoff_study_entry_lacks_it(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    domain_status = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table", "claim_evidence_map"],
    )
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-28T13:40:08+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "active_stage_attempt_id": "sat-live-queue",
                    "active_workflow_id": "wf-live-queue",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    live_stage_log = {
        "surface_kind": "opl_stage_progress_log_summary",
        "projection_scope": "current_control_state",
        "attempt_count": 1,
        "completed_attempt_count": 0,
        "blocked_attempt_count": 0,
        "runner_progress_event_count": 2,
        "missing_usage_telemetry_attempt_count": 1,
        "attempt_refs": ["/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"],
        "authority_boundary": {
            "opl": "stage_attempt_progress_observability_projection_only",
            "domain": "truth_quality_artifact_gate_owner",
            "can_authorize_quality_verdict": False,
        },
    }
    monkeypatch.setattr(
        domain_status,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_liveness_audit": {
                "status": "live",
                "source": "opl_current_control_state_provider_attempt",
                "provider_attempt_source": "opl_family_runtime_queue_inspect",
                "authority": "observability_only",
                "active_run_id": "opl-stage-attempt://sat-live-queue",
                "active_stage_attempt_id": "sat-live-queue",
                "active_workflow_id": "wf-live-queue",
                "running_provider_attempt": True,
                "handoff_path": str(handoff_path),
                "handoff_generated_at": "2026-05-28T13:40:08+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "stage_progress_log": live_stage_log,
            },
            "runtime_health_snapshot": {"health_status": "running"},
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["surface_kind"] == "opl_current_control_state_study_handoff"
    assert dashboard["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert dashboard["active_stage_attempt_id"] == "sat-live-queue"
    assert dashboard["active_workflow_id"] == "wf-live-queue"
    assert dashboard["running_provider_attempt"] is True
    assert dashboard["stage_progress_log"]["attempt_count"] == 1
    assert dashboard["stage_progress_log"]["runner_progress_event_count"] == 2
    assert dashboard["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"
    ]
    assert (
        dashboard["stage_progress_log"]["authority_boundary"]["can_authorize_quality_verdict"]
        is False
    )
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_count"] == 1
    assert result["progress_first_monitoring_summary"]["active_stage_attempt_id"] == "sat-live-queue"
    assert result["progress_first_monitoring_summary"]["active_workflow_id"] == "wf-live-queue"
    assert result["progress_first_monitoring_summary"]["running_provider_attempt"] is True
    assert result["progress_first_monitoring_summary"]["stage_progress_log"]["attempt_count"] == 1
    assert result["progress_first_monitoring_summary"]["stage_progress_log"]["runner_progress_event_count"] == 2
    assert result["progress_first_monitoring_summary"]["authority_boundary"]["can_write_runtime_owned_surfaces"] is False
    assert "stage_progress_log: attempts `1`" in markdown


def test_study_progress_live_opl_attempt_supersedes_stale_handoff_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    domain_status = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table"],
    )
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-01T08:09:03+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": None,
                    "running_provider_attempt": False,
                    "runtime_health": {
                        "health_status": "escalated",
                        "runtime_liveness_status": "live",
                        "blocking_reasons": ["live_worker_requires_worker_running"],
                    },
                    "why_not_applied": [
                        "opl_current_control_state.handoff_required",
                        "ai_reviewer_trace_missing",
                    ],
                    "next_owner": "external_supervisor",
                    "external_supervisor_required": True,
                    "blocked_reason": "runtime_recovery_not_authorized",
                }
            ],
        },
    )
    live_stage_log = {
        "surface_kind": "opl_stage_progress_log_summary",
        "projection_scope": "stage_attempt_workbench",
        "attempt_count": 1,
        "runner_progress_event_count": 4,
        "attempt_refs": ["/stage_attempt_workbench/attempts/sat-live/stage_progress_log"],
    }
    monkeypatch.setattr(
        domain_status,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_status": "active",
            "decision": "resume",
            "reason": "controller_work_unit_pending",
            "active_run_id": "opl-stage-attempt://sat-live",
            "runtime_liveness_audit": {
                "status": "live",
                "source": "opl_current_control_state_provider_attempt",
                "provider_attempt_source": "opl_family_runtime_queue_inspect",
                "authority": "observability_only",
                "active_run_id": "opl-stage-attempt://sat-live",
                "active_stage_attempt_id": "sat-live",
                "active_workflow_id": "wf-live",
                "running_provider_attempt": True,
                "handoff_path": str(handoff_path),
                "handoff_generated_at": "2026-06-01T08:10:00+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "stage_progress_log": live_stage_log,
            },
            "runtime_health_snapshot": {
                "health_status": "running",
                "worker_liveness_state": {"state": "live", "worker_running": True},
                "blocking_reasons": [],
            },
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["active_run_id"] == "opl-stage-attempt://sat-live"
    assert dashboard["running_provider_attempt"] is True
    assert dashboard["runtime_health"]["health_status"] == "running"
    assert dashboard["runtime_health"]["runtime_liveness_status"] == "live"
    assert dashboard["external_supervisor_required"] is False
    assert dashboard["blocked_reason"] is None
    assert dashboard["why_not_applied"] == ["ai_reviewer_trace_missing"]
    assert dashboard["stage_progress_log"]["runner_progress_event_count"] == 4
    assert result["progress_first_monitoring_summary"]["active_run_id"] == "opl-stage-attempt://sat-live"
    assert result["progress_first_monitoring_summary"]["running_provider_attempt"] is True
    assert (
        result["progress_first_monitoring_summary"]["worker_liveness"]["runtime_liveness_status"]
        == "live"
    )
    assert "runtime_recovery_not_authorized" not in (
        result["user_visible_projection"].get("why_not_progressing") or ""
    )
