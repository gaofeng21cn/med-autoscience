from .shared import *

def test_build_report_blocks_when_catalog_entry_missing_template_metadata(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    figure_catalog_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "figures" / "figure_catalog.json"
    )
    payload = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    payload["figures"][0].pop("template_id", None)
    figure_catalog_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "figure_catalog_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"] if hit["pattern_id"] == "figure_catalog")
    assert "template_id" in excerpts

def test_build_report_blocks_when_table3_markdown_contains_forbidden_term(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table3_path = paper_root / "tables" / "T3_interpretation.md"
    table3_path.parent.mkdir(parents=True, exist_ok=True)
    table3_path.write_text(
        "| Clinical Item | Interpretation |\n| --- | --- |\n| High risk | deployment-facing follow-up recommendation |\n",
        encoding="utf-8",
    )
    payload = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    payload["tables"].append(
        {
            "table_id": "T3",
            "table_shell_id": full_id("table3_clinical_interpretation_summary"),
            "input_schema_id": "clinical_interpretation_summary_v1",
            "qc_profile": "publication_table_interpretation",
            "qc_result": {"status": "pass", "issues": []},
            "title": "Clinical interpretation summary",
            "caption": "Clinical interpretation anchors.",
            "paper_role": "supplementary",
            "asset_paths": ["paper/tables/T3_interpretation.md"],
        }
    )
    dump_json(table_catalog_path, payload)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(hit["path"].endswith("T3_interpretation.md") for hit in report["top_hits"])
    assert any(hit["phrase"] == "deployment-facing" for hit in report["top_hits"])


def test_build_report_does_not_scan_non_table3_markdown_body(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table1_path = paper_root / "tables" / "T1.md"
    table1_path.parent.mkdir(parents=True, exist_ok=True)
    table1_path.write_text(
        "| Characteristic | Value |\n| --- | --- |\n| Follow-up | deployment-facing summary |\n",
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["top_hits"] == []


def test_build_report_does_not_scan_non_markdown_table3_assets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table3_path = paper_root / "tables" / "T3_interpretation.md"
    table3_json_path = paper_root / "tables" / "T3_sidecar.json"
    table3_path.parent.mkdir(parents=True, exist_ok=True)
    table3_path.write_text(
        "| Clinical Item | Interpretation |\n| --- | --- |\n| High risk | Close endocrine follow-up |\n",
        encoding="utf-8",
    )
    table3_json_path.write_text(
        json.dumps({"note": "deployment-facing debug artifact"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    payload = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    payload["tables"].append(
        {
            "table_id": "T3",
            "table_shell_id": "table3_clinical_interpretation_summary",
            "input_schema_id": "clinical_interpretation_summary_v1",
            "qc_profile": "publication_table_interpretation",
            "qc_result": {"status": "pass", "issues": []},
            "title": "Clinical interpretation summary",
            "caption": "Clinical interpretation anchors.",
            "paper_role": "supplementary",
            "asset_paths": ["paper/tables/T3_interpretation.md", "paper/tables/T3_sidecar.json"],
        }
    )
    table_catalog_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["top_hits"] == []


def test_build_report_scans_only_table3_markdown_table_body(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table3_path = paper_root / "tables" / "T3_interpretation.md"
    table3_path.parent.mkdir(parents=True, exist_ok=True)
    table3_path.write_text(
        "# deployment-facing title\n\n| Clinical Item | Interpretation |\n| --- | --- |\n| High risk | Close endocrine follow-up |\n",
        encoding="utf-8",
    )
    payload = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    payload["tables"].append(
        {
            "table_id": "T3",
            "table_shell_id": "table3_clinical_interpretation_summary",
            "input_schema_id": "clinical_interpretation_summary_v1",
            "qc_profile": "publication_table_interpretation",
            "qc_result": {"status": "pass", "issues": []},
            "title": "Clinical interpretation summary",
            "caption": "Clinical interpretation anchors.",
            "paper_role": "supplementary",
            "asset_paths": ["paper/tables/T3_interpretation.md"],
        }
    )
    table_catalog_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["top_hits"] == []


def test_build_report_blocks_cross_endpoint_residue_in_figure_catalog(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = _paper_root_from_quest(quest_root)
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    payload = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    payload["figures"][0]["caption"] = (
        "Risk-layering display for Risk of later persistent global hypopituitarism."
    )
    dump_json(figure_catalog_path, payload)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(
        hit["pattern_id"] == "residual_hypopituitarism_endpoint_label"
        and hit["location"] == "figures[0].caption"
        for hit in report["top_hits"]
    )


def test_build_report_blocks_process_instruction_in_supplement_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = _paper_root_from_quest(quest_root)
    reproducibility_path = paper_root / "manuscript_safe_reproducibility_supplement.json"
    payload = json.loads(reproducibility_path.read_text(encoding="utf-8"))
    payload["random_seed_policy"] = (
        "Keep the removal_rate 3-month MRI provenance caveat explicit and re-audit it in the methods."
    )
    dump_json(reproducibility_path, payload)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(
        hit["pattern_id"] == "process_instruction_reaudit_methods"
        and hit["path"].endswith("manuscript_safe_reproducibility_supplement.json")
        for hit in report["top_hits"]
    )


def test_build_report_blocks_engineering_residue_in_table_catalog(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = _paper_root_from_quest(quest_root)
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    payload = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    payload["tables"][0]["note"] = "Confirmed historical specification; monitor comparator drift."
    dump_json(table_catalog_path, payload)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    hit_pattern_ids = {hit["pattern_id"] for hit in report["top_hits"]}
    assert "confirmed_historical_specification_residue" in hit_pattern_ids
    assert "comparator_drift_residue" in hit_pattern_ids


def test_build_report_blocks_public_data_without_surface_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _attach_public_anchor_study_context(monkeypatch, module, tmp_path, quest_root)
    _inject_public_data_surface_mentions(quest_root)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "public_evidence_decisions_missing_or_incomplete" in report["blockers"]
    assert report["public_data_anchor_count"] == 2
    assert report["public_data_surface_reference_count"] >= 1
    assert any(hit["pattern_id"] == "paper_facing_public_data_reference" for hit in report["top_hits"])


def test_build_report_blocks_public_data_when_decisions_drop_from_manuscript(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _attach_public_anchor_study_context(monkeypatch, module, tmp_path, quest_root)
    _inject_public_data_surface_mentions(quest_root)
    _write_public_evidence_decisions(
        quest_root,
        [
            {
                "entry_id": "PE1",
                "dataset_ids": ["mapping-pituitary", "geo-gse169498"],
                "analysis_ids": ["A1"],
                "paper_surface_decision": "drop_from_manuscript",
                "decision_rationale": "Public datasets were retained for audit only and did not earn a manuscript-facing result.",
            }
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "paper_facing_public_data_without_earned_evidence" in report["blockers"]
    assert report["public_evidence_decision_count"] == 1
    assert report["public_evidence_earned_count"] == 0


def test_build_report_allows_public_data_after_appendix_earned_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _attach_public_anchor_study_context(monkeypatch, module, tmp_path, quest_root)
    _inject_public_data_surface_mentions(quest_root)
    _write_public_evidence_decisions(
        quest_root,
        [
            {
                "entry_id": "PE1",
                "dataset_ids": ["mapping-pituitary", "geo-gse169498"],
                "analysis_ids": ["A1"],
                "paper_surface_decision": "appendix_earned",
                "decision_rationale": "The public datasets earned a constrained appendix role after a separate route-specific audit.",
                "result_statement": "Public MRI and omics anchors provide bounded appendix-only anatomy and biology context.",
                "linked_display_items": ["F4"],
                "linked_sections": ["discussion", "appendix"],
                "interpretation_boundary": "Appendix context only; no external validation or mechanistic claim.",
            }
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["public_evidence_decision_count"] == 1
    assert report["public_evidence_earned_count"] == 1
    assert "public_evidence_decisions_missing_or_incomplete" not in report["blockers"]
    assert "paper_facing_public_data_without_earned_evidence" not in report["blockers"]


def test_validate_figure_catalog_requires_real_qc_result_fields() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_figure_catalog(
        {
            "figures": [
                {
                    "figure_id": "F8",
                    "template_id": "umap_scatter_grouped",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "embedding_grouped_inputs_v1",
                    "qc_profile": "publication_embedding_scatter",
                    "qc_result": {"status": "pass"},
                    "export_paths": ["paper/figures/F8.png", "paper/figures/F8.pdf"],
                }
            ]
        }
    )

    assert "engine_id" in errors[0]


def test_validate_figure_catalog_blocks_readability_failures() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_figure_catalog(
        {
            "figures": [
                {
                    "figure_id": "F3",
                    "template_id": "time_to_event_risk_group_summary",
                    "renderer_family": "python",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_grouped_inputs_v1",
                    "qc_profile": "publication_survival_curve",
                    "qc_result": {
                        "status": "fail",
                        "checked_at": "2026-04-04T00:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_survival_curve",
                        "layout_sidecar_path": "paper/figures/generated/F3.layout.json",
                        "audit_classes": ["readability"],
                        "issues": [
                            {
                                "audit_class": "readability",
                                "rule_id": "risk_separation_not_readable",
                                "message": "survival groups are too compressed to convey the intended separation",
                            }
                        ],
                        "failure_reason": "risk_separation_not_readable",
                        "readability_findings": [
                            {
                                "audit_class": "readability",
                                "rule_id": "risk_separation_not_readable",
                                "message": "survival groups are too compressed to convey the intended separation",
                            }
                        ],
                        "revision_note": "",
                    },
                    "export_paths": ["paper/figures/F3.png", "paper/figures/F3.pdf"],
                }
            ]
        }
    )

    assert any("readability" in error for error in errors)


def test_validate_figure_catalog_blocks_failed_illustration_shell_qc() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_figure_catalog(
        {
            "figures": [
                {
                    "figure_id": "GA1",
                    "template_id": "submission_graphical_abstract",
                    "renderer_family": "python",
                    "paper_role": "submission_companion",
                    "input_schema_id": "submission_graphical_abstract_inputs_v1",
                    "qc_profile": "submission_graphical_abstract",
                    "qc_result": {
                        "status": "fail",
                        "checked_at": "2026-04-05T00:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "submission_graphical_abstract",
                        "layout_sidecar_path": "paper/figures/generated/GA1.layout.json",
                        "audit_classes": ["layout"],
                        "issues": [
                            {
                                "audit_class": "layout",
                                "rule_id": "panel_text_out_of_panel",
                                "message": "graphical-abstract panel text must stay within a panel",
                            }
                        ],
                        "failure_reason": "panel_text_out_of_panel",
                        "readability_findings": [],
                        "revision_note": "",
                    },
                    "export_paths": ["paper/figures/generated/GA1.svg", "paper/figures/generated/GA1.png"],
                }
            ]
        }
    )

    assert any("blocks publication" in error for error in errors)


def test_validate_figure_semantics_manifest_blocks_story_role_drift_for_setup_shell() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    base_payload = {
        "figure_id": "S1",
        "research_question": "How was the formal analysis cohort assembled before model fitting?",
        "direct_message": "The cohort-flow shell documents study assembly and exclusion logic for the audited analysis cohort.",
        "clinical_implication": "Supports transparent setup reporting before the manuscript turns to result evidence.",
        "interpretation_boundary": "Study setup only; it is not itself a result claim.",
        "panel_messages": [
            {
                "panel_id": "A",
                "message": "The figure traces screened, excluded, and analyzed patients.",
            }
        ],
        "legend_glossary": [
            {
                "term": "analysis cohort",
                "explanation": "Patients retained for the prespecified audited model analysis.",
            }
        ],
        "threshold_semantics": "Not applicable to the cohort-flow shell.",
        "stratification_basis": "Not applicable to the cohort-flow shell.",
        "recommendation_boundary": "No treatment recommendation is made from this setup figure.",
        "renderer_contract": {
            "figure_semantics": "illustration",
            "renderer_family": "python",
            "template_id": full_id("cohort_flow_figure"),
            "selection_rationale": "The registered cohort-flow shell preserves the audited study-setup surface.",
            "layout_qc_profile": "publication_illustration_flow",
            "required_exports": ["png", "svg", "pdf"],
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        },
    }

    assert module.validate_figure_semantics_manifest(
        {"figures": [dict(base_payload, story_role="study_setup")]}
    ) == []

    errors = module.validate_figure_semantics_manifest(
        {"figures": [dict(base_payload, story_role="study_assembly_support")]}
    )

    assert any("canonical story role" in error for error in errors)
    assert any("study_setup" in error for error in errors)


def test_validate_figure_semantics_manifest_accepts_setup_story_role_alias() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    payload = {
        "figure_id": "S1",
        "story_role": "study_population_and_design_anchor",
        "research_question": "Which cohorts define the external validation comparison?",
        "direct_message": "The cohort-flow shell defines the development and external validation populations.",
        "clinical_implication": "Keeps the setup figure on the manuscript-facing cohort-definition role.",
        "interpretation_boundary": "Study setup only; it is not itself a result claim.",
        "panel_messages": [
            {
                "panel_id": "A",
                "message": "The figure traces the development and validation cohorts.",
            }
        ],
        "legend_glossary": [
            {
                "term": "external validation cohort",
                "explanation": "Participants reserved for manuscript-facing transportability evaluation.",
            }
        ],
        "threshold_semantics": "Not applicable to the cohort-flow shell.",
        "stratification_basis": "Not applicable to the cohort-flow shell.",
        "recommendation_boundary": "No treatment recommendation is made from this setup figure.",
        "renderer_contract": {
            "figure_semantics": "illustration",
            "renderer_family": "python",
            "template_id": full_id("cohort_flow_figure"),
            "selection_rationale": "The registered cohort-flow shell preserves the audited study-setup surface.",
            "layout_qc_profile": "publication_illustration_flow",
            "required_exports": ["png", "svg", "pdf"],
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        },
    }

    assert module.validate_figure_semantics_manifest({"figures": [payload]}) == []


def test_validate_figure_catalog_allows_supplementary_cohort_flow_shell() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    base_payload = {
        "figure_id": "S1",
        "template_id": "cohort_flow_figure",
        "renderer_family": "python",
        "input_schema_id": "cohort_flow_shell_inputs_v1",
        "qc_profile": "publication_illustration_flow",
        "qc_result": {
            "status": "pass",
            "checked_at": "2026-04-05T00:00:00+00:00",
            "engine_id": "display_layout_qc_v1",
            "qc_profile": "publication_illustration_flow",
            "layout_sidecar_path": "paper/figures/generated/S1.layout.json",
            "audit_classes": [],
            "issues": [],
            "readability_findings": [],
            "revision_note": "",
        },
        "export_paths": [
            "paper/figures/generated/S1.svg",
            "paper/figures/generated/S1.png",
            "paper/figures/generated/S1.pdf",
        ],
    }

    supplementary_errors = module.validate_figure_catalog(
        {"figures": [dict(base_payload, paper_role="supplementary")]}
    )
    main_text_errors = module.validate_figure_catalog(
        {"figures": [dict(base_payload, paper_role="main_text")]}
    )
    appendix_errors = module.validate_figure_catalog(
        {"figures": [dict(base_payload, paper_role="appendix")]}
    )

    assert supplementary_errors == []
    assert main_text_errors == []
    assert any("paper_role `appendix`" in error for error in appendix_errors)


def test_validate_table_catalog_accepts_md_only_second_stage_tables() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T2_summary.md"],
                },
                {
                    "table_id": "T3",
                    "table_shell_id": "table3_clinical_interpretation_summary",
                    "paper_role": "supplementary",
                    "input_schema_id": "clinical_interpretation_summary_v1",
                    "qc_profile": "publication_table_interpretation",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T3_summary.md"],
                },
            ]
        }
    )

    assert errors == []


def test_build_report_blocks_single_panel_label_without_layout_evidence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        generated_figure_text_override=(
            "<svg>"
            "<text x='24' y='32'>A</text>"
            "<text x='64' y='32'>Threshold-specific operating characteristics for the extended preoperative model</text>"
            "</svg>\n"
        ),
    )
    layout_sidecar_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "figures" / "generated" / "F4.layout.json"
    )
    dump_json(
        layout_sidecar_path,
        {
            "figure_id": "F4",
            "template_id": "roc_curve_binary",
            "renderer_family": "r_ggplot2",
            "qc_profile": "publication_evidence_curve",
            "status": "pass",
            "updated_at": "2026-04-18T14:00:00+00:00",
        },
    )

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "blocked"
    assert "figure_layout_sidecar_missing_or_incomplete" in report["blockers"]
    pattern_ids = {hit["pattern_id"] for hit in report["top_hits"]}
    assert "figure_layout_sidecar_missing_publication_metrics" in pattern_ids
    assert "single_panel_figure_contains_panel_label" in pattern_ids


def test_validate_table_catalog_rejects_missing_md_export_for_second_stage_table() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T2_summary.csv"],
                }
            ]
        }
    )

    assert "missing required export formats" in errors[0]
    assert "md" in errors[0]


def test_validate_table_catalog_accepts_csv_and_md_anchor_generic_tables() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "performance_summary_table_generic",
                    "paper_role": "main_text",
                    "input_schema_id": "performance_summary_table_generic_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": [
                        "paper/tables/T2_performance_summary.csv",
                        "paper/tables/T2_performance_summary.md",
                    ],
                },
                {
                    "table_id": "T3",
                    "table_shell_id": "grouped_risk_event_summary_table",
                    "paper_role": "main_text",
                    "input_schema_id": "grouped_risk_event_summary_table_v1",
                    "qc_profile": "publication_table_interpretation",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": [
                        "paper/tables/T3_grouped_risk_summary.csv",
                        "paper/tables/T3_grouped_risk_summary.md",
                    ],
                },
            ]
        }
    )

    assert errors == []


def test_validate_table_catalog_rejects_missing_csv_for_anchor_generic_tables() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "performance_summary_table_generic",
                    "paper_role": "main_text",
                    "input_schema_id": "performance_summary_table_generic_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T2_performance_summary.md"],
                }
            ]
        }
    )

    assert "missing required export formats" in errors[0]
    assert "csv" in errors[0]
