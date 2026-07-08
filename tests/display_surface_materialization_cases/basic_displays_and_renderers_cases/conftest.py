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


@pytest.fixture(autouse=True)
def fake_display_pack_subprocess_renderer(monkeypatch) -> None:
    def fake_subprocess_renderer(**kwargs) -> dict[str, object]:
        output_png_path = kwargs["output_png_path"]
        output_pdf_path = kwargs["output_pdf_path"]
        layout_sidecar_path = kwargs["layout_sidecar_path"]
        template_id = full_id(
            kwargs.get("request_short_template_id") or str(kwargs["full_template_id"]).rsplit("::", 1)[-1]
        )
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        if output_pdf_path is not None:
            output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": kwargs["figure_id"]}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)
