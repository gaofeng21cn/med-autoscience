from .shared import *

def test_materialize_display_surface_centers_rooted_hierarchy_branch_connectors_on_target_panels(
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
                {
                    "step_id": "screened",
                    "label": "Screened institutional NF-PitNET records",
                    "n": 409,
                    "detail": "Source population before first-surgery eligibility filtering",
                },
                {
                    "step_id": "included",
                    "label": "Included: first-surgery NF-PitNET cohort",
                    "n": 357,
                    "detail": "Eligible primary surgery cases",
                },
                {
                    "step_id": "analysis",
                    "label": "Included in final analysis cohort",
                    "n": 357,
                    "detail": "Observed early postoperative MRI-based resection status",
                },
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Not eligible for the first-surgery analysis cohort",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Repeated nested validation",
                    "items": [{"label": "5-fold outer x 20 repeats", "detail": "4-fold inner tuning"}],
                },
                {
                    "block_id": "core",
                    "block_type": "left_middle",
                    "title": "Core model",
                    "items": [{"label": "Preoperative Core Model", "detail": "Confirmed comparator"}],
                },
                {
                    "block_id": "primary",
                    "block_type": "right_middle",
                    "title": "Primary model",
                    "items": [{"label": "Clinical Utility Model", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "audit",
                    "block_type": "left_bottom",
                    "title": "Secondary model",
                    "items": [{"label": "Pathology-Augmented Model", "detail": "Secondary postoperative comparison"}],
                },
                {
                    "block_id": "context",
                    "block_type": "right_bottom",
                    "title": "Contextual models",
                    "items": [{"label": "Elastic-Net / Random-Forest", "detail": "Contextual comparison models"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    boxes = {item["box_id"]: item for item in layout["layout_boxes"] + layout["panel_boxes"] + layout["guide_boxes"]}

    def center_x(box: dict[str, float]) -> float:
        return (float(box["x0"]) + float(box["x1"])) / 2.0

    assert abs(center_x(boxes["hierarchy_connector_branch_to_left"]) - center_x(boxes["secondary_panel_core"])) < 0.01
    assert abs(center_x(boxes["hierarchy_connector_branch_to_right"]) - center_x(boxes["secondary_panel_primary"])) < 0.01

def test_materialize_display_surface_uses_readable_card_typography_for_cohort_flow(tmp_path: Path) -> None:
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
                {
                    "step_id": "screened",
                    "label": "Screened institutional NF-PitNET records",
                    "n": 409,
                    "detail": "Source population before first-surgery eligibility filtering",
                },
                {
                    "step_id": "included",
                    "label": "Included: first-surgery NF-PitNET cohort",
                    "n": 357,
                    "detail": "Eligible primary surgery cases",
                },
                {
                    "step_id": "analysis",
                    "label": "Included in final analysis cohort",
                    "n": 357,
                    "detail": "Observed early postoperative MRI-based resection status",
                },
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Not eligible for the first-surgery analysis cohort",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Repeated nested validation",
                    "items": [{"label": "5-fold outer x 20 repeats", "detail": "4-fold inner tuning"}],
                },
                {
                    "block_id": "core",
                    "block_type": "left_middle",
                    "title": "Core model",
                    "items": [{"label": "Preoperative Core Model", "detail": "Confirmed comparator"}],
                },
                {
                    "block_id": "primary",
                    "block_type": "right_middle",
                    "title": "Primary model",
                    "items": [{"label": "Clinical Utility Model", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "audit",
                    "block_type": "left_bottom",
                    "title": "Secondary model",
                    "items": [{"label": "Pathology-Augmented Model", "detail": "Secondary postoperative comparison"}],
                },
                {
                    "block_id": "context",
                    "block_type": "right_bottom",
                    "title": "Contextual models",
                    "items": [{"label": "Elastic-Net / Random-Forest", "detail": "Contextual comparison models"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    svg_text = (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").read_text(encoding="utf-8")
    assert extract_svg_font_size(svg_text, "Screened institutional NF-PitNET") >= 10.9
    assert extract_svg_font_size(svg_text, "Repeated nested validation") >= 10.5
    assert extract_svg_font_size(svg_text, "Preoperative Core Model") >= 9.3
    assert extract_svg_font_size(svg_text, "5-fold outer x 20 repeats") >= 9.0

def test_materialize_display_surface_anchors_exclusion_branch_to_split_stage(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly with stage-anchored exclusions",
            "steps": [
                {"step_id": "screened", "label": "Screened records", "n": 409, "detail": "Source population"},
                {"step_id": "included", "label": "Included cohort", "n": 357, "detail": "Primary surgery cases"},
                {"step_id": "analysis", "label": "Analysis cohort", "n": 357, "detail": "Observed endpoint"},
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
                }
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    layout_boxes = {item["box_id"]: item for item in layout["layout_boxes"]}
    guide_boxes = {item["box_id"]: item for item in layout["guide_boxes"]}
    screened = layout_boxes["step_screened"]
    included = layout_boxes["step_included"]
    analysis = layout_boxes["step_analysis"]
    exclusion = layout_boxes["exclusion_repeat"]
    branch = guide_boxes["flow_branch_repeat"]

    def center_x(box: dict[str, float]) -> float:
        return (float(box["x0"]) + float(box["x1"])) / 2.0

    exclusion_center_y = (float(exclusion["y0"]) + float(exclusion["y1"])) / 2.0
    assert abs(center_x(screened) - center_x(included)) < 0.02
    assert abs(center_x(included) - center_x(analysis)) < 0.02
    assert float(exclusion["x0"]) > float(screened["x1"])
    assert float(included["y1"]) <= exclusion_center_y <= float(screened["y0"])
    assert float(branch["y0"]) >= float(included["y1"])
    assert float(branch["y1"]) <= float(screened["y0"])

def test_materialize_display_surface_renders_sparse_modern_cohort_flow_without_panel_b_overlap(
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
            "title": "Sparse modern cohort flow",
            "caption": "Panel B stays hierarchical without overlapping sparse-role cards.",
            "steps": [
                {"step_id": "locked", "label": "Source study records", "n": 409},
                {"step_id": "first_surgery", "label": "First-surgery NF-PitNET cases", "n": 357},
                {"step_id": "analysis", "label": "Analyzed first-surgery cohort", "n": 357},
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "early_residual",
                    "label": "Early residual / non-GTR",
                    "detail": "Primary manuscript endpoint",
                    "event_n": 57,
                }
            ],
            "design_panels": [
                {
                    "panel_id": "validation_contract",
                    "layout_role": "wide_top",
                    "style_role": "secondary",
                    "title": "Validation design",
                    "lines": [
                        {
                            "label": "Repeated nested validation",
                            "detail": "20 repeats x 5 outer folds; 4-fold inner tuning",
                        }
                    ],
                },
                {
                    "panel_id": "model_hierarchy",
                    "layout_role": "right_bottom",
                    "style_role": "secondary",
                    "title": "Model comparison frame",
                    "lines": [
                        {"label": "Core preoperative model", "detail": "Confirmed comparator"},
                        {"label": "Clinically informed preoperative model", "detail": "Primary knowledge-guided model"},
                    ],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
    validation_box = panel_boxes["secondary_panel_validation_contract"]
    model_box = panel_boxes["secondary_panel_model_hierarchy"]
    footer_box = panel_boxes["secondary_panel_endpoint_inventory"]

    assert validation_box["y0"] > model_box["y1"]
    assert model_box["y0"] > footer_box["y1"]
    assert validation_box["x0"] < model_box["x1"]
    assert validation_box["x1"] > model_box["x0"]

def test_materialize_display_surface_supports_sparse_wide_bottom_panel_role(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation and score construction",
            "caption": "Sparse modern hierarchy supports a wide-bottom contract block.",
            "steps": [
                {"step_id": "source", "label": "Source cohort", "n": 409, "detail": "Study population"},
                {"step_id": "analysis", "label": "Final analysis cohort", "n": 357, "detail": "Eligible cases"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat_salvage",
                    "from_step_id": "source",
                    "label": "Excluded: repeat or salvage surgery",
                    "n": 52,
                    "detail": "Removed before first-surgery cohort lock",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "Repeated nested validation", "detail": "5-fold outer x 20 repeats; 4-fold inner tuning"}],
                },
                {
                    "block_id": "score_rule",
                    "block_type": "wide_bottom",
                    "title": "Grouped rule",
                    "items": [{"label": "Low / intermediate / high risk", "detail": "Study-defined grouped contract"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
    validation_box = panel_boxes["secondary_panel_validation"]
    bottom_box = panel_boxes["secondary_panel_score_rule"]

    assert validation_box["y0"] > bottom_box["y1"]
    assert validation_box["x0"] < bottom_box["x1"]
    assert validation_box["x1"] > bottom_box["x0"]

def test_materialize_display_surface_records_render_context_for_cohort_flow(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly",
            "steps": [{"step_id": "screened", "label": "Screened", "n": 409, "detail": "Source population"}],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "5-fold outer repeats", "detail": "4-fold inner tuning"}],
                }
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    assert layout["render_context"]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert "style_roles" in layout["render_context"]
    assert "palette" in layout["render_context"]

def test_materialize_display_surface_expands_exclusion_box_for_wrapped_copy(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly with exclusion accounting",
            "caption": "Source-to-analysis cohort derivation with explicit inclusion and exclusion accounting.",
            "steps": [
                {
                    "step_id": "source_total",
                    "label": "Screened institutional NF-PitNET records",
                    "n": 409,
                    "detail": "Source population before first-surgery eligibility filtering",
                },
                {
                    "step_id": "first_surgery",
                    "label": "Included: first-surgery NF-PitNET cohort",
                    "n": 357,
                    "detail": "Eligible primary surgery cases",
                },
                {
                    "step_id": "analysis",
                    "label": "Included in final analysis cohort",
                    "n": 357,
                    "detail": "Observed early postoperative MRI-based resection status",
                },
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat_salvage",
                    "from_step_id": "source_total",
                    "label": "Excluded: repeat or salvage surgery",
                    "n": 52,
                    "detail": "Removed before locking the first-surgery analysis cohort",
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
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8")
    )
    exclusion_box = next(
        item for item in layout_sidecar["layout_boxes"] if item["box_id"] == "exclusion_repeat_salvage"
    )
    assert exclusion_box["y1"] - exclusion_box["y0"] >= 0.10
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_registered_evidence_figures(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_evidence=True)
    render_calls: list[dict[str, str]] = []
    original_loader = module.display_pack_runtime.load_python_plugin_callable

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(
            {
                "template_id": template_id,
                "display_id": str(display_payload.get("display_id") or ""),
            }
        )

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if display_registry.is_evidence_figure_template(template_id):
            return fake_render_r_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5", "F6"]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.pdf").exists()
    assert {item["template_id"] for item in render_calls} == {
        full_id("roc_curve_binary"),
        full_id("pr_curve_binary"),
        full_id("calibration_curve_binary"),
        full_id("decision_curve_binary"),
        full_id("kaplan_meier_grouped"),
    }

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F2"]["template_id"] == full_id("roc_curve_binary")
    assert figures_by_id["F2"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["F2"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F2"]["input_schema_id"] == "binary_prediction_curve_inputs_v1"
    assert figures_by_id["F5"]["qc_profile"] == "publication_evidence_curve"
    assert figures_by_id["F6"]["template_id"] == full_id("kaplan_meier_grouped")
    assert figures_by_id["F6"]["input_schema_id"] == "time_to_event_grouped_inputs_v1"

def test_materialize_display_surface_generates_full_registered_template_set(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    render_calls: list[tuple[str, str]] = []
    original_loader = module.display_pack_runtime.load_python_plugin_callable

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append((template_id, str(display_payload.get("display_id") or "")))

    def fake_render_python_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append((template_id, str(display_payload.get("display_id") or "")))

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if display_registry.is_evidence_figure_template(template_id):
            spec = display_registry.get_evidence_figure_spec(template_id)
            if spec.renderer_family == "r_ggplot2":
                return fake_render_r_evidence_figure
            return fake_render_python_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == [
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
        "F9",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
        "F20",
        "F21",
        "F22",
        "F23",
        "F24",
        "F25",
    ]
    assert result["tables_materialized"] == ["T1", "T2", "T3"]
    assert (paper_root / "figures" / "generated" / "F7_cumulative_incidence_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F8_umap_scatter_grouped.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F10_heatmap_group_comparison.png").exists()
    assert (paper_root / "figures" / "generated" / "F12_forest_effect_main.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F13_shap_summary_beeswarm.png").exists()
    assert (paper_root / "figures" / "generated" / "F14_time_to_event_discrimination_calibration_panel.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F15_time_to_event_risk_group_summary.png").exists()
    assert (paper_root / "figures" / "generated" / "F16_time_to_event_decision_curve.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F17_multicenter_generalizability_overview.png").exists()
    assert (paper_root / "figures" / "generated" / "F18_time_dependent_roc_horizon.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F19_tsne_scatter_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F20_subgroup_forest.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F21_clustered_heatmap.png").exists()
    assert (paper_root / "figures" / "generated" / "F22_clinical_impact_curve_binary.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F23_multivariable_forest.png").exists()
    assert (paper_root / "figures" / "generated" / "F24_phate_scatter_grouped.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F25_diffusion_map_scatter_grouped.png").exists()
    assert (paper_root / "tables" / "generated" / "T2_time_to_event_performance_summary.md").exists()
    assert (paper_root / "tables" / "generated" / "T3_clinical_interpretation_summary.md").exists()
    assert {template_id for template_id, _ in render_calls} == {
        full_id("roc_curve_binary"),
        full_id("pr_curve_binary"),
        full_id("calibration_curve_binary"),
        full_id("decision_curve_binary"),
        full_id("time_dependent_roc_horizon"),
        full_id("kaplan_meier_grouped"),
        full_id("cumulative_incidence_grouped"),
        full_id("umap_scatter_grouped"),
        full_id("pca_scatter_grouped"),
        full_id("tsne_scatter_grouped"),
        full_id("heatmap_group_comparison"),
        full_id("correlation_heatmap"),
        full_id("clustered_heatmap"),
        full_id("clinical_impact_curve_binary"),
        full_id("forest_effect_main"),
        full_id("multivariable_forest"),
        full_id("subgroup_forest"),
        full_id("phate_scatter_grouped"),
        full_id("diffusion_map_scatter_grouped"),
        full_id("shap_summary_beeswarm"),
        full_id("time_to_event_discrimination_calibration_panel"),
        full_id("time_to_event_risk_group_summary"),
        full_id("time_to_event_decision_curve"),
        full_id("multicenter_generalizability_overview"),
    }

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F7"]["template_id"] == full_id("cumulative_incidence_grouped")
    assert figures_by_id["F8"]["input_schema_id"] == "embedding_grouped_inputs_v1"
    assert figures_by_id["F10"]["qc_profile"] == "publication_heatmap"
    assert figures_by_id["F12"]["qc_profile"] == "publication_forest_plot"
    assert figures_by_id["F13"]["renderer_family"] == "python"
    assert figures_by_id["F13"]["input_schema_id"] == "shap_summary_inputs_v1"
    assert figures_by_id["F14"]["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert figures_by_id["F15"]["qc_profile"] == "publication_survival_curve"
    assert figures_by_id["F16"]["qc_profile"] == "publication_decision_curve"
    assert figures_by_id["F17"]["qc_profile"] == "publication_multicenter_overview"
    assert figures_by_id["F18"]["template_id"] == full_id("time_dependent_roc_horizon")
    assert figures_by_id["F18"]["input_schema_id"] == "binary_prediction_curve_inputs_v1"
    assert figures_by_id["F19"]["template_id"] == full_id("tsne_scatter_grouped")
    assert figures_by_id["F19"]["qc_profile"] == "publication_embedding_scatter"
    assert figures_by_id["F20"]["template_id"] == full_id("subgroup_forest")
    assert figures_by_id["F20"]["qc_profile"] == "publication_forest_plot"
    assert figures_by_id["F21"]["template_id"] == full_id("clustered_heatmap")
    assert figures_by_id["F21"]["input_schema_id"] == "clustered_heatmap_inputs_v1"
    assert figures_by_id["F21"]["qc_profile"] == "publication_heatmap"
    assert figures_by_id["F22"]["template_id"] == full_id("clinical_impact_curve_binary")
    assert figures_by_id["F22"]["input_schema_id"] == "binary_prediction_curve_inputs_v1"
    assert figures_by_id["F22"]["qc_profile"] == "publication_evidence_curve"
    assert figures_by_id["F23"]["template_id"] == full_id("multivariable_forest")
    assert figures_by_id["F23"]["input_schema_id"] == "forest_effect_inputs_v1"
    assert figures_by_id["F23"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F24"]["template_id"] == full_id("phate_scatter_grouped")
    assert figures_by_id["F24"]["input_schema_id"] == "embedding_grouped_inputs_v1"
    assert figures_by_id["F24"]["qc_profile"] == "publication_embedding_scatter"
    assert figures_by_id["F25"]["template_id"] == full_id("diffusion_map_scatter_grouped")
    assert figures_by_id["F25"]["input_schema_id"] == "embedding_grouped_inputs_v1"
    assert figures_by_id["F25"]["qc_profile"] == "publication_embedding_scatter"

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {item["table_id"]: item for item in table_catalog["tables"]}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("table2_time_to_event_performance_summary")
    assert tables_by_id["T2"]["qc_profile"] == "publication_table_performance"
    assert tables_by_id["T3"]["table_shell_id"] == full_id("table3_clinical_interpretation_summary")
    assert tables_by_id["T3"]["qc_profile"] == "publication_table_interpretation"

def test_render_python_evidence_figure_prefers_pack_entrypoint_for_migrated_python_template(
    tmp_path: Path,
    monkeypatch,
) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    output_png_path = tmp_path / "output.png"
    output_pdf_path = tmp_path / "output.pdf"
    layout_sidecar_path = tmp_path / "output.layout.json"
    template_id = full_id("time_to_event_risk_group_summary")
    render_calls: list[str] = []

    def fake_external_renderer(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(str(display_payload["display_id"]))

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "resolve_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )

    controller_module._render_python_evidence_figure(
        template_id=template_id,
        display_payload={
            "display_id": "F3",
            "risk_group_summaries": [
                {
                    "label": "Low risk",
                    "sample_size": 72,
                    "events_5y": 4,
                    "mean_predicted_risk_5y": 0.08,
                    "observed_km_risk_5y": 0.06,
                }
            ],
        },
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    assert render_calls == ["F3"]
    assert output_png_path.read_text(encoding="utf-8") == "PNG"
    assert output_pdf_path.read_text(encoding="utf-8") == "%PDF"
    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["template_id"] == template_id

def test_materialize_display_surface_materializes_optional_submission_graphical_abstract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "submission_graphical_abstract.json",
        {
            "schema_version": 1,
            "shell_id": "submission_graphical_abstract",
            "display_id": "submission_graphical_abstract",
            "catalog_id": "GA1",
            "paper_role": "submission_companion",
            "title": "Submission companion overview",
            "caption": "A programmatic graphical abstract aligned to the audited paper-facing surface.",
            "panels": [
                {
                    "panel_id": "cohort_split",
                    "panel_label": "A",
                    "title": "Cohort and split",
                    "subtitle": "Locked analysis cohort",
                    "rows": [{"cards": [{"card_id": "analytic", "title": "Analytic cohort", "value": "15,787", "detail": "Formal modeling cohort"}]}],
                },
                {
                    "panel_id": "primary_endpoint",
                    "panel_label": "B",
                    "title": "Primary endpoint",
                    "subtitle": "Cardiovascular mortality",
                    "rows": [{"cards": [{"card_id": "ridge", "title": "Validation C-index", "value": "0.857", "detail": "Primary five-year endpoint", "accent_role": "primary"}]}],
                },
                {
                    "panel_id": "supportive_context",
                    "panel_label": "C",
                    "title": "Supportive context",
                    "subtitle": "Applicability boundary",
                    "rows": [{"cards": [{"card_id": "boundary", "title": "Transportability boundary", "value": "No external validation", "detail": "Internal cohort only", "accent_role": "audit"}]}],
                },
            ],
            "footer_pills": [
                {"pill_id": "p1", "panel_id": "cohort_split", "label": "Internal validation only", "style_role": "neutral"},
                {"pill_id": "p2", "panel_id": "primary_endpoint", "label": "Supportive endpoint retained", "style_role": "secondary"},
                {"pill_id": "p3", "panel_id": "supportive_context", "label": "No external validation", "style_role": "audit"},
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert "GA1" in result["figures_materialized"]
    assert (paper_root / "figures" / "generated" / "GA1_graphical_abstract.svg").exists()
    assert (paper_root / "figures" / "generated" / "GA1_graphical_abstract.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["GA1"]["template_id"] == full_id("submission_graphical_abstract")
    assert figures_by_id["GA1"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["GA1"]["qc_profile"] == "submission_graphical_abstract"
    assert figures_by_id["GA1"]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_workflow_fact_sheet_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure2",
                    "display_kind": "figure",
                    "requirement_key": "workflow_fact_sheet_panel",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "workflow_fact_sheet_panel.json", _make_workflow_fact_sheet_panel_payload())

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F2"]
    assert (paper_root / "figures" / "generated" / "F2_workflow_fact_sheet_panel.svg").exists()
    assert (paper_root / "figures" / "generated" / "F2_workflow_fact_sheet_panel.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F2"]["template_id"] == full_id("workflow_fact_sheet_panel")
    assert figures_by_id["F2"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["F2"]["input_schema_id"] == "workflow_fact_sheet_panel_inputs_v1"
    assert figures_by_id["F2"]["qc_profile"] == "publication_workflow_fact_sheet_panel"
    assert figures_by_id["F2"]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_design_evidence_composite_shell(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure3",
                    "display_kind": "figure",
                    "requirement_key": "design_evidence_composite_shell",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/Figure3.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "design_evidence_composite_shell.json", _make_design_evidence_composite_shell_payload())

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F3"]
    assert (paper_root / "figures" / "generated" / "F3_design_evidence_composite_shell.svg").exists()
    assert (paper_root / "figures" / "generated" / "F3_design_evidence_composite_shell.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F3"]["template_id"] == full_id("design_evidence_composite_shell")
    assert figures_by_id["F3"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["F3"]["input_schema_id"] == "design_evidence_composite_shell_inputs_v1"
    assert figures_by_id["F3"]["qc_profile"] == "publication_design_evidence_composite_shell"
    assert figures_by_id["F3"]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_baseline_missingness_qc_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure4",
                    "display_kind": "figure",
                    "requirement_key": "baseline_missingness_qc_panel",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/Figure4.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "baseline_missingness_qc_panel.json", _make_baseline_missingness_qc_panel_payload())

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F4"]
    assert (paper_root / "figures" / "generated" / "F4_baseline_missingness_qc_panel.svg").exists()
    assert (paper_root / "figures" / "generated" / "F4_baseline_missingness_qc_panel.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F4"]["template_id"] == full_id("baseline_missingness_qc_panel")
    assert figures_by_id["F4"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["F4"]["input_schema_id"] == "baseline_missingness_qc_panel_inputs_v1"
    assert figures_by_id["F4"]["qc_profile"] == "publication_baseline_missingness_qc_panel"
    assert figures_by_id["F4"]["qc_result"]["status"] == "pass"
