from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_quest(tmp_path: Path, name: str, status: str = "running") -> Path:
    quest_root = tmp_path / "runtime" / "quests" / name
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": name,
            "status": status,
            "active_run_id": "run-1" if status in {"running", "active"} else None,
        },
    )
    return quest_root


def make_study_runtime_status_payload(
    *,
    study_id: str = "001-risk",
    decision: str = "create_and_start",
    reason: str = "quest_missing",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": f"/tmp/studies/{study_id}",
        "entry_mode": "full_research",
        "execution": {"quest_id": study_id, "auto_resume": True},
        "quest_id": study_id,
        "quest_root": f"/tmp/runtime/quests/{study_id}",
        "quest_exists": True,
        "quest_status": "created",
        "runtime_binding_path": f"/tmp/studies/{study_id}/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": decision,
        "reason": reason,
    }


def test_applies_new_blocker_once(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[tuple[str, bool]] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append((quest_root.name, apply))
        return {
            "status": "blocked",
            "blockers": ["missing_post_main_publishability_gate"],
            "allow_write": False,
            "missing_non_scalar_deliverables": ["calibration_plot"],
            "submission_minimal_present": False,
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert calls == [("q001", False), ("q001", True)]
    assert result["controllers"]["publication_gate"]["action"] == "applied"


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
    assert saved_state.controllers["publication_gate"].last_applied_fingerprint == "fp-1"
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


def test_watch_runtime_hard_recovers_active_no_live_resume_even_without_apply(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
    quest_root = profile.runtime_root / "001-risk"
    calls: list[tuple[str, str]] = []

    def parked_status() -> dict[str, object]:
        return {
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_parked_on_unchanged_finalize_state",
            ),
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "execution": {
                "engine": "med-deepscientist",
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

    def recovered_status(*, source: str) -> dict[str, object]:
        return {
            **parked_status(),
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-resumed",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-resumed",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
            "autonomous_runtime_notice": {
                "active_run_id": "run-resumed",
            },
            "source": source,
        }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or parked_status(),
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source))
        or recovered_status(source=source),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("status", "001-risk"),
        ("ensure", "runtime_watch_auto_recovery"),
    ]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
        }
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "resume",
            "preflight_reason": "quest_parked_on_unchanged_finalize_state",
            "applied_decision": "resume",
            "applied_reason": "quest_parked_on_unchanged_finalize_state",
            "source": "runtime_watch_auto_recovery",
        }
    ]
    assert result["managed_study_supervision"][0]["health_status"] == "live"


def test_watch_quest_writes_latest_runtime_watch_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    latest_json = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    latest_markdown = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.md"

    assert result["latest_report_json"] == str(latest_json)
    assert result["latest_report_markdown"] == str(latest_markdown)
    assert latest_json.exists()
    assert latest_markdown.exists()


def test_watch_runtime_writes_study_supervision_report_and_escalates_after_consecutive_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    dump_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "runtime_watch",
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
                "engine": "med-deepscientist",
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

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: failing_status(),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

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

    first_supervision = first["managed_study_supervision"][0]
    second_supervision = second["managed_study_supervision"][0]
    latest_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"

    assert first_supervision["health_status"] == "degraded"
    assert first_supervision["consecutive_failure_count"] == 1
    assert second_supervision["health_status"] == "escalated"
    assert second_supervision["consecutive_failure_count"] == 2
    assert second_supervision["needs_human_intervention"] is True
    assert latest_payload["health_status"] == "escalated"
    assert latest_payload["next_action_summary"]
    assert escalation_path.exists()
    escalation_payload = json.loads(escalation_path.read_text(encoding="utf-8"))
    runtime_event_payload = json.loads(
        (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").read_text(encoding="utf-8")
    )

    assert escalation_payload["reason"] == "resume_request_failed"
    assert runtime_event_payload["event_kind"] == "supervision_changed"
    assert runtime_event_payload["event_source"] == "runtime_supervision"
    assert runtime_event_payload["outer_loop_input"]["reason"] == "resume_request_failed"


def test_watch_runtime_writes_supervision_changed_event_when_degraded_runtime_recovers_to_live(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    dump_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "runtime_watch",
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
                "engine": "med-deepscientist",
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
                "engine": "med-deepscientist",
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

    def next_status(*, profile, study_root, source):
        index = min(call_index["value"], len(states) - 1)
        call_index["value"] += 1
        return states[index]

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", next_status)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

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

    first_supervision = first["managed_study_supervision"][0]
    second_supervision = second["managed_study_supervision"][0]
    runtime_event_payload = json.loads(
        (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").read_text(encoding="utf-8")
    )

    assert first_supervision["health_status"] == "degraded"
    assert second_supervision["health_status"] == "live"
    assert second_supervision["last_transition"] == "recovered"
    assert runtime_event_payload["event_kind"] == "supervision_changed"
    assert runtime_event_payload["outer_loop_input"]["runtime_liveness_status"] == "live"
    assert runtime_event_payload["outer_loop_input"]["active_run_id"] == "run-live"


def test_suppresses_duplicate_data_asset_gate_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["outdated_private_release"],
            "study_id": quest_root.name,
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_applies_data_asset_gate_advisory_once(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "advisory",
            "blockers": [],
            "advisories": ["public_data_extension_available"],
            "study_id": quest_root.name,
            "public_support_dataset_ids": ["geo-gse000001"],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["status"] == "advisory"
    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_reapplies_data_asset_gate_when_unresolved_dataset_ids_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"unresolved_dataset_ids": ["ds_a"]}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["unresolved_private_data_contract"],
            "advisories": [],
            "study_id": quest_root.name,
            "outdated_dataset_ids": [],
            "unresolved_dataset_ids": list(state["unresolved_dataset_ids"]),
            "public_support_dataset_ids": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    state["unresolved_dataset_ids"] = ["ds_b"]
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "applied"
    assert calls == [False, True, False, True]


def test_watch_loop_runs_runtime_ticks_on_interval(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    runtime_root.mkdir(parents=True)
    seen: list[tuple[str, object]] = []

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        seen.append(("tick", runtime_root, apply, ensure_study_runtimes))
        return {
            "runtime_root": str(runtime_root),
            "scanned_quests": [],
        }

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    def fake_sleep(seconds: float) -> None:
        seen.append(("sleep", seconds))

    result = module.run_watch_loop(
        runtime_root=runtime_root,
        apply=True,
        ensure_study_runtimes=True,
        interval_seconds=12,
        max_ticks=2,
        sleep_fn=fake_sleep,
    )

    assert result["tick_count"] == 2
    assert result["interval_seconds"] == 12
    assert result["last_result"] == {
        "runtime_root": str(runtime_root),
        "scanned_quests": [],
    }
    assert seen == [
        ("tick", runtime_root, True, True),
        ("sleep", 12),
        ("tick", runtime_root, True, True),
    ]


def test_watch_loop_continues_after_single_tick_failure(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    runtime_root.mkdir(parents=True)
    seen: list[tuple[str, object]] = []
    attempts = {"count": 0}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        attempts["count"] += 1
        seen.append(("tick", attempts["count"]))
        if attempts["count"] == 1:
            raise RuntimeError("transient daemon read failed")
        return {
            "runtime_root": str(runtime_root),
            "scanned_quests": ["q001"],
        }

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    def fake_sleep(seconds: float) -> None:
        seen.append(("sleep", seconds))

    result = module.run_watch_loop(
        runtime_root=runtime_root,
        apply=True,
        ensure_study_runtimes=True,
        interval_seconds=12,
        max_ticks=2,
        sleep_fn=fake_sleep,
    )

    assert result["tick_count"] == 2
    assert result["last_result"] == {
        "runtime_root": str(runtime_root),
        "scanned_quests": ["q001"],
    }
    assert result["tick_errors"] == [
        {
            "tick": 1,
            "error_type": "RuntimeError",
            "error": "transient daemon read failed",
        }
    ]
    assert seen == [
        ("tick", 1),
        ("sleep", 12),
        ("tick", 2),
    ]


def test_run_managed_supervisor_tick_uses_profile_runtime_root_and_always_enables_study_runtime_ensure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="glioma",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
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
    called: dict[str, object] = {}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        return {"mode": "managed_supervisor_tick"}

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    result = module.run_managed_supervisor_tick(profile=profile, apply=True)

    assert result == {"mode": "managed_supervisor_tick"}
    assert called == {
        "runtime_root": profile.runtime_root,
        "apply": True,
        "profile": profile,
        "ensure_study_runtimes": True,
    }


def test_run_managed_supervisor_loop_uses_profile_runtime_root_and_always_enables_study_runtime_ensure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="glioma",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
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
    called: dict[str, object] = {}

    def fake_run_watch_loop(
        *,
        runtime_root: Path,
        apply: bool,
        profile,
        ensure_study_runtimes: bool = False,
        interval_seconds: int,
        max_ticks: int | None,
        sleep_fn,
    ) -> dict[str, object]:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        called["interval_seconds"] = interval_seconds
        called["max_ticks"] = max_ticks
        called["sleep_fn"] = sleep_fn
        return {"mode": "managed_supervisor_loop"}

    monkeypatch.setattr(module, "run_watch_loop", fake_run_watch_loop)

    result = module.run_managed_supervisor_loop(
        profile=profile,
        apply=True,
        interval_seconds=45,
        max_ticks=3,
        sleep_fn=lambda _: None,
    )

    assert result == {"mode": "managed_supervisor_loop"}
    assert called["runtime_root"] == profile.runtime_root
    assert called["apply"] is True
    assert called["profile"] == profile
    assert called["ensure_study_runtimes"] is True
    assert called["interval_seconds"] == 45
    assert called["max_ticks"] == 3
