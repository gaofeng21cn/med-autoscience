from .shared import *

def test_materialize_display_surface_keeps_model_complexity_audit_audit_labels_clear_of_metric_column(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "model_audit",
                    "display_kind": "figure",
                    "requirement_key": "model_complexity_audit_panel",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/model_audit.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "model_complexity_audit_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "model_complexity_audit_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "model_audit",
                    "template_id": "model_complexity_audit_panel",
                    "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
                    "caption": "Discrimination, overall error, calibration, and bounded complexity audit across the candidate packages.",
                    "metric_panels": [
                        {
                            "panel_id": "auroc_panel",
                            "panel_label": "A",
                            "title": "Discrimination",
                            "x_label": "AUROC",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.8022},
                                {"label": "Clinically informed preoperative model", "value": 0.8004},
                                {"label": "Pathology-augmented model", "value": 0.7999},
                                {"label": "Elastic-net comparison model", "value": 0.8006},
                                {"label": "Random forest comparison model", "value": 0.8359},
                            ],
                        },
                        {
                            "panel_id": "brier_panel",
                            "panel_label": "B",
                            "title": "Overall error",
                            "x_label": "Brier score",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.1433},
                                {"label": "Clinically informed preoperative model", "value": 0.1099},
                                {"label": "Pathology-augmented model", "value": 0.1090},
                                {"label": "Elastic-net comparison model", "value": 0.1086},
                                {"label": "Random forest comparison model", "value": 0.1011},
                            ],
                        },
                        {
                            "panel_id": "slope_panel",
                            "panel_label": "C",
                            "title": "Calibration",
                            "x_label": "Calibration slope",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Core preoperative model", "value": 2.4065},
                                {"label": "Clinically informed preoperative model", "value": 1.0442},
                                {"label": "Pathology-augmented model", "value": 1.0395},
                                {"label": "Elastic-net comparison model", "value": 1.1096},
                                {"label": "Random forest comparison model", "value": 0.8017},
                            ],
                        },
                    ],
                    "audit_panels": [
                        {
                            "panel_id": "coefficient_panel",
                            "panel_label": "D",
                            "title": "Coefficient stability",
                            "x_label": "Mean odds ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Age", "value": 0.9117898553832784},
                                {"label": "Female sex", "value": 1.0309311059934487},
                                {"label": "Blurred Vision", "value": 1.183703663712767},
                                {"label": "Defect Field Vision", "value": 1.067175358232608},
                                {"label": "Preoperative hypopituitarism", "value": 1.121955952267307},
                                {"label": "Knosp grade", "value": 1.1321181751012195},
                                {"label": "Invasiveness", "value": 1.0176339267412329},
                                {"label": "Tumor diameter", "value": 1.443952677790654},
                                {"label": "Log Diameter", "value": 1.3878032746085207},
                                {"label": "Knosp Ge 3", "value": 1.0176339267412329},
                                {"label": "Knosp Ge 4", "value": 1.3314915096706699},
                                {"label": "Invasiveness Log Diameter", "value": 1.0860598862755477},
                            ],
                        },
                        {
                            "panel_id": "domain_panel",
                            "panel_label": "E",
                            "title": "Domain stability",
                            "x_label": "Mean absolute coefficient",
                            "rows": [
                                {"label": "Demographics", "value": 0.07697647508285217},
                                {"label": "Endocrine impairment", "value": 0.11428074753919776},
                                {"label": "Invasion burden", "value": 0.10914169938817306},
                                {"label": "Tumor burden", "value": 0.3444167074572295},
                                {"label": "Visual compromise", "value": 0.11849667910968223},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    captured_figures: list[Any] = []
    original_close = plt.close

    def _capture_close(fig: Any | None = None) -> None:
        if fig is not None:
            captured_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert captured_figures

    figure = captured_figures[-1]
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    metric_axes = figure.axes[:3]
    audit_axes = figure.axes[3:]
    metric_column_right_edge = max(axes.get_window_extent(renderer=renderer).x1 for axes in metric_axes)
    audit_label_left_edge = min(
        label.get_window_extent(renderer=renderer).x0
        for axes in audit_axes
        for label in axes.get_yticklabels()
        if label.get_text().strip()
    )

    assert audit_label_left_edge - metric_column_right_edge >= 12.0

    original_close(figure)

def test_materialize_display_surface_omits_figure_title_for_model_complexity_audit_panel_by_default(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "model_audit",
                    "display_kind": "figure",
                    "requirement_key": "model_complexity_audit_panel",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/model_audit.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "model_complexity_audit_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "model_complexity_audit_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "model_audit",
                    "template_id": "model_complexity_audit_panel",
                    "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
                    "caption": "Discrimination, calibration, and bounded complexity audit across candidate packages.",
                    "metric_panels": [
                        {
                            "panel_id": "auroc_panel",
                            "panel_label": "A",
                            "title": "Discrimination",
                            "x_label": "AUROC",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.80},
                                {"label": "Clinically informed preoperative model", "value": 0.81},
                                {"label": "Random forest comparison model", "value": 0.84},
                            ],
                        },
                        {
                            "panel_id": "brier_panel",
                            "panel_label": "B",
                            "title": "Overall error",
                            "x_label": "Brier score",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.14},
                                {"label": "Clinically informed preoperative model", "value": 0.11},
                                {"label": "Random forest comparison model", "value": 0.10},
                            ],
                        },
                    ],
                    "audit_panels": [
                        {
                            "panel_id": "coefficient_panel",
                            "panel_label": "C",
                            "title": "Coefficient stability",
                            "x_label": "Mean odds ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Age", "value": 0.91},
                                {"label": "Tumor diameter", "value": 1.44},
                                {"label": "Knosp grade", "value": 1.13},
                            ],
                        }
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F4_model_complexity_audit_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert sum(1 for item in layout_sidecar["layout_boxes"] if item["box_type"] == "subplot_title") == 3

@pytest.mark.parametrize(
    ("template_id", "display_id"),
    [
        ("shap_summary_beeswarm", "Figure13"),
        ("time_to_event_discrimination_calibration_panel", "Figure14"),
        ("time_to_event_risk_group_summary", "Figure15"),
        ("time_to_event_decision_curve", "Figure16"),
        ("multicenter_generalizability_overview", "Figure17"),
    ],
)
def test_render_python_evidence_figure_emits_qc_passable_layout_sidecar(
    tmp_path: Path,
    template_id: str,
    display_id: str,
) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    qc_module = importlib.import_module("med_autoscience.display_layout_qc")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    spec = controller_module.display_registry.get_evidence_figure_spec(template_id)
    _, display_payload = controller_module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id=display_id,
    )
    if template_id in {
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
    }:
        style_roles = {
            "model_curve": "#245A6B",
            "comparator_curve": "#B89A6D",
            "reference_line": "#6B7280",
        }
        if template_id == "time_to_event_decision_curve":
            style_roles["highlight_band"] = "#E7E1D8"
        display_payload = {
            **display_payload,
            "render_context": {
                "style_profile_id": "paper_neutral_clinical_v1",
                "style_roles": style_roles,
                "layout_override": {},
                "readability_override": {},
            },
        }
    output_png_path = tmp_path / f"{display_id}_{template_id}.png"
    output_pdf_path = tmp_path / f"{display_id}_{template_id}.pdf"
    layout_sidecar_path = tmp_path / f"{display_id}_{template_id}.layout.json"

    controller_module._render_python_evidence_figure(
        template_id=spec.template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    qc_result = qc_module.run_display_layout_qc(
        qc_profile=spec.layout_qc_profile,
        layout_sidecar=layout_sidecar,
    )

    assert qc_result["status"] == "pass", qc_result
    assert qc_result["issues"] == []
    if template_id == "shap_summary_beeswarm":
        assert layout_sidecar["metrics"]["figure_height_inches"] > 0
        assert layout_sidecar["metrics"]["figure_width_inches"] > 0
        assert len(layout_sidecar["metrics"]["feature_labels"]) == 2
        feature_label_boxes = [box for box in layout_sidecar["layout_boxes"] if box["box_type"] == "feature_label"]
        feature_row_boxes = [box for box in layout_sidecar["layout_boxes"] if box["box_type"] == "feature_row"]
        assert len(feature_label_boxes) == 2
        assert len(feature_row_boxes) == 2
        assert all(box["x1"] <= layout_sidecar["panel_boxes"][0]["x0"] for box in feature_label_boxes)
        zero_line_box = next(box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "zero_line")
        panel_box = layout_sidecar["panel_boxes"][0]
        assert panel_box["y0"] <= zero_line_box["y0"] <= panel_box["y1"]
        assert panel_box["y0"] <= zero_line_box["y1"] <= panel_box["y1"]
        assert all(panel_box["y0"] <= box["y0"] <= panel_box["y1"] for box in feature_row_boxes)
        assert all(panel_box["y0"] <= box["y1"] <= panel_box["y1"] for box in feature_row_boxes)

def test_render_python_evidence_figure_uses_pack_entrypoint_for_time_to_event_risk_group_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    spec = controller_module.display_registry.get_evidence_figure_spec("time_to_event_risk_group_summary")
    _, display_payload = controller_module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id="Figure15",
    )
    display_payload = {
        **display_payload,
        "render_context": {
            "style_profile_id": "paper_neutral_clinical_v1",
            "style_roles": {
                "model_curve": "#245A6B",
                "comparator_curve": "#B89A6D",
                "reference_line": "#6B7280",
            },
            "layout_override": {},
            "readability_override": {},
        },
    }

    output_png_path = tmp_path / "Figure15_pack_entrypoint.png"
    output_pdf_path = tmp_path / "Figure15_pack_entrypoint.pdf"
    layout_sidecar_path = tmp_path / "Figure15_pack_entrypoint.layout.json"

    controller_module._render_python_evidence_figure(
        template_id=spec.template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    assert output_png_path.exists()
    assert output_pdf_path.exists()
    assert layout_sidecar_path.exists()

def test_render_r_evidence_figure_uses_pack_entrypoint_for_r_template(tmp_path: Path, monkeypatch) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    render_calls: list[str] = []

    def fake_external_renderer(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "load_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )

    output_png_path = tmp_path / "Figure2_pack_entrypoint.png"
    output_pdf_path = tmp_path / "Figure2_pack_entrypoint.pdf"
    layout_sidecar_path = tmp_path / "Figure2_pack_entrypoint.layout.json"

    controller_module._render_r_evidence_figure(
        template_id=full_id("roc_curve_binary"),
        display_payload={"display_id": "Figure2"},
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    assert render_calls == [full_id("roc_curve_binary")]
    assert output_png_path.exists()
    assert output_pdf_path.exists()
    assert layout_sidecar_path.exists()

def test_r_evidence_renderer_sources_accept_new_concrete_backlog_templates() -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    repo_root = Path(__file__).resolve().parents[1]
    pack_src = repo_root / "display-packs" / "fenggaolab.org.medical-display-core" / "src"
    sys.path.insert(0, str(pack_src))
    try:
        pack_module = importlib.import_module("fenggaolab_org_medical_display_core.evidence_figures")
    finally:
        sys.path.pop(0)

    for source in (controller_module._R_EVIDENCE_RENDERER_SOURCE, pack_module._R_EVIDENCE_RENDERER_SOURCE):
        assert 'clinical_impact_curve_binary = list(series = display_payload$series, reference_line = display_payload$reference_line)' in source
        assert 'phate_scatter_grouped = build_embedding_metrics(display_payload, panel_box)' in source
        assert 'diffusion_map_scatter_grouped = build_embedding_metrics(display_payload, panel_box)' in source
        assert 'multivariable_forest = list(rows = display_payload$rows)' in source
        assert 'if (template_id %in% c("forest_effect_main", "subgroup_forest", "multivariable_forest") && !is.null(panel_box))' in source
        assert 'clinical_impact_curve_binary = plot_binary_curve(payload)' in source
        assert 'phate_scatter_grouped = plot_embedding_scatter(payload)' in source
        assert 'diffusion_map_scatter_grouped = plot_embedding_scatter(payload)' in source
        assert 'multivariable_forest = plot_forest(payload)' in source

def test_render_cohort_flow_figure_uses_pack_entrypoint(tmp_path: Path, monkeypatch) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    render_calls: list[str] = []

    def fake_external_renderer(**kwargs: object) -> None:
        output_svg_path = kwargs["output_svg_path"]
        output_png_path = kwargs["output_png_path"]
        output_layout_path = kwargs["output_layout_path"]
        assert isinstance(output_svg_path, Path)
        assert isinstance(output_png_path, Path)
        assert isinstance(output_layout_path, Path)
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(json.dumps(_minimal_layout_sidecar_for_template(full_id("cohort_flow_figure"))), encoding="utf-8")
        render_calls.append("cohort_flow_figure")

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "load_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )
    monkeypatch.setattr(
        controller_module,
        "_run_graphviz_layout",
        lambda **_: (_ for _ in ()).throw(AssertionError("legacy cohort flow renderer should not run once pack entrypoint is active")),
    )

    controller_module._render_cohort_flow_figure(
        output_svg_path=tmp_path / "flow.svg",
        output_png_path=tmp_path / "flow.png",
        output_layout_path=tmp_path / "flow.layout.json",
        title="Cohort flow",
        steps=[{"step_id": "screened", "label": "Screened", "n": 10}],
        exclusions=[],
        endpoint_inventory=[],
        design_panels=[],
        render_context={},
    )

    assert render_calls == ["cohort_flow_figure"]

def test_render_submission_graphical_abstract_uses_pack_entrypoint(tmp_path: Path, monkeypatch) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    render_calls: list[str] = []

    def fake_external_renderer(**kwargs: object) -> None:
        output_svg_path = kwargs["output_svg_path"]
        output_png_path = kwargs["output_png_path"]
        output_layout_path = kwargs["output_layout_path"]
        assert isinstance(output_svg_path, Path)
        assert isinstance(output_png_path, Path)
        assert isinstance(output_layout_path, Path)
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_id("submission_graphical_abstract")), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append("submission_graphical_abstract")

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "load_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )
    monkeypatch.setattr(
        controller_module,
        "_choose_shared_submission_graphical_abstract_arrow_lane",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("legacy graphical abstract renderer should not run once pack entrypoint is active")
        ),
    )

    controller_module._render_submission_graphical_abstract(
        output_svg_path=tmp_path / "ga.svg",
        output_png_path=tmp_path / "ga.png",
        output_layout_path=tmp_path / "ga.layout.json",
        shell_payload={"title": "GA", "panels": [], "footer_pills": []},
        render_context={},
    )

    assert render_calls == ["submission_graphical_abstract"]

def test_materialize_display_surface_uses_pack_entrypoint_for_table_shell(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    render_calls: list[str] = []

    def fake_table_renderer(
        *,
        template_id: str,
        payload_path: Path,
        payload: dict[str, object],
        output_md_path: Path,
        output_csv_path: Path | None = None,
    ) -> dict[str, str]:
        _ensure_output_parents(output_md_path, output_csv_path)
        output_md_path.write_text(
            "# Baseline characteristics\n\n| Characteristic | Overall |\n| --- | --- |\n| Age | 61 |\n",
            encoding="utf-8",
        )
        if output_csv_path is not None:
            output_csv_path.write_text("Characteristic,Overall\nAge,61\n", encoding="utf-8")
        render_calls.append(template_id)
        assert payload_path.name == "baseline_characteristics_schema.json"
        assert payload["title"] == "Baseline characteristics"
        return {
            "title": "Baseline characteristics",
            "caption": "Baseline characteristics across prespecified groups.",
        }

    original_loader = module.display_pack_runtime.load_python_plugin_callable

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("table1_baseline_characteristics"):
            return fake_table_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_write_table_outputs",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("legacy host table writer should not run once pack entrypoint is active")
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_write_rectangular_table_outputs",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("legacy host table writer should not run once pack entrypoint is active")
        ),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("table1_baseline_characteristics")]

def test_materialize_display_surface_applies_publication_style_and_display_override(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "decision_curve",
                    "template_id": "time_to_event_decision_curve",
                    "layout_override": {
                        "highlight_band": {"xmin": 0.5, "xmax": 3.0, "unit": "percent"},
                        "legend_position": "lower_center",
                    },
                    "readability_override": {
                        "focus_window": {"panel_id": "A", "y_min": -0.002, "y_max": 0.006},
                    },
                }
            ],
        },
    )
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "decision_curve",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/decision_curve.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "time_to_event_decision_curve_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_decision_curve_inputs_v1",
            "displays": [
                {
                    "display_id": "decision_curve",
                    "template_id": "time_to_event_decision_curve",
                    "title": "Five-year decision curve",
                    "caption": "Net benefit for the locked survival model across the prespecified threshold range.",
                    "panel_a_title": "Decision-curve net benefit",
                    "panel_b_title": "Model-treated fraction",
                    "x_label": "Threshold risk (%)",
                    "y_label": "Net benefit",
                    "treated_fraction_y_label": "Patients classified above threshold (%)",
                    "reference_line": {"x": [0.5, 4.0], "y": [0.0, 0.0], "label": "Treat none"},
                    "series": [
                        {"label": "Model", "x": [0.5, 1.0, 2.0, 4.0], "y": [0.004, 0.003, 0.001, 0.0]},
                        {"label": "Treat all", "x": [0.5, 1.0, 2.0, 4.0], "y": [0.002, -0.003, -0.014, -0.035]},
                    ],
                    "treated_fraction_series": {
                        "label": "Model",
                        "x": [0.5, 1.0, 2.0, 4.0],
                        "y": [45.0, 28.0, 12.0, 2.0],
                    },
                }
            ],
        },
    )

    render_contexts: list[dict[str, object]] = []
    original_loader = module.display_pack_runtime.load_python_plugin_callable

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
        render_contexts.append(dict(display_payload.get("render_context") or {}))

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("time_to_event_decision_curve"):
            return fake_render_python_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    report = module.materialize_display_surface(paper_root=paper_root)
    catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    f4 = next(item for item in catalog["figures"] if item["figure_id"] == "F4")
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F4_time_to_event_decision_curve.layout.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["status"] == "materialized"
    assert len(render_contexts) == 1
    assert render_contexts[0]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert render_contexts[0]["style_roles"]["model_curve"] == "#245A6B"
    assert render_contexts[0]["layout_override"]["highlight_band"]["xmax"] == 3.0
    assert f4["render_context"]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert f4["render_context"]["style_roles"]["model_curve"] == "#245A6B"
    assert f4["render_context"]["layout_override"]["highlight_band"]["xmax"] == 3.0
    assert layout_sidecar["render_context"]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert layout_sidecar["render_context"]["style_roles"]["model_curve"] == "#245A6B"
    assert layout_sidecar["render_context"]["layout_override"]["highlight_band"]["xmax"] == 3.0
    assert layout_sidecar["render_context"]["readability_override"]["focus_window"]["panel_id"] == "A"

def test_materialize_display_surface_rejects_incomplete_cohort_flow_input(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "steps": [],
        },
    )

    try:
        module.materialize_display_surface(paper_root=paper_root)
    except ValueError as exc:
        assert "cohort_flow.json" in str(exc)
    else:
        raise AssertionError("expected incomplete cohort flow input to fail")

def test_load_evidence_display_payload_rejects_incomplete_clustered_heatmap_grid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    clustered_payload_path = paper_root / "clustered_heatmap_inputs.json"
    clustered_payload = json.loads(clustered_payload_path.read_text(encoding="utf-8"))
    clustered_payload["displays"][0]["cells"].pop()
    dump_json(clustered_payload_path, clustered_payload)

    spec = module.display_registry.get_evidence_figure_spec("clustered_heatmap")

    with pytest.raises(ValueError, match="must cover every declared row/column coordinate exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure21",
        )

def test_load_evidence_display_payload_rejects_gsva_heatmap_without_score_method(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "gsva_ssgsea_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "gsva_ssgsea_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure23",
                    "template_id": "gsva_ssgsea_heatmap",
                    "title": "GSVA heatmap for stromal programs",
                    "caption": "Pathway activity overview.",
                    "x_label": "Samples",
                    "y_label": "Gene-set programs",
                    "row_order": [{"label": "TGF-beta signaling"}],
                    "column_order": [{"label": "Sample-01"}],
                    "cells": [{"x": "Sample-01", "y": "TGF-beta signaling", "value": 0.58}],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("gsva_ssgsea_heatmap")

    with pytest.raises(ValueError, match="score_method"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure23",
        )

def test_load_evidence_display_payload_rejects_performance_heatmap_value_outside_unit_interval(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "performance_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "performance_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure25",
                    "template_id": "performance_heatmap",
                    "title": "AUC heatmap across APOE4 subgroups and predictor sets",
                    "caption": "Random-forest discrimination remains strongest for the integrated model across APOE4-stratified analyses.",
                    "x_label": "Analytic subgroup",
                    "y_label": "Predictor set",
                    "metric_name": "AUC",
                    "row_order": [
                        {"label": "Clinical baseline"},
                        {"label": "Integrated model"},
                    ],
                    "column_order": [
                        {"label": "All participants"},
                        {"label": "APOE4 carriers"},
                    ],
                    "cells": [
                        {"x": "All participants", "y": "Clinical baseline", "value": 0.71},
                        {"x": "APOE4 carriers", "y": "Clinical baseline", "value": 1.07},
                        {"x": "All participants", "y": "Integrated model", "value": 0.83},
                        {"x": "APOE4 carriers", "y": "Integrated model", "value": 0.79},
                    ],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("performance_heatmap")

    with pytest.raises(ValueError, match="must stay within \\[0, 1\\]"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure25",
        )

def test_load_evidence_display_payload_rejects_confusion_matrix_with_invalid_row_fraction_sum(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "confusion_matrix_heatmap_binary_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "confusion_matrix_heatmap_binary_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "confusion_matrix_heatmap_binary",
                    "title": "Binary confusion matrix on the held-out cohort",
                    "caption": "Row-normalized confusion matrix with an invalid row sum.",
                    "x_label": "Predicted class",
                    "y_label": "Observed class",
                    "metric_name": "Observed proportion",
                    "normalization": "row_fraction",
                    "row_order": [
                        {"label": "Observed negative"},
                        {"label": "Observed positive"},
                    ],
                    "column_order": [
                        {"label": "Predicted negative"},
                        {"label": "Predicted positive"},
                    ],
                    "cells": [
                        {"x": "Predicted negative", "y": "Observed negative", "value": 0.88},
                        {"x": "Predicted positive", "y": "Observed negative", "value": 0.19},
                        {"x": "Predicted negative", "y": "Observed positive", "value": 0.19},
                        {"x": "Predicted positive", "y": "Observed positive", "value": 0.81},
                    ],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("confusion_matrix_heatmap_binary")

    with pytest.raises(ValueError, match="must sum to 1.0 when normalization=row_fraction"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure26",
        )
