from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_current_authority_stale_delivery_syncs_then_closes_gate_replay(
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
    submission_manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    delivery_manifest_path = study_root / "manuscript" / "delivery_manifest.json"
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_zip = study_root / "manuscript" / "current_package.zip"
    _write_json(submission_manifest_path, {"schema_version": 1})
    _write_text(paper_root / "submission_minimal" / "manuscript.docx", "docx")
    _write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    gate_report = {
        "status": "blocked",
        "blockers": ["stale_study_delivery_mirror"],
        "current_required_action": "complete_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "stale_source_changed",
        "study_delivery_stale_reason": "delivery_manifest_source_changed",
        "submission_minimal_present": True,
        "submission_minimal_docx_present": True,
        "submission_minimal_pdf_present": True,
        "submission_minimal_manifest_path": str(submission_manifest_path),
        "submission_minimal_authority_status": "current",
        "submission_minimal_evaluated_source_signature": "source::abc",
        "submission_minimal_authority_source_signature": "source::abc",
        "study_delivery_manifest_path": str(delivery_manifest_path),
        "study_delivery_current_package_root": str(current_package_root),
        "study_delivery_current_package_zip": str(current_package_zip),
        "gate_fingerprint": "publication-gate::stale-delivery",
        "blocking_artifact_refs": [
            {
                "blocker": "stale_study_delivery_mirror",
                "artifact_path": str(delivery_manifest_path),
                "artifact_role": "study_delivery_mirror",
                "stale_reason": "delivery_manifest_source_changed",
            }
        ],
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
        lambda **_: (_ for _ in ()).throw(
            AssertionError("current authority should sync delivery without rebuilding submission_minimal")
        ),
    )
    monkeypatch.setattr(
        module,
        "_sync_submission_minimal_delivery",
        lambda *, paper_root, profile: (
            sync_calls.append(paper_root),
            {
                "status": "synced",
                "delivery_manifest_path": str(delivery_manifest_path),
                "current_package_root": str(current_package_root),
                "current_package_zip": str(current_package_zip),
                "source_signature": "source::abc",
                "authority_source_signature": "source::abc",
            },
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
    assert [item["unit_id"] for item in result["unit_results"]] == ["sync_submission_minimal_delivery"]
    assert result["selected_publication_work_unit"]["unit_id"] == "publication_gate_replay"
    assert result["stale_gate_replay_closure"]["status"] == "closed"
    assert result["stale_gate_replay_closure"]["closure_reason"] == "stale_study_delivery_mirror_replay_closed"
    proof = result["current_package_freshness_proof"]
    assert proof["status"] == "fresh"
    assert proof["submission_manifest_path"] == str(submission_manifest_path)
    assert proof["delivery_manifest_path"] == str(delivery_manifest_path)
    assert proof["current_package_zip"] == str(current_package_zip)
    assert proof["source_signature"] == "source::abc"
    assert proof["authority_source_signature"] == "source::abc"
    assert proof["gate_fingerprint"] == "publication-gate::stale-delivery"

    publication_eval_payload["eval_id"] = "publication-eval::004-invasive-architecture::quest-004::followup"
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: (_ for _ in ()).throw(AssertionError("closed delivery replay must not run again")),
    )

    skipped = module.run_gate_clearing_batch(
        profile=profile,
        study_id="004-invasive-architecture",
        study_root=study_root,
        quest_id="quest-004",
        source="test-source",
    )

    assert skipped["status"] == "skipped_stale_gate_replay_closed"
    assert skipped["selected_publication_work_unit"]["unit_id"] == "publication_gate_replay"
