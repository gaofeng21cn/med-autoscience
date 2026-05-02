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
