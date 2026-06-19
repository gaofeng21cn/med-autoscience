from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

from .managed_recovery_probe_cases import *  # noqa: F403,F401,E402


def test_watch_runtime_does_not_auto_recover_package_ready_handoff(
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
    calls: list[tuple[str, str]] = []

    def parked_status() -> dict[str, object]:
        return {
            **make_progress_projection_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_parked_on_unchanged_finalize_state",
            ),
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "execution": {
                "engine": "opl-hosted-stage-runtime",
                "opl_runtime_ref": "opl_hosted_stage_runtime",
                "runtime_ref": "opl_hosted_stage_runtime",
                "runtime_engine_id": "opl-hosted-stage-runtime",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            },
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

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: (
            record_projection_call(calls, study_root=Path(study_root), kwargs=kwargs),
            parked_status(),
        )[1],
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == [("status", "001-risk"), ("currentness", "001-risk")]
    action = result["managed_study_actions"][0]
    assert action["study_id"] == "001-risk"
    assert action["decision"] == "resume"
    assert action["reason"] == "quest_parked_on_unchanged_finalize_state"
    assert action["current_work_unit"]["status"] == "executable_owner_action"
    assert action["current_execution_envelope"]["state_kind"] == "parked"
    assert result["managed_study_auto_recoveries"] == []

def test_watch_runtime_holds_auto_recovery_when_flapping_circuit_breaker_is_active(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        {
            "surface_kind": "mas_opl_runtime_owner_handoff",
            "schema_version": 1,
            "recorded_at": "2026-04-26T00:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "status": "handoff_required",
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_runtime_read_model_retired": True,
            "mas_materializes_runtime_supervision": False,
            "health_status": "recovering",
            "runtime_stability_status": "flapping",
            "flapping_episode_count": 2,
            "flapping_circuit_breaker": True,
            "runtime_reason": "quest_marked_running_but_no_live_session",
            "typed_blocker": {
                "blocker_type": "opl_runtime_owner_handoff_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
            },
        },
    )
    no_live_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "running",
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
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: (
            record_projection_call(calls, study_root=Path(study_root), kwargs=kwargs),
            no_live_status,
        )[1],
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == [("status", "001-risk"), ("currentness", "001-risk")]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_recovery_holds"] == [
        {
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "hold_reason": "flapping_circuit_breaker_active",
            "recommended_probe": "refresh_runtime_liveness_before_resume",
            "flapping_episode_count": 2,
            "recovery_probe": {
                "probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::2",
                "status": "hold_active",
                "recommended_action": "hold",
                "reason": "flapping_circuit_breaker_active",
                "next_probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::3",
                "liveness": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
                "current_status": {
                    "quest_status": "running",
                    "decision": "resume",
                    "reason": "quest_marked_running_but_no_live_session",
                    "runtime_stability_status": "flapping",
                    "flapping_circuit_breaker": True,
                    "flapping_episode_count": 2,
                },
            },
        }
    ]
    assert not (study_root / "artifacts" / "runtime" / "recovery_probe" / "latest.json").exists()

def test_watch_runtime_does_not_hold_recovery_for_plain_opl_runtime_handoff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        {
            "surface_kind": "mas_opl_runtime_owner_handoff",
            "schema_version": 1,
            "recorded_at": "2026-06-01T00:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "status": "handoff_required",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_runtime_read_model_retired": True,
            "mas_materializes_runtime_supervision": False,
            "typed_blocker": {
                "blocker_type": "opl_runtime_owner_handoff_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "reason": "mas_runtime_supervision_retired",
            },
        },
    )
    no_live_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "running",
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
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: no_live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.domain_status_projection,
        "request_opl_stage_attempt",
        lambda **kwargs: calls.append(kwargs)
        or {
            **no_live_status,
            "status": "opl_stage_attempt_requested",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
        raising=False,
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_recovery_holds"] == []
    assert result["managed_study_auto_recoveries"] == []
    action = result["managed_study_actions"][0]
    assert action["study_id"] == "001-risk"
    assert action["decision"] == "blocked"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["resume_postcondition"]["status"] == "opl_stage_attempt_admission_required"
    assert action["resume_postcondition"]["typed_blocker"]["owner"] == "one-person-lab"
    assert not (study_root / "artifacts" / "runtime" / "recovery_probe" / "latest.json").exists()
