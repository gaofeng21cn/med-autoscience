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


def test_build_report_blocks_missing_statistical_reviewer_audit(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_statistical_reviewer_audit=False,
    )

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "statistical_reviewer_audit_missing_or_incomplete" in report["blockers"]
    assert report["statistical_reviewer_audit_present"] is False
    assert report["statistical_reviewer_audit_reason_code"] == "missing_statistical_reviewer_audit"


def test_build_report_blocks_unresolved_statistical_review_domain(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    audit_path = _paper_root_from_quest(quest_root) / "review" / "statistical_reviewer_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["sections"]["sample_size_or_precision"]["status"] = "open"
    audit["sections"]["sample_size_or_precision"]["assessment"] = "Precision support remains unresolved."
    dump_json(audit_path, audit)

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "statistical_reviewer_audit_missing_or_incomplete" in report["blockers"]
    assert report["statistical_reviewer_audit_reason_code"] == "sample_size_or_precision_not_passed"
    assert any(hit["phrase"] == "sample_size_or_precision_not_passed" for hit in report["top_hits"])


def test_build_report_blocks_missing_structured_disclosure_audit(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_disclosure_audit=False,
    )

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "structured_disclosure_audit_missing_or_incomplete" in report["blockers"]
    assert report["structured_disclosure_audit_present"] is False
    assert any(hit["pattern_id"] == "structured_disclosure_audit" for hit in report["top_hits"])


def test_build_report_requires_disclosure_data_asset_evidence(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    audit_path = _paper_root_from_quest(quest_root) / "review" / "structured_disclosure_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["data_asset_evidence"].pop("privacy_evidence")
    dump_json(audit_path, audit)

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "structured_disclosure_audit_missing_or_incomplete" in report["blockers"]
    assert any(
        hit["pattern_id"] == "structured_disclosure_audit" and "privacy_evidence" in hit["excerpt"]
        for hit in report["top_hits"]
    )


def test_build_report_carries_statistical_and_disclosure_audits_when_clear(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["statistical_reviewer_audit_valid"] is True
    assert report["structured_disclosure_audit_valid"] is True
