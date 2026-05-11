from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_deterministic_quality_gates_project_five_gate_classes_without_authorizing_quality(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="blocked",
        medical_publication_surface_report={
            "blockers": [
                "claim_evidence_map_missing_or_incomplete",
                "statistical_reporting_incomplete",
                "figure_catalog_missing_or_incomplete",
                "forbidden_manuscript_terms_present",
            ],
            "claim_evidence_map_valid": False,
            "structured_reporting_checklist": {
                "claim_evidence_alignment": {"status": "blocked"},
                "statistical_reporting": {"status": "blocked"},
            },
        },
        manuscript_files={
            "build/review_manuscript.md": "The paper-facing analysis used the locked v2026-03-31 dataset.\n",
        },
    )

    report = module.build_gate_report(module.build_gate_state(quest_root))
    gates = report["deterministic_quality_gates"]

    assert gates["surface"] == "deterministic_quality_gate_projection"
    assert gates["authority"]["deterministic_projection_can_replace_ai_reviewer"] is False
    assert set(gates["gates"]) == {
        "citation_grounding",
        "numeric_grounding",
        "display_grounding",
        "internal_language_leakage",
        "artifact_rebuild_proof",
    }
    assert "citation_grounding" in gates["blocking_gate_keys"]
    assert "numeric_grounding" in gates["blocking_gate_keys"]
    assert "display_grounding" in gates["blocking_gate_keys"]
    assert "internal_language_leakage" in gates["blocking_gate_keys"]
    assert "artifact_rebuild_proof" in gates["blocking_gate_keys"]
    assert "claim_evidence_map_missing_or_incomplete" in gates["gates"]["citation_grounding"]["blockers"]
    assert "statistical_reporting_incomplete" in gates["gates"]["numeric_grounding"]["blockers"]
    assert "figure_catalog_missing_or_incomplete" in gates["gates"]["display_grounding"]["blockers"]
    assert "forbidden_manuscript_terminology" in gates["gates"]["internal_language_leakage"]["blockers"]
    assert "delivery_manifest_missing" in gates["gates"]["artifact_rebuild_proof"]["blockers"]


def test_deterministic_quality_gates_keep_clear_projection_separate_from_ai_review(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="clear",
        medical_publication_surface_report={
            "claim_evidence_map_valid": True,
            "evidence_ledger_valid": True,
            "structured_reporting_checklist": {
                "claim_evidence_alignment": {"status": "pass"},
                "statistical_reporting": {"status": "pass"},
            },
        },
    )

    study_root = tmp_path / "studies" / "002-early-residual-risk"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    dump_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [
                {
                    "citation_key": "ref1",
                    "source_kind": "doi",
                    "doi": "10.1000/ref1",
                }
            ],
        },
    )
    source_root = paper_root / "build"
    source_refs = ["review_manuscript.md"]
    artifact_proof = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    source_signature, _entries, _missing = artifact_proof._source_signature(
        study_root=study_root,
        source_root=source_root,
        paper_root=paper_root,
        source_refs=source_refs,
    )
    dump_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "schema_version": 1,
            "source_signature": source_signature,
            "authority_source_signature": source_signature,
            "source_relative_paths": source_refs,
            "source": {"paper_root": str(paper_root.resolve())},
            "surface_roles": {
                "controller_authorized_paper_root": str(paper_root.resolve()),
                "controller_authorized_package_source_root": str(source_root.resolve()),
            },
            "blocking_artifact_refs": [],
        },
    )

    report = module.build_gate_report(module.build_gate_state(quest_root))
    gates = report["deterministic_quality_gates"]

    assert gates["status"] == "clear"
    assert gates["blocking_gate_keys"] == []
    assert all(gate["status"] == "clear" for gate in gates["gates"].values())
    assert gates["authority"] == {
        "deterministic_projection_can_replace_ai_reviewer": False,
        "scientific_quality_authority": "publication_eval_and_controller_decisions",
    }


def test_deterministic_quality_gates_include_medical_literature_hygiene_evidence(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="clear",
        medical_publication_surface_report={
            "claim_evidence_map_valid": True,
            "evidence_ledger_valid": True,
            "structured_reporting_checklist": {
                "claim_evidence_alignment": {"status": "pass"},
                "statistical_reporting": {"status": "pass"},
            },
        },
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    write_text(
        paper_root / "build" / "review_manuscript.md",
        "The manuscript cites one unsupported reference [@ref1].\n",
    )
    dump_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [
                {
                    "citation_key": "ref1",
                    "source_kind": "local_note",
                }
            ],
        },
    )

    report = module.build_gate_report(module.build_gate_state(quest_root))
    citation_gate = report["deterministic_quality_gates"]["gates"]["citation_grounding"]
    hygiene_ref = citation_gate["evidence_refs"][0]["medical_literature_hygiene"]

    assert "unsupported_citation_blockers_present" in citation_gate["blockers"]
    assert hygiene_ref["surface"] == "medical_literature_hygiene_projection"
    assert hygiene_ref["authority"] == {
        "can_replace_medical_literature_review": False,
        "can_authorize_publication_quality": False,
    }


def test_literature_hygiene_blocker_keeps_publication_gate_blocked(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(
        module.study_delivery_sync,
        "can_sync_study_delivery",
        lambda *, paper_root: False,
    )
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_status="clear",
        medical_publication_surface_report={
            "claim_evidence_map_valid": True,
            "evidence_ledger_valid": True,
            "structured_reporting_checklist": {
                "claim_evidence_alignment": {"status": "pass"},
                "statistical_reporting": {"status": "pass"},
            },
        },
        manuscript_files={
            "build/review_manuscript.md": "The manuscript cites the registry source [@ref1].\n",
        },
    )
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    dump_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [],
        },
    )
    authority = module.submission_minimal.describe_submission_minimal_authority(paper_root=paper_root)
    manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_signature"] = authority["source_signature"]
    manifest["source_contract"] = {"source_signature": authority["source_signature"]}
    dump_json(manifest_path, manifest)
    artifact_proof = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    source_root = paper_root / "build"
    source_refs = ["review_manuscript.md"]
    source_signature, _entries, _missing = artifact_proof._source_signature(
        study_root=study_root,
        source_root=source_root,
        paper_root=paper_root,
        source_refs=source_refs,
    )
    dump_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "schema_version": 1,
            "source_signature": source_signature,
            "authority_source_signature": source_signature,
            "source_relative_paths": source_refs,
            "source": {"paper_root": str(paper_root.resolve())},
            "surface_roles": {
                "controller_authorized_paper_root": str(paper_root.resolve()),
                "controller_authorized_package_source_root": str(source_root.resolve()),
            },
            "blocking_artifact_refs": [],
        },
    )

    report = module.build_gate_report(module.build_gate_state(quest_root))
    gates = report["deterministic_quality_gates"]
    citation_gate = gates["gates"]["citation_grounding"]

    assert gates["status"] == "blocked"
    assert gates["blocking_gate_keys"] == ["citation_grounding"]
    assert citation_gate["blockers"] == ["citation_key_sync_failed"]
    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["recommended_action"] == "return_to_publishability_gate"
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["blockers"] == ["citation_key_sync_failed"]

    work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    route = work_units.derive_publication_work_units(report)

    assert route["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
