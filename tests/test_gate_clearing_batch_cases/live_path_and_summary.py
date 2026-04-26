from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_run_gate_clearing_batch_executes_delivery_refresh_fast_lane_for_stale_projection_only(
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
            "current_required_action": "continue_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "stale_projection_missing",
            "study_delivery_stale_reason": "delivery_projection_missing",
            "study_delivery_missing_source_paths": [],
        },
    )
    monkeypatch.setattr(
        module,
        "_eligible_mapping_payload",
        lambda **_: (None, {}),
    )
    sync_calls: list[tuple[str, str, bool]] = []

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
        promote_to_final: bool = False,
    ) -> dict[str, object]:
        sync_calls.append((stage, publication_profile, promote_to_final))
        return {
            "status": "synced",
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        }

    monkeypatch.setattr(
        module.study_delivery_sync,
        "can_sync_study_delivery",
        lambda *, paper_root: True,
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        fake_sync,
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "materialize_submission_delivery_stale_notice",
        lambda **_: (_ for _ in ()).throw(AssertionError("projection-missing should use sync_study_delivery")),
    )
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("stale projection fast lane should not rebuild submission_minimal")
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

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert sync_calls == [("submission_minimal", "general_medical_journal", False)]
    assert [item["unit_id"] for item in result["unit_results"]] == ["sync_submission_minimal_delivery"]
    assert result["unit_results"][0]["status"] == "synced"
    assert result["gate_replay"]["status"] == "clear"
    assert result["gate_blockers"] == ["stale_study_delivery_mirror"]
def test_run_gate_clearing_batch_skips_repair_units_when_unit_fingerprints_match_latest_record(
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
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "materialize_display_surface", "status": "materialized"},
                {"unit_id": "sync_submission_minimal_delivery", "status": "synced"},
            ],
            "unit_fingerprints": {
                "materialize_display_surface": "display-fp",
                "sync_submission_minimal_delivery": "delivery-fp",
            },
            "gate_replay": {
                "status": "blocked",
                "blockers": ["stale_study_delivery_mirror", "medical_publication_surface_blocked"],
            },
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
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
            "blockers": ["stale_study_delivery_mirror", "medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "study_delivery_status": "stale_projection_missing",
            "study_delivery_stale_reason": "delivery_projection_missing",
            "study_delivery_missing_source_paths": [],
        },
    )
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module,
        "_repair_unit_fingerprint",
        lambda *, unit_id, **kwargs: {
            "materialize_display_surface": "display-fp",
            "sync_submission_minimal_delivery": "delivery-fp",
        }.get(unit_id),
    )
    monkeypatch.setattr(
        module,
        "_materialize_display_surface",
        lambda **_: (_ for _ in ()).throw(AssertionError("matching display fingerprint should skip heavy refresh")),
    )
    monkeypatch.setattr(
        module,
        "_repair_paper_live_paths",
        lambda **_: {"ok": True, "status": "updated", "repaired_files": ["paper/live-paths.json"]},
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "can_sync_study_delivery",
        lambda *, paper_root: True,
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "sync_study_delivery",
        lambda **_: (_ for _ in ()).throw(AssertionError("matching delivery fingerprint should skip sync")),
    )
    replay_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **kwargs: (
            replay_calls.append(kwargs),
            {
                "status": "blocked",
                "allow_write": False,
                "blockers": ["stale_study_delivery_mirror"],
                "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            },
        )[1],
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert replay_calls == [
        {
            "quest_root": quest_root,
            "apply": True,
            "source": "test-source",
            "enqueue_intervention": False,
        }
    ]
    assert result["ok"] is True
    result_by_unit = {item["unit_id"]: item for item in result["unit_results"]}
    assert set(result_by_unit) == {
        "repair_paper_live_paths",
        "materialize_display_surface",
        "sync_submission_minimal_delivery",
    }
    assert result_by_unit["materialize_display_surface"]["status"] == "skipped_matching_unit_fingerprint"
    assert result_by_unit["sync_submission_minimal_delivery"]["status"] == "skipped_matching_unit_fingerprint"
    assert result_by_unit["materialize_display_surface"]["fingerprint"] == "display-fp"
    assert result_by_unit["sync_submission_minimal_delivery"]["fingerprint"] == "delivery-fp"
    saved = json.loads(latest_record_path.read_text(encoding="utf-8"))
    assert saved["source_eval_id"] == publication_eval_payload["eval_id"]
    assert saved["unit_fingerprints"] == {
        "materialize_display_surface": "display-fp",
        "sync_submission_minimal_delivery": "delivery-fp",
    }
def test_run_gate_clearing_batch_skips_submission_refresh_only_when_inputs_match_and_previous_run_succeeded(
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
    _write_submission_minimal_fingerprint_inputs(paper_root)
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    matching_gate_report = {
        "status": "blocked",
        "blockers": ["stale_study_delivery_mirror"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
    }
    matching_fingerprint = module._repair_unit_fingerprint(
        unit_id="create_submission_minimal_package",
        paper_root=paper_root,
        gate_report=matching_gate_report,
        profile=profile,
    )
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
            ],
            "unit_fingerprints": {
                "create_submission_minimal_package": matching_fingerprint,
            },
        },
    )
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(matching_gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("matching submission fingerprint plus previous success should skip heavy rebuild")
        ),
    )
    sync_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda *, paper_root, profile: (
            sync_calls.append(paper_root),
            {"status": "synced", "current_package_root": "studies/004-invasive-architecture/manuscript/current_package"},
        )[1],
    )
    replay_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **kwargs: (
            replay_calls.append(kwargs),
            {
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "report_json": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            },
        )[1],
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    result_by_unit = {item["unit_id"]: item for item in result["unit_results"]}
    assert result_by_unit["create_submission_minimal_package"]["status"] == "skipped_matching_unit_fingerprint"
    assert result_by_unit["create_submission_minimal_package"]["fingerprint"] == matching_fingerprint
    assert result_by_unit["create_submission_minimal_package"]["last_success_status"] == "ok"
    assert result_by_unit["sync_submission_minimal_delivery"]["status"] == "synced"
    assert sync_calls == [paper_root]
    assert replay_calls == [
        {
            "quest_root": quest_root,
            "apply": True,
            "source": "test-source",
            "enqueue_intervention": False,
        }
    ]
def test_run_gate_clearing_batch_reruns_submission_refresh_when_previous_matching_run_failed(
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
    _write_submission_minimal_fingerprint_inputs(paper_root)
    gate_report = {
        "status": "blocked",
        "blockers": ["submission_surface_qc_failure_present"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
    }
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    matching_fingerprint = module._repair_unit_fingerprint(
        unit_id="create_submission_minimal_package",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "failed"},
            ],
            "unit_fingerprints": {
                "create_submission_minimal_package": matching_fingerprint,
            },
        },
    )
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    rebuild_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda *, paper_root, profile: (rebuild_calls.append(paper_root), {"status": "ready"})[1],
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

    assert rebuild_calls == [paper_root]
    assert result["unit_results"][0]["unit_id"] == "create_submission_minimal_package"
    assert result["unit_results"][0]["status"] == "ready"
def test_run_gate_clearing_batch_reruns_submission_refresh_when_quality_inputs_change(
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
    _write_submission_minimal_fingerprint_inputs(paper_root)
    gate_report = {
        "status": "blocked",
        "blockers": ["submission_surface_qc_failure_present"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
    }
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    previous_fingerprint = module._repair_unit_fingerprint(
        unit_id="create_submission_minimal_package",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
            ],
            "unit_fingerprints": {
                "create_submission_minimal_package": previous_fingerprint,
            },
        },
    )
    _write_text(paper_root / "build" / "compiled_manuscript.md", "# Results\n\nUpdated content changes the submission package.\n")
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    rebuild_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda *, paper_root, profile: (rebuild_calls.append(paper_root), {"status": "ready"})[1],
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

    assert rebuild_calls == [paper_root]
    assert result["unit_results"][0]["unit_id"] == "create_submission_minimal_package"
    assert result["unit_results"][0]["status"] == "ready"
def test_run_gate_clearing_batch_reruns_submission_refresh_when_submission_outputs_disappear(
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
    _write_submission_minimal_fingerprint_inputs(paper_root)
    _write_text(paper_root / "submission_minimal" / "manuscript.docx", "docx placeholder")
    _write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
    _write_json(
        paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )
    gate_report = {
        "status": "blocked",
        "blockers": ["submission_surface_qc_failure_present"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
    }
    latest_record_path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    previous_fingerprint = module._repair_unit_fingerprint(
        unit_id="create_submission_minimal_package",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    _write_json(
        latest_record_path,
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::004-invasive-architecture::quest-004::2026-04-21T12:42:39+00:00",
            "status": "executed",
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
            ],
            "unit_fingerprints": {
                "create_submission_minimal_package": previous_fingerprint,
            },
        },
    )
    (paper_root / "submission_minimal" / "paper.pdf").unlink()
    (paper_root / "submission_minimal" / "submission_manifest.json").unlink()
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    rebuild_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda *, paper_root, profile: (rebuild_calls.append(paper_root), {"status": "ready"})[1],
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

    assert rebuild_calls == [paper_root]
    assert result["unit_results"][0]["unit_id"] == "create_submission_minimal_package"
    assert result["unit_results"][0]["status"] == "ready"
def test_run_gate_clearing_batch_rebuilds_submission_minimal_when_delivery_surface_reports_missing_source(
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
    _write_submission_minimal_fingerprint_inputs(paper_root)
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::2026-04-22T12:42:39+00:00"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    gate_report = {
        "status": "blocked",
        "blockers": ["stale_study_delivery_mirror"],
        "current_required_action": "return_to_publishability_gate",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "stale_source_missing",
        "study_delivery_stale_reason": "current_submission_source_missing",
        "submission_minimal_present": False,
        "submission_minimal_docx_present": False,
        "submission_minimal_pdf_present": False,
        "submission_minimal_manifest_path": None,
        "submission_minimal_authority_status": "not_applicable",
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    rebuild_calls: list[Path] = []
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda *, paper_root, profile: (rebuild_calls.append(paper_root), {"status": "ready"})[1],
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

    assert rebuild_calls == [paper_root]
    assert result["unit_results"][0]["unit_id"] == "create_submission_minimal_package"
    assert result["unit_results"][0]["status"] == "ready"


def test_study_outer_loop_executes_gate_clearing_batch_controller_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    runtime_protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"

    _write_json(
        study_root / "artifacts" / "controller" / "study_charter.json",
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-21T12:42:39+00:00",
                "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_resolve_runtime_escalation_record",
        lambda **_: (
            runtime_protocol.RuntimeEscalationRecordRef(
                record_id="runtime-escalation::001-risk::quest-001::publication_quality_gap::2026-04-21T12:42:39+00:00",
                artifact_path=str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            ),
            None,
        ),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **kwargs: (
            seen.setdefault("batch_kwargs", kwargs),
            {"ok": True, "status": "executed"},
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref={
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        publication_eval_ref={
            "eval_id": publication_eval_payload["eval_id"],
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        decision_type="bounded_analysis",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Gate-clearing batch should run before resuming the same study line.",
        source="test-source",
        recorded_at="2026-04-21T12:45:00+00:00",
    )

    assert seen["batch_kwargs"] == {
        "profile": profile,
        "study_id": "001-risk",
        "study_root": study_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert result["executed_controller_action"]["action_type"] == "run_gate_clearing_batch"
    assert result["executed_controller_action"]["result"] == {"ok": True, "status": "executed"}
