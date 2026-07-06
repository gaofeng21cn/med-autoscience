from tests.display_surface_materialization_cases.shared import *


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
