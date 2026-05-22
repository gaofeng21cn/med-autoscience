from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_suppresses_duplicate_blocker(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "suppressed"
    assert calls == [False, True, False]

def test_suppresses_duplicate_figure_loop_guard_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )

    assert first["controllers"]["figure_loop_guard"]["action"] == "applied"
    assert second["controllers"]["figure_loop_guard"]["action"] == "suppressed"
    assert calls == [False, True, False]

def test_domain_health_diagnostic_surfaces_deferred_figure_loop_guard_stop(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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
            "quest_stop_defer_reason": "self_owned_domain_health_diagnostic" if apply else None,
        }

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )

    controller = result["controllers"]["figure_loop_guard"]
    assert controller["action"] == "applied"
    assert controller["quest_stop_applied"] is False
    assert controller["quest_stop_deferred"] is True
    assert controller["quest_stop_defer_reason"] == "self_owned_domain_health_diagnostic"

def test_suppresses_duplicate_medical_literature_audit_blocker_even_when_report_paths_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_literature_audit": fake_runner},
        apply=True,
    )
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_literature_audit": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_literature_audit"]["action"] == "applied"
    assert second["controllers"]["medical_literature_audit"]["action"] == "suppressed"
    assert calls == [False, True, False]

def test_suppresses_duplicate_medical_reporting_audit_blocker_even_when_report_paths_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_reporting_audit": fake_runner},
        apply=True,
    )
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_reporting_audit": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_reporting_audit"]["action"] == "applied"
    assert second["controllers"]["medical_reporting_audit"]["action"] == "suppressed"
    assert calls == [False, True, False]

def test_blocked_with_apply_disabled_records_suppression_without_second_apply(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=False,
    )

    assert result["controllers"]["publication_gate"]["action"] == "suppressed"
    assert result["controllers"]["publication_gate"]["suppression_reason"] == "apply_disabled"
    assert calls == [False]

def test_controller_missing_artifacts_does_not_crash_domain_health_diagnostic(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")

    def missing_artifact_runner(*, quest_root: Path, apply: bool) -> dict:
        raise FileNotFoundError(f"No main RESULT.json found under {quest_root}")

    result = module.run_domain_health_diagnostic_for_quest(
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
        module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    state["value"] = "baseline-comparable"
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert calls == [False, True, False, True]
