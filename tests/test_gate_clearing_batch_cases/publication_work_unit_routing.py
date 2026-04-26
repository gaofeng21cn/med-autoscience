from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_next_work_unit_filter_preserves_submission_refresh_dependency_closure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    scheduler = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_scheduler")
    work_units = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_work_units")
    profile = make_profile(tmp_path)
    paper_root = tmp_path / "paper"
    paper_root.mkdir(parents=True)

    repair_units = [
        module.GateClearingRepairUnit(
            unit_id="repair_paper_live_paths",
            label="repair paper live paths",
            parallel_safe=True,
            run=lambda: {"status": "updated"},
        ),
        module.GateClearingRepairUnit(
            unit_id="workspace_display_repair_script",
            label="workspace display repair script",
            parallel_safe=True,
            depends_on=("repair_paper_live_paths",),
            run=lambda: {"status": "updated"},
        ),
        module.GateClearingRepairUnit(
            unit_id="create_submission_minimal_package",
            label="create submission minimal package",
            parallel_safe=False,
            depends_on=("workspace_display_repair_script",),
            run=lambda: {"status": "ready"},
        ),
        module.GateClearingRepairUnit(
            unit_id="sync_submission_minimal_delivery",
            label="sync submission minimal delivery",
            parallel_safe=False,
            depends_on=("create_submission_minimal_package",),
            run=lambda: {"status": "synced"},
        ),
        module.GateClearingRepairUnit(
            unit_id="freeze_scientific_anchor_fields",
            label="freeze scientific anchor fields",
            parallel_safe=True,
            run=lambda: {"status": "updated"},
        ),
    ]

    filtered_units = work_units.filter_repair_units_for_publication_work_unit(
        repair_units,
        next_work_unit={"unit_id": "submission_minimal_refresh"},
    )

    assert [unit.unit_id for unit in filtered_units] == [
        "repair_paper_live_paths",
        "workspace_display_repair_script",
        "create_submission_minimal_package",
        "sync_submission_minimal_delivery",
    ]
    execution_plan = scheduler.build_repair_unit_execution_plan(filtered_units)
    assert execution_plan["status"] == "planned"
    assert execution_plan["critical_path_depth"] == 4
    assert execution_plan["waves"] == [
        {
            "wave_index": 1,
            "parallel_unit_ids": ["repair_paper_live_paths"],
            "sequential_unit_ids": [],
            "unit_ids": ["repair_paper_live_paths"],
        },
        {
            "wave_index": 2,
            "parallel_unit_ids": ["workspace_display_repair_script"],
            "sequential_unit_ids": [],
            "unit_ids": ["workspace_display_repair_script"],
        },
        {
            "wave_index": 3,
            "parallel_unit_ids": [],
            "sequential_unit_ids": ["create_submission_minimal_package"],
            "unit_ids": ["create_submission_minimal_package"],
        },
        {
            "wave_index": 4,
            "parallel_unit_ids": [],
            "sequential_unit_ids": ["sync_submission_minimal_delivery"],
            "unit_ids": ["sync_submission_minimal_delivery"],
        },
    ]
    unit_results, _, _ = module._execute_repair_units(
        repair_units=filtered_units,
        latest_batch={},
        paper_root=paper_root,
        gate_report={},
        profile=profile,
    )
    assert [item["status"] for item in unit_results] == ["updated", "updated", "ready", "synced"]


def test_next_work_unit_limits_gate_clearing_batch_to_analysis_repair_without_submission_refresh(
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
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence and paper-facing traceability blockers.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "stale_submission_minimal_authority",
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    materialize_calls: list[Path] = []
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated", "repaired_files": []})
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda *, paper_root: (materialize_calls.append(paper_root), {"status": "materialized"})[1],
    )
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(AssertionError("analysis work unit must not refresh submission_minimal")),
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(AssertionError("analysis work unit must not refresh current_package")),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_submission_minimal_authority"],
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

    assert materialize_calls == [paper_root]
    assert result["repair_unit_execution_plan"]["status"] == "planned"
    assert result["repair_unit_execution_plan"]["parallel_wave_count"] == 2
    assert [item["unit_id"] for item in result["unit_results"]] == [
        "repair_paper_live_paths",
        "materialize_display_surface",
    ]
    assert result["selected_publication_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"


def test_submission_minimal_refresh_skips_current_package_sync_until_authority_settles(
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
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "submission_minimal_refresh",
        "lane": "finalize",
        "summary": "Refresh submission_minimal and then the human-facing current_package.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    gate_report = {
        "status": "blocked",
        "blockers": ["stale_submission_minimal_authority", "stale_study_delivery_mirror"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))

    def fake_create(*, paper_root: Path, profile) -> dict[str, object]:
        _write_text(paper_root / "submission_minimal" / "manuscript.docx", "fresh docx")
        _write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
        _write_json(paper_root / "submission_minimal" / "submission_manifest.json", {"schema_version": 1})
        return {"status": "ready"}

    monkeypatch.setattr(module, "_create_submission_minimal_package", fake_create)
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(AssertionError("unsettled authority must not refresh current_package")),
    )
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_study_delivery_mirror"],
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
    assert result["unit_results"][1]["status"] == "skipped_authority_not_settled"
    assert "authority_fingerprints" in result["unit_results"][1]
    assert result["unit_results"][1]["retry_reason"] == "authority_not_settled"
    assert result["unit_results"][1]["retry_after_seconds"] > 0
    assert result["selected_publication_work_unit"]["lifecycle_status"] == "blocked"
    assert result["selected_publication_work_unit"]["retry"]["reason"] == "authority_not_settled"
    lifecycle_record = json.loads(
        (
            study_root
            / "artifacts"
            / "controller"
            / "publication_work_unit_lifecycle"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert lifecycle_record["status"] == "blocked"
    assert lifecycle_record["retry"]["reason"] == "authority_not_settled"


def test_gate_clearing_batch_records_step_durations_with_monkeypatched_clock(
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
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence and paper-facing traceability blockers.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    clock_values = iter(
        [
            (1_000_000_000, "2026-04-26T00:00:01+00:00"),
            (1_250_000_000, "2026-04-26T00:00:01.250000+00:00"),
            (2_000_000_000, "2026-04-26T00:00:02+00:00"),
            (2_500_000_000, "2026-04-26T00:00:02.500000+00:00"),
            (3_000_000_000, "2026-04-26T00:00:03+00:00"),
            (4_500_000_000, "2026-04-26T00:00:04.500000+00:00"),
        ]
    )

    def fake_clock() -> tuple[int, str]:
        return next(clock_values)

    monkeypatch.setattr(module, "_clock_snapshot", fake_clock)
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
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
            "study_delivery_status": "current",
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated"})
    monkeypatch.setattr(module, "_materialize_display_surface", lambda **_: {"status": "materialized"})
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {"status": "blocked", "allow_write": False, "blockers": ["medical_publication_surface_blocked"]},
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert result["unit_results"][0]["started_at"] == "2026-04-26T00:00:01+00:00"
    assert result["unit_results"][0]["finished_at"] == "2026-04-26T00:00:01.250000+00:00"
    assert result["unit_results"][0]["duration_seconds"] == 0.25
    assert result["unit_results"][1]["duration_seconds"] == 0.5
    assert result["gate_replay_step"]["started_at"] == "2026-04-26T00:00:03+00:00"
    assert result["gate_replay_step"]["finished_at"] == "2026-04-26T00:00:04.500000+00:00"
    assert result["gate_replay_step"]["duration_seconds"] == 1.5


def test_submission_minimal_refresh_syncs_current_package_after_authority_settles(
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
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "submission_minimal_refresh",
        "lane": "finalize",
        "summary": "Refresh submission_minimal and then the human-facing current_package.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    gate_report = {
        "status": "blocked",
        "blockers": ["stale_submission_minimal_authority", "stale_study_delivery_mirror"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS", 0)
    settled_ns = time.time_ns() - module.CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS - 1_000_000_000

    def fake_create(*, paper_root: Path, profile) -> dict[str, object]:
        import os

        for relative_path, content in {
            "manuscript.docx": "settled docx",
            "paper.pdf": "%PDF-1.4\n",
            "submission_manifest.json": '{"schema_version":1}\n',
        }.items():
            target = paper_root / "submission_minimal" / relative_path
            _write_text(target, content)
            os.utime(target, ns=(settled_ns, settled_ns))
        return {"status": "ready"}

    sync_calls: list[Path] = []
    monkeypatch.setattr(module, "_create_submission_minimal_package", fake_create)
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda *, paper_root, profile: (
            sync_calls.append(paper_root),
            {"status": "synced", "current_package_root": str(study_root / "manuscript" / "current_package")},
        )[1],
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

    assert sync_calls == [paper_root]
    assert result["unit_results"][1]["unit_id"] == "sync_submission_minimal_delivery"
    assert result["unit_results"][1]["status"] == "synced"
    assert result["current_package_freshness_proof"]["status"] == "fresh"
    assert result["current_package_freshness_proof"]["source_unit_id"] == "sync_submission_minimal_delivery"
    proof_record = json.loads(
        (
            study_root
            / "artifacts"
            / "controller"
            / "current_package_freshness"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert proof_record["status"] == "fresh"
    assert proof_record["source_eval_id"] == publication_eval_payload["eval_id"]
