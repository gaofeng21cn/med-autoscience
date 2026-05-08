from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_watch_runtime_records_failed_managed_recovery_without_aborting_tick(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
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
    preflight = make_study_runtime_status_payload(
        study_id="001-risk",
        decision="resume",
        reason="quest_marked_running_but_no_live_session",
    )
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: preflight)
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: (_ for _ in ()).throw(RuntimeError("startup sync timed out")),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "blocked", "reason": "resume_request_failed"}
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "resume",
            "preflight_reason": "quest_marked_running_but_no_live_session",
            "applied_decision": "blocked",
            "applied_reason": "resume_request_failed",
            "source": "runtime_watch",
        }
    ]


def test_watch_runtime_managed_recovery_uses_turn_lifecycle_receipt(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    mas_runtime_core = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core")
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
    mas_runtime_core.create_quest(runtime_root=runtime_root, payload={"quest_id": "001-risk", "study_id": "001-risk"})
    preflight = make_study_runtime_status_payload(
        study_id="001-risk",
        decision="resume",
        reason="quest_marked_running_but_no_live_session",
    )
    preflight["quest_root"] = str(quest_root)

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: preflight)
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: {
            **preflight,
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "resume_postcondition": {
                "effective": True,
                **mas_runtime_core.resume_quest(
                    runtime_root=runtime_root,
                    quest_id="001-risk",
                    source=kwargs.get("source") or "runtime_watch",
                ),
            },
        },
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    receipt = json.loads((quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json").read_text(encoding="utf-8"))
    assert result["managed_study_actions"][0]["decision"] == "resume"
    assert state["worker_running"] is True
    assert state["active_run_id"].startswith("mas-run-")
    assert receipt["reason"] == "explicit_resume"
    assert receipt["started"] is True
    assert receipt["idempotency_key"].startswith("turn-")
