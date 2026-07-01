from tests.display_surface_materialization_cases.shared import *

def test_materialize_display_surface_uses_transportability_governance_template_for_f5(
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
                    "display_id": "transportability_governance",
                    "display_kind": "figure",
                    "requirement_key": "center_transportability_governance_summary_panel",
                    "catalog_id": "F5",
                    "shell_path": "paper/figures/Figure5.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "center_transportability_governance_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "center_transportability_governance_summary_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "transportability_governance",
                    "template_id": full_id("center_transportability_governance_summary_panel"),
                    "title": "Transportability governance",
                    "caption": "Center-level transportability governance summary.",
                    "metric_family": "c_index",
                    "metric_panel_title": "Cohort discrimination",
                    "metric_x_label": "C-index",
                    "metric_reference_value": 0.74,
                    "batch_shift_threshold": 0.04,
                    "slope_acceptance_lower": 0.85,
                    "slope_acceptance_upper": 1.15,
                    "oe_ratio_acceptance_lower": 0.85,
                    "oe_ratio_acceptance_upper": 1.15,
                    "summary_panel_title": "Transportability action",
                    "centers": [
                        {
                            "center_id": "china",
                            "center_label": "China validation",
                            "cohort_role": "external_validation",
                            "support_count": 22800,
                            "event_count": 2180,
                            "metric_estimate": 0.74,
                            "metric_lower": 0.72,
                            "metric_upper": 0.76,
                            "max_shift": 0.03,
                            "slope": 0.96,
                            "oe_ratio": 1.02,
                            "verdict": "stable",
                            "action": "Proceed with monitoring",
                        },
                        {
                            "center_id": "us",
                            "center_label": "US transport",
                            "cohort_role": "transport_target",
                            "support_count": 16420,
                            "event_count": 1520,
                            "metric_estimate": 0.73,
                            "metric_lower": 0.71,
                            "metric_upper": 0.75,
                            "max_shift": 0.05,
                            "slope": 0.91,
                            "oe_ratio": 1.08,
                            "verdict": "monitor",
                            "action": "Monitor calibration drift",
                        },
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
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
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
    assert render_calls == [full_id("center_transportability_governance_summary_panel")]
    assert (paper_root / "figures" / "generated" / "F5_center_transportability_governance_summary_panel.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F5"]["template_id"] == full_id("center_transportability_governance_summary_panel")
    assert figures_by_id["F5"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F5"]["input_schema_id"] == "center_transportability_governance_summary_panel_inputs_v1"
    assert figures_by_id["F5"]["paper_role"] == "main_text"
    assert (
        figures_by_id["F5"]["source_renderer"]
        == "MAS/Transportability::center_transportability_governance_summary_panel"
    )
    assert (
        figures_by_id["F5"]["figure_purpose"]
        == "transportability_discrimination_plus_recalibration_governance_decision_matrix"
    )
    assert figures_by_id["F5"]["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"


def test_materialize_display_surface_reports_missing_evidence_payload_with_owner_route_context(
    tmp_path: Path,
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
                    "display_id": "transportability_governance",
                    "display_kind": "figure",
                    "requirement_key": "center_transportability_governance_summary_panel",
                    "catalog_id": "F5",
                    "shell_path": "paper/figures/Figure5.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})

    with pytest.raises(ValueError) as excinfo:
        module.materialize_display_surface(paper_root=paper_root)

    message = str(excinfo.value)
    assert "display_id=`transportability_governance`" in message
    assert "requirement_short_id=`center_transportability_governance_summary_panel`" in message
    assert "template_id=`fenggaolab.org.medical-display-core::center_transportability_governance_summary_panel`" in message
    assert "input_schema_id=`center_transportability_governance_summary_panel_inputs_v1`" in message
    assert "expected_input_path=" in message


def test_materialize_display_surface_uses_lookup_only_time_to_event_alias_specs(
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
                    "display_id": "Figure2",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                },
                {
                    "display_id": "Figure3",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/Figure3.shell.json",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "time_to_event_discrimination_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure2",
                    "template_id": full_id("time_to_event_discrimination_calibration_panel"),
                    "title": "Time-to-event discrimination and calibration",
                    "caption": "Discrimination and calibration summary.",
                    "panel_a_title": "Discrimination",
                    "panel_b_title": "Calibration",
                    "discrimination_x_label": "Model",
                    "calibration_x_label": "Predicted 5-year risk",
                    "calibration_y_label": "Observed 5-year risk",
                    "discrimination_points": [
                        {"label": "Model", "c_index": 0.81},
                    ],
                    "calibration_summary": [
                        {
                            "group_label": "Low risk",
                            "group_order": 1,
                            "n": 80,
                            "events_5y": 5,
                            "predicted_risk_5y": 0.07,
                            "observed_risk_5y": 0.06,
                        },
                        {
                            "group_label": "High risk",
                            "group_order": 2,
                            "n": 60,
                            "events_5y": 18,
                            "predicted_risk_5y": 0.28,
                            "observed_risk_5y": 0.30,
                        },
                    ],
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_grouped_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure3",
                    "template_id": full_id("time_to_event_risk_group_summary"),
                    "title": "Risk-group summary",
                    "caption": "Risk-group event summary.",
                    "panel_a_title": "Risk gradient",
                    "panel_b_title": "Events",
                    "x_label": "Risk group",
                    "y_label": "5-year risk",
                    "event_count_y_label": "Events",
                    "risk_group_summaries": [
                        {
                            "label": "Low risk",
                            "sample_size": 80,
                            "events_5y": 5,
                            "mean_predicted_risk_5y": 0.07,
                            "observed_km_risk_5y": 0.06,
                        },
                        {
                            "label": "High risk",
                            "sample_size": 60,
                            "events_5y": 18,
                            "mean_predicted_risk_5y": 0.28,
                            "observed_km_risk_5y": 0.30,
                        },
                    ],
                }
            ],
        },
    )
    render_calls: list[tuple[str, str | None]] = []

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
        template_id = full_id(request_short_template_id or full_template_id.rsplit("::", 1)[-1])
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
        render_calls.append((full_template_id, request_short_template_id))
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [
        (full_id("time_dependent_roc_horizon"), "time_to_event_discrimination_calibration_panel"),
        (full_id("risk_layering_monotonic_bars"), "time_to_event_risk_group_summary"),
    ]
    assert (paper_root / "figures" / "generated" / "F2_time_to_event_discrimination_calibration_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F3_time_to_event_risk_group_summary.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F2"]["template_id"] == full_id("time_to_event_discrimination_calibration_panel")
    assert figures_by_id["F2"]["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert figures_by_id["F2"]["qc_result"]["status"] == "pass"
    assert figures_by_id["F2"]["source_renderer"] == "MAS/DisplayPack::time_to_event_discrimination_calibration_panel"
    assert figures_by_id["F2"]["figure_purpose"] == "time_to_event_discrimination_plus_calibration_summary"
    assert figures_by_id["F2"]["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"
    assert figures_by_id["F3"]["template_id"] == full_id("time_to_event_risk_group_summary")
    assert figures_by_id["F3"]["input_schema_id"] == "time_to_event_grouped_inputs_v1"
    assert figures_by_id["F3"]["qc_result"]["status"] == "pass"
    assert figures_by_id["F3"]["source_renderer"] == "MAS/DisplayPack::time_to_event_risk_group_summary"
    assert figures_by_id["F3"]["figure_purpose"] == "time_to_event_risk_group_gradient_plus_event_counts"
    assert figures_by_id["F3"]["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"
