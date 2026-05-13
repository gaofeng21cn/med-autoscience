from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

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

def test_runtime_watch_reapplies_publication_gate_when_ai_reviewer_eval_masks_return_to_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    result_payload = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked"],
        "allow_write": False,
        "missing_non_scalar_deliverables": [],
        "submission_minimal_present": True,
        "supervisor_phase": "publishability_gate_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": True,
        "current_required_action": "return_to_publishability_gate",
        "deferred_downstream_actions": [],
        "controller_stage_note": "return to publication gate",
        "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
    }
    stable_fingerprint = module.build_fingerprint("publication_gate", result_payload)

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return dict(result_payload)

    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "load_watch_state",
        lambda quest_root: module.runtime_watch_protocol.RuntimeWatchState(
            schema_version=1,
            updated_at="2026-04-30T12:00:00+00:00",
            controllers={
                "publication_gate": module.runtime_watch_protocol.RuntimeWatchControllerState(
                    last_seen_fingerprint=stable_fingerprint,
                    last_applied_fingerprint=stable_fingerprint,
                    last_applied_at="2026-04-30T12:00:00+00:00",
                    last_status="blocked",
                    last_suppression_reason=None,
                )
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_publication_gate_ai_reviewer_eval_masks_return_to_gate",
        lambda *, dry_run_result: True,
    )

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert calls == [False, True]
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
