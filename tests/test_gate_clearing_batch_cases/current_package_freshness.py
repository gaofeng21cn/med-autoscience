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
    quest_root = profile.managed_runtime_home / "quests" / "quest-004"
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
    assert result["selected_publication_work_unit"]["unit_id"] == "submission_delivery_sync_closure"
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
    assert skipped["selected_publication_work_unit"]["unit_id"] == "submission_delivery_sync_closure"


def test_explicit_gate_specificity_does_not_block_actionable_stale_delivery_sync(
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
    submission_manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    delivery_manifest_path = study_root / "manuscript" / "delivery_manifest.json"
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_zip = study_root / "manuscript" / "current_package.zip"
    _write_json(submission_manifest_path, {"schema_version": 1})
    _write_text(paper_root / "submission_minimal" / "manuscript.docx", "docx")
    _write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"][0]["work_unit_fingerprint"] = (
        "publication-blockers::delivery-specificity"
    )
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete package-artifact targets.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
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
            AssertionError("delivery-only stale mirror must not rebuild submission_minimal")
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
    assert result["status"] == "executed"
    assert result.get("terminal_state") != "gate_needs_specificity"
    assert [item["unit_id"] for item in result["unit_results"]] == ["sync_submission_minimal_delivery"]
    assert result["selected_publication_work_unit"]["unit_id"] == "submission_delivery_sync_closure"
    assert result["current_package_freshness_proof"]["status"] == "fresh"


def test_blocked_delivery_sync_clears_stale_current_package_freshness_proof(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_package_freshness")
    study_root = tmp_path / "study"
    proof_path = module.stable_current_package_freshness_path(study_root=study_root)
    _write_json(
        proof_path,
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": "publication-eval::old",
            "source_unit_id": "sync_submission_minimal_delivery",
            "unit_status": "skipped_matching_unit_fingerprint",
            "submission_manifest_path": "/tmp/old/submission_manifest.json",
            "current_package_zip": "/tmp/old/current_package.zip",
            "source_signature": "source::old",
            "authority_source_signature": "source::old",
            "proof_path": str(proof_path),
        },
    )

    proof = module.write_current_package_freshness_proof(
        study_root=study_root,
        source_eval_id="publication-eval::new",
        gate_report={
            "gate_fingerprint": "publication-gate::blocked-delivery",
            "blockers": ["stale_study_delivery_mirror"],
        },
        unit_results=[
            {
                "unit_id": "sync_submission_minimal_delivery",
                "status": "control_plane_route_blocked",
                "result": {
                    "status": "control_plane_route_blocked",
                    "control_plane_route_gate": {
                        "blocking_reasons": ["control_plane_snapshot_missing"],
                    },
                },
            }
        ],
        clock=lambda: (0, "2026-05-03T16:40:00+00:00"),
        schema_version=1,
    )

    assert proof is None
    assert not proof_path.exists()


def test_current_delivery_gate_report_writes_freshness_proof_without_resync(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_package_freshness")
    study_root = tmp_path / "study"
    proof = module.write_current_package_freshness_proof(
        study_root=study_root,
        source_eval_id="publication-eval::current-delivery",
        gate_report={
            "gate_fingerprint": "publication-gate::current-delivery",
            "study_delivery_status": "current",
            "submission_minimal_manifest_path": "/tmp/study/paper/submission_minimal/audit/submission_manifest.json",
            "study_delivery_manifest_path": "/tmp/study/manuscript/delivery_manifest.json",
            "study_delivery_current_package_root": "/tmp/study/manuscript/current_package",
            "study_delivery_current_package_zip": "/tmp/study/manuscript/current_package.zip",
            "study_delivery_evaluated_source_signature": "delivery::abc",
            "study_delivery_authority_source_signature": "delivery::abc",
        },
        unit_results=[],
        clock=lambda: (0, "2026-05-10T10:10:00+00:00"),
        schema_version=1,
    )

    assert proof is not None
    assert proof["status"] == "fresh"
    assert proof["source_unit_id"] == "publication_gate_current_delivery"
    assert proof["source_signature"] == "delivery::abc"
    assert proof["authority_source_signature"] == "delivery::abc"
    assert proof["current_package_zip"] == "/tmp/study/manuscript/current_package.zip"
    assert module.stable_current_package_freshness_path(study_root=study_root).is_file()


def test_gate_clearing_batch_prefers_replay_report_for_current_delivery_freshness(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    report_path = tmp_path / "publishability_gate" / "latest.json"
    _write_json(
        report_path,
        {
            "status": "clear",
            "study_delivery_status": "current",
            "submission_minimal_manifest_path": "/tmp/study/paper/submission_minimal/audit/submission_manifest.json",
            "study_delivery_manifest_path": "/tmp/study/manuscript/delivery_manifest.json",
            "study_delivery_current_package_root": "/tmp/study/manuscript/current_package",
            "study_delivery_current_package_zip": "/tmp/study/manuscript/current_package.zip",
            "study_delivery_evaluated_source_signature": "delivery::replay",
            "study_delivery_authority_source_signature": "delivery::replay",
        },
    )

    payload = module._freshness_gate_report_payload(
        gate_report={"status": "blocked", "study_delivery_status": "stale_source_changed"},
        gate_replay={"status": "clear", "report_json": str(report_path)},
    )

    assert payload["study_delivery_status"] == "current"
    assert payload["study_delivery_current_package_zip"] == "/tmp/study/manuscript/current_package.zip"
    assert payload["study_delivery_evaluated_source_signature"] == "delivery::replay"


def test_closed_gate_clearing_batch_backfills_missing_freshness_proof_from_replay_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    study_root = tmp_path / "study"
    report_path = tmp_path / "publishability_gate" / "latest.json"
    _write_json(
        report_path,
        {
            "status": "clear",
            "study_delivery_status": "current",
            "submission_minimal_manifest_path": "/tmp/study/paper/submission_minimal/audit/submission_manifest.json",
            "study_delivery_manifest_path": "/tmp/study/manuscript/delivery_manifest.json",
            "study_delivery_current_package_root": "/tmp/study/manuscript/current_package",
            "study_delivery_current_package_zip": "/tmp/study/manuscript/current_package.zip",
            "study_delivery_evaluated_source_signature": "delivery::closed",
            "study_delivery_authority_source_signature": "delivery::closed",
        },
    )

    proof = module._closed_batch_current_freshness_proof(
        latest_batch={
            "status": "executed",
            "gate_replay": {"status": "clear", "report_json": str(report_path)},
        },
        study_root=study_root,
        source_eval_id="publication-eval::closed",
    )

    assert proof is not None
    assert proof["status"] == "fresh"
    assert proof["source_unit_id"] == "publication_gate_current_delivery"
    assert proof["source_signature"] == "delivery::closed"
    assert (
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json"
    ).is_file()
