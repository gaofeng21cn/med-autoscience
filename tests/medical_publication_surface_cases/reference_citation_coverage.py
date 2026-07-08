from tests.medical_publication_surface_cases.shared import (
    annotations,
    _quest_factory,
    _shared_base,
    importlib,
    json,
    Path,
    SimpleNamespace,
    Any,
    pytest,
    display_registry,
    TIME_TO_EVENT_DIRECT_MIGRATION_DISPLAY_PLAN,
    CHARTER_EXPECTATION_FIXTURES,
    _canonicalize_registry_id,
    full_id,
    _normalize_namespaced_ids,
    dump_json,
    _write_review_ledger,
    _charter_expectation_record,
    _write_charter_expectation_closures,
    _write_study_charter,
    _paper_root_from_quest,
    _copy_medical_writing_authority_surfaces,
    _attach_study_charter_context,
    _attach_public_anchor_study_context,
    _inject_public_data_surface_mentions,
    _write_public_evidence_decisions,
    write_endpoint_provenance_note_fixture,
    default_threshold_renderer_contract,
    write_medical_manuscript_blueprint_fixture,
    write_medical_prose_review_fixture,
    time_to_event_direct_migration,
    _write_time_to_event_direct_migration_surface,
    write_numeric_trace_fixture,
    write_reproducibility_supplement_fixture,
    write_statistical_reviewer_audit_fixture,
    write_structured_disclosure_audit_fixture,
    make_quest,
)


def test_build_report_blocks_when_manuscript_under_cites_reference_database(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = _paper_root_from_quest(quest_root)
    manuscript_path = paper_root / "draft.md"
    manuscript_path.write_text(
        manuscript_path.read_text(encoding="utf-8")
        + "\nThe model was interpreted against prior cardiovascular risk literature [@ref_1; @ref_2; @ref_3; @ref_4; @ref_5; @ref_6; @ref_7; @ref_8].\n",
        encoding="utf-8",
    )
    reference_items = [
        f"@article{{ref_{index},\n  title = {{Reference {index}}},\n  journal = {{Medical Journal}},\n  year = {{2024}}\n}}\n"
        for index in range(1, 24)
    ]
    (paper_root / "references.bib").write_text("\n".join(reference_items), encoding="utf-8")

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "reference_citation_coverage_incomplete" in report["blockers"]
    assert report["reference_citation_coverage"]["bib_entry_count"] == 23
    assert report["reference_citation_coverage"]["cited_key_count"] == 8
    assert any(hit["pattern_id"] == "reference_citation_coverage_low" for hit in report["top_hits"])
