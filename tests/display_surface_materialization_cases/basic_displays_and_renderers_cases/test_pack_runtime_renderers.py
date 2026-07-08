from tests.display_surface_materialization_cases.shared import (
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


def test_materialize_display_surface_does_not_reference_stale_subprocess_svg(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    stale_svg_path = paper_root / "figures" / "generated" / "F1_cohort_flow.svg"
    stale_svg_path.parent.mkdir(parents=True, exist_ok=True)
    stale_svg_path.write_text("<svg><text>stale</text></svg>\n", encoding="utf-8")

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
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    module.materialize_display_surface(paper_root=paper_root)

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    entry = next(item for item in figure_catalog["figures"] if item["figure_id"] == "F1")
    assert entry["export_paths"] == [
        "paper/figures/generated/F1_cohort_flow.png",
        "paper/figures/generated/F1_cohort_flow.pdf",
    ]
    assert not stale_svg_path.exists()


def test_materialize_display_surface_uses_pack_runtime_for_cohort_flow_shell(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    render_calls: list[str] = []

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
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(full_template_id)
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("cohort_flow_figure")]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.pdf").exists()


def test_materialize_display_surface_syncs_figure_semantics_renderer_contract(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": {
                "F1": {
                    "figure_id": "F1",
                    "title": "Cohort flow",
                    "renderer_contract": {
                        "renderer": "python",
                        "allowed_renderers": ["python", "r_ggplot2"],
                        "template_id": "F1",
                        "layout_qc_profile": "F1",
                        "fallback_on_failure": False,
                        "failure_action": "block_and_fix_environment",
                    },
                },
            },
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
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert "paper/figure_semantics_manifest.json" in result["display_pack_surface_sync"]["updated_files"]
    figure_semantics = json.loads((paper_root / "figure_semantics_manifest.json").read_text(encoding="utf-8"))
    renderer_contract = figure_semantics["figures"]["F1"]["renderer_contract"]
    assert renderer_contract["template_id"] == full_id("cohort_flow_figure")
    assert renderer_contract["layout_qc_profile"] == "publication_illustration_flow"
    assert renderer_contract["renderer_family"] == "r_ggplot2"
    assert renderer_contract["renderer"] == "r_ggplot2"
    assert renderer_contract["required_exports"] == ["png", "pdf"]


def test_materialize_display_surface_uses_pack_runtime_for_r_evidence_template(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "roc_curve",
                    "display_kind": "figure",
                    "requirement_key": "roc_curve_binary",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "binary_prediction_curve_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "binary_prediction_curve_inputs_v1",
            "displays": [
                {
                    "display_id": "roc_curve",
                    "template_id": "roc_curve_binary",
                    "title": "ROC curve",
                    "caption": "Receiver operating characteristic curve.",
                    "x_label": "1 - Specificity",
                    "y_label": "Sensitivity",
                    "series": [
                        {
                            "label": "Model",
                            "x": [0.0, 0.2, 1.0],
                            "y": [0.0, 0.8, 1.0],
                        }
                    ],
                }
            ],
        },
    )
    render_calls: list[str] = []

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
        request_short_template_id: str | None = None,
    ) -> dict[str, object]:
        template_id = full_template_id
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        sidecar = _minimal_layout_sidecar_for_template(template_id)
        if request_short_template_id:
            sidecar["template_id"] = request_short_template_id
        layout_sidecar_path.write_text(
            json.dumps(sidecar, ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("roc_curve_binary")]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()
