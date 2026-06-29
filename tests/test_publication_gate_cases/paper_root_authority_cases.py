from __future__ import annotations

from .shared import *


def test_build_gate_state_prefers_complete_bound_study_canonical_paper_when_branch_differs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        include_submission_authority_inputs=False,
    )
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    study_paper_root = study_root / "paper"
    dump_json(worktree_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/old"})
    dump_json(study_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "main"})
    write_text(study_paper_root / "draft.md", "# Draft\n\nJournal-style manuscript.\n")
    dump_json(study_paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    dump_json(study_paper_root / "medical_prose_review.json", {"schema_version": 1})
    dump_json(study_paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(study_paper_root / "results_narrative_map.json", {"schema_version": 1})
    dump_json(study_paper_root / "figure_semantics_manifest.json", {"schema_version": 1})
    dump_json(study_paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(study_paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})

    state = module.build_gate_state(quest_root)

    assert state.paper_bundle_manifest_path == study_paper_root.resolve() / "paper_bundle_manifest.json"
    assert state.paper_root == study_paper_root.resolve()
    assert state.study_root == study_root.resolve()


def test_build_gate_state_falls_back_to_stage_native_body_authority_without_projected_bundle(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        include_submission_authority_inputs=False,
    )
    projected_manifest = quest_root / "paper" / "paper_bundle_manifest.json"
    if projected_manifest.exists():
        projected_manifest.unlink()
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    stage_native_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    dump_json(stage_native_paper_root / "paper_bundle_manifest.json", {"schema_version": 1})
    write_text(stage_native_paper_root / "draft.md", "# Draft\n\nStage-native manuscript.\n")
    dump_json(stage_native_paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "medical_prose_review.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "results_narrative_map.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "figure_semantics_manifest.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(stage_native_paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    source_root = stage_native_paper_root / "submission_minimal"
    write_text(source_root / "manuscript.docx", "docx")
    write_text(source_root / "paper.pdf", "%PDF")
    dump_json(
        source_root / "audit" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_root == stage_native_paper_root.resolve()
    assert state.submission_minimal_manifest_path == source_root.resolve() / "audit" / "submission_manifest.json"
    assert report["paper_root"] == str(stage_native_paper_root.resolve())
    assert report["submission_minimal_present"] is True


def test_build_gate_state_prefers_stage_native_body_authority_for_direct_study_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    study_root = tmp_path / "studies" / "003-stage-native"
    write_text(study_root / "study.yaml", "study_id: 003-stage-native\n")
    stage_native_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    legacy_paper_root = study_root / "paper"
    dump_json(legacy_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "legacy"})
    dump_json(stage_native_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "current"})
    write_text(stage_native_paper_root / "draft.md", "# Draft\n\nStage-native manuscript.\n")
    dump_json(stage_native_paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "medical_prose_review.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "results_narrative_map.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "figure_semantics_manifest.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(stage_native_paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    source_root = stage_native_paper_root / "submission_minimal"
    write_text(source_root / "manuscript.docx", "docx")
    write_text(source_root / "paper.pdf", "%PDF")
    dump_json(
        source_root / "audit" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )

    state = module.build_gate_state(study_root)
    report = module.build_gate_report(state)

    assert state.paper_root == stage_native_paper_root.resolve()
    assert state.submission_minimal_manifest_path == source_root.resolve() / "audit" / "submission_manifest.json"
    assert report["paper_root"] == str(stage_native_paper_root.resolve())
    assert report["submission_minimal_present"] is True


def test_build_gate_state_uses_stage_native_manifest_and_publication_surface_for_direct_study_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    study_root = tmp_path / "studies" / "003-stage-native"
    write_text(study_root / "study.yaml", "study_id: 003-stage-native\n")
    stage_native_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    legacy_paper_root = study_root / "paper"
    dump_json(legacy_paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "legacy"})
    dump_json(
        stage_native_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "current",
            "compile_report_path": "paper/build/compile_report.json",
        },
    )
    dump_json(
        stage_native_paper_root / "build" / "compile_report.json",
        {
            "status": "passed",
            "source_markdown_path": "paper/draft.md",
            "docx_path": "paper/submission_minimal/manuscript.docx",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        },
    )
    dump_json(
        stage_native_paper_root / "medical_publication_surface.json",
        {
            "schema_version": "general_medical_journal_surface_v1",
            "status": "ready",
            "blockers": [],
        },
    )
    write_text(stage_native_paper_root / "draft.md", "# Draft\n\nStage-native manuscript.\n")
    dump_json(stage_native_paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "medical_prose_review.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "results_narrative_map.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "figure_semantics_manifest.json", {"schema_version": 1})
    dump_json(stage_native_paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(stage_native_paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    source_root = stage_native_paper_root / "submission_minimal"
    write_text(source_root / "manuscript.docx", "docx")
    write_text(source_root / "paper.pdf", "%PDF")
    dump_json(
        source_root / "audit" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
            "manuscript": {
                "source_markdown_path": "paper/draft.md",
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )

    state = module.build_gate_state(study_root)
    report = module.build_gate_report(state)

    assert state.paper_root == stage_native_paper_root.resolve()
    assert state.paper_bundle_manifest_path == stage_native_paper_root.resolve() / "paper_bundle_manifest.json"
    assert state.compile_report_path == stage_native_paper_root.resolve() / "build" / "compile_report.json"
    assert state.compile_report == {
        "status": "passed",
        "source_markdown_path": "paper/draft.md",
        "docx_path": "paper/submission_minimal/manuscript.docx",
        "pdf_path": "paper/submission_minimal/paper.pdf",
    }
    assert state.latest_medical_publication_surface_path == (
        stage_native_paper_root.resolve() / "medical_publication_surface.json"
    )
    assert state.latest_medical_publication_surface == {
        "schema_version": "general_medical_journal_surface_v1",
        "status": "ready",
        "blockers": [],
    }
    assert state.submission_minimal_docx_present is True
    assert state.submission_minimal_pdf_present is True
    assert "missing_paper_compile_report" not in report["blockers"]
    assert "missing_current_medical_publication_surface_report" not in report["blockers"]


def test_build_gate_state_ignores_recursive_compile_report_path_in_bound_study_manifest(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=False,
        include_main_result=False,
        include_submission_authority_inputs=False,
    )
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    study_paper_root = study_root / "paper"
    repeated_compile_path = (
        "studies/002-early-residual-risk/paper/"
        "studies/002-early-residual-risk/paper/"
        "build/compile_report.json"
    )
    dump_json(
        study_paper_root / "paper_bundle_manifest.json",
        {"schema_version": 1, "paper_branch": "main", "compile_report_path": repeated_compile_path},
    )
    dump_json(study_paper_root / "compile_report.json", {"status": "compiled"})
    write_text(study_paper_root / "draft.md", "# Draft\n\nJournal-style manuscript.\n")
    dump_json(study_paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    dump_json(study_paper_root / "medical_prose_review.json", {"schema_version": 1})
    dump_json(study_paper_root / "claim_evidence_map.json", {"schema_version": 1})
    dump_json(study_paper_root / "results_narrative_map.json", {"schema_version": 1})
    dump_json(study_paper_root / "figure_semantics_manifest.json", {"schema_version": 1})
    dump_json(study_paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(study_paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})

    state = module.build_gate_state(quest_root)

    assert state.compile_report_path == study_paper_root.resolve() / "compile_report.json"
    assert state.compile_report == {"status": "compiled"}
