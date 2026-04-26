from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


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
