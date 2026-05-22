from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_scan_runtime_processes_managed_quests_including_non_live_states(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q-created", status="created")
    make_quest(tmp_path, "q-idle", status="idle")
    make_quest(tmp_path, "q-paused", status="paused")
    make_quest(tmp_path, "q-running", status="running")
    make_quest(tmp_path, "q-active", status="active")
    make_quest(tmp_path, "q-waiting", status="waiting_for_user")
    make_quest(tmp_path, "q-stopped", status="stopped")
    make_quest(tmp_path, "q-completed", status="completed")
    seen: list[str] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        seen.append(quest_root.name)
        return {
            "status": "clear",
            "blockers": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": False,
        }

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=runtime_root,
        controller_runners={"publication_gate": fake_runner},
        apply=False,
    )

    assert sorted(seen) == ["q-active", "q-created", "q-idle", "q-paused", "q-running", "q-stopped", "q-waiting"]
    assert sorted(result["scanned_quests"]) == [
        "q-active",
        "q-created",
        "q-idle",
        "q-paused",
        "q-running",
        "q-stopped",
        "q-waiting",
    ]

def test_watch_runtime_can_ensure_managed_studies_before_scanning(tmp_path: Path, monkeypatch) -> None:
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

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: make_progress_projection_payload(
            study_id=Path(study_root).name,
            decision="create_and_start",
            reason="quest_missing",
        ),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "create_and_start", "reason": "quest_missing"}
    ]

def test_watch_runtime_materializes_managed_study_autonomy_slo_status(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "quest-001",
            "status": "running",
            "active_run_id": "run-001",
        },
    )
    dump_json(
        quest_root / ".ds" / "runs" / "run-001" / "telemetry.json",
        {
            "run_id": "run-001",
            "turn_progress_kind": "read_churn_without_artifact_delta",
            "read_churn_ratio": 0.8,
            "same_result_reinjection_count": 5,
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "active_run_id": "run-001",
        "runtime_liveness_status": "live",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-001",
            "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-001"},
        },
    }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_path = study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))

    slo_summary = result["managed_study_autonomy_slo_statuses"][0]
    assert slo_summary["study_id"] == "001-risk"
    assert slo_summary["quest_id"] == "quest-001"
    assert slo_summary["state"] == "breach"
    assert "read_churn_without_artifact_delta" in slo_summary["breach_types"]
    assert slo_summary["ai_doctor_request_required"] is True
    assert slo_summary["ai_doctor_state"] == "attempt_recorded"
    assert slo_summary["quality_gate_relaxation_allowed"] is False
    assert slo_summary["status_path"] == str(latest_path)
    assert latest["state"] == "breach"
    assert latest["ai_doctor_state"] == "attempt_recorded"
    assert latest["ai_doctor_attempt"]["state"] == "repair_plan_recorded"
    assert result["managed_study_autonomy_repair_actions"][0]["state"] == "blocked"
    assert result["managed_study_autonomy_repair_actions"][0]["reason"] == "runtime_recovery_not_authorized"
    assert "read_churn_without_artifact_delta" in latest["breach_types"]
    assert latest["mds_progress_markers"]["read_churn_ratio"] == 0.8
    assert latest["quality_gate_relaxation_allowed"] is False
    assert (study_root / "artifacts" / "autonomy" / "ai_doctor_requests" / "latest.json").exists()
    assert (study_root / "artifacts" / "autonomy" / "ai_doctor_attempts" / "latest.json").exists()

def test_watch_runtime_skips_outer_loop_wakeup_when_inputs_stabilize_after_no_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "active_run_id": "run-1",
        "runtime_liveness_status": "live",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-1",
            "runtime_audit": {
                "status": "live",
                "worker_running": True,
                "active_run_id": "run-1",
            },
        },
        "execution": {
            "engine": "mas-runtime-core",
                "runtime_backend_id": "mas_runtime_core",
                "runtime_engine_id": "mas-runtime-core",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
    }
    build_calls: list[str] = []

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.study_outer_loop,
        "build_domain_health_diagnostic_outer_loop_tick_request",
        lambda **kwargs: (build_calls.append(str(kwargs["study_root"])), None)[1],
    )

    first = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    second = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    third = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    latest_record = json.loads(latest_path.read_text(encoding="utf-8"))

    assert build_calls == [str(study_root), str(study_root)]
    assert first["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "no_request"
    assert second["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "no_request"
    assert third["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "skipped_unchanged_inputs"
    assert latest_record["outcome"] == "skipped_unchanged_inputs"
    assert latest_record["input_fingerprint"] == second["managed_study_outer_loop_wakeup_audits"][0]["input_fingerprint"]

def test_domain_health_diagnostic_uses_typed_surface_attributes_for_managed_study_actions(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
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

    class AttributeOnlyProgressProjectionStatus(typed_surface.ProgressProjectionStatus):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("domain_health_diagnostic should not use mapping access for typed progress projection status")

        def get(self, key: str, default: object | None = None) -> object | None:
            raise AssertionError("domain_health_diagnostic should not use mapping access for typed progress projection status")

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: AttributeOnlyProgressProjectionStatus.from_payload(
            make_progress_projection_payload()
        ),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "create_and_start", "reason": "quest_missing"}
    ]

def test_domain_health_diagnostic_uses_typed_surface_attributes_for_read_only_managed_study_actions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
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

    class AttributeOnlyProgressProjectionStatus(typed_surface.ProgressProjectionStatus):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("domain_health_diagnostic should not use mapping access for typed progress projection status")

        def get(self, key: str, default: object | None = None) -> object | None:
            raise AssertionError("domain_health_diagnostic should not use mapping access for typed progress projection status")

    monkeypatch.setattr(
        module.study_runtime_router,
        "progress_projection",
        lambda *, profile, study_root: AttributeOnlyProgressProjectionStatus.from_payload(
            make_progress_projection_payload(decision="noop")
        ),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "noop", "reason": "quest_missing"}
    ]
