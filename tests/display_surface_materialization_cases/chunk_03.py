from .shared import *

def test_materialize_display_surface_generates_center_coverage_batch_transportability_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure47",
                    "display_kind": "figure",
                    "requirement_key": "center_coverage_batch_transportability_panel",
                    "catalog_id": "F47",
                    "shell_path": "paper/figures/Figure47.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(
        paper_root / "center_coverage_batch_transportability_panel.json",
        _make_center_coverage_batch_transportability_panel_payload(),
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F47"]
    assert (paper_root / "figures" / "generated" / "F47_center_coverage_batch_transportability_panel.svg").exists()
    assert (paper_root / "figures" / "generated" / "F47_center_coverage_batch_transportability_panel.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F47"]["template_id"] == full_id("center_coverage_batch_transportability_panel")
    assert figures_by_id["F47"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["F47"]["input_schema_id"] == "center_coverage_batch_transportability_panel_inputs_v1"
    assert figures_by_id["F47"]["qc_profile"] == "publication_center_coverage_batch_transportability_panel"
    assert figures_by_id["F47"]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_transportability_recalibration_governance_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure48",
                    "display_kind": "figure",
                    "requirement_key": "transportability_recalibration_governance_panel",
                    "catalog_id": "F48",
                    "shell_path": "paper/figures/Figure48.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(
        paper_root / "transportability_recalibration_governance_panel.json",
        _make_transportability_recalibration_governance_panel_payload(),
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F48"]
    assert (paper_root / "figures" / "generated" / "F48_transportability_recalibration_governance_panel.svg").exists()
    assert (paper_root / "figures" / "generated" / "F48_transportability_recalibration_governance_panel.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F48"]["template_id"] == full_id("transportability_recalibration_governance_panel")
    assert figures_by_id["F48"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["F48"]["input_schema_id"] == "transportability_recalibration_governance_panel_inputs_v1"
    assert figures_by_id["F48"]["qc_profile"] == "publication_transportability_recalibration_governance_panel"
    assert figures_by_id["F48"]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_uses_pack_runtime_for_workflow_fact_sheet_panel(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
                }
            ],
        },
    )
    dump_json(paper_root / "workflow_fact_sheet_panel.json", _make_workflow_fact_sheet_panel_payload())
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("workflow_fact_sheet_panel"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("workflow_fact_sheet_panel")]
    assert (paper_root / "figures" / "generated" / "F2_workflow_fact_sheet_panel.svg").exists()

def test_materialize_display_surface_uses_pack_runtime_for_design_evidence_composite_shell(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
                }
            ],
        },
    )
    dump_json(paper_root / "design_evidence_composite_shell.json", _make_design_evidence_composite_shell_payload())
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("design_evidence_composite_shell"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("design_evidence_composite_shell")]
    assert (paper_root / "figures" / "generated" / "F3_design_evidence_composite_shell.svg").exists()

def test_materialize_display_surface_uses_pack_runtime_for_baseline_missingness_qc_panel(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
                }
            ],
        },
    )
    dump_json(paper_root / "baseline_missingness_qc_panel.json", _make_baseline_missingness_qc_panel_payload())
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("baseline_missingness_qc_panel"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("baseline_missingness_qc_panel")]
    assert (paper_root / "figures" / "generated" / "F4_baseline_missingness_qc_panel.svg").exists()

def test_materialize_display_surface_uses_pack_runtime_for_center_coverage_batch_transportability_panel(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure47",
                    "display_kind": "figure",
                    "requirement_key": "center_coverage_batch_transportability_panel",
                    "catalog_id": "F47",
                }
            ],
        },
    )
    dump_json(
        paper_root / "center_coverage_batch_transportability_panel.json",
        _make_center_coverage_batch_transportability_panel_payload(),
    )
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("center_coverage_batch_transportability_panel"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("center_coverage_batch_transportability_panel")]
    assert (paper_root / "figures" / "generated" / "F47_center_coverage_batch_transportability_panel.svg").exists()

def test_materialize_display_surface_uses_pack_runtime_for_transportability_recalibration_governance_panel(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure48",
                    "display_kind": "figure",
                    "requirement_key": "transportability_recalibration_governance_panel",
                    "catalog_id": "F48",
                }
            ],
        },
    )
    dump_json(
        paper_root / "transportability_recalibration_governance_panel.json",
        _make_transportability_recalibration_governance_panel_payload(),
    )
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("transportability_recalibration_governance_panel"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("transportability_recalibration_governance_panel")]
    assert (paper_root / "figures" / "generated" / "F48_transportability_recalibration_governance_panel.svg").exists()

def test_materialize_display_surface_uses_pack_runtime_for_submission_graphical_abstract(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
                    "rows": [{"cards": [{"card_id": "analytic", "title": "Analytic cohort", "value": "15,787"}]}],
                }
            ],
            "footer_pills": [],
        },
    )
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("submission_graphical_abstract"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_render_submission_graphical_abstract",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("host submission graphical abstract renderer should not be used")
        ),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("submission_graphical_abstract")]
    assert (paper_root / "figures" / "generated" / "GA1_graphical_abstract.svg").exists()

def test_choose_submission_graphical_abstract_arrow_lane_prefers_shared_blank_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")

    lane_center_y = module._choose_submission_graphical_abstract_arrow_lane(
        left_panel_box={"x0": 10.0, "y0": 100.0, "x1": 210.0, "y1": 480.0},
        right_panel_box={"x0": 250.0, "y0": 100.0, "x1": 450.0, "y1": 480.0},
        left_occupied_boxes=(
            {"x0": 24.0, "y0": 120.0, "x1": 196.0, "y1": 190.0},
            {"x0": 24.0, "y0": 392.0, "x1": 196.0, "y1": 450.0},
        ),
        right_occupied_boxes=(
            {"x0": 264.0, "y0": 130.0, "x1": 436.0, "y1": 200.0},
            {"x0": 264.0, "y0": 382.0, "x1": 436.0, "y1": 440.0},
        ),
        clearance_pt=12.0,
        arrow_half_height_pt=18.0,
    )

    assert 240.0 <= lane_center_y <= 320.0

def test_choose_submission_graphical_abstract_arrow_lane_prefers_shared_midline_over_larger_top_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")

    lane_center_y = module._choose_submission_graphical_abstract_arrow_lane(
        left_panel_box={"x0": 10.0, "y0": 100.0, "x1": 210.0, "y1": 500.0},
        right_panel_box={"x0": 250.0, "y0": 100.0, "x1": 450.0, "y1": 500.0},
        left_occupied_boxes=(
            {"x0": 24.0, "y0": 240.0, "x1": 196.0, "y1": 280.0},
            {"x0": 24.0, "y0": 350.0, "x1": 196.0, "y1": 380.0},
        ),
        right_occupied_boxes=(
            {"x0": 264.0, "y0": 240.0, "x1": 436.0, "y1": 280.0},
            {"x0": 264.0, "y0": 350.0, "x1": 436.0, "y1": 380.0},
        ),
        clearance_pt=12.0,
        arrow_half_height_pt=18.0,
    )

    assert 300.0 <= lane_center_y <= 330.0

def test_materialize_display_surface_wraps_or_stacks_long_graphical_abstract_boundary_cards(tmp_path: Path) -> None:
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
                    "rows": [
                        {
                            "cards": [
                                {
                                    "card_id": "internal_boundary",
                                    "title": "Applicability boundary",
                                    "value": "Internal validation only",
                                    "detail": "Multicenter support inside the current cohort",
                                    "accent_role": "contrast",
                                },
                                {
                                    "card_id": "transportability_boundary",
                                    "title": "Transportability boundary",
                                    "value": "No external validation",
                                    "detail": "Do not expand beyond the audited cohort",
                                    "accent_role": "audit",
                                },
                            ]
                        }
                    ],
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
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["GA1"]["qc_result"]["status"] == "pass"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "GA1_graphical_abstract.layout.json").read_text(encoding="utf-8")
    )
    value_boxes = {
        item["box_id"]: item
        for item in layout_sidecar["layout_boxes"]
        if item["box_type"] == "card_value"
    }
    arrow_boxes = [
        item
        for item in layout_sidecar["guide_boxes"]
        if item["box_type"] == "arrow_connector"
    ]
    arrow_mid_ys = [((item["y0"] + item["y1"]) / 2.0) for item in arrow_boxes]
    assert value_boxes["supportive_context_internal_boundary_value"]["x1"] <= 1.0
    assert value_boxes["supportive_context_transportability_boundary_value"]["x1"] <= 1.0
    assert len(arrow_boxes) == 2
    assert max(arrow_mid_ys) - min(arrow_mid_ys) <= 0.03

def test_materialize_display_surface_supports_generic_anchor_table_shells(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    (paper_root / "figures").mkdir(parents=True)
    (paper_root / "tables").mkdir(parents=True)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "performance_summary",
                    "display_kind": "table",
                    "requirement_key": "performance_summary_table_generic",
                    "catalog_id": "T2",
                },
                {
                    "display_id": "grouped_risk_event_summary",
                    "display_kind": "table",
                    "requirement_key": "grouped_risk_event_summary_table",
                    "catalog_id": "T3",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "performance_summary_table_generic.json",
        {
            "schema_version": 1,
            "table_shell_id": "performance_summary_table_generic",
            "display_id": "performance_summary",
            "catalog_id": "T2",
            "title": "Unified repeated nested validation results across candidate packages",
            "caption": "Pooled out-of-fold discrimination, error, and calibration summaries across candidate packages.",
            "row_header_label": "Model",
            "columns": [
                {"column_id": "auroc", "label": "AUROC"},
                {"column_id": "auprc", "label": "AUPRC"},
            ],
            "rows": [
                {"row_id": "simple", "label": "Simple 3-month score", "values": ["0.7081", "0.4740"]},
                {"row_id": "core", "label": "Core logistic confirmation", "values": ["0.6987", "0.4556"]},
            ],
        },
    )
    dump_json(
        paper_root / "grouped_risk_event_summary_table.json",
        {
            "schema_version": 1,
            "table_shell_id": "grouped_risk_event_summary_table",
            "display_id": "grouped_risk_event_summary",
            "catalog_id": "T3",
            "title": "Event rates across score bands and grouped-risk strata",
            "caption": "Observed event counts and risks across score-band and grouped-risk strata.",
            "surface_column_label": "Surface",
            "stratum_column_label": "Stratum",
            "cases_column_label": "Cases",
            "events_column_label": "Events",
            "risk_column_label": "Risk",
            "rows": [
                {
                    "row_id": "score_band_0",
                    "surface": "Score band",
                    "stratum": "0",
                    "cases": 95,
                    "events": 8,
                    "risk_display": "8.4%",
                },
                {
                    "row_id": "grouped_risk_high",
                    "surface": "Grouped risk",
                    "stratum": "High",
                    "cases": 66,
                    "events": 37,
                    "risk_display": "56.1%",
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["tables_materialized"] == ["T2", "T3"]
    assert (paper_root / "tables" / "generated" / "T2_performance_summary_table_generic.csv").exists()
    assert (paper_root / "tables" / "generated" / "T2_performance_summary_table_generic.md").exists()
    assert (paper_root / "tables" / "generated" / "T3_grouped_risk_event_summary_table.csv").exists()
    assert (paper_root / "tables" / "generated" / "T3_grouped_risk_event_summary_table.md").exists()

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {item["table_id"]: item for item in table_catalog["tables"]}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("performance_summary_table_generic")
    assert tables_by_id["T2"]["input_schema_id"] == "performance_summary_table_generic_v1"
    assert tables_by_id["T2"]["asset_paths"] == [
        "paper/tables/generated/T2_performance_summary_table_generic.csv",
        "paper/tables/generated/T2_performance_summary_table_generic.md",
    ]
    assert tables_by_id["T3"]["table_shell_id"] == full_id("grouped_risk_event_summary_table")
    assert tables_by_id["T3"]["input_schema_id"] == "grouped_risk_event_summary_table_v1"
    assert tables_by_id["T3"]["asset_paths"] == [
        "paper/tables/generated/T3_grouped_risk_event_summary_table.csv",
        "paper/tables/generated/T3_grouped_risk_event_summary_table.md",
    ]

def test_materialize_display_surface_accepts_appendix_table_alias_a1_for_grouped_risk_table(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    (paper_root / "figures").mkdir(parents=True)
    (paper_root / "tables").mkdir(parents=True)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "appendix_table_a1_public_anchors",
                    "display_kind": "table",
                    "requirement_key": "grouped_risk_event_summary_table",
                    "catalog_id": "A1",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "grouped_risk_event_summary_table.json",
        {
            "schema_version": 1,
            "table_shell_id": "grouped_risk_event_summary_table",
            "display_id": "appendix_table_a1_public_anchors",
            "catalog_id": "A1",
            "title": "Retained public anchor summary",
            "caption": "Observed anchor counts across retained public anatomy and biology sources.",
            "surface_column_label": "Anchor surface",
            "stratum_column_label": "Retained subset",
            "cases_column_label": "Cases",
            "events_column_label": "Events",
            "risk_column_label": "Share",
            "rows": [
                {
                    "row_id": "mapping_pituitary_nfpa",
                    "surface": "Mapping pituitary",
                    "stratum": "NFPA",
                    "cases": 85,
                    "events": 27,
                    "risk_display": "31.8%",
                },
                {
                    "row_id": "gse169498_invasive",
                    "surface": "GSE169498",
                    "stratum": "Invasive",
                    "cases": 73,
                    "events": 49,
                    "risk_display": "67.1%",
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["tables_materialized"] == ["TA1"]
    assert (paper_root / "tables" / "generated" / "TA1_grouped_risk_event_summary_table.csv").exists()
    assert (paper_root / "tables" / "generated" / "TA1_grouped_risk_event_summary_table.md").exists()

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {item["table_id"]: item for item in table_catalog["tables"]}
    assert tables_by_id["TA1"]["table_shell_id"] == full_id("grouped_risk_event_summary_table")
    assert tables_by_id["TA1"]["input_schema_id"] == "grouped_risk_event_summary_table_v1"
    assert tables_by_id["TA1"]["asset_paths"] == [
        "paper/tables/generated/TA1_grouped_risk_event_summary_table.csv",
        "paper/tables/generated/TA1_grouped_risk_event_summary_table.md",
    ]

def test_materialize_display_surface_uses_pack_runtime_for_baseline_table_shell(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_table_renderer(
        *,
        template_id: str,
        payload_path: Path,
        payload: dict[str, object],
        output_md_path: Path,
        output_csv_path: Path | None,
    ) -> dict[str, str]:
        _ensure_output_parents(output_md_path, output_csv_path)
        output_md_path.write_text("| Characteristic | Overall |\n| --- | --- |\n| Age | 61 |\n", encoding="utf-8")
        assert output_csv_path is not None
        output_csv_path.write_text("Characteristic,Overall\nAge,61\n", encoding="utf-8")
        render_calls.append(template_id)
        return {
            "title": "Baseline characteristics",
            "caption": "Baseline characteristics across prespecified groups.",
        }

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("table1_baseline_characteristics"):
            return fake_table_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_write_table_outputs",
        lambda **_: (_ for _ in ()).throw(AssertionError("host table writer should not be used")),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("table1_baseline_characteristics")]
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()

def test_materialize_display_surface_writes_layout_sidecar_and_real_qc_result(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
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

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if display_registry.is_evidence_figure_template(template_id):
            spec = display_registry.get_evidence_figure_spec(template_id)
            if spec.renderer_family == "r_ggplot2":
                return fake_render_r_evidence_figure
            return fake_render_python_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    module.materialize_display_surface(paper_root=paper_root)

    layout_sidecar_path = paper_root / "figures" / "generated" / "F17_multicenter_generalizability_overview.layout.json"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = {item["figure_id"]: item["qc_result"] for item in figure_catalog["figures"]}["F17"]

    assert layout_sidecar_path.exists()
    assert qc_result["status"] == "pass", qc_result
    assert qc_result["engine_id"] == "display_layout_qc_v1"
    assert qc_result["qc_profile"] == "publication_multicenter_overview"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")
    assert qc_result["issues"] == []
    assert qc_result["audit_classes"] == []
    assert qc_result["failure_reason"] == ""
    assert qc_result["readability_findings"] == []
    assert qc_result["revision_note"] == ""
