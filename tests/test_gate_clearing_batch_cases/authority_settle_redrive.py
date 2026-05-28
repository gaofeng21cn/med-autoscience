from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_authority_settle_redrive_syncs_delivery_without_recreating_package(
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
    quest_id = "quest-004"
    paper_root = (
        profile.managed_runtime_home
        / "quests"
        / quest_id
        / ".ds"
        / "worktrees"
        / "paper-run-004"
        / "paper"
    )
    for relative_path, content in {
        "submission_manifest.json": '{"schema_version":1}\n',
        "manuscript.docx": "settled docx",
        "paper.pdf": "%PDF-1.4\n",
    }.items():
        _write_text(paper_root / "submission_minimal" / relative_path, content)
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["eval_id"] = (
        "publication-eval::004-invasive-architecture::quest-004::2026-05-02T17:56:00+00:00"
    )
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask gate for specific blocker objects.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_json(
        module.stable_gate_clearing_batch_path(study_root=study_root),
        {
            "schema_version": 1,
            "source_eval_id": (
                "publication-eval::004-invasive-architecture::quest-004::2026-05-02T17:55:00+00:00"
            ),
            "selected_publication_work_unit": {
                "unit_id": "gate_needs_specificity",
                "retry": {
                    "reason": "authority_not_settled",
                    "retry_after": "2026-05-02T17:55:30+00:00",
                    "retry_after_seconds": 5,
                },
            },
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
                {
                    "unit_id": "sync_submission_minimal_delivery",
                    "status": "skipped_authority_not_settled",
                    "retry_reason": "authority_not_settled",
                    "retry_after": "2026-05-02T17:55:30+00:00",
                    "retry_after_seconds": 5,
                },
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "reviewer_first_concerns_unresolved",
            "claim_evidence_consistency_failed",
            "submission_hardening_incomplete",
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "blocked",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
        "submission_minimal_present": True,
        "submission_minimal_docx_present": True,
        "submission_minimal_pdf_present": True,
        "submission_minimal_manifest_path": str(paper_root / "submission_minimal" / "submission_manifest.json"),
        "submission_minimal_authority_status": "current",
    }
    sync_calls: list[Path] = []

    monkeypatch.setattr(module, "CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS", 0)
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(AssertionError("settled redrive must not recreate package")),
    )
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
            "status": "blocked",
            "allow_write": False,
            "blockers": [
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
                "submission_surface_qc_failure_present",
            ],
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert sync_calls == [paper_root]
    assert [item["unit_id"] for item in result["unit_results"]] == ["sync_submission_minimal_delivery"]
    assert result["unit_results"][0]["status"] == "synced"
    assert result["selected_publication_work_unit"]["unit_id"] == "submission_delivery_sync_closure"


def test_authority_settle_redrive_syncs_delivery_for_bundle_stage_retry_without_delivery_status(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    quest_id = "quest-003"
    paper_root = (
        profile.managed_runtime_home
        / "quests"
        / quest_id
        / ".ds"
        / "worktrees"
        / "paper-run-003"
        / "paper"
    )
    for relative_path, content in {
        "submission_manifest.json": '{"schema_version":1}\n',
        "manuscript.docx": "settled docx",
        "paper.pdf": "%PDF-1.4\n",
    }.items():
        _write_text(paper_root / "submission_minimal" / relative_path, content)
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["eval_id"] = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::quest-003::2026-05-28T08:23:46+00:00"
    )
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "submission_minimal_refresh",
        "lane": "controller",
        "summary": "Refresh submission-minimal package and delivery freshness.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_json(
        module.stable_gate_clearing_batch_path(study_root=study_root),
        {
            "schema_version": 1,
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::quest-003::2026-05-28T08:23:46+00:00"
            ),
            "selected_publication_work_unit": {
                "unit_id": "submission_minimal_refresh",
                "retry": {
                    "reason": "authority_not_settled",
                    "retry_after": "2026-05-28T08:23:51+00:00",
                    "retry_after_seconds": 5,
                },
            },
            "unit_results": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
                {
                    "unit_id": "sync_submission_minimal_delivery",
                    "status": "skipped_authority_not_settled",
                    "retry_reason": "authority_not_settled",
                    "retry_after": "2026-05-28T08:23:51+00:00",
                    "retry_after_seconds": 5,
                },
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
        ],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "blocked",
        "draft_handoff_delivery_status": "stale",
        "submission_minimal_present": True,
        "submission_minimal_docx_present": True,
        "submission_minimal_pdf_present": True,
        "submission_minimal_manifest_path": str(paper_root / "submission_minimal" / "submission_manifest.json"),
        "submission_minimal_authority_status": "current",
    }
    sync_calls: list[Path] = []

    monkeypatch.setattr(module, "CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS", 0)
    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: (_ for _ in ()).throw(AssertionError("settled retry must not recreate package")),
    )
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
            "status": "blocked",
            "allow_write": False,
            "blockers": [
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
            ],
        },
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
    )

    assert sync_calls == [paper_root]
    assert [item["unit_id"] for item in result["unit_results"]] == ["sync_submission_minimal_delivery"]
    assert result["unit_results"][0]["status"] == "synced"
    assert result["selected_publication_work_unit"]["unit_id"] == "submission_delivery_sync_closure"
