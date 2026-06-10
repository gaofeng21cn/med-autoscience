from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_watch_runtime_writes_supervision_changed_event_when_degraded_runtime_recovers_to_live(
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
        portfolio_root=workspace_root / "memory" / "portfolio",
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

    states = [
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "opl-hosted-stage-runtime",
                "opl_runtime_ref": "opl_hosted_stage_runtime",
                "runtime_ref": "opl_hosted_stage_runtime",
                "runtime_engine_id": "opl-hosted-stage-runtime",
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
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "opl-hosted-stage-runtime",
                "opl_runtime_ref": "opl_hosted_stage_runtime",
                "runtime_ref": "opl_hosted_stage_runtime",
                "runtime_engine_id": "opl-hosted-stage-runtime",
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
            "decision": "noop",
            "reason": "quest_already_running",
            "launch_report_path": str(launch_report_path),
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    ]
    call_index = {"value": 0}

    projection_states = [states[0], states[0], states[1]]

    def next_status(**_: object):
        index = min(call_index["value"], len(projection_states) - 1)
        call_index["value"] += 1
        return projection_states[index]

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", next_status)
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
    latest_handoff = json.loads(
        (study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json").read_text(encoding="utf-8")
    )

    assert first_handoff["status"] == "handoff_required"
    assert second_handoff["status"] == "handoff_required"
    assert second_handoff["runtime_owner"] == "one-person-lab"
    assert second_handoff["mas_runtime_read_model_retired"] is True
    assert second_handoff["typed_blocker"]["blocker_type"] == "opl_runtime_owner_handoff_required"
    assert latest_handoff["provider_completion_is_domain_completion"] is False
    assert not (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").exists()
def test_watch_runtime_refreshes_recovery_requested_status_to_live_within_same_tick(
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
        portfolio_root=workspace_root / "memory" / "portfolio",
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
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "001-risk",
            "status": "running",
            "active_run_id": "run-live",
        },
    )

    calls: list[tuple[str, str]] = []
    recovery_requested = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "opl-hosted-stage-runtime",
            "opl_runtime_ref": "opl_hosted_stage_runtime",
            "runtime_ref": "opl_hosted_stage_runtime",
            "runtime_engine_id": "opl-hosted-stage-runtime",
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
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }
    live_status = {
        **recovery_requested,
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "autonomous_runtime_notice": {
            "active_run_id": "run-live",
            "browser_url": "http://127.0.0.1:21003",
            "quest_session_api_url": "http://127.0.0.1:21003/api/quests/001-risk/session",
        },
        "execution_owner_guard": {
            "active_run_id": "run-live",
        },
    }

    projection_states = [recovery_requested, live_status]
    call_index = {"value": 0}

    def next_projection(*, profile, study_root, **kwargs):
        call_kind = record_projection_call(calls, study_root=Path(study_root), kwargs=kwargs)
        if call_kind == "currentness":
            index = min(call_index["value"], len(projection_states) - 1)
            return projection_states[index]
        index = min(call_index["value"], len(projection_states) - 1)
        call_index["value"] += 1
        return projection_states[index]

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        next_projection,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [quest_root])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    handoff = result["managed_study_opl_runtime_owner_handoffs"][0]
    latest_handoff = json.loads(
        (study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == [
        ("status", "001-risk"),
        ("currentness", "001-risk"),
        ("status", "001-risk"),
        ("currentness", "001-risk"),
    ]
    assert result["managed_study_actions"][0]["study_id"] == "001-risk"
    assert result["managed_study_actions"][0]["decision"] == "blocked"
    assert result["managed_study_actions"][0]["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["managed_study_actions"][0]["resume_postcondition"]["typed_blocker"]["owner"] == "one-person-lab"
    assert handoff["status"] == "handoff_required"
    assert handoff["runtime_owner"] == "one-person-lab"
    assert handoff["provider_completion_is_domain_completion"] is False
    assert latest_handoff["mas_materializes_runtime_supervision"] is False
def test_runtime_alert_delivery_backend_contract_is_not_exposed() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    assert not hasattr(module, "runtime_backend_contract")
    assert not hasattr(module, "deliver_alert")
