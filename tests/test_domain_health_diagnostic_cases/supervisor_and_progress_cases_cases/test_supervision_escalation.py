from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_watch_runtime_writes_study_supervision_report_and_escalates_after_consecutive_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    dump_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "domain_health_diagnostic",
            "decision": "blocked",
            "reason": "resume_request_failed",
        },
    )

    def failing_status() -> dict[str, object]:
        return {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "opl-provider-backed-stage-runtime",
                "runtime_backend_id": "opl_provider_backed_stage_runtime",
                "runtime_engine_id": "opl-provider-backed-stage-runtime",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "resume_request_failed",
            "launch_report_path": str(launch_report_path),
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": "run-stale",
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": "run-stale",
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: failing_status())
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    first = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    second = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    first_handoff = first["managed_study_opl_runtime_owner_handoffs"][0]
    second_handoff = second["managed_study_opl_runtime_owner_handoffs"][0]
    latest_path = study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"

    assert first_handoff["status"] == "handoff_required"
    assert second_handoff["status"] == "handoff_required"
    assert second_handoff["runtime_owner"] == "one-person-lab"
    assert second_handoff["typed_blocker"]["blocker_type"] == "opl_runtime_owner_handoff_required"
    assert latest_payload["mas_runtime_read_model_retired"] is True
    assert latest_payload["next_action_summary"]
    assert escalation_path.exists()
    escalation_payload = json.loads(escalation_path.read_text(encoding="utf-8"))

    assert escalation_payload["reason"] == "resume_request_failed"
    assert "runtime_event_ref" not in latest_payload
    assert not (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").exists()
