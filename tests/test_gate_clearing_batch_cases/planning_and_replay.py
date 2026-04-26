from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_submission_minimal_fingerprint_payload_ignores_materialized_submission_source_from_compile_report(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    submission_minimal_tests = importlib.import_module("tests.test_submission_minimal")
    paper_root = submission_minimal_tests.make_materialized_submission_source_workspace(tmp_path)
    profile = make_profile(tmp_path)

    payload = module._submission_minimal_fingerprint_payload(
        paper_root=paper_root,
        gate_report={
            "status": "blocked",
            "blockers": ["stale_submission_minimal_authority"],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
        profile=profile,
    )

    assert payload["compiled_markdown"]["path"] == str((paper_root / "draft.md").resolve())
def test_execute_repair_units_treats_all_skipped_dependents_as_terminal_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    paper_root = tmp_path / "paper"
    paper_root.mkdir(parents=True)

    def _raise_failure() -> dict[str, Any]:
        raise RuntimeError("simulated upstream failure")

    repair_units = [
        module.GateClearingRepairUnit(
            unit_id="upstream_failure",
            label="upstream failure",
            parallel_safe=True,
            run=_raise_failure,
        ),
        module.GateClearingRepairUnit(
            unit_id="dependent_parallel",
            label="dependent parallel",
            parallel_safe=True,
            run=lambda: {"status": "ok"},
            depends_on=("upstream_failure",),
        ),
        module.GateClearingRepairUnit(
            unit_id="dependent_sequential",
            label="dependent sequential",
            parallel_safe=False,
            run=lambda: {"status": "ok"},
            depends_on=("upstream_failure", "dependent_parallel"),
        ),
    ]

    unit_results, unit_fingerprints, execution_summary = module._execute_repair_units(
        repair_units=repair_units,
        latest_batch={},
        paper_root=paper_root,
        gate_report={},
        profile=profile,
    )

    assert [item["status"] for item in unit_results] == [
        "failed",
        "skipped_failed_dependency",
        "skipped_failed_dependency",
    ]
    assert unit_results[1]["failed_dependencies"] == ["upstream_failure"]
    assert unit_results[2]["failed_dependencies"] == ["upstream_failure", "dependent_parallel"]
    assert unit_fingerprints == {}
    assert execution_summary == {
        "parallel_wave_count": 1,
        "parallel_unit_count": 1,
        "sequential_unit_count": 0,
        "skipped_dependency_unit_count": 2,
    }
def test_parse_json_object_from_cli_stdout_ignores_launcher_preamble() -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")

    payload = module._parse_json_object_from_cli_stdout(
        "\n".join(
            [
                "DeepScientist detected a runtime change and is rebuilding the local uv-managed environment.",
                "[1/2] Preparing uv-managed Python runtime",
                "{",
                '  "ok": true,',
                '  "status": "updated",',
                '  "repaired_files": ["paper/claim_evidence_map.json"]',
                "}",
            ]
        )
    )

    assert payload == {
        "ok": True,
        "status": "updated",
        "repaired_files": ["paper/claim_evidence_map.json"],
    }
def test_build_gate_clearing_batch_recommended_action_promotes_blocked_bounded_analysis(tmp_path: Path) -> None:
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
    mapping_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "analysis-analysis-c7574291-freeze-scientific-anchor-and-gate-map"
        / "experiments"
        / "analysis"
        / "analysis-c7574291"
        / "freeze-scientific-anchor-and-gate-map"
        / "outputs"
        / "scientific_anchor_mapping.json"
    )
    _write_json(
        mapping_path,
        {
            "proposed_scientific_followup_questions": ["Q1"],
            "proposed_explanation_targets": ["T1"],
            "clinician_facing_interpretation_target": "Clinician-facing interpretation target.",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "missing_medical_story_contract",
            "table_catalog_missing_or_incomplete",
        ],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert action["gate_clearing_batch_mapping_path"] == str(mapping_path)
    assert "scientific-anchor fields can be frozen" in action["gate_clearing_batch_reason"]
def test_build_gate_clearing_batch_recommended_action_uses_surface_blocker_details(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="cross_sectional",
        endpoint_type="treatment_gap",
        manuscript_family="observational_study",
    )
    publication_eval_payload = _write_blocked_publication_eval(
        study_root,
        quest_id="003-dpcc-primary-care-phenotype-treatment-gap",
    )
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_blockers": [
            "missing_medical_story_contract",
            "figure_semantics_manifest_missing_or_incomplete",
            "undefined_methodology_labels_present",
            "treatment_gap_reporting_incomplete",
        ],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="003-dpcc-primary-care-phenotype-treatment-gap",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert "paper-facing display/reporting blockers" in action["gate_clearing_batch_reason"]
def test_build_gate_clearing_batch_recommended_action_promotes_bundle_stage_return_to_finalize(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Let MAS re-evaluate the finalize-stage blockers before the same paper line resumes.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    gate_report = {
        "status": "blocked",
        "blockers": [
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "controller_stage_note": "Only finalize or submission-bundle repairs remain on the current paper line.",
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_named_blockers": [],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-004",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["route_target"] == "finalize"
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert "finalize/submission bundle blockers are deterministic same-line repair candidates" in action[
        "gate_clearing_batch_reason"
    ]


def test_build_gate_clearing_batch_recommended_action_widens_bounded_analysis_to_submission_refresh(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    assert publication_eval_payload["recommended_actions"][0]["action_type"] == "bounded_analysis"
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "paper_line_open_supplementary_count": 0,
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_current": True,
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-004",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["route_target"] == "finalize"
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert action["next_work_unit"] == {
        "unit_id": "submission_minimal_refresh",
        "lane": "finalize",
        "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
    }
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
def test_run_gate_clearing_batch_executes_bundle_stage_submission_refresh_then_replays_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

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
                "submission_surface_qc_failure_present",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "blocked"
    assert result["gate_blockers"] == ["submission_surface_qc_failure_present"]
def test_run_gate_clearing_batch_refreshes_stale_submission_minimal_authority_without_bundle_stage_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

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
            "blockers": ["stale_submission_minimal_authority"],
            "current_required_action": "continue_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == ["create_submission_minimal_package"]
    assert result["gate_replay"]["status"] == "clear"
    assert result["gate_blockers"] == ["stale_submission_minimal_authority"]
def test_run_gate_clearing_batch_executes_bundle_stage_workspace_refresh_before_submission_replay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "generate_display_exports.py").write_text("print('ok')\n", encoding="utf-8")
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

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
                "submission_surface_qc_failure_present",
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module,
        "_run_workspace_display_repair_script",
        lambda **_: {"status": "updated", "script_path": str(paper_root / "build" / "generate_display_exports.py")},
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["submission_surface_qc_failure_present"],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "workspace_display_repair_script",
        "create_submission_minimal_package",
    ]
    assert result["gate_replay"]["status"] == "blocked"
    assert result["gate_blockers"] == ["submission_surface_qc_failure_present"]
def test_run_gate_clearing_batch_syncs_stale_submission_delivery_after_bundle_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Return to controller so MAS can clear the finalize-stage blockers.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

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
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_source_changed",
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {"output_root": "paper/submission_minimal", "status": "ready"},
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **_: {"status": "synced", "current_package_root": "studies/004-invasive-architecture/manuscript/current_package"},
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    assert result["unit_results"][1]["status"] == "synced"
    assert result["gate_replay"]["status"] == "clear"
def test_run_gate_clearing_batch_reuses_embedded_submission_delivery_sync_after_bundle_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-004"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-004" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")

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
            ],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_source_changed",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module.submission_minimal,
        "create_submission_minimal_package",
        lambda **_: {
            "output_root": "paper/submission_minimal",
            "status": "ready",
            "delivery_sync": {
                "status": "synced",
                "current_package_root": "studies/004-invasive-architecture/manuscript/current_package",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("embedded delivery_sync should be reused instead of re-running study_delivery_sync")
        ),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert [item["unit_id"] for item in result["unit_results"]] == [
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    assert result["unit_results"][1]["status"] == "synced"
    assert result["unit_results"][1]["result"]["current_package_root"] == (
        "studies/004-invasive-architecture/manuscript/current_package"
    )
