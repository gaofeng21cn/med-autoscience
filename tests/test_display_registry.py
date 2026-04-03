from __future__ import annotations

import importlib

import pytest


def test_registry_exposes_phase2_time_to_event_and_generalizability_surface() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    evidence_specs = module.list_evidence_figure_specs()
    illustration_specs = module.list_illustration_shell_specs()
    table_specs = module.list_table_shell_specs()

    assert {item.template_id for item in evidence_specs} >= {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "kaplan_meier_grouped",
        "cumulative_incidence_grouped",
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "heatmap_group_comparison",
        "correlation_heatmap",
        "forest_effect_main",
        "shap_summary_beeswarm",
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
    }
    assert {item.shell_id for item in illustration_specs} == {"cohort_flow_figure"}
    assert {item.shell_id for item in table_specs} >= {
        "table1_baseline_characteristics",
        "table2_time_to_event_performance_summary",
        "table3_clinical_interpretation_summary",
    }


def test_time_to_event_publication_surface_specs_are_registered() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    figure14 = module.get_evidence_figure_spec("time_to_event_discrimination_calibration_panel")
    figure15 = module.get_evidence_figure_spec("time_to_event_risk_group_summary")
    figure16 = module.get_evidence_figure_spec("time_to_event_decision_curve")
    figure17 = module.get_evidence_figure_spec("multicenter_generalizability_overview")
    table2 = module.get_table_shell_spec("table2_time_to_event_performance_summary")
    table3 = module.get_table_shell_spec("table3_clinical_interpretation_summary")

    assert figure14.renderer_family == "python"
    assert figure14.input_schema_id == "time_to_event_discrimination_calibration_inputs_v1"
    assert figure15.input_schema_id == "time_to_event_grouped_inputs_v1"
    assert figure16.layout_qc_profile == "publication_decision_curve"
    assert figure17.evidence_class == "generalizability"
    assert table2.required_exports == ("md",)
    assert table3.input_schema_id == "clinical_interpretation_summary_v1"


def test_resolve_display_registry_rejects_unknown_template() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    with pytest.raises(ValueError, match="unknown evidence figure template"):
        module.get_evidence_figure_spec("unknown_template")
