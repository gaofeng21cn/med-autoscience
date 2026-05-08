from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_run_gate_clearing_batch_executes_parallel_units_then_replays_gate(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-001" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "stale_study_delivery_mirror",
                "medical_publication_surface_blocked",
                "claim_evidence_consistency_failed",
            ],
            "medical_publication_surface_status": "blocked",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (
            paper_root / "scientific_anchor_mapping.json",
            {
                "proposed_scientific_followup_questions": ["Q1"],
                "proposed_explanation_targets": ["T1"],
                "clinician_facing_interpretation_target": "Clinician target.",
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_freeze_scientific_anchor_fields",
        lambda **_: {"status": "updated", "scientific_followup_question_count": 1},
    )
    monkeypatch.setattr(
        module,
        "_repair_paper_live_paths",
        lambda **_: {"ok": True, "status": "updated", "repaired_files": ["paper/claim_evidence_map.json"]},
    )
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda **_: {"status": "materialized", "tables_materialized": ["T1"]},
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    replay_kwargs: dict[str, Any] = {}

    def fake_run_controller(**kwargs: Any) -> dict[str, Any]:
        replay_kwargs.update(kwargs)
        return {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["claim_evidence_consistency_failed"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        }

    monkeypatch.setattr(module.publication_gate, "run_controller", fake_run_controller)

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "freeze_scientific_anchor_fields",
        "repair_paper_live_paths",
        "materialize_display_surface",
    ]
    assert result["gate_replay"]["status"] == "blocked"
    assert replay_kwargs["enqueue_intervention"] is False
    record = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert record["source_eval_id"] == publication_eval_payload["eval_id"]
    assert record["unit_results"][0]["unit_id"] == "freeze_scientific_anchor_fields"

def test_run_gate_clearing_batch_waits_for_live_path_repair_before_display_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-001" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_blocked_publication_eval(study_root, quest_id="quest-001")

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": [
                "medical_publication_surface_blocked",
            ],
            "medical_publication_surface_status": "blocked",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (
            paper_root / "scientific_anchor_mapping.json",
            {
                "proposed_scientific_followup_questions": ["Q1"],
                "proposed_explanation_targets": ["T1"],
            },
        ),
    )
    freeze_started = threading.Event()
    repair_started = threading.Event()
    repair_done = threading.Event()
    overlap_seen: dict[str, bool] = {"value": False}

    def fake_freeze(**_: Any) -> dict[str, Any]:
        freeze_started.set()
        assert repair_started.wait(1), "freeze_scientific_anchor_fields should overlap with live-path repair"
        overlap_seen["value"] = not repair_done.is_set()
        return {"status": "updated"}

    def fake_repair(**_: Any) -> dict[str, Any]:
        repair_started.set()
        assert freeze_started.wait(1), "repair_paper_live_paths should overlap with anchor freeze"
        time.sleep(0.15)
        repair_done.set()
        return {"status": "updated"}

    def fake_materialize(**_: Any) -> dict[str, Any]:
        assert repair_done.is_set(), "display refresh must wait for live-path repair"
        return {"status": "materialized"}

    monkeypatch.setattr(module, "_freeze_scientific_anchor_fields", fake_freeze)
    monkeypatch.setattr(module, "_repair_paper_live_paths", fake_repair)
    monkeypatch.setattr(module, "_materialize_display_surface", fake_materialize)
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["medical_publication_surface_blocked"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        quest_id="quest-001",
        source="test-source",
    )

    result_by_unit = {item["unit_id"]: item for item in result["unit_results"]}
    assert overlap_seen["value"] is True
    assert result_by_unit["freeze_scientific_anchor_fields"]["status"] == "updated"
    assert result_by_unit["repair_paper_live_paths"]["status"] == "updated"
    assert result_by_unit["materialize_display_surface"]["status"] == "materialized"
