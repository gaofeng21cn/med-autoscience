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


def test_build_default_controller_runners_includes_figure_loop_guard() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runners = module.build_default_controller_runners()
    assert "figure_loop_guard" in runners


def test_runtime_watch_registers_medical_runtime_audits() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runners = module.build_default_controller_runners()

    assert "medical_literature_audit" in runners
    assert "medical_reporting_audit" in runners


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


def test_scan_runtime_only_processes_active_quests(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q-running", status="running")
    make_quest(tmp_path, "q-active", status="active")
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

    assert sorted(seen) == ["q-active", "q-running"]
    assert sorted(result["scanned_quests"]) == ["q-active", "q-running"]


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
    seen: list[str] = []

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: {"study_id": Path(study_root).name, "decision": "create_and_start", "reason": "quest_missing"},
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
