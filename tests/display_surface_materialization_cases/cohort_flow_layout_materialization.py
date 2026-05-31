from .shared import *


def test_materialize_display_surface_renders_cohort_flow_with_exclusions_and_design_panels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
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
    svg_text = (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").read_text(encoding="utf-8")
    assert "Cohort derivation, exclusions, and study design" not in svg_text
    assert "Repeat or" in svg_text
    assert "salvage" in svg_text
    assert "Endpoint inventory" in svg_text
    assert "Validation framework" in svg_text
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"
    assert qc_result["qc_profile"] == "publication_illustration_flow"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")


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


def test_materialize_display_surface_renders_cohort_flow_with_two_subfigure_panels_and_role_aware_grid(
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

    assert "subfigure_panel_A" in panel_boxes
    assert "subfigure_panel_B" in panel_boxes
    assert "title" not in layout_boxes
    assert "panel_label_A" in layout_boxes
    assert "panel_label_B" in layout_boxes
    assert panel_boxes["secondary_panel_validation"]["x0"] <= panel_boxes["secondary_panel_core"]["x0"]
    assert panel_boxes["secondary_panel_validation"]["x1"] >= panel_boxes["secondary_panel_primary"]["x1"]
    assert panel_boxes["secondary_panel_core"]["x1"] < panel_boxes["secondary_panel_primary"]["x0"]
    assert panel_boxes["secondary_panel_audit"]["x1"] < panel_boxes["secondary_panel_context"]["x0"]
    assert panel_boxes["secondary_panel_core"]["y0"] > panel_boxes["secondary_panel_audit"]["y1"]
    assert "hierarchy_root_trunk" in guide_boxes
    assert "hierarchy_root_branch" in guide_boxes
    assert "hierarchy_connector_left_middle_to_left_bottom" in guide_boxes
    assert "hierarchy_connector_right_middle_to_right_bottom" in guide_boxes
