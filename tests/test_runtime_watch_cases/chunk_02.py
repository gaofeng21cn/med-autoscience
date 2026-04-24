from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_runtime_watch_uses_runtime_watch_protocol_helpers(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    seen: dict[str, object] = {}

    def fake_load_watch_state(path: Path) -> object:
        seen["loaded"] = str(path)
        return module.runtime_watch_protocol.RuntimeWatchState(
            schema_version=1,
            updated_at=None,
            controllers={},
        )

    def fake_plan_controller_intervention(**kwargs) -> object:
        seen.setdefault("planned", []).append(kwargs)
        return module.runtime_watch_protocol.RuntimeWatchInterventionPlan(
            action=module.runtime_watch_protocol.RuntimeWatchControllerAction.APPLIED,
            should_apply=True,
            suppression_reason=None,
            controller_state=module.runtime_watch_protocol.RuntimeWatchControllerState(
                last_seen_fingerprint="fp-1",
                last_applied_fingerprint="fp-1",
                last_applied_at="2026-04-02T12:00:00+00:00",
                last_status="blocked",
                last_suppression_reason=None,
            ),
        )

    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "load_watch_state",
        fake_load_watch_state,
    )
    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "plan_controller_intervention",
        fake_plan_controller_intervention,
    )
    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "save_watch_state",
        lambda quest_root, payload: seen.setdefault("saved", []).append((str(quest_root), payload)),
    )
    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "write_watch_report",
        lambda *, quest_root, report, markdown: seen.setdefault("reported", []).append((str(quest_root), report))
        or (quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json", quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.md"),
    )

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["missing_post_main_publishability_gate"],
                "allow_write": False,
                "missing_non_scalar_deliverables": ["calibration_plot"],
                "submission_minimal_present": False,
                "report_json": "dry.json",
                "report_markdown": "dry.md",
            }
        },
        apply=True,
    )

    assert seen["loaded"] == str(quest_root)
    assert len(seen["planned"]) == 1
    assert len(seen["saved"]) == 1
    assert len(seen["reported"]) == 1
    saved_state = seen["saved"][0][1]
    assert saved_state.controllers["publication_gate"].last_applied_fingerprint is not None
    assert result["controllers"]["publication_gate"]["action"] == "applied"
def test_runtime_watch_preserves_publication_supervisor_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["missing_post_main_publishability_gate"],
                "allow_write": False,
                "missing_non_scalar_deliverables": [],
                "submission_minimal_present": True,
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    controller = result["controllers"]["publication_gate"]
    assert controller["supervisor_phase"] == "publishability_gate_blocked"
    assert controller["phase_owner"] == "publication_gate"
    assert controller["upstream_scientific_anchor_ready"] is True
    assert controller["bundle_tasks_downstream_only"] is True
    assert controller["current_required_action"] == "return_to_publishability_gate"
    assert controller["deferred_downstream_actions"] == []
    assert "downstream-only" in controller["controller_stage_note"]
def test_runtime_watch_applies_publication_gate_when_clear_status_still_needs_draft_handoff_sync(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "clear",
            "blockers": [],
            "allow_write": True,
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": False,
            "draft_handoff_delivery_required": True,
            "draft_handoff_delivery_status": "missing",
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert calls == [False, True]
    assert result["controllers"]["publication_gate"]["action"] == "applied"
def test_runtime_watch_does_not_reapply_after_draft_handoff_sync_stabilizes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"draft_handoff_synced": False}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        if apply:
            state["draft_handoff_synced"] = True
        status = "current" if state["draft_handoff_synced"] else "missing"
        return {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked"],
            "allow_write": False,
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": False,
            "draft_handoff_delivery_required": True,
            "draft_handoff_delivery_status": status,
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["publication_gate"]["action"] == "applied"
    assert second["controllers"]["publication_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_build_default_controller_runners_includes_figure_loop_guard() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runners = module.build_default_controller_runners()
    assert "figure_loop_guard" in runners
def test_runtime_watch_registers_medical_runtime_audits() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runners = module.build_default_controller_runners()

    assert "medical_literature_audit" in runners
    assert "medical_reporting_audit" in runners
def test_runtime_watch_orders_publication_surface_before_gate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[tuple[str, bool]] = []
    state = {"surface_blocked": False}

    def fake_medical_publication_surface(*, quest_root: Path, apply: bool) -> dict:
        calls.append(("medical_publication_surface", apply))
        if apply:
            state["surface_blocked"] = True
        return {
            "status": "blocked",
            "blockers": ["methods_section_structure_missing_or_incomplete"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [
                {
                    "path": "paper/draft.md",
                    "location": "line 33",
                    "phrase": "Methods",
                }
            ],
            "intervention_enqueued": apply,
        }

    def fake_publication_gate(*, quest_root: Path, apply: bool) -> dict:
        calls.append(("publication_gate", apply))
        blocked = state["surface_blocked"]
        return {
            "status": "blocked" if blocked else "clear",
            "blockers": ["medical_publication_surface_blocked"] if blocked else [],
            "allow_write": not blocked,
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": True,
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": fake_publication_gate,
            "medical_publication_surface": fake_medical_publication_surface,
        },
        apply=True,
    )

    assert result["controllers"]["medical_publication_surface"]["status"] == "blocked"
    assert result["controllers"]["publication_gate"]["status"] == "blocked"
    assert result["controllers"]["publication_gate"]["blockers"] == ["medical_publication_surface_blocked"]
    assert calls == [
        ("medical_publication_surface", False),
        ("medical_publication_surface", True),
        ("publication_gate", False),
        ("publication_gate", True),
    ]
def test_suppresses_duplicate_blocker(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [{"path": "paper/draft.md", "location": "line 1", "phrase": "deployment-facing"}],
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_suppresses_duplicate_figure_loop_guard_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["figure_loop_budget_exceeded"],
            "dominant_figure_id": "F4B",
            "dominant_figure_mentions": 18,
            "reference_count": 7,
            "report_json": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )

    assert first["controllers"]["figure_loop_guard"]["action"] == "applied"
    assert second["controllers"]["figure_loop_guard"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_runtime_watch_surfaces_deferred_figure_loop_guard_stop(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        return {
            "status": "blocked",
            "blockers": ["figure_loop_budget_exceeded"],
            "dominant_figure_id": "F4B",
            "dominant_figure_mentions": 18,
            "reference_count": 7,
            "report_json": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.md"),
            "intervention_enqueued": apply,
            "quest_stop_applied": False,
            "quest_stop_deferred": apply,
            "quest_stop_defer_reason": "self_owned_runtime_watch" if apply else None,
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )

    controller = result["controllers"]["figure_loop_guard"]
    assert controller["action"] == "applied"
    assert controller["quest_stop_applied"] is False
    assert controller["quest_stop_deferred"] is True
    assert controller["quest_stop_defer_reason"] == "self_owned_runtime_watch"
def test_suppresses_duplicate_medical_literature_audit_blocker_even_when_report_paths_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"run": 0}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        state["run"] += 1
        suffix = f"scan-{state['run']}"
        return {
            "status": "blocked",
            "blockers": ["reference_gaps_present"],
            "action": "clear",
            "missing_pmids": ["12345"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_literature_audit" / f"{suffix}.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_literature_audit" / f"{suffix}.md"),
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_literature_audit": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_literature_audit": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_literature_audit"]["action"] == "applied"
    assert second["controllers"]["medical_literature_audit"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_suppresses_duplicate_medical_reporting_audit_blocker_even_when_report_paths_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"run": 0}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        state["run"] += 1
        suffix = f"scan-{state['run']}"
        return {
            "status": "blocked",
            "blockers": ["missing_reporting_guideline_checklist"],
            "action": "clear",
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_reporting_audit" / f"{suffix}.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_reporting_audit" / f"{suffix}.md"),
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_reporting_audit": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_reporting_audit": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_reporting_audit"]["action"] == "applied"
    assert second["controllers"]["medical_reporting_audit"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_blocked_with_apply_disabled_records_suppression_without_second_apply(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["missing_post_main_publishability_gate"],
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=False,
    )

    assert result["controllers"]["publication_gate"]["action"] == "suppressed"
    assert result["controllers"]["publication_gate"]["suppression_reason"] == "apply_disabled"
    assert calls == [False]
def test_controller_missing_artifacts_does_not_crash_runtime_watch(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    def missing_artifact_runner(*, quest_root: Path, apply: bool) -> dict:
        raise FileNotFoundError(f"No main RESULT.json found under {quest_root}")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": missing_artifact_runner},
        apply=True,
    )

    controller = result["controllers"]["publication_gate"]
    assert controller["status"] == "awaiting_artifacts"
    assert controller["action"] == "clear"
    assert controller["suppression_reason"] == "precondition_missing"
    assert "missing_artifact:No main RESULT.json found under" in controller["advisories"][0]
def test_reapplies_when_fingerprint_changes(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    state = {"value": "deployment-facing"}
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [{"path": "paper/draft.md", "location": "line 1", "phrase": state["value"]}],
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    state["value"] = "baseline-comparable"
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert calls == [False, True, False, True]
def test_scan_runtime_processes_managed_quests_including_non_live_states(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
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

    result = module.run_watch_for_runtime(
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

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: make_study_runtime_status_payload(
            study_id=Path(study_root).name,
            decision="create_and_start",
            reason="quest_missing",
        ),
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
        {"study_id": "001-risk", "decision": "create_and_start", "reason": "quest_missing"}
    ]
def test_watch_runtime_skips_outer_loop_wakeup_when_inputs_stabilize_after_no_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    status_payload = {
        **make_study_runtime_status_payload(
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
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
    }
    build_calls: list[str] = []

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.study_outer_loop,
        "build_runtime_watch_outer_loop_tick_request",
        lambda **kwargs: (build_calls.append(str(kwargs["study_root"])), None)[1],
    )

    first = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    second = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    third = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    latest_record = json.loads(latest_path.read_text(encoding="utf-8"))

    assert build_calls == [str(study_root), str(study_root)]
    assert first["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "no_request"
    assert second["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "no_request"
    assert third["managed_study_outer_loop_wakeup_audits"][0]["outcome"] == "skipped_unchanged_inputs"
    assert latest_record["outcome"] == "skipped_unchanged_inputs"
    assert latest_record["input_fingerprint"] == second["managed_study_outer_loop_wakeup_audits"][0]["input_fingerprint"]
def test_watch_runtime_uses_typed_surface_attributes_for_managed_study_actions(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
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

    class AttributeOnlyStudyRuntimeStatus(typed_surface.StudyRuntimeStatus):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

        def get(self, key: str, default: object | None = None) -> object | None:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: AttributeOnlyStudyRuntimeStatus.from_payload(
            make_study_runtime_status_payload()
        ),
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
        {"study_id": "001-risk", "decision": "create_and_start", "reason": "quest_missing"}
    ]
def test_watch_runtime_uses_typed_surface_attributes_for_read_only_managed_study_actions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
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

    class AttributeOnlyStudyRuntimeStatus(typed_surface.StudyRuntimeStatus):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

        def get(self, key: str, default: object | None = None) -> object | None:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: AttributeOnlyStudyRuntimeStatus.from_payload(
            make_study_runtime_status_payload(decision="noop")
        ),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "noop", "reason": "quest_missing"}
    ]
