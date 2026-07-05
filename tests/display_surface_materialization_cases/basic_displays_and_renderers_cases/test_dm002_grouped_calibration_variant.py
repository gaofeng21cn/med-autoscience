from tests.display_surface_materialization_cases.shared import *


def test_materialize_display_surface_accepts_single_panel_dm002_grouped_calibration_payload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "km_risk_stratification",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/Figure3.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "time_to_event_grouped_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [
                {
                    "display_id": "km_risk_stratification",
                    "template_id": full_id("time_to_event_risk_group_summary"),
                    "title": "Grouped calibration across NHANES transported-score deciles",
                    "caption": "Observed mortality versus mean predicted risk across NHANES deciles.",
                    "plot_variant": "nhanes_decile_grouped_calibration",
                    "panel_a_title": "Grouped calibration across NHANES deciles",
                    "x_label": "NHANES predicted-risk decile",
                    "y_label": "5-year mortality risk",
                    "risk_group_summaries": [
                        {
                            "label": "Decile 1",
                            "risk_group_label": "1",
                            "group_order": 1,
                            "sample_size": 566,
                            "events_5y": 13,
                            "mean_predicted_risk_5y": 0.0161,
                            "observed_km_risk_5y": 0.0230,
                            "observed_5y_rate_ci_95": {"lower": 0.0135, "upper": 0.0389},
                        },
                        {
                            "label": "Decile 10",
                            "risk_group_label": "10",
                            "group_order": 10,
                            "sample_size": 565,
                            "events_5y": 214,
                            "mean_predicted_risk_5y": 0.0308,
                            "observed_km_risk_5y": 0.3788,
                            "observed_5y_rate_ci_95": {"lower": 0.3397, "upper": 0.4195},
                        },
                    ],
                }
            ],
        },
    )
    renderer_payloads: list[dict[str, object]] = []

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
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_id("time_to_event_risk_group_summary")), ensure_ascii=False),
            encoding="utf-8",
        )
        renderer_payloads.append(display_payload)
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert len(renderer_payloads) == 1
    renderer_payload = renderer_payloads[0]
    assert renderer_payload["plot_variant"] == "nhanes_decile_grouped_calibration"
    assert "panel_b_title" not in renderer_payload
    assert "event_count_y_label" not in renderer_payload
    first_group = renderer_payload["risk_group_summaries"][0]
    assert first_group["group_order"] == 1
    assert first_group["risk_group_label"] == "1"
    assert first_group["observed_5y_rate_ci_95"] == {"lower": 0.0135, "upper": 0.0389}
