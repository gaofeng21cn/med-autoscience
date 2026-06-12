from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_stage_log_from_live_opl_queue_when_handoff_lacks_study(
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
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-26T20:11:03+00:00",
            "authority": "observability_only",
            "studies": [{"study_id": "other-study"}],
        },
    )
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
                "handoff_generated_at": "2026-05-26T20:11:03+00:00",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "stage_progress_log": {
                    "surface_kind": "opl_stage_progress_log_summary",
                    "projection_scope": "stage_attempt_workbench",
                    "attempt_count": 3,
                    "completed_attempt_count": 2,
                    "blocked_attempt_count": 1,
                    "missing_usage_telemetry_attempt_count": 1,
                    "attempt_refs": [
                        "/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"
                    ],
                    "authority_boundary": {
                        "opl": "stage_attempt_progress_observability_projection_only",
                        "domain": "truth_quality_artifact_gate_owner",
                        "can_authorize_quality_verdict": False,
                    },
                },
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
    assert dashboard["surface_kind"] == "opl_current_control_state_provider_attempt_handoff"
    assert dashboard["source_path"] == str(handoff_path)
    assert dashboard["authority"] == "observability_only"
    assert dashboard["active_run_id"] == "opl-stage-attempt://sat-live-queue"
    assert dashboard["stage_progress_log"]["attempt_count"] == 3
    assert dashboard["stage_progress_log"]["attempt_refs"] == [
        "/stage_attempt_workbench/attempts/sat-live-queue/stage_progress_log"
    ]
    assert (
        dashboard["stage_progress_log"]["authority_boundary"]["can_authorize_quality_verdict"]
        is False
    )
    assert compact["opl_current_control_state_handoff"]["stage_progress_log"]["attempt_count"] == 3
    assert "stage_progress_log: attempts `3`" in markdown
