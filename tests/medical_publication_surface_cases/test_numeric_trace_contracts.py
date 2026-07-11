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


def test_build_report_projects_numeric_trace(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["numeric_trace_present"] is True
    assert report["numeric_trace_valid"] is True


def test_write_surface_files_materializes_domain_report(tmp_path: Path) -> None:
    controller = importlib.import_module("med_autoscience.controllers.medical_publication_surface.controller")
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    json_path, markdown_path = controller.write_surface_files(quest_root, report)

    report_root = quest_root / "artifacts" / "reports" / "medical_publication_surface"
    assert json.loads(json_path.read_text(encoding="utf-8")) == report
    assert (report_root / "latest.json").read_text(encoding="utf-8") == json_path.read_text(encoding="utf-8")
    assert (report_root / "latest.md").read_text(encoding="utf-8") == markdown_path.read_text(encoding="utf-8")


def test_validate_claim_evidence_map_accepts_optional_numeric_trace_refs() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_claim_evidence_map(
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The cohort included 312 eligible patients.",
                    "status": "supported",
                    "paper_role": "main_text",
                    "display_bindings": ["T1"],
                    "sections": ["results"],
                    "evidence_items": [
                        {
                            "item_id": "EV1",
                            "support_level": "direct",
                            "source_paths": ["paper/tables/T1_baseline.csv"],
                            "numeric_trace_refs": ["NT1"],
                        }
                    ],
                }
            ]
        }
    )

    assert errors == []


@pytest.mark.parametrize("numeric_trace_refs", [[], ["NT1", ""], "NT1"])
def test_validate_claim_evidence_map_rejects_invalid_numeric_trace_refs(numeric_trace_refs: object) -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_claim_evidence_map(
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The cohort included 312 eligible patients.",
                    "status": "supported",
                    "paper_role": "main_text",
                    "display_bindings": ["T1"],
                    "sections": ["results"],
                    "evidence_items": [
                        {
                            "item_id": "EV1",
                            "support_level": "direct",
                            "source_paths": ["paper/tables/T1_baseline.csv"],
                            "numeric_trace_refs": numeric_trace_refs,
                        }
                    ],
                }
            ]
        }
    )

    assert errors == [
        "claims[0].evidence_items[0].numeric_trace_refs must contain at least one non-empty string"
    ]


def test_build_report_blocks_missing_numeric_trace(tmp_path: Path) -> None:
    reporting = importlib.import_module("med_autoscience.controllers.medical_publication_surface.reporting")
    shared_base = importlib.import_module("med_autoscience.controllers.medical_publication_surface.shared_base")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    numeric_trace_path = _paper_root_from_quest(quest_root) / "numeric_trace.json"
    numeric_trace_path.unlink(missing_ok=True)

    report = reporting.build_surface_report(shared_base.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "numeric_trace_missing_or_incomplete" in report["blockers"]
    assert report["numeric_trace_path"] == str(numeric_trace_path)
    assert report["numeric_trace_present"] is False
    assert report["numeric_trace_valid"] is False


def test_validate_numeric_trace_rejects_missing_mechanical_trace_fields() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_numeric_trace(
        {
            "traces": [
                {
                    "trace_id": "NT1",
                    "claim_id": "C1",
                    "source_paths": ["artifacts/results/main_result.json"],
                }
            ]
        }
    )

    assert errors == [
        "missing traces[0] fields: reported_value, statistic_kind, source_field, "
        "rounding_rule, manuscript_refs, verification_status, evidence_refs"
    ]
