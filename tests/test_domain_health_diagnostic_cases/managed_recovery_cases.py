from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_watch_runtime_records_opl_stage_attempt_handoff_without_mas_recovery(tmp_path: Path, monkeypatch) -> None:
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
    preflight = make_progress_projection_payload(
        study_id="001-risk",
        decision="resume",
        reason="quest_marked_running_but_no_live_session",
    )
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: preflight)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_auto_recoveries"] == []
    action = result["managed_study_actions"][0]
    assert action["study_id"] == "001-risk"
    assert action["decision"] == "blocked"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["resume_postcondition"]["status"] == "opl_stage_attempt_admission_required"
    assert action["resume_postcondition"]["typed_blocker"]["owner"] == "one-person-lab"


def test_watch_runtime_isolates_managed_study_projection_errors(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "legacy" / "runtime",
        med_deepscientist_repo_root=None,
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    bad_study = profile.studies_root / "001-retired"
    good_study = profile.studies_root / "002-live"
    bad_study.mkdir(parents=True, exist_ok=True)
    good_study.mkdir(parents=True, exist_ok=True)
    (bad_study / "study.yaml").write_text("study_id: 001-retired\n", encoding="utf-8")
    (good_study / "study.yaml").write_text("study_id: 002-live\n", encoding="utf-8")

    def fake_status(*, study_root: Path, **_: object) -> dict[str, object]:
        if Path(study_root).name == "001-retired":
            raise ValueError("manual_finish.compatibility_guard_only is retired; use manual_finish_guard_only")
        return {
            **make_progress_projection_payload(
                study_id="002-live",
                decision="noop",
                reason="quest_already_running",
            ),
            "study_root": str(good_study),
            "quest_id": "002-live",
            "quest_root": str(profile.runtime_root / "002-live"),
            "quest_status": "running",
            "active_run_id": "run-002",
        }

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", fake_status)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    outer_loop_calls: list[str] = []

    def fake_outer_loop_request(*, study_root: Path, **_: object) -> None:
        outer_loop_calls.append(Path(study_root).name)
        if Path(study_root).name == "001-retired":
            raise AssertionError("isolated projection errors must not enter outer-loop wakeup")
        return None

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", fake_outer_loop_request)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    actions = {action["study_id"]: action for action in result["managed_study_actions"]}
    assert actions["001-retired"]["decision"] == "blocked"
    assert actions["001-retired"]["reason"] == "study_projection_contract_error"
    assert actions["002-live"]["decision"] == "blocked"
    assert actions["002-live"]["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert actions["002-live"]["resume_postcondition"]["status"] == "opl_stage_attempt_admission_required"
    assert outer_loop_calls == ["002-live"]


def test_watch_runtime_managed_recovery_records_opl_provider_handoff_blocker(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "legacy" / "runtime",
        med_deepscientist_repo_root=None,
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
    runtime_root = profile.runtime_root.parent
    quest_root = runtime_root / "quests" / "001-risk"
    quest_root.mkdir(parents=True, exist_ok=True)
    preflight = make_progress_projection_payload(
        study_id="001-risk",
        decision="resume",
        reason="quest_marked_running_but_no_live_session",
    )
    preflight["quest_root"] = str(quest_root)

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: preflight)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_auto_recoveries"] == []
    action = result["managed_study_actions"][0]
    assert action["decision"] == "blocked"
    assert action["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert action["resume_postcondition"]["status"] == "opl_stage_attempt_admission_required"
    assert action["resume_postcondition"]["typed_blocker"] == {
        "blocker_type": "opl_stage_attempt_admission_required",
        "owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "reason": "mas_runtime_attempt_execution_retired",
        "required_handoff": "Hydrate MAS DomainIntent/owner-route refs through OPL current_control_state.",
    }
