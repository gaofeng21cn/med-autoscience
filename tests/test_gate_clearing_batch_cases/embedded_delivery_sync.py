from __future__ import annotations

from . import shared as _shared

globals().update({name: value for name, value in vars(_shared).items() if not name.startswith("__")})


def test_submission_minimal_refresh_reuses_embedded_delivery_sync_for_freshness_proof(
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-004"
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
        "blockers": ["submission_surface_qc_failure_present"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
        "gate_fingerprint": "publication-gate::embedded-delivery",
    }

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS", 0)
    monkeypatch.setattr(
        module,
        "_create_submission_minimal_package",
        lambda **_: {
            "status": "ready",
            "delivery_sync": {
                "status": "synced",
                "delivery_manifest_path": str(study_root / "manuscript" / "delivery_manifest.json"),
                "current_package_root": str(study_root / "manuscript" / "current_package"),
                "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
                "source_signature": "source::embedded",
                "authority_source_signature": "source::embedded",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda **_: (_ for _ in ()).throw(AssertionError("embedded delivery sync should be reused")),
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
    assert result["unit_results"][1]["reused_embedded_delivery_sync"] is True
    assert result["current_package_freshness_proof"]["status"] == "fresh"
    assert result["current_package_freshness_proof"]["source_signature"] == "source::embedded"
