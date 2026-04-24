from .shared import *

def test_build_report_flags_forbidden_terms_and_missing_ama_defaults(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(
        tmp_path,
        medicalized=False,
        ama_defaults=False,
        include_methods_manifest=False,
        include_results_narrative_map=False,
        include_figure_semantics_manifest=False,
        include_derived_analysis_manifest=False,
        figure_led_results=True,
        include_reproducibility_supplement=False,
        include_endpoint_provenance_note=False,
        include_operational_method_labels=False,
    )

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert "ama_pdf_defaults_missing" in report["blockers"]
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    assert "results_narrative_map_missing_or_incomplete" in report["blockers"]
    assert "introduction_structure_missing_or_incomplete" in report["blockers"]
    assert "methods_section_structure_missing_or_incomplete" in report["blockers"]
    assert "results_section_structure_missing_or_incomplete" in report["blockers"]
    assert "figure_semantics_manifest_missing_or_incomplete" in report["blockers"]
    assert "evidence_ledger_missing_or_incomplete" in report["blockers"]
    assert "derived_analysis_manifest_missing_or_incomplete" in report["blockers"]
    assert "figure_table_led_results_narration_present" in report["blockers"]
    assert "manuscript_safe_reproducibility_supplement_missing_or_incomplete" in report["blockers"]
    assert "endpoint_provenance_note_missing_or_unapplied" in report["blockers"]
    assert "undefined_methodology_labels_present" in report["blockers"]
    assert report["ama_csl_present"] is False
    assert report["ama_pdf_defaults_present"] is False
    assert any(hit["phrase"] == "deployment-facing" for hit in report["top_hits"])
    assert any(hit["phrase"] == "online service:" for hit in report["top_hits"])
    assert any(hit["phrase"] == "roc_auc" for hit in report["top_hits"])
    assert any(hit["phrase"] == "average_precision" for hit in report["top_hits"])
    assert any(hit["phrase"] == "brier_score" for hit in report["top_hits"])
    assert any(hit["phrase"] == "calibration_intercept" for hit in report["top_hits"])
    assert any(hit["phrase"] == "calibration_slope" for hit in report["top_hits"])
    assert any(hit["phrase"] == "Figure 1 shows" for hit in report["top_hits"])
    assert any(hit["phrase"] == "calibration-first" for hit in report["top_hits"])
    assert any("endpoint_provenance_note" in hit["pattern_id"] for hit in report["top_hits"])


def test_build_report_clears_when_assets_are_medicalized_and_ama_defaults_exist(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "clear"
    assert report["blockers"] == []
    assert report["evidence_ledger_present"] is True
    assert report["evidence_ledger_valid"] is True


def test_build_report_projects_study_charter_linkage_for_ledgers(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    study_root = _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root)

    report = module.build_surface_report(module.build_surface_state(quest_root))
    linkage = report["charter_contract_linkage"]

    assert linkage["status"] == "linked"
    assert linkage["study_charter_ref"] == {
        "charter_id": "charter::002-early-residual-risk::v1",
        "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
    }
    assert linkage["paper_quality_contract"]["present"] is True
    assert linkage["ledger_linkages"]["evidence_ledger"]["status"] == "linked"
    assert linkage["ledger_linkages"]["review_ledger"]["status"] == "linked"

    markdown = module.render_surface_markdown(report)
    assert "## Charter Contract Linkage" in markdown
    assert "charter::002-early-residual-risk::v1" in markdown
    assert "- evidence_ledger_linkage_status: `linked`" in markdown
    assert "- review_ledger_linkage_status: `linked`" in markdown


def test_build_report_treats_missing_charter_expectation_closure_records_as_advisory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root, include_charter_expectations=True)

    report = module.build_surface_report(module.build_surface_state(quest_root))
    summary = report["charter_expectation_closure_summary"]

    assert report["status"] == "clear"
    assert "charter_expectation_closure_incomplete" not in report["blockers"]
    assert summary["status"] == "advisory"
    assert summary["blocking_items"] == []
    assert len(summary["advisory_items"]) == 3
    assert {item["closure_status"] for item in summary["advisory_items"]} == {"not_recorded"}
    assert all(item["blocker"] is False for item in summary["advisory_items"])
    assert all(item["recorded"] is False for item in summary["advisory_items"])
    assert not any(hit["pattern_id"] == "charter_expectation_closure_blocker" for hit in report["top_hits"])

    markdown = module.render_surface_markdown(report)
    assert "## Charter Expectation Closure Summary" in markdown
    assert "not_recorded" in markdown


@pytest.mark.parametrize("closure_status", ["open", "in_progress", "blocked", "resolved"])
def test_build_report_blocks_when_charter_expectation_closure_status_is_not_closed(
    tmp_path: Path,
    monkeypatch,
    closure_status: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root, include_charter_expectations=True)
    paper_root = _paper_root_from_quest(quest_root)
    _write_charter_expectation_closures(
        paper_root / "evidence_ledger.json",
        [_charter_expectation_record("minimum_sci_ready_evidence_package")],
    )
    _write_charter_expectation_closures(
        paper_root / "review" / "review_ledger.json",
        [
            _charter_expectation_record("scientific_followup_questions", status=closure_status),
            _charter_expectation_record("manuscript_conclusion_redlines"),
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))
    summary = report["charter_expectation_closure_summary"]
    blocker = next(
        item
        for item in summary["blocking_items"]
        if item["expectation_key"] == "scientific_followup_questions"
    )

    assert report["status"] == "blocked"
    assert "charter_expectation_closure_incomplete" in report["blockers"]
    expected_status = closure_status if closure_status in {"open", "in_progress", "blocked"} else "invalid_status"
    assert blocker["closure_status"] == expected_status
    assert blocker["blocker"] is True
    assert blocker["ledger_name"] == "review_ledger"


def test_build_report_projects_blocking_charter_expectation_closure_gaps(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root, include_charter_expectations=True)
    paper_root = _paper_root_from_quest(quest_root)
    _write_charter_expectation_closures(
        paper_root / "evidence_ledger.json",
        [_charter_expectation_record("minimum_sci_ready_evidence_package")],
    )
    _write_charter_expectation_closures(
        paper_root / "review" / "review_ledger.json",
        [
            _charter_expectation_record("scientific_followup_questions", status="open"),
            _charter_expectation_record("manuscript_conclusion_redlines"),
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))
    gaps = report["charter_expectation_closure_gaps"]

    assert report["status"] == "blocked"
    assert "charter_expectation_closure_incomplete" in report["blockers"]
    assert len(gaps) == 1
    assert gaps[0]["expectation_key"] == "scientific_followup_questions"
    assert (
        gaps[0]["expectation_text"]
        == CHARTER_EXPECTATION_FIXTURES["scientific_followup_questions"]["expectation_text"]
    )
    assert gaps[0]["ledger_name"] == "review_ledger"
    assert gaps[0]["closure_status"] == "open"
    assert gaps[0]["contract_json_pointer"] == "/paper_quality_contract/review_expectations/scientific_followup_questions"
    assert gaps[0]["blocker"] is True

    markdown = module.render_surface_markdown(report)
    assert "## Charter Expectation Closure Gaps" in markdown
    assert CHARTER_EXPECTATION_FIXTURES["scientific_followup_questions"]["expectation_text"] in markdown
    assert "contract_json_pointer=`/paper_quality_contract/review_expectations/scientific_followup_questions`" in markdown
    assert "ledger=`review_ledger`" in markdown
    assert "closure_status=`open`" in markdown


def test_build_report_blocks_when_charter_expectation_closure_records_are_duplicated(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root, include_charter_expectations=True)
    paper_root = _paper_root_from_quest(quest_root)
    _write_charter_expectation_closures(
        paper_root / "evidence_ledger.json",
        [
            _charter_expectation_record("minimum_sci_ready_evidence_package"),
            _charter_expectation_record(
                "minimum_sci_ready_evidence_package",
                note="Duplicate closure record should block the report.",
            ),
        ],
    )
    _write_charter_expectation_closures(
        paper_root / "review" / "review_ledger.json",
        [
            _charter_expectation_record("scientific_followup_questions"),
            _charter_expectation_record("manuscript_conclusion_redlines"),
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))
    summary = report["charter_expectation_closure_summary"]
    blocker = next(
        item
        for item in summary["blocking_items"]
        if item["expectation_key"] == "minimum_sci_ready_evidence_package"
    )

    assert report["status"] == "blocked"
    assert "charter_expectation_closure_incomplete" in report["blockers"]
    assert blocker["closure_status"] == "duplicate_records"
    assert blocker["record_count"] == 2
    assert blocker["blocker"] is True


def test_build_report_clears_when_charter_expectation_closures_are_explicitly_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root, include_charter_expectations=True)
    paper_root = _paper_root_from_quest(quest_root)
    _write_charter_expectation_closures(
        paper_root / "evidence_ledger.json",
        [_charter_expectation_record("minimum_sci_ready_evidence_package")],
    )
    _write_charter_expectation_closures(
        paper_root / "review" / "review_ledger.json",
        [
            _charter_expectation_record("scientific_followup_questions"),
            _charter_expectation_record("manuscript_conclusion_redlines"),
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))
    summary = report["charter_expectation_closure_summary"]

    assert report["status"] == "clear"
    assert "charter_expectation_closure_incomplete" not in report["blockers"]
    assert summary["status"] == "clear"
    assert summary["declared_record_count"] == 3
    assert summary["closed_item_count"] == 3
    assert summary["blocking_items"] == []


def test_build_report_blocks_when_study_charter_is_missing(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    study_root = _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root)
    (study_root / "artifacts" / "controller" / "study_charter.json").unlink()

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "study_charter_missing" in report["blockers"]
    assert report["charter_contract_linkage"]["status"] == "study_charter_missing"


def test_build_report_blocks_when_evidence_ledger_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_evidence_ledger=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "evidence_ledger_missing_or_incomplete" in report["blockers"]
    assert report["evidence_ledger_present"] is False
    assert report["evidence_ledger_valid"] is False


def test_build_report_blocks_when_evidence_ledger_shape_is_invalid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    evidence_ledger_path = _paper_root_from_quest(quest_root) / "evidence_ledger.json"
    dump_json(
        evidence_ledger_path,
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Incomplete shape for blocker coverage.",
                }
            ],
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "evidence_ledger_missing_or_incomplete" in report["blockers"]
    assert report["evidence_ledger_present"] is True
    assert report["evidence_ledger_valid"] is False
    assert any(hit["pattern_id"] == "evidence_ledger" for hit in report["top_hits"])
    assert report["ama_csl_present"] is True
    assert report["ama_pdf_defaults_present"] is True


def test_build_report_accepts_item_only_evidence_ledger_when_claim_map_is_complete(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    evidence_ledger_path = _paper_root_from_quest(quest_root) / "evidence_ledger.json"
    dump_json(
        evidence_ledger_path,
        {
            "schema_version": 1,
            "selected_outline_ref": "outline-001",
            "items": [
                {
                    "item_id": "EXP-001",
                    "title": "Retained manuscript-facing evidence item.",
                    "status": "completed",
                    "paper_role": "main_text",
                    "section_id": "results",
                    "claim_links": ["C1"],
                    "source_paths": ["paper/results_narrative_map.json"],
                }
            ],
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "evidence_ledger_missing_or_incomplete" not in report["blockers"]
    assert report["evidence_ledger_present"] is True
    assert report["evidence_ledger_valid"] is True


def test_build_report_ignores_unreferenced_generated_readme(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    readme_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "figures" / "generated" / "README.md"
    readme_path.write_text(
        "# Generated Figure Outputs\n\n"
        "Any unreferenced stale generated files are pruned during `materialize-display-surface`.\n",
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert all(not hit["path"].endswith("paper/figures/generated/README.md") for hit in report["top_hits"])


def test_build_report_allows_generic_clinical_surface_language(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    draft_path = paper_root / "draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").replace(
            "### Added-value assessment of model complexity",
            "### Monotonic score surface\n\n"
            "The core logistic model remained recoverable on a conventional regression surface.\n\n"
            "### Added-value assessment of model complexity",
        ),
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert all(hit["pattern_id"] != "surface" for hit in report["top_hits"])


def test_build_report_blocks_when_introduction_does_not_follow_three_move_structure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_introduction=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "introduction_structure_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "introduction_structure" for hit in report["top_hits"])


def test_build_report_blocks_when_methods_subsections_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_methods=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_section_structure_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "methods_section_structure" for hit in report["top_hits"])


def test_build_report_blocks_when_results_section_lacks_subsection_structure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_results=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "results_section_structure_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "results_section_structure" for hit in report["top_hits"])


def test_build_report_accepts_quick_review_with_top_level_main_sections(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    review_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "build"
        / "review_manuscript.md"
    )
    review_text = review_path.read_text(encoding="utf-8")
    review_text = review_text.replace("\n## Introduction\n", "\n# Introduction\n")
    review_text = review_text.replace("\n## Materials and Methods\n", "\n# Materials and Methods\n")
    review_text = review_text.replace("\n## Results\n", "\n# Results\n")
    review_path.write_text(review_text, encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "introduction_structure_missing_or_incomplete" not in report["blockers"]
    assert "methods_section_structure_missing_or_incomplete" not in report["blockers"]
    assert "results_section_structure_missing_or_incomplete" not in report["blockers"]


def test_build_report_accepts_review_with_relative_subsection_levels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    review_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "build"
        / "review_manuscript.md"
    )
    review_text = review_path.read_text(encoding="utf-8")
    review_text = review_text.replace("\n## Introduction\n", "\n# Introduction\n")
    review_text = review_text.replace("\n## Materials and Methods\n", "\n# Materials and Methods\n")
    review_text = review_text.replace("\n### Study design and cohort\n", "\n## Study design and cohort\n")
    review_text = review_text.replace(
        "\n### Variable definition and measurement\n",
        "\n## Variable definition and measurement\n",
    )
    review_text = review_text.replace("\n### Model building\n", "\n## Model building\n")
    review_text = review_text.replace("\n### Validation framework\n", "\n## Validation framework\n")
    review_text = review_text.replace("\n## Results\n", "\n# Results\n")
    review_text = review_text.replace("\n### Cohort characteristics\n", "\n## Cohort characteristics\n")
    review_text = review_text.replace(
        "\n### Unified validation and clinical utility\n",
        "\n## Unified validation and clinical utility\n",
    )
    review_text = review_text.replace(
        "\n### Added-value assessment of model complexity\n",
        "\n## Added-value assessment of model complexity\n",
    )
    review_text = review_text.replace("\n## Discussion\n", "\n# Discussion\n")
    review_path.write_text(review_text, encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "introduction_structure_missing_or_incomplete" not in report["blockers"]
    assert "methods_section_structure_missing_or_incomplete" not in report["blockers"]
    assert "results_section_structure_missing_or_incomplete" not in report["blockers"]


