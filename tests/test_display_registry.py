from __future__ import annotations

from med_autoscience import display_registry


def test_time_to_event_publication_surface_specs_are_registered() -> None:
    figure2 = display_registry.get_evidence_figure_spec("time_to_event_discrimination_calibration_panel")
    figure3 = display_registry.get_evidence_figure_spec("time_to_event_risk_group_summary")
    figure4 = display_registry.get_evidence_figure_spec("time_to_event_decision_curve")
    figure5 = display_registry.get_evidence_figure_spec("multicenter_generalizability_overview")
    table2 = display_registry.get_table_shell_spec("table2_time_to_event_performance_summary")
    table3 = display_registry.get_table_shell_spec("table3_clinical_interpretation_summary")

    assert figure2.renderer_family == "python"
    assert figure2.required_exports == ("png", "pdf")
    assert figure3.input_schema_id == "time_to_event_grouped_inputs_v1"
    assert figure4.layout_qc_profile == "publication_decision_curve"
    assert figure5.allowed_paper_roles == ("main_text", "supplementary")
    assert table2.required_exports == ("md",)
    assert table3.input_schema_id == "clinical_interpretation_summary_v1"
