from .shared import (
    annotations,
    _shared_base,
    _registry_id_helpers,
    _workspace_surface_fixtures,
    _layout_sidecar_fixtures,
    _illustration_payload_fixtures,
    _current_evidence_payload_fixtures,
    importlib,
    json,
    Path,
    re,
    sys,
    Any,
    plt,
    pytest,
    display_registry,
    get_template_short_id,
    full_id,
    dump_json,
    extract_svg_font_size,
    write_default_publication_display_contracts,
    restrict_display_registry_to_display_ids,
    build_display_surface_workspace,
    minimal_current_layout_sidecar,
    minimal_tail_layout_sidecar,
    _center_transportability_governance_display,
    _current_evidence_input_envelopes,
    _make_generalizability_subgroup_composite_panel_display,
)


def test_display_layout_qc_rejects_v2_participant_flow_with_prose_context_cards() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
            "layout_boxes": [
                {
                    "box_id": "participant_step_source",
                    "box_type": "main_step",
                    "x0": 0.14,
                    "y0": 0.70,
                    "x1": 0.86,
                    "y1": 0.82,
                },
                {
                    "box_id": "participant_step_analysis",
                    "box_type": "main_step",
                    "x0": 0.14,
                    "y0": 0.50,
                    "x1": 0.86,
                    "y1": 0.62,
                },
                {
                    "box_id": "participant_endpoint_design_context",
                    "box_type": "context_note",
                    "x0": 0.06,
                    "y0": 0.06,
                    "x1": 0.94,
                    "y1": 0.28,
                },
            ],
            "panel_boxes": [
                {
                    "box_id": "participant_flow_main",
                    "box_type": "subfigure_panel",
                    "x0": 0.06,
                    "y0": 0.42,
                    "x1": 0.98,
                    "y1": 0.86,
                }
            ],
            "guide_boxes": [
                {
                    "box_id": "flow_spine_source_to_analysis",
                    "box_type": "flow_connector",
                    "x0": 0.50,
                    "y0": 0.62,
                    "x1": 0.50,
                    "y1": 0.70,
                }
            ],
            "metrics": {
                "layout_mode": "participant_flow",
                "layout_generation": "scholarskills_cohort_flow_v2",
                "flow_visual_policy": "purpose_first_reporting_flow_no_legacy_card_shell",
                "steps": [{"step_id": "source"}, {"step_id": "analysis"}],
                "flow_nodes": [
                    {
                        "box_id": "participant_step_source",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74,
                        "rendered_width_pt": 460,
                        "padding_pt": 10,
                    },
                    {
                        "box_id": "participant_step_analysis",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74,
                        "rendered_width_pt": 460,
                        "padding_pt": 10,
                    },
                    {
                        "box_id": "participant_endpoint_design_context",
                        "box_type": "context_note",
                        "line_count": 5,
                        "max_line_chars": 76,
                        "rendered_height_pt": 92,
                        "rendered_width_pt": 570,
                        "padding_pt": 7,
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert "participant_flow_context_card_shell" in {issue["rule_id"] for issue in result["issues"]}


def test_display_layout_qc_rejects_v2_participant_flow_with_truncated_step_detail() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
            "layout_boxes": [
                {
                    "box_id": "participant_step_source",
                    "box_type": "main_step",
                    "x0": 0.14,
                    "y0": 0.72,
                    "x1": 0.86,
                    "y1": 0.86,
                },
                {
                    "box_id": "participant_step_denominator",
                    "box_type": "main_step",
                    "x0": 0.14,
                    "y0": 0.48,
                    "x1": 0.86,
                    "y1": 0.62,
                },
                {
                    "box_id": "participant_step_analysis",
                    "box_type": "main_step",
                    "x0": 0.14,
                    "y0": 0.24,
                    "x1": 0.86,
                    "y1": 0.38,
                },
            ],
            "panel_boxes": [
                {
                    "box_id": "participant_flow_main",
                    "box_type": "subfigure_panel",
                    "x0": 0.06,
                    "y0": 0.18,
                    "x1": 0.98,
                    "y1": 0.90,
                }
            ],
            "guide_boxes": [
                {
                    "box_id": "flow_spine_source_to_denominator",
                    "box_type": "flow_connector",
                    "x0": 0.50,
                    "y0": 0.62,
                    "x1": 0.50,
                    "y1": 0.72,
                },
                {
                    "box_id": "flow_spine_denominator_to_analysis",
                    "box_type": "flow_connector",
                    "x0": 0.50,
                    "y0": 0.38,
                    "x1": 0.50,
                    "y1": 0.48,
                },
            ],
            "metrics": {
                "layout_mode": "participant_flow",
                "layout_generation": "scholarskills_cohort_flow_v2",
                "flow_visual_policy": "purpose_first_reporting_flow_no_legacy_card_shell",
                "steps": [
                    {"step_id": "source"},
                    {"step_id": "denominator"},
                    {"step_id": "analysis"},
                ],
                "flow_nodes": [
                    {
                        "box_id": "participant_step_source",
                        "box_type": "main_step",
                        "line_count": 4,
                        "max_line_chars": 42,
                        "rendered_height_pt": 94,
                        "rendered_width_pt": 460,
                        "padding_pt": 10,
                        "detail_truncated": True,
                    },
                    {
                        "box_id": "participant_step_denominator",
                        "box_type": "main_step",
                        "line_count": 3,
                        "max_line_chars": 42,
                        "rendered_height_pt": 94,
                        "rendered_width_pt": 460,
                        "padding_pt": 10,
                    },
                    {
                        "box_id": "participant_step_analysis",
                        "box_type": "main_step",
                        "line_count": 3,
                        "max_line_chars": 42,
                        "rendered_height_pt": 94,
                        "rendered_width_pt": 460,
                        "padding_pt": 10,
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert "participant_flow_step_detail_truncated" in {issue["rule_id"] for issue in result["issues"]}


def test_display_layout_qc_rejects_low_information_v2_participant_flow() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
            "layout_boxes": [
                {
                    "box_id": "participant_step_china",
                    "box_type": "main_step",
                    "x0": 0.14,
                    "y0": 0.70,
                    "x1": 0.86,
                    "y1": 0.82,
                },
                {
                    "box_id": "participant_step_nhanes",
                    "box_type": "main_step",
                    "x0": 0.14,
                    "y0": 0.50,
                    "x1": 0.86,
                    "y1": 0.62,
                },
            ],
            "panel_boxes": [
                {
                    "box_id": "participant_flow_main",
                    "box_type": "subfigure_panel",
                    "x0": 0.06,
                    "y0": 0.42,
                    "x1": 0.98,
                    "y1": 0.86,
                }
            ],
            "guide_boxes": [
                {
                    "box_id": "flow_spine_china_to_nhanes",
                    "box_type": "flow_connector",
                    "x0": 0.50,
                    "y0": 0.62,
                    "x1": 0.50,
                    "y1": 0.70,
                }
            ],
            "metrics": {
                "layout_mode": "participant_flow",
                "layout_generation": "scholarskills_cohort_flow_v2",
                "flow_visual_policy": "purpose_first_reporting_flow_no_legacy_card_shell",
                "steps": [{"step_id": "china"}, {"step_id": "nhanes"}],
                "exclusions": [],
                "design_panels": [
                    {
                        "panel_id": "common_predictor_set",
                        "lines": [
                            {"label": "Age", "detail": ""},
                            {"label": "Sex", "detail": ""},
                        ],
                    }
                ],
                "flow_nodes": [
                    {
                        "box_id": "participant_step_china",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74,
                        "rendered_width_pt": 460,
                        "padding_pt": 10,
                    },
                    {
                        "box_id": "participant_step_nhanes",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74,
                        "rendered_width_pt": 460,
                        "padding_pt": 10,
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert "participant_flow_low_information_accounting" in {issue["rule_id"] for issue in result["issues"]}


def test_materialize_display_surface_renders_cohort_flow_with_exclusions_and_design_panels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _write_prepared_dependency_environment(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure1",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/Figure1.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Unified study cohort and design shell",
            "steps": [
                {"step_id": "source", "label": "Source records", "n": 409, "detail": "Institutional cohort"},
                {"step_id": "first_surgery", "label": "First-surgery cases", "n": 357},
                {"step_id": "analysis", "label": "Analysis cohort", "n": 357, "detail": "Observed endpoint available"},
            ],
            "exclusions": [
                {
                    "exclusion_id": "repeat_or_salvage",
                    "from_step_id": "source",
                    "label": "Repeat or salvage surgery excluded",
                    "n": 52,
                    "detail": "Not eligible for the first-surgery cohort",
                }
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "main_endpoint",
                    "label": "Early residual / non-GTR",
                    "event_n": 57,
                    "detail": "57 non-GTR vs 300 GTR",
                }
            ],
            "design_panels": [
                {
                    "panel_id": "validation_framework",
                    "title": "Validation framework",
                    "layout_role": "top_right",
                    "lines": [
                        {"label": "Repeated nested validation", "detail": "5 outer folds x 20 repeats; 4-fold inner tuning"}
                    ],
                },
                {
                    "panel_id": "model_hierarchy",
                    "title": "Model hierarchy",
                    "layout_role": "wide_left",
                    "lines": [
                        {"label": "Core preoperative model", "detail": "Confirmed comparator"},
                        {"label": "Clinical utility model", "detail": "Knowledge-guided primary model"},
                    ],
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar_path = paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json"
    assert layout_sidecar_path.exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"
    assert qc_result["engine_id"] == "display_layout_qc_v1"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")
    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    layout_boxes = {item["box_id"]: item for item in layout_sidecar["layout_boxes"]}
    assert not any(item["box_type"] == "summary_panel" for item in layout_sidecar["layout_boxes"])
    assert not any(item["box_type"] in {"context_note", "design_context_note"} for item in layout_sidecar["layout_boxes"])
    step_boxes = [item for item in layout_sidecar["layout_boxes"] if item["box_type"] == "main_step"]
    participant_panel = next(item for item in layout_sidecar["panel_boxes"] if item["box_id"] == "participant_flow_main")
    panel_width = participant_panel["x1"] - participant_panel["x0"]
    content_x0 = min(item["x0"] for item in step_boxes)
    content_x1 = max(item["x1"] for item in step_boxes)
    content_center = (content_x0 + content_x1) / 2.0
    panel_center = (participant_panel["x0"] + participant_panel["x1"]) / 2.0
    assert step_boxes
    assert (content_x1 - content_x0) / panel_width >= 0.66
    assert abs(content_center - panel_center) / panel_width <= 0.10


def test_materialize_display_surface_renders_exclusion_aware_cohort_flow_shell(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation, exclusions, and study design",
            "caption": "Cohort derivation with explicit exclusion accounting.",
            "steps": [
                {"step_id": "source_total", "label": "Source study records", "n": 409, "detail": "Institutional cleaned cohort"},
                {"step_id": "first_surgery", "label": "First-surgery NF-PitNET cases", "n": 357, "detail": "Primary cohort"},
                {"step_id": "analysis", "label": "Analyzed cohort", "n": 357, "detail": "Observed resection status"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat_salvage",
                    "from_step_id": "source_total",
                    "label": "Repeat or salvage surgery",
                    "n": 52,
                    "detail": "Excluded before first-surgery cohort lock",
                }
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "non_gtr",
                    "label": "Early residual / non-GTR",
                    "n": 57,
                    "detail": "Primary endpoint",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation_frame",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [
                        {"label": "Repeated nested validation", "detail": "5-fold outer x 20 repeats; 4-fold inner tuning"}
                    ],
                },
                {
                    "block_id": "primary_model",
                    "block_type": "left_bottom",
                    "title": "Primary model",
                    "items": [{"label": "Clinically informed preoperative model", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "comparator_model",
                    "block_type": "right_bottom",
                    "title": "Comparator",
                    "items": [{"label": "Preoperative core model", "detail": "Confirmed comparator"}],
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.pdf").exists()
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8")
    )
    assert layout_sidecar["metrics"]["exclusions"]
    assert layout_sidecar["metrics"]["steps"]
    assert layout_sidecar["metrics"]["design_panels"]
    assert not any(item["box_type"] == "summary_panel" for item in layout_sidecar["layout_boxes"])
    assert not any(item["box_type"] in {"context_note", "design_context_note"} for item in layout_sidecar["layout_boxes"])
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"
    assert qc_result["qc_profile"] == "publication_illustration_flow"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")


def test_materialize_display_surface_preserves_current_generated_cohort_flow_over_stale_current_body(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    current_body_paper_root = (
        paper_root.parent
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    dump_json(
        current_body_paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "catalog_id": "F1",
            "title": "Stale two-cohort cutover flow",
            "steps": [
                {"step_id": "china", "label": "China cohort", "n": 15787},
                {"step_id": "nhanes", "label": "NHANES cohort", "n": 7408},
            ],
            "design_panels": [],
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
            "display_id": "Figure1",
            "catalog_id": "F1",
            "status": "materialized_from_current_transportability_layout",
            "title": "External-validation cohort flow and model-input boundary",
            "flow_mode": "source_layer_accounting",
            "denominator_step_id": "harmonized_diabetes_analysis_sources",
            "steps": [
                {"step_id": "harmonized_diabetes_analysis_sources", "label": "Harmonized diabetes analysis sources", "n": 23195},
            ],
            "source_layers": [
                {
                    "layer_id": "china_development_source",
                    "step_id": "harmonized_diabetes_analysis_sources",
                    "label": "China development cohort",
                    "n": 15787,
                },
                {
                    "layer_id": "nhanes_validation_source",
                    "step_id": "harmonized_diabetes_analysis_sources",
                    "label": "NHANES external validation cohort",
                    "n": 7408,
                },
            ],
            "subcohort_coverage": [
                {
                    "coverage_id": "score_derivation_endpoint",
                    "label": "China score derivation and mortality endpoint accounting",
                    "n": 15787,
                    "denominator_n": 23195,
                },
                {
                    "coverage_id": "external_validation_no_refit",
                    "label": "NHANES external validation after unit harmonization",
                    "n": 7408,
                    "denominator_n": 23195,
                },
            ],
            "endpoint_inventory": [
                {"endpoint_id": "china_mortality", "label": "China 5-year all-cause mortality", "event_n": 309},
                {"endpoint_id": "nhanes_mortality", "label": "NHANES 5-year all-cause mortality", "event_n": 704},
            ],
            "design_panels": [
                {
                    "panel_id": "model_input_boundary",
                    "layout_role": "wide_bottom",
                    "title": "Model-input boundary",
                    "lines": [
                        {
                            "label": "Validation policy",
                            "detail": "External validation only; no NHANES refitting or treatment-effect claim.",
                        }
                    ],
                }
            ],
        },
    )

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(
                _minimal_layout_sidecar_for_template(full_template_id, display_payload),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["source_hydration"]["preserved_current_generated_sources"] == ["paper/cohort_flow.json"]
    assert "paper/cohort_flow.json" not in result["source_hydration"]["hydrated_files"]
    cohort_flow = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    assert cohort_flow["status"] == "materialized_from_current_transportability_layout"
    assert cohort_flow["flow_mode"] == "source_layer_accounting"
    assert [item["step_id"] for item in cohort_flow["steps"]] == ["harmonized_diabetes_analysis_sources"]
    assert [item["layer_id"] for item in cohort_flow["source_layers"]] == [
        "china_development_source",
        "nhanes_validation_source",
    ]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_materialize_display_surface_accepts_legacy_full_right_sidecar_role(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation and split schema",
            "steps": [
                {"step_id": "source_total", "label": "Source study records", "n": 409, "detail": "Institutional cleaned cohort"},
                {"step_id": "analysis", "label": "Analyzed cohort", "n": 357, "detail": "Observed resection status"},
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "non_gtr",
                    "label": "Early residual / non-GTR",
                    "n": 57,
                    "detail": "Primary endpoint",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "split_schema",
                    "block_type": "full_right",
                    "title": "Center-based split schema",
                    "items": [
                        {"label": "Derivation centers", "detail": "n=200"},
                        {"label": "Validation centers", "detail": "n=157"},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8")
    )
    panel_roles = {item["layout_role"] for item in layout_sidecar["metrics"]["design_panels"]}
    assert "wide_top" in panel_roles
    assert "full_right" not in panel_roles


def test_materialize_display_surface_keeps_design_summary_inputs_out_of_figure_canvas(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly and analytic design",
            "caption": "Study flow with explicit analytic design hierarchy.",
            "steps": [
                {"step_id": "screened", "label": "Screened records", "n": 409, "detail": "Source population"},
                {"step_id": "included", "label": "Included cohort", "n": 357, "detail": "Primary surgery cases"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Removed before first-surgery cohort lock",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "5-fold outer repeats", "detail": "4-fold inner tuning"}],
                },
                {
                    "block_id": "core",
                    "block_type": "left_middle",
                    "title": "Core model",
                    "items": [{"label": "Comparator", "detail": "Confirmed preoperative baseline"}],
                },
                {
                    "block_id": "primary",
                    "block_type": "right_middle",
                    "title": "Primary model",
                    "items": [{"label": "Clinical utility", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "audit",
                    "block_type": "left_bottom",
                    "title": "Secondary model",
                    "items": [{"label": "Pathology audit", "detail": "Bounded postoperative audit"}],
                },
                {
                    "block_id": "context",
                    "block_type": "right_bottom",
                    "title": "Contextual models",
                    "items": [{"label": "Benchmark ceilings", "detail": "Context only"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
    layout_boxes = {item["box_id"]: item for item in layout["layout_boxes"]}
    guide_boxes = {item["box_id"]: item for item in layout["guide_boxes"]}

    assert layout["metrics"]["layout_mode"] == "participant_flow"
    assert layout["metrics"]["design_panels"]
    assert "participant_flow_main" in panel_boxes
    assert "title" not in layout_boxes
    assert "participant_design_context" not in layout_boxes
    assert not any(item["box_type"] == "design_context_note" for item in layout["layout_boxes"])
    assert not any(item["box_type"] == "context_note" for item in layout["layout_boxes"])
    assert not any(item["box_type"] == "summary_panel" for item in layout["layout_boxes"])
    assert "flow_spine_screened_to_included" in guide_boxes


def test_materialize_display_surface_normalizes_dense_participant_flow_sidecar(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "DPCC cohort assembly and analytic support set",
            "caption": "Participant-accounting flow with repeated-visit support sets.",
            "steps": [
                {"step_id": "deidentified_release_visits", "label": "Deidentified release visits", "n": 56420},
                {"step_id": "processed_patients", "label": "Processed patients", "n": 21384},
                {"step_id": "index_analysis_cohort", "label": "Index analysis cohort", "n": 16642},
                {"step_id": "repeated_visit_support_panel", "label": "Repeated visit support panel", "n": 9135},
                {"step_id": "transition_eligible_support_set", "label": "Transition-eligible support set", "n": 6830},
            ],
            "sidecar_blocks": [
                {
                    "block_id": "site_support",
                    "block_type": "wide_top",
                    "title": "Site-held-out support",
                    "items": [{"label": "Held-out sites", "detail": "Transportability and treatment-gap evidence"}],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    for section in ("layout_boxes", "panel_boxes", "guide_boxes"):
        for index, box in enumerate(layout[section]):
            assert 0 <= box["x0"] <= box["x1"] <= 1, (section, index, box)
            assert 0 <= box["y0"] <= box["y1"] <= 1, (section, index, box)
    layout_boxes = {item["box_id"]: item for item in layout["layout_boxes"]}
    assert "title" not in layout_boxes
    assert layout["metrics"]["source_renderer"] == "MAS/ReportingFlow::cohort_flow_figure"
    assert layout["metrics"]["figure_purpose"] == "participant_accounting_and_strobe_consort_flow"
    assert layout["metrics"]["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"
    assert "generated_fallback_renderer" not in layout["metrics"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    entry = figure_catalog["figures"][0]
    assert entry["source_renderer"] == "MAS/ReportingFlow::cohort_flow_figure"
    assert entry["figure_purpose"] == "participant_accounting_and_strobe_consort_flow"
    assert entry["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"


def test_materialize_display_surface_renders_source_layer_accounting_without_sequential_spine(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort and source-layer accounting",
            "caption": "Cohort denominator and source layers with Xiangya2 subcohort coverage.",
            "flow_mode": "source_layer_accounting",
            "denominator_step_id": "registry_records",
            "steps": [
                {"step_id": "registry_records", "label": "Declared analytic registry records", "n": 4189},
                {"step_id": "alliance_platform_records", "label": "Alliance platform source layer", "n": 2451},
                {"step_id": "xiangya2_management_records", "label": "Xiangya2 management clinic source layer", "n": 1204},
                {"step_id": "xiangya2_precision_records", "label": "Xiangya2 precision clinic source layer", "n": 534},
            ],
            "source_layers": [
                {
                    "layer_id": "alliance_platform_records",
                    "step_id": "alliance_platform_records",
                    "label": "Alliance platform source layer",
                    "n": 2451,
                },
                {
                    "layer_id": "xiangya2_management_records",
                    "step_id": "xiangya2_management_records",
                    "label": "Xiangya2 management clinic source layer",
                    "n": 1204,
                },
                {
                    "layer_id": "xiangya2_precision_records",
                    "step_id": "xiangya2_precision_records",
                    "label": "Xiangya2 precision clinic source layer",
                    "n": 534,
                },
            ],
            "subcohort_coverage": [
                {
                    "coverage_id": "xiangya2_subcohort",
                    "label": "Xiangya2 subcohort",
                    "n": 1748,
                    "denominator_n": 4189,
                },
                {
                    "coverage_id": "phq9_available",
                    "label": "PHQ-9 available",
                    "n": 979,
                    "denominator_n": 1748,
                },
                {
                    "coverage_id": "gad7_available",
                    "label": "GAD-7 available",
                    "n": 993,
                    "denominator_n": 1748,
                },
            ],
            "exported_centers": 33,
            "exclusions": [],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    assert layout["metrics"]["layout_mode"] == "source_layer_accounting"
    assert layout["metrics"]["layout_generation"] == "scholarskills_cohort_flow_v2"
    assert layout["metrics"]["flow_visual_policy"] == "purpose_first_reporting_flow_no_legacy_card_shell"
    assert layout["metrics"]["figure_title_policy"] == "metadata_only_no_drawn_title"
    assert layout["metrics"]["reporting_flow_kind"] == "cohort_source_layer_and_subcohort_coverage"
    assert layout["metrics"]["figure_purpose"] == "participant_accounting_and_strobe_source_boundary"
    assert layout["metrics"]["uses_ggconsort"] is True
    assert [item["n"] for item in layout["metrics"]["source_layers"]] == [2451, 1204, 534]
    assert [item["n"] for item in layout["metrics"]["subcohort_coverage"]] == [1748, 979, 993]
    assert layout["metrics"]["exported_centers"] == 33
    assert not any(item["box_type"] == "flow_connector" for item in layout["guide_boxes"])
    assert any(item["box_type"] == "source_layer_connector" for item in layout["guide_boxes"])
    assert any(item["box_type"] == "source_layer_box" for item in layout["layout_boxes"])
    assert any(item["box_type"] == "coverage_step" for item in layout["layout_boxes"])
    assert any(item["box_type"] == "coverage_flow_connector" for item in layout["guide_boxes"])
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    entry = figure_catalog["figures"][0]
    assert entry["qc_result"]["status"] == "pass"
    assert entry["figure_purpose"] == "participant_accounting_and_strobe_source_boundary"


def test_visual_audit_blocks_legacy_cohort_flow_sidecar_without_scholarskills_v2_policy(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    figure_path = paper_root / "figures" / "generated" / "F1_cohort_flow.png"
    layout_path = paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.write_text("not a real png but sufficient for artifact hashing", encoding="utf-8")
    dump_json(
        layout_path,
        {
            "template_id": "cohort_flow_figure",
            "metrics": {
                "layout_mode": "source_layer_accounting",
                "renderer_family": "r_ggplot2",
                "uses_ggconsort": True,
            },
        },
    )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "figures": [
                {
                    "figure_id": "F1",
                    "export_paths": ["paper/figures/generated/F1_cohort_flow.png"],
                    "qc_result": {
                        "layout_sidecar_path": "paper/figures/generated/F1_cohort_flow.layout.json",
                    },
                }
            ]
        },
    )

    result = module.materialize_display_visual_audit(paper_root=paper_root)

    assert result["visual_audit_receipt"]["final_status"] == "findings_open"
    receipt = json.loads((paper_root / "figure_visual_audit_receipt.json").read_text(encoding="utf-8"))
    assert receipt["findings"][0]["promotion_decision"] == "promote_to_qc"
